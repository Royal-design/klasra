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
from app.models.password_reset import PasswordResetToken
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
    tuple[TestClient, sessionmaker[Session], InMemoryEmailProvider], None, None
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
                email="teacher@school.example.com",
                full_name="Ada Lovelace",
                password_hash=hash_password("InitialPassword123!"),
                is_platform_admin=False,
                is_active=True,
            )
        )
        db.commit()

    with TestClient(app) as client:
        yield client, SessionLocal, email_provider

    Base.metadata.drop_all(engine)
    engine.dispose()


def _extract_reset_token(email_text: str) -> str:
    for token_part in email_text.split():
        if "reset-password?token=" in token_part:
            parsed = urlparse(token_part)
            return parse_qs(parsed.query)["token"][0]
    raise AssertionError("Reset token URL not found in email body")


def test_openapi_exposes_csrf_authorize_scheme(
    env: tuple[TestClient, sessionmaker[Session], InMemoryEmailProvider],
) -> None:
    client, _session_local, _email_provider = env
    schema = client.get("/openapi.json").json()
    schemes = schema["components"]["securitySchemes"]
    assert "CSRFToken" in schemes
    assert schemes["CSRFToken"]["type"] == "apiKey"
    assert schemes["CSRFToken"]["in"] == "header"
    assert schemes["CSRFToken"]["name"] == "X-CSRF-Token"


def test_forgot_and_reset_password_flow_and_single_use_enforcement(
    env: tuple[TestClient, sessionmaker[Session], InMemoryEmailProvider],
) -> None:
    client, session_local, email_provider = env

    # Log in first to confirm active sessions are revoked upon password reset
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@school.example.com", "password": "InitialPassword123!"},
    )
    assert login_resp.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200

    # Unknown email returns identical generic 200 and sends NO email
    unknown_resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nobody@school.example.com"},
    )
    assert unknown_resp.status_code == 200
    assert len(email_provider.sent) == 0

    # Known email returns identical generic 200 and sends reset email
    known_resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "teacher@school.example.com"},
    )
    assert known_resp.status_code == 200
    assert known_resp.json() == unknown_resp.json()
    assert len(email_provider.sent) == 1

    raw_token = _extract_reset_token(email_provider.sent[0].text)

    # Confirm raw token is NOT stored in DB (only its SHA-256 hash)
    with session_local() as db:
        token_row = db.scalar(select(PasswordResetToken))
        assert token_row is not None
        assert token_row.token_hash != raw_token

    # Reset password succeeds
    reset_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "BrandNewPassword123!"},
    )
    assert reset_resp.status_code == 200

    # Reusing the same token fails with 410 Gone
    replay_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "AnotherPassword123!"},
    )
    assert replay_resp.status_code == 410
    assert replay_resp.json()["error"]["code"] == "TOKEN_INVALID_OR_EXPIRED"

    # Previous active session was invalidated
    assert client.get("/api/v1/auth/me").status_code == 401

    # Old password fails, new password succeeds
    assert (
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "teacher@school.example.com",
                "password": "InitialPassword123!",
            },
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "teacher@school.example.com",
                "password": "BrandNewPassword123!",
            },
        ).status_code
        == 200
    )

    with session_local() as db:
        actions = set(db.scalars(select(AuditEvent.action)).all())
    assert {"auth.password_reset_requested", "auth.password_reset_completed"} <= actions


def test_change_password_requires_csrf_and_revokes_session(
    env: tuple[TestClient, sessionmaker[Session], InMemoryEmailProvider],
) -> None:
    client, _session_local, _email_provider = env

    csrf = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@school.example.com", "password": "InitialPassword123!"},
    ).json()["csrf_token"]

    # Missing CSRF -> 403
    no_csrf = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "InitialPassword123!",
            "new_password": "UpdatedPassword123!",
        },
    )
    assert no_csrf.status_code == 403

    # Wrong current password -> 401
    wrong_pw = client.post(
        "/api/v1/auth/change-password",
        headers={"X-CSRF-Token": csrf},
        json={
            "current_password": "WrongPassword123!",
            "new_password": "UpdatedPassword123!",
        },
    )
    assert wrong_pw.status_code == 401

    # Valid change -> 200 and session revoked
    ok_resp = client.post(
        "/api/v1/auth/change-password",
        headers={"X-CSRF-Token": csrf},
        json={
            "current_password": "InitialPassword123!",
            "new_password": "UpdatedPassword123!",
        },
    )
    assert ok_resp.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401


def test_resend_config_requires_api_key_and_from_address() -> None:
    with pytest.raises(ValueError, match="RESEND_API_KEY"):
        Settings(
            _env_file=None,
            app_env="test",
            database_url="sqlite+pysqlite:///:memory:",
            email_provider="resend",
        )
