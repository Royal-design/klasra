from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.user import User


@pytest.fixture()
def env(tmp_path: Path) -> Generator[tuple[TestClient, dict], None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    settings = Settings(
        app_env="test",
        database_url="sqlite+pysqlite:///:memory:",
        cors_origins="http://localhost:3000",
        cookie_secure=False,
        rate_limit_per_minute=500,
        login_rate_limit_per_minute=100,
        upload_storage_dir=str(tmp_path / "uploads"),
        max_upload_bytes=1024,  # 1 KB limit in test for size check
    )
    app = create_app(settings=settings)

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
        p_csrf = client.post(
            "/api/v1/auth/login",
            json={"email": "platform@lms.example.com", "password": "PlatformSecret123!"},
        ).json()["csrf_token"]

        school_a = client.post(
            "/api/v1/schools",
            headers={"X-CSRF-Token": p_csrf},
            json={
                "name": "Alpha Secondary",
                "slug": "alpha",
                "initial_admin": {
                    "email": "admin@alpha.example.com",
                    "full_name": "Alpha Admin",
                    "password": "SchoolAdminPass123!",
                },
            },
        ).json()["school"]["id"]

        csrf_a = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@alpha.example.com", "password": "SchoolAdminPass123!"},
        ).json()["csrf_token"]

        # Create assigned teacher, unassigned teacher, enrolled student, unenrolled student
        t_assigned = client.post(
            f"/api/v1/schools/{school_a}/users",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "email": "t.assigned@alpha.example.com",
                "full_name": "Assigned Teacher",
                "password": "ValidPassword123!",
                "role": "teacher",
            },
        ).json()["user_id"]
        client.post(
            f"/api/v1/schools/{school_a}/users",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "email": "t.other@alpha.example.com",
                "full_name": "Other Teacher",
                "password": "ValidPassword123!",
                "role": "teacher",
            },
        )
        s_enrolled = client.post(
            f"/api/v1/schools/{school_a}/users",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "email": "s.enrolled@alpha.example.com",
                "full_name": "Enrolled Student",
                "password": "ValidPassword123!",
                "role": "student",
            },
        ).json()["user_id"]
        client.post(
            f"/api/v1/schools/{school_a}/users",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "email": "s.other@alpha.example.com",
                "full_name": "Unenrolled Student",
                "password": "ValidPassword123!",
                "role": "student",
            },
        )

        # Academic structure + offering + enrollment
        year_id = client.post(
            f"/api/v1/schools/{school_a}/academic-years",
            headers={"X-CSRF-Token": csrf_a},
            json={"name": "2026-2027", "start_date": "2026-09-01", "end_date": "2027-07-15"},
        ).json()["id"]
        level_id = client.post(
            f"/api/v1/schools/{school_a}/year-levels",
            headers={"X-CSRF-Token": csrf_a},
            json={"name": "Year 8", "display_order": 8},
        ).json()["id"]
        group_id = client.post(
            f"/api/v1/schools/{school_a}/class-groups",
            headers={"X-CSRF-Token": csrf_a},
            json={"academic_year_id": year_id, "year_level_id": level_id, "name": "Year 8 Blue"},
        ).json()["id"]
        subject_id = client.post(
            f"/api/v1/schools/{school_a}/subjects",
            headers={"X-CSRF-Token": csrf_a},
            json={"code": "MATH", "name": "Mathematics"},
        ).json()["id"]
        offering_id = client.post(
            f"/api/v1/schools/{school_a}/subject-offerings",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "class_group_id": group_id,
                "subject_id": subject_id,
                "teacher_user_ids": [t_assigned],
            },
        ).json()["id"]
        client.post(
            f"/api/v1/schools/{school_a}/enrollments",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "student_user_id": s_enrolled,
                "class_group_id": group_id,
                "effective_from": "2026-09-01",
            },
        )

        yield client, {"offering_id": offering_id, "uploads_dir": tmp_path / "uploads"}

    Base.metadata.drop_all(engine)
    engine.dispose()


def _login(client: TestClient, email: str, password: str = "ValidPassword123!") -> str:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["csrf_token"]


