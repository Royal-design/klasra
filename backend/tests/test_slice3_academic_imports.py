import io
from collections.abc import Generator

import openpyxl
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
def env() -> Generator[tuple[TestClient, sessionmaker[Session], dict], None, None]:
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

        yield client, SessionLocal, {"school_a": school_a, "school_b": school_b}

    Base.metadata.drop_all(engine)
    engine.dispose()


def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["csrf_token"]


def test_academic_hierarchy_cross_school_isolation_and_enrollments(
    env: tuple[TestClient, sessionmaker[Session], dict],
) -> None:
    client, session_local, ctx = env
    school_a = ctx["school_a"]
    school_b = ctx["school_b"]

    csrf_a = _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")

    # Create teacher & student in School A
    teacher_a = client.post(
        f"/api/v1/schools/{school_a}/users",
        headers={"X-CSRF-Token": csrf_a},
        json={
            "email": "teacher@alpha.example.com",
            "full_name": "Mr. Bello",
            "password": "TeacherPassword123!",
            "role": "teacher",
        },
    ).json()["user_id"]

    student_a = client.post(
        f"/api/v1/schools/{school_a}/users",
        headers={"X-CSRF-Token": csrf_a},
        json={
            "email": "student@alpha.example.com",
            "full_name": "Chidi Okafor",
            "password": "StudentPassword123!",
            "role": "student",
        },
    ).json()["user_id"]

    # SCH-02: Academic Year & Term
    year_resp = client.post(
        f"/api/v1/schools/{school_a}/academic-years",
        headers={"X-CSRF-Token": csrf_a},
        json={"name": "2026-2027", "start_date": "2026-09-01", "end_date": "2027-07-15"},
    )
    assert year_resp.status_code == 201
    year_id = year_resp.json()["id"]

    # Term outside academic year -> 422
    bad_term = client.post(
        f"/api/v1/schools/{school_a}/terms",
        headers={"X-CSRF-Token": csrf_a},
        json={
            "academic_year_id": year_id,
            "name": "Invalid Term",
            "start_date": "2026-08-01",
            "end_date": "2026-12-15",
        },
    )
    assert bad_term.status_code == 422
    assert bad_term.json()["error"]["code"] == "TERM_OUTSIDE_ACADEMIC_YEAR"

    term_id = client.post(
        f"/api/v1/schools/{school_a}/terms",
        headers={"X-CSRF-Token": csrf_a},
        json={
            "academic_year_id": year_id,
            "name": "Term 1",
            "start_date": "2026-09-01",
            "end_date": "2026-12-15",
        },
    ).json()["id"]

    # SCH-03: Year Level, Class Groups, Subject, Subject Offering + Teacher
    level_id = client.post(
        f"/api/v1/schools/{school_a}/year-levels",
        headers={"X-CSRF-Token": csrf_a},
        json={"name": "Year 8", "display_order": 8},
    ).json()["id"]

    group_blue = client.post(
        f"/api/v1/schools/{school_a}/class-groups",
        headers={"X-CSRF-Token": csrf_a},
        json={"academic_year_id": year_id, "year_level_id": level_id, "name": "Year 8 Blue"},
    ).json()["id"]

    group_red = client.post(
        f"/api/v1/schools/{school_a}/class-groups",
        headers={"X-CSRF-Token": csrf_a},
        json={"academic_year_id": year_id, "year_level_id": level_id, "name": "Year 8 Red"},
    ).json()["id"]

    subject_id = client.post(
        f"/api/v1/schools/{school_a}/subjects",
        headers={"X-CSRF-Token": csrf_a},
        json={"code": "math", "name": "Mathematics"},
    ).json()["id"]

    # Reject assigning a student as a teacher -> 422
    bad_offering = client.post(
        f"/api/v1/schools/{school_a}/subject-offerings",
        headers={"X-CSRF-Token": csrf_a},
        json={
            "class_group_id": group_blue,
            "subject_id": subject_id,
            "term_id": term_id,
            "teacher_user_ids": [student_a],
        },
    )
    assert bad_offering.status_code == 422
    assert bad_offering.json()["error"]["code"] == "INVALID_TEACHER_ASSIGNMENT"

    offering_resp = client.post(
        f"/api/v1/schools/{school_a}/subject-offerings",
        headers={"X-CSRF-Token": csrf_a},
        json={
            "class_group_id": group_blue,
            "subject_id": subject_id,
            "term_id": term_id,
            "teacher_user_ids": [teacher_a],
        },
    )
    assert offering_resp.status_code == 201
    assert offering_resp.json()["teacher_user_ids"] == [teacher_a]

    # SCH-04: Enroll -> Transfer (history preserved) -> Withdraw
    enroll_resp = client.post(
        f"/api/v1/schools/{school_a}/enrollments",
        headers={"X-CSRF-Token": csrf_a},
        json={
            "student_user_id": student_a,
            "class_group_id": group_blue,
            "effective_from": "2026-09-01",
        },
    )
    assert enroll_resp.status_code == 201
    enroll_id = enroll_resp.json()["id"]

    transfer_resp = client.post(
        f"/api/v1/schools/{school_a}/enrollments/{enroll_id}/transfer",
        headers={"X-CSRF-Token": csrf_a},
        json={"target_class_group_id": group_red, "effective_date": "2026-10-01"},
    )
    assert transfer_resp.status_code == 200
    assert transfer_resp.json()["previous_enrollment"]["status"] == "transferred"
    assert transfer_resp.json()["previous_enrollment"]["effective_to"] == "2026-10-01"
    new_enroll_id = transfer_resp.json()["new_enrollment"]["id"]
    assert transfer_resp.json()["new_enrollment"]["status"] == "active"
    assert transfer_resp.json()["new_enrollment"]["class_group_id"] == group_red

    withdraw_resp = client.post(
        f"/api/v1/schools/{school_a}/enrollments/{new_enroll_id}/withdraw",
        headers={"X-CSRF-Token": csrf_a},
        json={"effective_date": "2026-11-15"},
    )
    assert withdraw_resp.status_code == 200
    assert withdraw_resp.json()["status"] == "withdrawn"
    assert withdraw_resp.json()["effective_to"] == "2026-11-15"

    # Both historical enrollments still exist
    all_enrollments = client.get(
        f"/api/v1/schools/{school_a}/enrollments",
        params={"student_user_id": student_a},
    ).json()
    assert len(all_enrollments["items"]) == 2
    assert all_enrollments["meta"]["total"] == 2

    # Cross-school isolation: School B Admin cannot read School A or reference School A's year
    csrf_b = _login(client, "admin@beta.example.com", "SchoolAdminPass123!")
    assert client.get(f"/api/v1/schools/{school_a}/academic-years").status_code == 403
    cross_term = client.post(
        f"/api/v1/schools/{school_b}/terms",
        headers={"X-CSRF-Token": csrf_b},
        json={
            "academic_year_id": year_id,
            "name": "Cross School Term",
            "start_date": "2026-09-01",
            "end_date": "2026-12-01",
        },
    )
    assert cross_term.status_code == 404

    with session_local() as db:
        actions = set(db.scalars(select(AuditEvent.action)).all())
    assert {"enrollment.created", "enrollment.transferred", "enrollment.withdrawn"} <= actions


