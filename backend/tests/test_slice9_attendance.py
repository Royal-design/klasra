from collections.abc import Generator
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
def env() -> Generator[
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
                "full_name": "Mr. Musa",
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
                "full_name": "Unenrolled Student",
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
            json={"name": "Year 11", "display_order": 11},
        ).json()["id"]
        group_id = client.post(
            f"/api/v1/schools/{school_a}/class-groups",
            headers={"X-CSRF-Token": csrf_a},
            json={"academic_year_id": year_id, "year_level_id": level_id, "name": "Year 11A"},
        ).json()["id"]
        subject_id = client.post(
            f"/api/v1/schools/{school_a}/subjects",
            headers={"X-CSRF-Token": csrf_a},
            json={"code": "PHY", "name": "Physics"},
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
        # Only enroll student1
        client.post(
            f"/api/v1/schools/{school_a}/enrollments",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "student_user_id": student1_id,
                "class_group_id": group_id,
                "effective_from": "2026-09-01",
            },
        )

        # Link and approve Parent 1 for Student 1
        link_id = client.post(
            f"/api/v1/schools/{school_a}/guardian-links/invite",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "student_user_id": student1_id,
                "guardian_email": "parent1@family.example.com",
                "guardian_full_name": "Parent One",
                "relationship_label": "Father",
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
                "offering_id": offering_id,
                "student1_id": student1_id,
                "student2_id": student2_id,
            },
        )

    Base.metadata.drop_all(engine)
    engine.dispose()


def _login(client: TestClient, email: str, password: str = "ValidPassword123!") -> str:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["csrf_token"]


def test_attendance_recording_attribution_and_views(
    env: tuple[TestClient, sessionmaker[Session], InMemoryEmailProvider, dict],
) -> None:
    client, session_local, _email_provider, ctx = env
    offering_id = ctx["offering_id"]
    student1_id = ctx["student1_id"]
    student2_id = ctx["student2_id"]

    t_csrf = _login(client, "teacher@alpha.example.com")

    # Reject recording attendance for unenrolled student -> 422
    bad_batch = client.put(
        f"/api/v1/offerings/{offering_id}/attendance",
        headers={"X-CSRF-Token": t_csrf},
        json={
            "attendance_date": "2026-11-26",
            "entries": [{"student_user_id": student2_id, "status": "present"}],
        },
    )
    assert bad_batch.status_code == 422
    assert bad_batch.json()["error"]["code"] == "STUDENT_NOT_ENROLLED"

    # Record initial attendance -> present
    rec1 = client.put(
        f"/api/v1/offerings/{offering_id}/attendance",
        headers={"X-CSRF-Token": t_csrf},
        json={
            "attendance_date": "2026-11-26",
            "entries": [
                {"student_user_id": student1_id, "status": "present", "notes": "On time"}
            ],
        },
    )
    assert rec1.status_code == 200
    assert rec1.json()[0]["status"] == "present"
    assert rec1.json()[0]["recorded_by_full_name"] == "Mr. Musa"

    # Update attendance -> late (audit trail records previous & new status)
    rec2 = client.put(
        f"/api/v1/offerings/{offering_id}/attendance",
        headers={"X-CSRF-Token": t_csrf},
        json={
            "attendance_date": "2026-11-26",
            "entries": [
                {"student_user_id": student1_id, "status": "late", "notes": "Arrived 10m late"}
            ],
        },
    )
    assert rec2.status_code == 200
    assert rec2.json()[0]["status"] == "late"
    assert rec2.json()[0]["updated_by_full_name"] == "Mr. Musa"

    # School Admin can view offering attendance
    _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")
    admin_view = client.get(f"/api/v1/offerings/{offering_id}/attendance").json()
    assert admin_view["meta"]["total"] == 1
    assert admin_view["items"][0]["subject_name"] == "Physics"

    # Student 1 views own attendance (PROG-01); Student 2 sees none
    _login(client, "s1@alpha.example.com")
    s1_att = client.get("/api/v1/students/me/attendance").json()
    assert s1_att["meta"]["total"] == 1
    assert s1_att["items"][0]["status"] == "late"

    _login(client, "s2@alpha.example.com")
    assert client.get("/api/v1/students/me/attendance").json()["meta"]["total"] == 0

    # Approved Parent 1 views Student 1's attendance (PROG-02); blocked from Student 2 (403)
    _login(client, "parent1@family.example.com")
    p1_att = client.get(f"/api/v1/parent/children/{student1_id}/attendance").json()
    assert p1_att["meta"]["total"] == 1
    assert p1_att["items"][0]["status"] == "late"
    assert client.get(f"/api/v1/parent/children/{student2_id}/attendance").status_code == 403

    with session_local() as db:
        actions = set(db.scalars(select(AuditEvent.action)).all())
    assert {"attendance.recorded", "attendance.updated"} <= actions