def test_lessons_visibility_and_secure_file_upload_download(
    env: tuple[TestClient, dict],
) -> None:
    client, ctx = env
    offering_id = ctx["offering_id"]

    # Unassigned teacher cannot create or list lessons
    t_other_csrf = _login(client, "t.other@alpha.example.com")
    assert (
        client.post(
            f"/api/v1/offerings/{offering_id}/lessons",
            headers={"X-CSRF-Token": t_other_csrf},
            json={"title": "Unauthorized", "content": "Nope", "status": "published"},
        ).status_code
        == 403
    )
    assert client.get(f"/api/v1/offerings/{offering_id}/lessons").status_code == 403

    # Assigned teacher creates 1 draft + 1 published lesson
    t_csrf = _login(client, "t.assigned@alpha.example.com")
    draft = client.post(
        f"/api/v1/offerings/{offering_id}/lessons",
        headers={"X-CSRF-Token": t_csrf},
        json={"title": "Draft Lesson", "content": "Work in progress", "status": "draft"},
    )
    assert draft.status_code == 201
    draft_id = draft.json()["id"]

    published = client.post(
        f"/api/v1/offerings/{offering_id}/lessons",
        headers={"X-CSRF-Token": t_csrf},
        json={"title": "Algebra Basics", "content": "x + 2 = 5", "status": "published"},
    )
    assert published.status_code == 201
    pub_id = published.json()["id"]
    assert published.json()["author_full_name"] == "Assigned Teacher"

    # Security checks on attachments:
    # 1) Disallowed extension (.exe) -> 415
    assert (
        client.post(
            f"/api/v1/offerings/{offering_id}/lessons/{pub_id}/attachments",
            headers={"X-CSRF-Token": t_csrf},
            files={"file": ("malware.exe", b"MZ...", "application/octet-stream")},
        ).status_code
        == 415
    )
    # 2) Forged PDF magic bytes -> 415
    assert (
        client.post(
            f"/api/v1/offerings/{offering_id}/lessons/{pub_id}/attachments",
            headers={"X-CSRF-Token": t_csrf},
            files={"file": ("fake.pdf", b"not-a-pdf", "application/pdf")},
        ).status_code
        == 415
    )
    # 3) Oversized file (> 1024 bytes test limit) -> 413
    assert (
        client.post(
            f"/api/v1/offerings/{offering_id}/lessons/{pub_id}/attachments",
            headers={"X-CSRF-Token": t_csrf},
            files={"file": ("big.pdf", b"%PDF-" + b"a" * 2000, "application/pdf")},
        ).status_code
        == 413
    )

    # 4) Valid PDF upload with path-traversal filename sanitized & saved under UUID
    pdf_bytes = b"%PDF-1.4\n%Test lesson notes"
    att_resp = client.post(
        f"/api/v1/offerings/{offering_id}/lessons/{pub_id}/attachments",
        headers={"X-CSRF-Token": t_csrf},
        files={"file": ("../../algebra_notes.pdf", pdf_bytes, "application/pdf")},
    )
    assert att_resp.status_code == 201
    file_id = att_resp.json()["id"]
    assert att_resp.json()["original_filename"] == "algebra_notes.pdf"

    # Attach a file to the draft lesson too (enrolled student must NOT download it)
    draft_att = client.post(
        f"/api/v1/offerings/{offering_id}/lessons/{draft_id}/attachments",
        headers={"X-CSRF-Token": t_csrf},
        files={"file": ("draft.txt", b"secret draft", "text/plain")},
    ).json()["id"]

    # Enrolled student sees ONLY published lessons (1 of 2), can download published attachment, blocked from draft attachment
    _login(client, "s.enrolled@alpha.example.com")
    student_lessons = client.get(f"/api/v1/offerings/{offering_id}/lessons").json()
    assert student_lessons["meta"]["total"] == 1
    assert student_lessons["items"][0]["title"] == "Algebra Basics"
    assert len(student_lessons["items"][0]["attachments"]) == 1

    dl = client.get(f"/api/v1/files/{file_id}/download")
    assert dl.status_code == 200
    assert dl.content == pdf_bytes
    assert "attachment" in dl.headers["content-disposition"]
    assert dl.headers["x-content-type-options"] == "nosniff"

    assert client.get(f"/api/v1/files/{draft_att}/download").status_code == 403

    # Unenrolled student cannot list lessons or download file -> 403
    _login(client, "s.other@alpha.example.com")
    assert client.get(f"/api/v1/offerings/{offering_id}/lessons").status_code == 403
    assert client.get(f"/api/v1/files/{file_id}/download").status_code == 403
