from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.user import User
from app.services.file_storage import InMemoryStorageBackend, save_uploaded_file


class _HealthySession:
    def execute(self, _statement: object) -> None:
        return None


def test_production_requires_secure_cookies() -> None:
    with pytest.raises(ValueError, match="COOKIE_SECURE"):
        Settings(
            _env_file=None,
            app_env="production",
            database_url="postgresql+psycopg://u:p@127.0.0.1:5432/lms",
            cookie_secure=False,
        )


def test_s3_storage_requires_bucket_and_keys() -> None:
    with pytest.raises(ValueError, match="S3_BUCKET"):
        Settings(
            _env_file=None,
            app_env="test",
            database_url="sqlite+pysqlite:///:memory:",
            storage_provider="s3",
        )


def test_request_id_header_and_separate_video_upload_limits() -> None:
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url="sqlite+pysqlite:///:memory:",
        cookie_secure=False,
        max_upload_bytes=1024,
        max_video_upload_bytes=4096,
    )
    backend = InMemoryStorageBackend()

    # Document within 1 KB limit succeeds
    saved_doc = save_uploaded_file(
        storage_backend=backend,
        raw_filename="notes.txt",
        content=b"hello world",
        max_bytes=settings.max_upload_bytes,
    )
    assert backend.get_bytes(storage_key=saved_doc.storage_key) == b"hello world"

    # Valid MP4 (2 KB > 1 KB doc limit, <= 4 KB video limit) succeeds when allow_video=True
    valid_mp4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 2048
    saved_vid = save_uploaded_file(
        storage_backend=backend,
        raw_filename="lecture.mp4",
        content=valid_mp4,
        max_bytes=settings.max_upload_bytes,
        allow_video=True,
        max_video_bytes=settings.max_video_upload_bytes,
    )
    assert saved_vid.content_type == "video/mp4"
    assert len(backend.get_bytes(storage_key=saved_vid.storage_key)) == len(valid_mp4)

    # Video rejected when allow_video=False (e.g., student submissions)
    with pytest.raises(AppError) as exc_info:
        save_uploaded_file(
            storage_backend=backend,
            raw_filename="lecture.mp4",
            content=valid_mp4,
            max_bytes=settings.max_upload_bytes,
            allow_video=False,
        )
    assert exc_info.value.status_code == 415

    # Fake MP4 magic bytes rejected
    with pytest.raises(AppError) as bad_magic:
        save_uploaded_file(
            storage_backend=backend,
            raw_filename="malware.mp4",
            content=b"MZ\x90\x00not-an-mp4-file",
            max_bytes=settings.max_upload_bytes,
            allow_video=True,
            max_video_bytes=settings.max_video_upload_bytes,
        )
    assert bad_magic.value.status_code == 415

    # Oversized video (> 4 KB) rejected with 413
    with pytest.raises(AppError) as too_large:
        save_uploaded_file(
            storage_backend=backend,
            raw_filename="huge.mp4",
            content=b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 5000,
            max_bytes=settings.max_upload_bytes,
            allow_video=True,
            max_video_bytes=settings.max_video_upload_bytes,
        )
    assert too_large.value.status_code == 413

    app = create_app(settings=settings, storage_backend=backend)

    def override_get_db() -> Generator[_HealthySession, None, None]:
        yield _HealthySession()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert "x-request-id" in resp.headers
    assert len(resp.headers["x-request-id"]) == 32


def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["csrf_token"]


