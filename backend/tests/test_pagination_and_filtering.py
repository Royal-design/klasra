from collections.abc import Generator

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


def _make_settings() -> Settings:
    return Settings(
        app_env="test",
        database_url="sqlite+pysqlite:///:memory:",
        cors_origins="http://localhost:3000",
        cookie_secure=False,
        rate_limit_per_minute=500,
        login_rate_limit_per_minute=100,
    )


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
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

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_schools_and_users_pagination_meta_and_filtering(client: TestClient) -> None:
    p_csrf = client.post(
        "/api/v1/auth/login",
        json={"email": "platform@lms.example.com", "password": "PlatformSecret123!"},
    ).json()["csrf_token"]

    school_ids = []
    for idx, (name, slug) in enumerate(
        [
            ("Alpha High", "alpha-high"),
            ("Beta College", "beta-college"),
            ("Gamma Academy", "gamma-academy"),
        ],
        start=1,
    ):
        resp = client.post(
            "/api/v1/schools",
            headers={"X-CSRF-Token": p_csrf},
            json={
                "name": name,
                "slug": slug,
                "initial_admin": {
                    "email": f"admin{idx}@{slug}.example.com",
                    "full_name": f"{name} Admin",
                    "password": "SchoolAdminPass123!",
                },
            },
        )
        assert resp.status_code == 201
        school_ids.append(resp.json()["school"]["id"])

    # Page 1 of 2 (page_size=2) -> 2 items, total=3, total_pages=2, has_next=True, has_prev=False
    page1 = client.get("/api/v1/schools", params={"page": 1, "page_size": 2}).json()
    assert len(page1["items"]) == 2
    assert page1["meta"] == {
        "total": 3,
        "page": 1,
        "page_size": 2,
        "total_pages": 2,
        "has_next": True,
        "has_prev": False,
    }

    # Page 2 -> 1 item, has_next=False, has_prev=True
    page2 = client.get("/api/v1/schools", params={"page": 2, "page_size": 2}).json()
    assert len(page2["items"]) == 1
    assert page2["meta"]["has_next"] is False
    assert page2["meta"]["has_prev"] is True

    # Search q=gamma -> 1 matching school
    search = client.get("/api/v1/schools", params={"q": "gamma"}).json()
    assert search["meta"]["total"] == 1
    assert search["items"][0]["slug"] == "gamma-academy"

    # Reject page_size > 100
    too_big = client.get("/api/v1/schools", params={"page_size": 200})
    assert too_big.status_code == 422

    # School Admin user filtering by role & q
    school_a = school_ids[0]
    csrf_a = client.post(
        "/api/v1/auth/login",
        json={"email": "admin1@alpha-high.example.com", "password": "SchoolAdminPass123!"},
    ).json()["csrf_token"]

    for email, name, role in [
        ("ada@alpha.example.com", "Ada Teacher", "teacher"),
        ("chidi@alpha.example.com", "Chidi Student", "student"),
        ("zainab@alpha.example.com", "Zainab Student", "student"),
    ]:
        r = client.post(
            f"/api/v1/schools/{school_a}/users",
            headers={"X-CSRF-Token": csrf_a},
            json={
                "email": email,
                "full_name": name,
                "password": "ValidPassword123!",
                "role": role,
            },
        )
        assert r.status_code == 201

    students = client.get(
        f"/api/v1/schools/{school_a}/users", params={"role": "student"}
    ).json()
    assert students["meta"]["total"] == 2
    assert all(item["role"] == "student" for item in students["items"])

    search_zainab = client.get(
        f"/api/v1/schools/{school_a}/users", params={"q": "zainab"}
    ).json()
    assert search_zainab["meta"]["total"] == 1
    assert search_zainab["items"][0]["email"] == "zainab@alpha.example.com"
