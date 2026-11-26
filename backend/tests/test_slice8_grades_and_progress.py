from collections.abc import Generator
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.audit import AuditEvent
from app.models.user import User
from app.services.email import InMemoryEmailProvider


@pytest.fixture()
def env(tmp_path: Path) -> Generator[
    tuple[TestClient, sessionmaker[Session], InMemoryEmailProvider, dict], None, None
]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    email_provider = InMemoryEmailProvider()
    settings = Settings(
        app_env="test",
        database_url="sqlite+pysqlite:///:memory:",
        cors_origins="http://localhost:3000",
        cookie_secure=False,
        rate_limit_per_minute=500,
        login_rate_limit_per_minute=100,
        upload_storage_dir=str(tmp_path / "uploads"),
    )
    app = create_app(settings=settings, email_provider=email_provider)

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

        teacher_id = client.post(
            f"/api/v1/schools/{school_a}/users",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "email": "teacher@alpha.example.com",
                "full_name": "Ms. Ada",
                "password": "ValidPassword123!",
                "role": "teacher",
            },
        ).json()["user_id"]
        student1_id = client.post(
            f"/api/v1/schools/{school_a}/users",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "email": "s1@alpha.example.com",
                "full_name": "Student One",
                "password": "ValidPassword123!",
                "role": "student",
            },
        ).json()["user_id"]
        student2_id = client.post(
            f"/api/v1/schools/{school_a}/users",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "email": "s2@alpha.example.com",
                "full_name": "Student Two",
                "password": "ValidPassword123!",
                "role": "student",
            },
        ).json()["user_id"]

        year_id = client.post(
            f"/api/v1/schools/{school_a}/academic-years",
            headers={"X-CSRF-Token": csrf_a},
            json={"name": "2026-2027", "start_date": "2026-09-01", "end_date": "2027-07-15"},
        ).json()["id"]
        level_id = client.post(
            f"/api/v1/schools/{school_a}/year-levels",
            headers={"X-CSRF-Token": csrf_a},
            json={"name": "Year 10", "display_order": 10},
        ).json()["id"]
        group_id = client.post(
            f"/api/v1/schools/{school_a}/class-groups",
            headers={"X-CSRF-Token": csrf_a},
            json={"academic_year_id": year_id, "year_level_id": level_id, "name": "Year 10A"},
        ).json()["id"]
        subject_id = client.post(
            f"/api/v1/schools/{school_a}/subjects",
            headers={"X-CSRF-Token": csrf_a},
            json={"code": "BIO", "name": "Biology"},
        ).json()["id"]
        offering_id = client.post(
            f"/api/v1/schools/{school_a}/subject-offerings",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "class_group_id": group_id,
                "subject_id": subject_id,
                "teacher_user_ids": [teacher_id],
            },
        ).json()["id"]
        for sid in (student1_id, student2_id):
            client.post(
                f"/api/v1/schools/{school_a}/enrollments",
                headers={"X-CSRF-Token": csrf_a},
                json={
                    "student_user_id": sid,
                    "class_group_id": group_id,
                    "effective_from": "2026-09-01",
                },
            )

        # Invite, verify, and approve Parent 1 for Student 1 ONLY
        link_id = client.post(
            f"/api/v1/schools/{school_a}/guardian-links/invite",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "student_user_id": student1_id,
                "guardian_email": "parent1@family.example.com",
                "guardian_full_name": "Parent One",
                "relationship_label": "Mother",
            },
        ).json()["id"]
        token = None
        for part in email_provider.sent[-1].text.split():
            if "parent/verify?token=" in part:
                token = parse_qs(urlparse(part).query)["token"][0]
        assert token is not None
        client.post(
            "/api/v1/guardian-links/verify",
            json={"token": token, "password": "ValidPassword123!"},
        )
        client.post(
            f"/api/v1/schools/{school_a}/guardian-links/{link_id}/approve",
            headers={"X-CSRF-Token": csrf_a},
            json={},
        )

        yield (
            client,
            SessionLocal,
            email_provider,
            {
                "school_a": school_a,
                "offering_id": offering_id,
                "student1_id": student1_id,
                "student2_id": student2_id,
            },
        )

    Base.metadata.drop_all(engine)
    engine.dispose()


