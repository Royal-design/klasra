from collections.abc import Generator
from datetime import datetime, timedelta, timezone
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
        max_upload_bytes=1024 * 1024,
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

        teacher_id = client.post(
            f"/api/v1/schools/{school_a}/users",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "email": "teacher@alpha.example.com",
                "full_name": "Mr. Bello",
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
            json={"name": "Year 9", "display_order": 9},
        ).json()["id"]
        group_id = client.post(
            f"/api/v1/schools/{school_a}/class-groups",
            headers={"X-CSRF-Token": csrf_a},
            json={"academic_year_id": year_id, "year_level_id": level_id, "name": "Year 9 Blue"},
        ).json()["id"]
        subject_id = client.post(
            f"/api/v1/schools/{school_a}/subjects",
            headers={"X-CSRF-Token": csrf_a},
            json={"code": "ENG", "name": "English"},
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

        yield client, {"offering_id": offering_id}

    Base.metadata.drop_all(engine)
    engine.dispose()


def _login(client: TestClient, email: str) -> str:
    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "ValidPassword123!"},
    )
    assert r.status_code == 200, r.text
    return r.json()["csrf_token"]


def test_assignments_submissions_resubmission_history_and_privacy(
    env: tuple[TestClient, dict],
) -> None:
    client, ctx = env
    offering_id = ctx["offering_id"]

    t_csrf = _login(client, "teacher@alpha.example.com")

    # 1. Assignment allowing resubmissions
    future_due = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    a1 = client.post(
        f"/api/v1/offerings/{offering_id}/assignments",
        headers={"X-CSRF-Token": t_csrf},
        json={
            "title": "Essay 1",
            "instructions": "Write 300 words.",
            "due_at": future_due,
            "allow_late_submissions": True,
            "allow_resubmissions": True,
            "status": "published",
        },
    )
    assert a1.status_code == 201
    a1_id = a1.json()["id"]

    # 2. Assignment blocking late submissions and resubmissions
    past_due = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    a2 = client.post(
        f"/api/v1/offerings/{offering_id}/assignments",
        headers={"X-CSRF-Token": t_csrf},
        json={
            "title": "Strict Quiz",
            "instructions": "No late work.",
            "due_at": past_due,
            "allow_late_submissions": False,
            "allow_resubmissions": False,
            "status": "published",
        },
    )
    assert a2.status_code == 201
    a2_id = a2.json()["id"]

    # Student 1 submits v1 (text + PDF) to Essay 1
    s1_csrf = _login(client, "s1@alpha.example.com")
    v1 = client.post(
        f"/api/v1/assignments/{a1_id}/submissions",
        headers={"X-CSRF-Token": s1_csrf},
        data={"text_content": "First draft essay"},
        files=[("files", ("essay_v1.pdf", b"%PDF-1.4\nDraft 1", "application/pdf"))],
    )
    assert v1.status_code == 201, v1.text
    assert v1.json()["version_number"] == 1
    assert v1.json()["is_latest"] is True
    assert v1.json()["is_late"] is False
    v1_file_id = v1.json()["attachments"][0]["id"]

    # Student 1 resubmits v2 -> history preserved, v2 is_latest=True
    v2 = client.post(
        f"/api/v1/assignments/{a1_id}/submissions",
        headers={"X-CSRF-Token": s1_csrf},
        data={"text_content": "Improved final essay"},
    )
    assert v2.status_code == 201
    assert v2.json()["version_number"] == 2
    assert v2.json()["is_latest"] is True

    # Student 1 sees both versions in their history
    s1_history = client.get(f"/api/v1/assignments/{a1_id}/submissions").json()
    assert s1_history["meta"]["total"] == 2
    versions = {row["version_number"]: row["is_latest"] for row in s1_history["items"]}
    assert versions == {1: False, 2: True}

    # Student 1 blocked from submitting late to Strict Quiz -> 409 LATE_SUBMISSION_NOT_ALLOWED
    late_err = client.post(
        f"/api/v1/assignments/{a2_id}/submissions",
        headers={"X-CSRF-Token": s1_csrf},
        data={"text_content": "Too late"},
    )
    assert late_err.status_code == 409
    assert late_err.json()["error"]["code"] == "LATE_SUBMISSION_NOT_ALLOWED"

    # Student 2 cannot see Student 1's submissions or download Student 1's submission PDF!
    _login(client, "s2@alpha.example.com")
    s2_list = client.get(f"/api/v1/assignments/{a1_id}/submissions").json()
    assert s2_list["meta"]["total"] == 0
    assert client.get(f"/api/v1/files/{v1_file_id}/download").status_code == 403

    # Assigned teacher sees all submissions and CAN download Student 1's PDF
    _login(client, "teacher@alpha.example.com")
    t_list = client.get(
        f"/api/v1/assignments/{a1_id}/submissions", params={"latest_only": True}
    ).json()
    assert t_list["meta"]["total"] == 1
    assert t_list["items"][0]["version_number"] == 2
    assert t_list["items"][0]["student_full_name"] == "Student One"
    assert client.get(f"/api/v1/files/{v1_file_id}/download").status_code == 200
