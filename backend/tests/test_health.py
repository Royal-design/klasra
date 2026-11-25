from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app


class _HealthySession:
    def execute(self, _statement: object) -> None:
        return None


class _FailingSession:
    def execute(self, _statement: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))


def _build_test_settings() -> Settings:
    return Settings(
        app_env="test",
        database_url="postgresql+psycopg://test_user:test_pass@127.0.0.1:5432/test_db",
        cors_origins="http://localhost:3000",
    )


def test_health_check_ok() -> None:
    app = create_app(settings=_build_test_settings())

    def override_get_db() -> Generator[_HealthySession, None, None]:
        yield _HealthySession()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"
    assert "default-src 'none'" in response.headers["content-security-policy"]


def test_health_check_database_unavailable_hides_internal_error() -> None:
    app = create_app(settings=_build_test_settings())

    def override_get_db() -> Generator[_FailingSession, None, None]:
        yield _FailingSession()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}
    assert "connection refused" not in response.text


def test_cors_rejects_wildcard_origin() -> None:
    with pytest.raises(ValueError, match="Wildcard"):
        Settings(
            app_env="test",
            database_url="postgresql+psycopg://test_user:test_pass@127.0.0.1:5432/test_db",
            cors_origins="*",
        )