def _login(client: TestClient, email: str) -> str:
    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "ValidPassword123!"},
    )
    assert r.status_code == 200, r.text
    return r.json()["csrf_token"]


def test_grading_publish_visibility_and_student_parent_scoping(
    env: tuple[TestClient, sessionmaker[Session], InMemoryEmailProvider, dict],
) -> None:
    client, session_local, _email_provider, ctx = env
    offering_id = ctx["offering_id"]
    student1_id = ctx["student1_id"]
    student2_id = ctx["student2_id"]

    # Teacher creates assignment (max_score=50)
    t_csrf = _login(client, "teacher@alpha.example.com")
    assignment_id = client.post(
        f"/api/v1/offerings/{offering_id}/assignments",
        headers={"X-CSRF-Token": t_csrf},
        json={
            "title": "Cell Structure Lab",
            "instructions": "Explain mitochondria.",
            "max_score": 50,
            "status": "published",
        },
    ).json()["id"]

    # Student 1 submits
    s1_csrf = _login(client, "s1@alpha.example.com")
    sub_id = client.post(
        f"/api/v1/assignments/{assignment_id}/submissions",
        headers={"X-CSRF-Token": s1_csrf},
        data={"text_content": "Mitochondria produce ATP."},
    ).json()["id"]

    # Teacher tries score > max_score -> 422 SCORE_EXCEEDS_MAX
    t_csrf = _login(client, "teacher@alpha.example.com")
    too_high = client.put(
        f"/api/v1/submissions/{sub_id}/grade",
        headers={"X-CSRF-Token": t_csrf},
        json={"score": 60, "feedback": "Too high", "is_published": True},
    )
    assert too_high.status_code == 422
    assert too_high.json()["error"]["code"] == "SCORE_EXCEEDS_MAX"

    # Teacher saves DRAFT grade (is_published=False) -> hidden from student & parent
    draft_grade = client.put(
        f"/api/v1/submissions/{sub_id}/grade",
        headers={"X-CSRF-Token": t_csrf},
        json={"score": 45, "letter_grade": "A", "feedback": "Great work!", "is_published": False},
    )
    assert draft_grade.status_code == 200
    assert draft_grade.json()["is_published"] is False

    _login(client, "s1@alpha.example.com")
    assert client.get("/api/v1/students/me/grades").json()["meta"]["total"] == 0

    _login(client, "parent1@family.example.com")
    assert client.get(f"/api/v1/parent/children/{student1_id}/grades").json()["meta"]["total"] == 0

    # Teacher publishes grade -> visible to Student 1 and Approved Parent 1 ONLY
    t_csrf = _login(client, "teacher@alpha.example.com")
    pub_grade = client.put(
        f"/api/v1/submissions/{sub_id}/grade",
        headers={"X-CSRF-Token": t_csrf},
        json={"score": 48, "letter_grade": "A+", "feedback": "Excellent detail!", "is_published": True},
    )
    assert pub_grade.status_code == 200
    assert pub_grade.json()["score"] == 48

    # Student 1 sees own grade with enriched fields
    _login(client, "s1@alpha.example.com")
    s1_grades = client.get("/api/v1/students/me/grades").json()
    assert s1_grades["meta"]["total"] == 1
    assert s1_grades["items"][0]["score"] == 48
    assert s1_grades["items"][0]["subject_name"] == "Biology"
    assert s1_grades["items"][0]["graded_by_full_name"] == "Ms. Ada"

    # Student 2 sees ZERO grades (PROG-01)
    _login(client, "s2@alpha.example.com")
    assert client.get("/api/v1/students/me/grades").json()["meta"]["total"] == 0

    # Approved Parent 1 sees Student 1's grade (PROG-02), blocked from Student 2 (403) & lessons (403)
    _login(client, "parent1@family.example.com")
    p1_grades = client.get(f"/api/v1/parent/children/{student1_id}/grades").json()
    assert p1_grades["meta"]["total"] == 1
    assert p1_grades["items"][0]["feedback"] == "Excellent detail!"
    assert client.get(f"/api/v1/parent/children/{student2_id}/grades").status_code == 403
    assert client.get(f"/api/v1/offerings/{offering_id}/lessons").status_code == 403

    with session_local() as db:
        actions = set(db.scalars(select(AuditEvent.action)).all())
    assert {"grade.recorded", "grade.updated"} <= actions