def test_spreadsheet_import_validate_and_commit_csv_and_xlsx(
    env: tuple[TestClient, sessionmaker[Session], dict],
) -> None:
    client, _session_local, ctx = env
    school_a = ctx["school_a"]
    school_b = ctx["school_b"]

    # Create a teacher in School B to test AUTH-03 conflict in School A import
    csrf_b = _login(client, "admin@beta.example.com", "SchoolAdminPass123!")
    client.post(
        f"/api/v1/schools/{school_b}/users",
        headers={"X-CSRF-Token": csrf_b},
        json={
            "email": "beta.teacher@beta.example.com",
            "full_name": "Beta Teacher",
            "password": "TeacherPassword123!",
            "role": "teacher",
        },
    )

    csrf_a = _login(client, "admin@alpha.example.com", "SchoolAdminPass123!")
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
    client.post(
        f"/api/v1/schools/{school_a}/class-groups",
        headers={"X-CSRF-Token": csrf_a},
        json={"academic_year_id": year_id, "year_level_id": level_id, "name": "Year 9 Gold"},
    )

    # 1. Unsupported extension -> 415
    bad_ext = client.post(
        f"/api/v1/schools/{school_a}/imports/validate",
        headers={"X-CSRF-Token": csrf_a},
        files={"file": ("users.txt", b"hello", "text/plain")},
    )
    assert bad_ext.status_code == 415

    # 2. Forged .xlsx magic bytes -> 415
    forged_xlsx = client.post(
        f"/api/v1/schools/{school_a}/imports/validate",
        headers={"X-CSRF-Token": csrf_a},
        files={"file": ("fake.xlsx", b"not-a-zip-file", "application/octet-stream")},
    )
    assert forged_xlsx.status_code == 415

    # 3. CSV with errors -> validate returns error report; commit rejects with 422
    bad_csv = (
        "email,full_name,role,academic_year,class_group\n"
        "not-an-email,Bad Email,student,2026-2027,Year 9 Gold\n"
        "escalate@alpha.example.com,Bad Role,school_admin,,\n"
        "beta.teacher@beta.example.com,Cross Teacher,teacher,,\n"
    ).encode("utf-8")

    val_resp = client.post(
        f"/api/v1/schools/{school_a}/imports/validate",
        headers={"X-CSRF-Token": csrf_a},
        files={"file": ("bad.csv", bad_csv, "text/csv")},
    )
    assert val_resp.status_code == 200
    codes = {err["code"] for err in val_resp.json()["errors"]}
    assert "INVALID_EMAIL" in codes
    assert "INVALID_ROLE" in codes
    assert "TEACHER_SINGLE_SCHOOL_VIOLATION" in codes

    bad_commit = client.post(
        f"/api/v1/schools/{school_a}/imports/commit",
        headers={"X-CSRF-Token": csrf_a},
        files={"file": ("bad.csv", bad_csv, "text/csv")},
    )
    assert bad_commit.status_code == 422
    assert bad_commit.json()["error"]["code"] == "IMPORT_VALIDATION_FAILED"

    # 4. Valid CSV commit (teacher + enrolled student)
    good_csv = (
        "email,full_name,role,academic_year,class_group\n"
        "t1@alpha.example.com,Teacher One,teacher,,\n"
        "s1@alpha.example.com,Student One,student,2026-2027,Year 9 Gold\n"
    ).encode("utf-8")
    commit_csv = client.post(
        f"/api/v1/schools/{school_a}/imports/commit",
        headers={"X-CSRF-Token": csrf_a},
        files={"file": ("good.csv", good_csv, "text/csv")},
    )
    assert commit_csv.status_code == 201, commit_csv.text
    assert commit_csv.json()["imported_users"] == 2
    assert commit_csv.json()["imported_memberships"] == 2
    assert commit_csv.json()["imported_enrollments"] == 1

    # 5. Valid XLSX commit
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.append(["email", "full_name", "role", "academic_year", "class_group"])
    ws.append(["s2@alpha.example.com", "Student Two", "student", "2026-2027", "Year 9 Gold"])
    buf = io.BytesIO()
    wb.save(buf)
    wb.close()

    commit_xlsx = client.post(
        f"/api/v1/schools/{school_a}/imports/commit",
        headers={"X-CSRF-Token": csrf_a},
        files={
            "file": (
                "good.xlsx",
                buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert commit_xlsx.status_code == 201, commit_xlsx.text
    assert commit_xlsx.json()["imported_users"] == 1
    assert commit_xlsx.json()["imported_enrollments"] == 1
