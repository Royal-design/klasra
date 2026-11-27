from collections.abc import Generator

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


def _make_settings(*, login_limit: int = 50) -> Settings:
    return Settings(
        app_env="test",
        database_url="sqlite+pysqlite:///:memory:",
        cors_origins="http://localhost:3000",
        cookie_secure=False,
        rate_limit_per_minute=500,
        login_rate_limit_per_minute=login_limit,
    )


@pytest.fixture()
def test_env() -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    app = create_app(settings=_make_settings())

    def override_get_db() -> Generator[Session, None, None]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Seed one platform admin
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
        yield client, SessionLocal

    Base.metadata.drop_all(engine)
    engine.dispose()


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


def _create_school(
    client: TestClient,
    csrf_token: str,
    *,
    name: str,
    slug: str,
    admin_email: str,
    admin_password: str = "SchoolAdminPass123!",
) -> dict:
    response = client.post(
        "/api/v1/schools",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "name": name,
            "slug": slug,
            "initial_admin": {
                "email": admin_email,
                "full_name": f"{name} Admin",
                "password": admin_password,
            },
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_auth_login_csrf_logout_and_invalid_credentials(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _session_local = test_env

    # Unauthenticated /me fails closed
    me_unauth = client.get("/api/v1/auth/me")
    assert me_unauth.status_code == 401
    assert me_unauth.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    # Wrong password & unknown email return identical generic 401
    bad_pw = client.post(
        "/api/v1/auth/login",
        json={"email": "platform@lms.example.com", "password": "WrongPassword123!"},
    )
    unknown = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@lms.example.com", "password": "WrongPassword123!"},
    )
    assert bad_pw.status_code == 401
    assert unknown.status_code == 401
    assert bad_pw.json() == unknown.json()

    # Valid login sets cookies & returns profile
    csrf = _login(client, "platform@lms.example.com", "PlatformSecret123!")
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "platform@lms.example.com"
    assert me.json()["is_platform_admin"] is True

    # Logout without CSRF fails closed
    no_csrf = client.post("/api/v1/auth/logout")
    assert no_csrf.status_code == 403
    assert no_csrf.json()["error"]["code"] == "CSRF_FAILED"

    # Logout with valid CSRF invalidates session
    ok_logout = client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
    assert ok_logout.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_platform_admin_school_lifecycle_and_isolation(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_local = test_env
    csrf = _login(client, "platform@lms.example.com", "PlatformSecret123!")

    created = _create_school(
        client,
        csrf,
        name="Greenfield Secondary",
        slug="greenfield",
        admin_email="admin@greenfield.example.com",
    )
    school_id = created["school"]["id"]

    # Duplicate slug -> 409
    dup = client.post(
        "/api/v1/schools",
        headers={"X-CSRF-Token": csrf},
        json={
            "name": "Greenfield Duplicate",
            "slug": "greenfield",
            "initial_admin": {
                "email": "admin2@greenfield.example.com",
                "full_name": "Admin Two",
                "password": "SchoolAdminPass123!",
            },
        },
    )
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "SCHOOL_SLUG_EXISTS"

    # Platform admin does NOT automatically access school-scoped user management
    school_users = client.get(f"/api/v1/schools/{school_id}/users")
    assert school_users.status_code == 403

    # Update school name & verify audit events exist
    updated = client.patch(
        f"/api/v1/schools/{school_id}",
        headers={"X-CSRF-Token": csrf},
        json={"name": "Greenfield High School"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Greenfield High School"

    with session_local() as db:
        actions = list(db.scalars(select(AuditEvent.action)).all())
    assert "school.created" in actions
    assert "school.updated" in actions


def test_school_admin_scoping_teacher_single_school_and_revocation(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_local = test_env
    platform_csrf = _login(client, "platform@lms.example.com", "PlatformSecret123!")

    school_a = _create_school(
        client,
        platform_csrf,
        name="Alpha College",
        slug="alpha",
        admin_email="admin@alpha.example.com",
    )
    school_b = _create_school(
        client,
        platform_csrf,
        name="Beta Academy",
        slug="beta",
        admin_email="admin@beta.example.com",
    )
    school_a_id = school_a["school"]["id"]
    school_b_id = school_b["school"]["id"]
    admin_a_membership_id = school_a["initial_admin_membership_id"]

    # Switch to School A Admin
    admin_a_csrf = _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")

    # School Admin cannot call Platform Admin endpoints
    assert client.get("/api/v1/schools").status_code == 403

    # School A Admin cannot access School B (cross-school fail closed)
    assert client.get(f"/api/v1/schools/{school_b_id}/users").status_code == 403

    # School A Admin creates a teacher in School A
    teacher_resp = client.post(
        f"/api/v1/schools/{school_a_id}/users",
        headers={"X-CSRF-Token": admin_a_csrf},
        json={
            "email": "teacher1@alpha.example.com",
            "full_name": "Ms. Ada",
            "password": "TeacherPassword123!",
            "role": "teacher",
        },
    )
    assert teacher_resp.status_code == 201
    teacher_membership_id = teacher_resp.json()["membership_id"]

    # School A Admin cannot demote/revoke the last active school_admin
    demote_self = client.patch(
        f"/api/v1/schools/{school_a_id}/memberships/{admin_a_membership_id}",
        headers={"X-CSRF-Token": admin_a_csrf},
        json={"status": "revoked"},
    )
    assert demote_self.status_code == 409
    assert demote_self.json()["error"]["code"] == "LAST_SCHOOL_ADMIN"

    # AUTH-03: School B Admin cannot assign the same active teacher to School B
    admin_b_csrf = _login(client, "admin@beta.example.com", "SchoolAdminPass123!")
    conflict_teacher = client.post(
        f"/api/v1/schools/{school_b_id}/users",
        headers={"X-CSRF-Token": admin_b_csrf},
        json={
            "email": "teacher1@alpha.example.com",
            "full_name": "Ms. Ada",
            "password": "TeacherPassword123!",
            "role": "teacher",
        },
    )
    assert conflict_teacher.status_code == 409
    assert conflict_teacher.json()["error"]["code"] == "TEACHER_SINGLE_SCHOOL_VIOLATION"

    # Teacher logs in -> cannot access School Admin endpoints
    _login(client, "teacher1@alpha.example.com", "TeacherPassword123!")
    assert client.get(f"/api/v1/schools/{school_a_id}/users").status_code == 403

    # Keep a separate cookie jar for the teacher to verify session invalidation on revoke
    teacher_session_cookie = client.cookies.get("lms_session")
    assert teacher_session_cookie is not None

    # School A Admin revokes teacher's membership
    admin_a_csrf = _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")
    revoked = client.patch(
        f"/api/v1/schools/{school_a_id}/memberships/{teacher_membership_id}",
        headers={"X-CSRF-Token": admin_a_csrf},
        json={"status": "revoked"},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"

    # Teacher's previous session cookie is now invalid (401)
    client.cookies.set("lms_session", teacher_session_cookie)
    assert client.get("/api/v1/auth/me").status_code == 401

    with session_local() as db:
        actions = list(db.scalars(select(AuditEvent.action)).all())
    assert "membership.created" in actions
    assert "membership.updated" in actions


def test_login_rate_limiting() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    app = create_app(settings=_make_settings(login_limit=2))

    def override_get_db() -> Generator[Session, None, None]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        for _ in range(2):
            r = client.post(
                "/api/v1/auth/login",
                json={"email": "x@y.example.com", "password": "BadPassword123!"},
            )
            assert r.status_code == 401

        limited = client.post(
            "/api/v1/auth/login",
            json={"email": "x@y.example.com", "password": "BadPassword123!"},
        )
        assert limited.status_code == 429
        assert limited.json()["error"]["code"] == "RATE_LIMITED"
        assert "Retry-After" in limited.headers

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_passwordless_user_creation_and_profile_endpoints(
    test_env: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _session_local = test_env
    platform_csrf = _login(client, "platform@lms.example.com", "PlatformSecret123!")

    # Create two schools to test profile scoping and passwordless user onboarding
    school_a = _create_school(
        client,
        platform_csrf,
        name="Emerald High",
        slug="emerald-high",
        admin_email="admin@emerald.example.com",
    )
    school_b = _create_school(
        client,
        platform_csrf,
        name="Cedar Academy",
        slug="cedar-academy",
        admin_email="admin@cedar.example.com",
    )
    school_a_id = school_a["school"]["id"]
    school_b_id = school_b["school"]["id"]

    admin_a_csrf = _login(client, "admin@emerald.example.com", "SchoolAdminPass123!")

    # 1. School Admin creates a student WITHOUT a password (triggers 24h setup link)
    created = client.post(
        f"/api/v1/schools/{school_a_id}/users",
        headers={"X-CSRF-Token": admin_a_csrf},
        json={
            "email": "newstudent@emerald.example.com",
            "full_name": "Chinedu Okafor",
            "role": "student",
        },
    )
    assert created.status_code == 201
    assert created.json()["email"] == "newstudent@emerald.example.com"

    # 2. Personal Profile update (PATCH /api/v1/auth/me)
    updated_me = client.patch(
        "/api/v1/auth/me",
        headers={"X-CSRF-Token": admin_a_csrf},
        json={"full_name": "Dr. Ada Mensah"},
    )
    assert updated_me.status_code == 200
    assert updated_me.json()["full_name"] == "Dr. Ada Mensah"

    # 3. School Profile GET & PATCH (status change is ignored/blocked for school_admin)
    profile = client.get(f"/api/v1/schools/{school_a_id}/profile")
    assert profile.status_code == 200
    assert profile.json()["slug"] == "emerald-high"

    patched_profile = client.patch(
        f"/api/v1/schools/{school_a_id}/profile",
        headers={"X-CSRF-Token": admin_a_csrf},
        json={
            "name": "Emerald Secondary School",
            "status": "suspended",
            "terminology_config": {"term_label": "Semester", "year_level_label": "Form"},
        },
    )
    assert patched_profile.status_code == 200
    body = patched_profile.json()
    assert body["name"] == "Emerald Secondary School"
    assert body["status"] == "active"  # School Admin cannot suspend their own school
    assert body["terminology_config"]["term_label"] == "Semester"

    # Cross-school profile access fails closed (403)
    assert client.get(f"/api/v1/schools/{school_b_id}/profile").status_code == 403
    assert (
        client.patch(
            f"/api/v1/schools/{school_b_id}/profile",
            headers={"X-CSRF-Token": admin_a_csrf},
            json={"name": "Hijacked Name"},
        ).status_code
        == 403
    )