def test_lesson_video_url_and_presigned_upload_playback_flow() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url="sqlite+pysqlite:///:memory:",
        cookie_secure=False,
        rate_limit_per_minute=500,
        login_rate_limit_per_minute=100,
        max_upload_bytes=1024,
        max_video_upload_bytes=10 * 1024,
        presigned_url_ttl_seconds=300,
    )
    backend = InMemoryStorageBackend()
    app = create_app(settings=settings, storage_backend=backend)

    def override_get_db() -> Generator[Session, None, None]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with SessionLocal() as db:
        db.add(
            User(
                email="platform@lms.example.com",
                full_name="Platform Admin",
                password_hash=hash_password("PlatformSecret123!"),
                is_platform_admin=True,
                is_active=True,
            )
        )
        db.commit()

    with TestClient(app) as client:
        # Bootstrap school, academic structure, teacher, enrolled student, outsider student
        p_csrf = _login(client, "platform@lms.example.com", "PlatformSecret123!")
        school_id = client.post(
            "/api/v1/schools",
            headers={"X-CSRF-Token": p_csrf},
            json={
                "name": "Video High",
                "slug": "video-high",
                "initial_admin": {
                    "email": "admin@video.example.com",
                    "full_name": "School Admin",
                    "password": "AdminPassword123!",
                },
            },
        ).json()["school"]["id"]
        a_csrf = _login(client, "admin@video.example.com", "AdminPassword123!")
        year_id = client.post(
            f"/api/v1/schools/{school_id}/academic-years",
            headers={"X-CSRF-Token": a_csrf},
            json={"name": "2026", "start_date": "2026-01-01", "end_date": "2026-12-31"},
        ).json()["id"]
        term_id = client.post(
            f"/api/v1/schools/{school_id}/terms",
            headers={"X-CSRF-Token": a_csrf},
            json={
                "academic_year_id": year_id,
                "name": "Term 1",
                "start_date": "2026-01-01",
                "end_date": "2026-04-30",
            },
        ).json()["id"]
        yl_id = client.post(
            f"/api/v1/schools/{school_id}/year-levels",
            headers={"X-CSRF-Token": a_csrf},
            json={"name": "Grade 10", "sort_order": 1},
        ).json()["id"]
        cg_id = client.post(
            f"/api/v1/schools/{school_id}/class-groups",
            headers={"X-CSRF-Token": a_csrf},
            json={"academic_year_id": year_id, "year_level_id": yl_id, "name": "10A"},
        ).json()["id"]
        subj_id = client.post(
            f"/api/v1/schools/{school_id}/subjects",
            headers={"X-CSRF-Token": a_csrf},
            json={"code": "PHY10", "name": "Physics"},
        ).json()["id"]
        offering_id = client.post(
            f"/api/v1/schools/{school_id}/subject-offerings",
            headers={"X-CSRF-Token": a_csrf},
            json={"class_group_id": cg_id, "subject_id": subj_id, "term_id": term_id},
        ).json()["id"]

        teacher_id = client.post(
            f"/api/v1/schools/{school_id}/users",
            headers={"X-CSRF-Token": a_csrf},
            json={
                "email": "teacher@video.example.com",
                "full_name": "Ms Physics",
                "password": "TeacherPassword123!",
                "role": "teacher",
            },
        ).json()["user_id"]
        client.post(
            f"/api/v1/schools/{school_id}/subject-offerings/{offering_id}/teachers",
            headers={"X-CSRF-Token": a_csrf},
            json={"teacher_user_id": teacher_id},
        )
        student_id = client.post(
            f"/api/v1/schools/{school_id}/users",
            headers={"X-CSRF-Token": a_csrf},
            json={
                "email": "student@video.example.com",
                "full_name": "Enrolled Student",
                "password": "StudentPassword123!",
                "role": "student",
            },
        ).json()["user_id"]
        enroll_resp = client.post(
            f"/api/v1/schools/{school_id}/enrollments",
            headers={"X-CSRF-Token": a_csrf},
            json={
                "student_user_id": student_id,
                "class_group_id": cg_id,
                "effective_from": "2026-01-10",
            },
        )
        assert enroll_resp.status_code == 201, enroll_resp.text
        client.post(
            f"/api/v1/schools/{school_id}/users",
            headers={"X-CSRF-Token": a_csrf},
            json={
                "email": "outsider@video.example.com",
                "full_name": "Unenrolled Student",
                "password": "StudentPassword123!",
                "role": "student",
            },
        )

        # Teacher creates lesson with disallowed video_url -> 422
        t_csrf = _login(client, "teacher@video.example.com", "TeacherPassword123!")
        bad_url_resp = client.post(
            f"/api/v1/offerings/{offering_id}/lessons",
            headers={"X-CSRF-Token": t_csrf},
            json={
                "title": "Bad Video Link",
                "content": "Notes",
                "video_url": "https://evil.example.com/watch?v=1",
            },
        )
        assert bad_url_resp.status_code == 422

        # Teacher creates lesson with valid YouTube HTTPS video_url -> 201
        lesson_resp = client.post(
            f"/api/v1/offerings/{offering_id}/lessons",
            headers={"X-CSRF-Token": t_csrf},
            json={
                "title": "Kinematics Intro",
                "content": "Watch the lecture video.",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "status": "published",
            },
        )
        assert lesson_resp.status_code == 201, lesson_resp.text
        lesson_data = lesson_resp.json()
        assert lesson_data["video_url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        lesson_id = lesson_data["id"]

        # Teacher requests presigned upload URL for a 3 KB .mp4 video (allowed under 10 KB video limit)
        presign_resp = client.post(
            f"/api/v1/offerings/{offering_id}/lessons/{lesson_id}/attachments/presign",
            headers={"X-CSRF-Token": t_csrf},
            json={"filename": "demo.mp4", "size_bytes": 3072},
        )
        assert presign_resp.status_code == 200, presign_resp.text
        presign_data = presign_resp.json()
        assert presign_data["content_type"] == "video/mp4"
        storage_key = presign_data["storage_key"]

        # Simulate browser direct PUT to S3 storage with valid MP4 ftyp header
        mp4_bytes = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 3060
        backend.put_bytes(storage_key=storage_key, content=mp4_bytes, content_type="video/mp4")

        # Teacher completes upload -> 201
        complete_resp = client.post(
            f"/api/v1/offerings/{offering_id}/lessons/{lesson_id}/attachments/complete",
            headers={"X-CSRF-Token": t_csrf},
            json={"storage_key": storage_key, "original_filename": "demo.mp4"},
        )
        assert complete_resp.status_code == 201, complete_resp.text
        file_id = complete_resp.json()["id"]

        # Enrolled student fetches signed playback URL (inline=true) -> 200
        _login(client, "student@video.example.com", "StudentPassword123!")
        play_resp = client.get(f"/api/v1/files/{file_id}/download-url?inline=true")
        assert play_resp.status_code == 200, play_resp.text
        play_data = play_resp.json()
        assert play_data["mode"] == "presigned"
        assert play_data["content_type"] == "video/mp4"
        assert "disposition=inline" in play_data["url"]

        # Unenrolled student gets 403
        _login(client, "outsider@video.example.com", "StudentPassword123!")
        denied_resp = client.get(f"/api/v1/files/{file_id}/download-url?inline=true")
        assert denied_resp.status_code == 403


def test_schema_input_normalization_consistency() -> None:
    import uuid

    from app.schemas.academic import SubjectCreateRequest
    from app.schemas.attendance import AttendanceEntryInput
    from app.schemas.grade import GradeUpsertRequest
    from app.schemas.guardian import GuardianInviteCreateRequest
    from app.schemas.lesson import LessonCreateRequest
    from app.schemas.membership import SchoolUserCreateRequest
    from app.schemas.registration import StudentSelfRegisterRequest

    g = GuardianInviteCreateRequest(
        student_user_id=uuid.uuid4(),
        guardian_email="parent@example.com",
        guardian_full_name="  Ada   O'Brien  ",
        relationship_label="  legal   guardian  ",
    )
    assert g.guardian_full_name == "Ada O'Brien"
    assert g.relationship_label == "Legal Guardian"

    g2 = GuardianInviteCreateRequest(
        student_user_id=uuid.uuid4(),
        guardian_email="parent2@example.com",
        guardian_full_name="Chidi",
        relationship_label="GUARDIAN",
    )
    assert g2.relationship_label == "Guardian"

    subj = SubjectCreateRequest(code="  math101 ", name="  Further   Mathematics ")
    assert subj.code == "MATH101"
    assert subj.name == "Further Mathematics"

    grade = GradeUpsertRequest(score=95, letter_grade=" a+ ")
    assert grade.letter_grade == "A+"
    assert GradeUpsertRequest(score=80, letter_grade="   ").letter_grade is None

    att = AttendanceEntryInput(student_user_id=uuid.uuid4(), status=" Present ")  # type: ignore[arg-type]
    assert att.status == "present"

    member = SchoolUserCreateRequest(
        email="t@example.com",
        full_name="  Jane   McDonald ",
        password="StrongPassword123!",
        role=" Teacher ",  # type: ignore[arg-type]
    )
    assert member.full_name == "Jane McDonald"
    assert member.role == "teacher"

    lesson = LessonCreateRequest(title="Intro", content="Body", status=" DRAFT ")  # type: ignore[arg-type]
    assert lesson.status == "draft"

    reg = StudentSelfRegisterRequest(
        email="s@example.com",
        full_name="  Kemi   Ade ",
        password="StrongPassword123!",
        code_or_token="ABCDEF1234",
        student_reference="  jss1-042 ",
    )
    assert reg.full_name == "Kemi Ade"
    assert reg.student_reference == "JSS1-042"
