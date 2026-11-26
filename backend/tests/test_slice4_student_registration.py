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
from app.models.registration import StudentInvite
from app.models.user import User
from app.services.email import InMemoryEmailProvider


def _make_settings() -> Settings:
    return Settings(
        app_env="test",
        database_url="sqlite+pysqlite:///:memory:",
        cors_origins="http://localhost:3000",
        cookie_secure=False,
        rate_limit_per_minute=500,
        login_rate_limit_per_minute=100,
        frontend_base_url="http://localhost:3000",
    )


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
    app = create_app(settings=_make_settings(), email_provider=email_provider)

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

        school_b = client.post(
            "/api/v1/schools",
            headers={"X-CSRF-Token": p_csrf},
            json={
                "name": "Beta Secondary",
                "slug": "beta",
                "initial_admin": {
                    "email": "admin@beta.example.com",
                    "full_name": "Beta Admin",
                    "password": "SchoolAdminPass123!",
                },
            },
        ).json()["school"]["id"]

        yield client, SessionLocal, email_provider, {"school_a": school_a, "school_b": school_b}

    Base.metadata.drop_all(engine)
    engine.dispose()


def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["csrf_token"]


def _extract_invite_token(email_text: str) -> str:
    for part in email_text.split():
        if "register/student?token=" in part:
            parsed = urlparse(part)
            return parse_qs(parsed.query)["token"][0]
    raise AssertionError("Invite token URL not found in email body")


def test_student_registration_code_pending_and_admin_approval(
    env: tuple[TestClient, sessionmaker[Session], InMemoryEmailProvider, dict],
) -> None:
    client, session_local, email_provider, ctx = env
    school_a = ctx["school_a"]
    school_b = ctx["school_b"]

    csrf_a = _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")

    # Set up a class group for enrollment upon approval
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

    # Create a single-use registration code
    code_resp = client.post(
        f"/api/v1/schools/{school_a}/registrations/codes",
        headers={"X-CSRF-Token": csrf_a},
        json={"label": "Year 8 Intake", "max_uses": 1, "expires_in_hours": 24},
    )
    assert code_resp.status_code == 201
    raw_code = code_resp.json()["code"]

    # Confirm raw code is NOT stored in DB
    with session_local() as db:
        invite_row = db.scalar(select(StudentInvite))
        assert invite_row is not None
        assert invite_row.token_hash != raw_code

    # Student self-registers using the code
    reg_resp = client.post(
        "/api/v1/registrations/students",
        json={
            "email": "student1@alpha.example.com",
            "full_name": "Tunde Adeyemi",
            "password": "StudentPassword123!",
            "code_or_token": raw_code,
            "student_reference": "ADM-2026-001",
        },
    )
    assert reg_resp.status_code == 201, reg_resp.text
    request_id = reg_resp.json()["id"]
    assert reg_resp.json()["status"] == "pending"

    # Reusing exhausted code fails with 410 Gone
    exhausted = client.post(
        "/api/v1/registrations/students",
        json={
            "email": "student2@alpha.example.com",
            "full_name": "Second Student",
            "password": "StudentPassword123!",
            "code_or_token": raw_code,
        },
    )
    assert exhausted.status_code == 410
    assert exhausted.json()["error"]["code"] == "TOKEN_INVALID_OR_EXPIRED"

    # Pending student logs in -> sees pending membership, blocked from school routes (403 MEMBERSHIP_PENDING)
    _login(client, "student1@alpha.example.com", "StudentPassword123!")
    me = client.get("/api/v1/auth/me").json()
    assert me["memberships"][0]["role"] == "student"
    assert me["memberships"][0]["status"] == "pending"
    blocked = client.get(f"/api/v1/schools/{school_a}/academic-years")
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "MEMBERSHIP_PENDING"

    # School B Admin cannot view or approve School A's request
    csrf_b = _login(client, "admin@beta.example.com", "SchoolAdminPass123!")
    assert client.get(f"/api/v1/schools/{school_a}/registrations/students").status_code == 403
    assert (
        client.post(
            f"/api/v1/schools/{school_b}/registrations/students/{request_id}/approve",
            headers={"X-CSRF-Token": csrf_b},
            json={},
        ).status_code
        == 404
    )

    # School A Admin lists and approves + enrolls student
    csrf_a = _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")
    pending_list = client.get(
        f"/api/v1/schools/{school_a}/registrations/students",
        params={"status": "pending"},
    ).json()
    assert len(pending_list["items"]) == 1
    assert pending_list["meta"]["total"] == 1

    approved = client.post(
        f"/api/v1/schools/{school_a}/registrations/students/{request_id}/approve",
        headers={"X-CSRF-Token": csrf_a},
        json={"class_group_id": group_id, "decision_notes": "Verified against admission list"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert len(email_provider.sent) == 1
    assert "approved" in email_provider.sent[0].subject.lower()

    # Double-approve fails with 409
    again = client.post(
        f"/api/v1/schools/{school_a}/registrations/students/{request_id}/approve",
        headers={"X-CSRF-Token": csrf_a},
        json={},
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "INVALID_STATE_TRANSITION"

    # Enrollment was created
    enrollments = client.get(
        f"/api/v1/schools/{school_a}/enrollments",
        params={"class_group_id": group_id},
    ).json()
    assert len(enrollments["items"]) == 1
    assert enrollments["meta"]["total"] == 1

    with session_local() as db:
        actions = set(db.scalars(select(AuditEvent.action)).all())
    assert {
        "student_registration_code.created",
        "student_registration.submitted",
        "student_registration.approved",
    } <= actions


def test_student_email_invitation_mismatch_and_rejection(
    env: tuple[TestClient, sessionmaker[Session], InMemoryEmailProvider, dict],
) -> None:
    client, _session_local, email_provider, ctx = env
    school_a = ctx["school_a"]

    csrf_a = _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")

    invite_resp = client.post(
        f"/api/v1/schools/{school_a}/registrations/invitations",
        headers={"X-CSRF-Token": csrf_a},
        json={"email": "invited@alpha.example.com", "label": "Transfer Student"},
    )
    assert invite_resp.status_code == 201
    assert len(email_provider.sent) == 1
    raw_token = _extract_invite_token(email_provider.sent[0].text)

    # Different email cannot claim the invitation
    mismatch = client.post(
        "/api/v1/registrations/students",
        json={
            "email": "someoneelse@alpha.example.com",
            "full_name": "Wrong Person",
            "password": "StudentPassword123!",
            "code_or_token": raw_token,
        },
    )
    assert mismatch.status_code == 403
    assert mismatch.json()["error"]["code"] == "INVITATION_EMAIL_MISMATCH"

    # Correct email registers as pending
    reg = client.post(
        "/api/v1/registrations/students",
        json={
            "email": "invited@alpha.example.com",
            "full_name": "Ngozi Eze",
            "password": "StudentPassword123!",
            "code_or_token": raw_token,
        },
    )
    assert reg.status_code == 201
    request_id = reg.json()["id"]

    # Student signs in before rejection
    _login(client, "invited@alpha.example.com", "StudentPassword123!")
    student_cookie = client.cookies.get("lms_session")
    assert student_cookie is not None

    # School Admin rejects request -> membership revoked + session invalidated + email sent
    csrf_a = _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")
    rejected = client.post(
        f"/api/v1/schools/{school_a}/registrations/students/{request_id}/reject",
        headers={"X-CSRF-Token": csrf_a},
        json={"decision_notes": "Duplicate application"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert len(email_provider.sent) == 2

    client.cookies.set("lms_session", student_cookie)
    assert client.get("/api/v1/auth/me").status_code == 401
