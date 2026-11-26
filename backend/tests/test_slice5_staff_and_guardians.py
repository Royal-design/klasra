import uuid
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
from app.models.guardian import GuardianLink
from app.models.staff_invite import StaffInvitation
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


def _extract_token(email_text: str, path_fragment: str) -> str:
    for part in email_text.split():
        if path_fragment in part:
            parsed = urlparse(part)
            return parse_qs(parsed.query)["token"][0]
    raise AssertionError(f"Token URL containing '{path_fragment}' not found")


def test_staff_teacher_email_invitation_and_single_school_rule(
    env: tuple[TestClient, sessionmaker[Session], InMemoryEmailProvider, dict],
) -> None:
    client, session_local, email_provider, ctx = env
    school_a = ctx["school_a"]
    school_b = ctx["school_b"]

    csrf_a = _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")
    inv_resp = client.post(
        f"/api/v1/schools/{school_a}/staff-invitations",
        headers={"X-CSRF-Token": csrf_a},
        json={
            "email": "newteacher@alpha.example.com",
            "full_name": "Mrs. Kemi",
            "role": "teacher",
        },
    )
    assert inv_resp.status_code == 201
    assert inv_resp.json()["status"] == "pending"
    assert len(email_provider.sent) == 1
    raw_token = _extract_token(email_provider.sent[0].text, "accept-staff-invite?token=")

    # Raw token not stored in DB
    with session_local() as db:
        row = db.scalar(select(StaffInvitation))
        assert row is not None
        assert row.token_hash != raw_token

    # Teacher accepts invitation & sets their own password
    accept_resp = client.post(
        "/api/v1/staff-invitations/accept",
        json={"token": raw_token, "password": "TeacherChosenPass123!"},
    )
    assert accept_resp.status_code == 201
    assert accept_resp.json()["role"] == "teacher"
    assert accept_resp.json()["status"] == "active"

    # Replay fails with 410 Gone
    replay = client.post(
        "/api/v1/staff-invitations/accept",
        json={"token": raw_token, "password": "TeacherChosenPass123!"},
    )
    assert replay.status_code == 410

    # Teacher can sign in and sees enriched school_name
    _login(client, "newteacher@alpha.example.com", "TeacherChosenPass123!")
    me = client.get("/api/v1/auth/me").json()
    assert me["memberships"][0]["school_name"] == "Alpha Secondary"

    # AUTH-03: School B cannot invite this active teacher as a teacher
    csrf_b = _login(client, "admin@beta.example.com", "SchoolAdminPass123!")
    conflict = client.post(
        f"/api/v1/schools/{school_b}/staff-invitations",
        headers={"X-CSRF-Token": csrf_b},
        json={
            "email": "newteacher@alpha.example.com",
            "full_name": "Mrs. Kemi",
            "role": "teacher",
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "TEACHER_SINGLE_SCHOOL_VIOLATION"


def test_multi_school_guardian_invite_verify_approve_and_revoke(
    env: tuple[TestClient, sessionmaker[Session], InMemoryEmailProvider, dict],
) -> None:
    client, session_local, email_provider, ctx = env
    school_a = ctx["school_a"]
    school_b = ctx["school_b"]

    # Create Student A in School A
    csrf_a = _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")
    student_a = client.post(
        f"/api/v1/schools/{school_a}/users",
        headers={"X-CSRF-Token": csrf_a},
        json={
            "email": "child1@alpha.example.com",
            "full_name": "Emeka Obi",
            "password": "StudentPassword123!",
            "role": "student",
        },
    ).json()["user_id"]

    # Create Student B in School B
    csrf_b = _login(client, "admin@beta.example.com", "SchoolAdminPass123!")
    student_b = client.post(
        f"/api/v1/schools/{school_b}/users",
        headers={"X-CSRF-Token": csrf_b},
        json={
            "email": "child2@beta.example.com",
            "full_name": "Amaka Obi",
            "password": "StudentPassword123!",
            "role": "student",
        },
    ).json()["user_id"]

    # 1. School A Admin invites parent@family.example.com for Student A
    csrf_a = _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")
    invite_a = client.post(
        f"/api/v1/schools/{school_a}/guardian-links/invite",
        headers={"X-CSRF-Token": csrf_a},
        json={
            "student_user_id": student_a,
            "guardian_email": "parent@family.example.com",
            "guardian_full_name": "Mr. Obi",
            "relationship_label": "Father",
        },
    )
    assert invite_a.status_code == 201
    link_a_id = invite_a.json()["id"]
    assert invite_a.json()["status"] == "invited"
    assert invite_a.json()["student_full_name"] == "Emeka Obi"
    token_a = _extract_token(email_provider.sent[-1].text, "parent/verify?token=")

    # Cannot approve before parent verifies contact
    early_approve = client.post(
        f"/api/v1/schools/{school_a}/guardian-links/{link_a_id}/approve",
        headers={"X-CSRF-Token": csrf_a},
        json={},
    )
    assert early_approve.status_code == 409

    # 2. Parent verifies School A token & creates single parent account -> pending_approval
    verify_a = client.post(
        "/api/v1/guardian-links/verify",
        json={"token": token_a, "password": "ParentSecret123!"},
    )
    assert verify_a.status_code == 200
    assert verify_a.json()["status"] == "pending_approval"

    # Single-use token cleared & replay fails with 410
    assert (
        client.post(
            "/api/v1/guardian-links/verify",
            json={"token": token_a, "password": "ParentSecret123!"},
        ).status_code
        == 410
    )
    with session_local() as db:
        link_row = db.get(GuardianLink, uuid.UUID(verify_a.json()["id"]))
        assert link_row is not None
        assert link_row.verification_token_hash is None

    # Before approval, parent sees ZERO children
    _login(client, "parent@family.example.com", "ParentSecret123!")
    assert client.get("/api/v1/parent/children").json()["items"] == []

    # Cross-school check: School B Admin cannot approve School A's link
    csrf_b = _login(client, "admin@beta.example.com", "SchoolAdminPass123!")
    assert (
        client.post(
            f"/api/v1/schools/{school_b}/guardian-links/{link_a_id}/approve",
            headers={"X-CSRF-Token": csrf_b},
            json={},
        ).status_code
        == 404
    )

    # 3. School A Admin approves Link A
    csrf_a = _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")
    approved_a = client.post(
        f"/api/v1/schools/{school_a}/guardian-links/{link_a_id}/approve",
        headers={"X-CSRF-Token": csrf_a},
        json={"decision_notes": "Verified ID"},
    )
    assert approved_a.status_code == 200
    assert approved_a.json()["status"] == "approved"

    # 4. AUTH-04: School B Admin invites the SAME parent email for Student B
    csrf_b = _login(client, "admin@beta.example.com", "SchoolAdminPass123!")
    invite_b = client.post(
        f"/api/v1/schools/{school_b}/guardian-links/invite",
        headers={"X-CSRF-Token": csrf_b},
        json={
            "student_user_id": student_b,
            "guardian_email": "parent@family.example.com",
            "guardian_full_name": "Mr. Obi",
            "relationship_label": "Father",
        },
    )
    assert invite_b.status_code == 201
    link_b_id = invite_b.json()["id"]
    token_b = _extract_token(email_provider.sent[-1].text, "parent/verify?token=")

    # Wrong password for existing parent account -> 401 (prevents account hijack)
    wrong_pw = client.post(
        "/api/v1/guardian-links/verify",
        json={"token": token_b, "password": "NotTheRealPassword123!"},
    )
    assert wrong_pw.status_code == 401

    # Correct existing password links to same parent account
    verify_b = client.post(
        "/api/v1/guardian-links/verify",
        json={"token": token_b, "password": "ParentSecret123!"},
    )
    assert verify_b.status_code == 200
    assert verify_b.json()["status"] == "pending_approval"

    # School B Admin approves Link B
    csrf_b = _login(client, "admin@beta.example.com", "SchoolAdminPass123!")
    assert (
        client.post(
            f"/api/v1/schools/{school_b}/guardian-links/{link_b_id}/approve",
            headers={"X-CSRF-Token": csrf_b},
            json={},
        ).status_code
        == 200
    )

    # Parent logs in once -> sees BOTH children across TWO schools!
    _login(client, "parent@family.example.com", "ParentSecret123!")
    children = client.get("/api/v1/parent/children").json()
    assert children["meta"]["total"] == 2
    school_names = {c["school_name"] for c in children["items"]}
    assert school_names == {"Alpha Secondary", "Beta Secondary"}

    # 5. School A Admin revokes Link A -> Student A immediately disappears from parent view
    csrf_a = _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")
    revoked_a = client.post(
        f"/api/v1/schools/{school_a}/guardian-links/{link_a_id}/revoke",
        headers={"X-CSRF-Token": csrf_a},
        json={"decision_notes": "Custody update"},
    )
    assert revoked_a.status_code == 200
    assert revoked_a.json()["status"] == "revoked"

    _login(client, "parent@family.example.com", "ParentSecret123!")
    remaining = client.get("/api/v1/parent/children").json()
    assert remaining["meta"]["total"] == 1
    assert remaining["items"][0]["school_name"] == "Beta Secondary"

    with session_local() as db:
        actions = set(db.scalars(select(AuditEvent.action)).all())
    assert {
        "guardian_link.invited",
        "guardian_link.verified",
        "guardian_link.approved",
        "guardian_link.revoked",
    } <= actions
