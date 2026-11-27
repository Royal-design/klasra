from collections.abc import Generator
from urllib.parse import parse_qs, urlparse

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
from app.services.email import InMemoryEmailProvider


def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["csrf_token"]


@pytest.fixture()
def env() -> Generator[tuple[TestClient, dict], None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url="sqlite+pysqlite:///:memory:",
        cookie_secure=False,
        rate_limit_per_minute=500,
        login_rate_limit_per_minute=100,
    )
    email_provider = InMemoryEmailProvider()
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
        p_csrf = _login(client, "platform@lms.example.com", "PlatformSecret123!")
        school_id = client.post(
            "/api/v1/schools",
            headers={"X-CSRF-Token": p_csrf},
            json={
                "name": "ScholarGrid High",
                "slug": "scholargrid-high",
                "initial_admin": {
                    "email": "admin@sg.example.com",
                    "full_name": "School Admin",
                    "password": "AdminPassword123!",
                },
            },
        ).json()["school"]["id"]
        a_csrf = _login(client, "admin@sg.example.com", "AdminPassword123!")
        year_id = client.post(
            f"/api/v1/schools/{school_id}/academic-years",
            headers={"X-CSRF-Token": a_csrf},
            json={"name": "2026", "start_date": "2026-01-01", "end_date": "2026-12-31"},
        ).json()["id"]
        yl_id = client.post(
            f"/api/v1/schools/{school_id}/year-levels",
            headers={"X-CSRF-Token": a_csrf},
            json={"name": "SS2", "display_order": 1},
        ).json()["id"]
        cg_id = client.post(
            f"/api/v1/schools/{school_id}/class-groups",
            headers={"X-CSRF-Token": a_csrf},
            json={"academic_year_id": year_id, "year_level_id": yl_id, "name": "SS2 Science"},
        ).json()["id"]
        subj_id = client.post(
            f"/api/v1/schools/{school_id}/subjects",
            headers={"X-CSRF-Token": a_csrf},
            json={"code": "BIO201", "name": "Biology"},
        ).json()["id"]
        teacher_id = client.post(
            f"/api/v1/schools/{school_id}/users",
            headers={"X-CSRF-Token": a_csrf},
            json={
                "email": "teacher@sg.example.com",
                "full_name": "Mr Biology",
                "password": "TeacherPassword123!",
                "role": "teacher",
            },
        ).json()["user_id"]
        offering_id = client.post(
            f"/api/v1/schools/{school_id}/subject-offerings",
            headers={"X-CSRF-Token": a_csrf},
            json={
                "class_group_id": cg_id,
                "subject_id": subj_id,
                "teacher_user_ids": [teacher_id],
            },
        ).json()["id"]
        student1_id = client.post(
            f"/api/v1/schools/{school_id}/users",
            headers={"X-CSRF-Token": a_csrf},
            json={
                "email": "student1@sg.example.com",
                "full_name": "Tobi Ade",
                "password": "StudentPassword123!",
                "role": "student",
            },
        ).json()["user_id"]
        student2_id = client.post(
            f"/api/v1/schools/{school_id}/users",
            headers={"X-CSRF-Token": a_csrf},
            json={
                "email": "student2@sg.example.com",
                "full_name": "Chidi Obi",
                "password": "StudentPassword123!",
                "role": "student",
            },
        ).json()["user_id"]
        for sid in (student1_id, student2_id):
            client.post(
                f"/api/v1/schools/{school_id}/enrollments",
                headers={"X-CSRF-Token": a_csrf},
                json={
                    "student_user_id": sid,
                    "class_group_id": cg_id,
                    "effective_from": "2026-01-10",
                },
            )

        # Invite, verify & approve parent for student1
        link_id = client.post(
            f"/api/v1/schools/{school_id}/guardian-links/invite",
            headers={"X-CSRF-Token": a_csrf},
            json={
                "student_user_id": student1_id,
                "guardian_email": "parent1@sg.example.com",
                "guardian_full_name": "Mrs Ade",
                "relationship_label": "mother",
            },
        ).json()["id"]
        last_email = email_provider.sent[-1].text
        token_url = [line for line in last_email.splitlines() if "token=" in line][0].strip()
        token = parse_qs(urlparse(token_url).query)["token"][0]
        client.post(
            "/api/v1/guardian-links/verify",
            json={"token": token, "password": "ParentPassword123!"},
        )
        client.post(
            f"/api/v1/schools/{school_id}/guardian-links/{link_id}/approve",
            headers={"X-CSRF-Token": a_csrf},
            json={"decision_notes": "Verified"},
        )

        yield client, {
            "offering_id": offering_id,
            "student1_id": student1_id,
            "student2_id": student2_id,
        }

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_quiz_auto_grading_exam_manual_grading_and_privacy(env: tuple[TestClient, dict]) -> None:
    client, ctx = env
    offering_id = ctx["offering_id"]
    student1_id = ctx["student1_id"]
    student2_id = ctx["student2_id"]

    # 1. Teacher creates a published auto-graded Quiz
    t_csrf = _login(client, "teacher@sg.example.com", "TeacherPassword123!")
    quiz_resp = client.post(
        f"/api/v1/offerings/{offering_id}/assessments",
        headers={"X-CSRF-Token": t_csrf},
        json={
            "title": "Cell Structure Quiz",
            "assessment_type": "quiz",
            "status": "published",
            "time_limit_minutes": 15,
            "max_attempts": 2,
            "show_results_immediately": True,
        },
    )
    assert quiz_resp.status_code == 201, quiz_resp.text
    quiz_id = quiz_resp.json()["id"]

    q1 = client.post(
        f"/api/v1/offerings/{offering_id}/assessments/{quiz_id}/questions",
        headers={"X-CSRF-Token": t_csrf},
        json={
            "question_type": "single_choice",
            "prompt": "Powerhouse of the cell?",
            "options": [
                {"key": "A", "label": "Nucleus"},
                {"key": "B", "label": "Mitochondria"},
            ],
            "correct_answers": ["B"],
            "points": 5,
            "display_order": 1,
        },
    ).json()
    q2 = client.post(
        f"/api/v1/offerings/{offering_id}/assessments/{quiz_id}/questions",
        headers={"X-CSRF-Token": t_csrf},
        json={
            "question_type": "multi_select",
            "prompt": "Select plant cell organelles:",
            "options": [
                {"key": "A", "label": "Chloroplast"},
                {"key": "B", "label": "Cell wall"},
                {"key": "C", "label": "Centriole"},
            ],
            "correct_answers": ["A", "B"],
            "points": 5,
            "display_order": 2,
        },
    ).json()

    # 2. Student1 lists assessments -> correct_answers MUST be hidden (None)
    s1_csrf = _login(client, "student1@sg.example.com", "StudentPassword123!")
    s_list = client.get(f"/api/v1/offerings/{offering_id}/assessments")
    assert s_list.status_code == 200
    assert s_list.json()["items"][0]["total_points"] == 10.0
    for q in s_list.json()["items"][0]["questions"]:
        assert q["correct_answers"] is None

    # Student1 starts and submits Quiz -> auto-graded 10/10 and immediately published
    attempt = client.post(
        f"/api/v1/assessments/{quiz_id}/attempts",
        headers={"X-CSRF-Token": s1_csrf},
    ).json()
    attempt_id = attempt["id"]
    submit_resp = client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        headers={"X-CSRF-Token": s1_csrf},
        json={
            "answers": [
                {"question_id": q1["id"], "selected_options": ["b"]},
                {"question_id": q2["id"], "selected_options": ["B", "A"]},
            ]
        },
    )
    assert submit_resp.status_code == 200, submit_resp.text
    sub_data = submit_resp.json()
    assert sub_data["status"] == "graded"
    assert sub_data["is_published"] is True
    assert sub_data["total_score"] == 10.0

    # Student1 and Approved Parent1 see the published quiz result; Parent1 blocked from Student2
    my_res = client.get("/api/v1/students/me/assessments")
    assert my_res.status_code == 200
    assert my_res.json()["meta"]["total"] == 1
    assert my_res.json()["items"][0]["total_score"] == 10.0

    _login(client, "parent1@sg.example.com", "ParentPassword123!")
    child_res = client.get(f"/api/v1/parent/children/{student1_id}/assessments")
    assert child_res.status_code == 200
    assert child_res.json()["meta"]["total"] == 1
    assert client.get(f"/api/v1/parent/children/{student2_id}/assessments").status_code == 403

    # 3. Teacher creates an Exam (max_attempts=1, mixed True/False + Short Answer, held until graded)
    t_csrf = _login(client, "teacher@sg.example.com", "TeacherPassword123!")
    exam_id = client.post(
        f"/api/v1/offerings/{offering_id}/assessments",
        headers={"X-CSRF-Token": t_csrf},
        json={
            "title": "Term 1 Biology Exam",
            "assessment_type": "exam",
            "status": "published",
            "max_attempts": 1,
            "show_results_immediately": False,
        },
    ).json()["id"]
    eq1 = client.post(
        f"/api/v1/offerings/{offering_id}/assessments/{exam_id}/questions",
        headers={"X-CSRF-Token": t_csrf},
        json={
            "question_type": "true_false",
            "prompt": "DNA is double-stranded.",
            "options": [{"key": "T", "label": "True"}, {"key": "F", "label": "False"}],
            "correct_answers": ["T"],
            "points": 10,
            "display_order": 1,
        },
    ).json()
    eq2 = client.post(
        f"/api/v1/offerings/{offering_id}/assessments/{exam_id}/questions",
        headers={"X-CSRF-Token": t_csrf},
        json={
            "question_type": "short_answer",
            "prompt": "Explain photosynthesis briefly.",
            "points": 20,
            "display_order": 2,
        },
    ).json()

    # Student1 starts & submits Exam -> score hidden until teacher grades & publishes
    s1_csrf = _login(client, "student1@sg.example.com", "StudentPassword123!")
    exam_att_id = client.post(
        f"/api/v1/assessments/{exam_id}/attempts",
        headers={"X-CSRF-Token": s1_csrf},
    ).json()["id"]
    exam_sub = client.post(
        f"/api/v1/attempts/{exam_att_id}/submit",
        headers={"X-CSRF-Token": s1_csrf},
        json={
            "answers": [
                {"question_id": eq1["id"], "selected_options": ["T"]},
                {"question_id": eq2["id"], "text_answer": "Plants convert sunlight to glucose."},
            ]
        },
    ).json()
    assert exam_sub["status"] == "submitted"
    assert exam_sub["is_published"] is False
    assert exam_sub["total_score"] is None

    # Starting a 2nd attempt on max_attempts=1 exam -> 409 MAX_ATTEMPTS_REACHED
    retry_resp = client.post(
        f"/api/v1/assessments/{exam_id}/attempts",
        headers={"X-CSRF-Token": s1_csrf},
    )
    assert retry_resp.status_code == 409

    # Teacher grades short_answer (18/20) and publishes -> total_score = 28/30
    t_csrf = _login(client, "teacher@sg.example.com", "TeacherPassword123!")
    graded = client.put(
        f"/api/v1/attempts/{exam_att_id}/grade",
        headers={"X-CSRF-Token": t_csrf},
        json={
            "answer_grades": [
                {"question_id": eq2["id"], "points_awarded": 18, "feedback": "Clear explanation."}
            ],
            "teacher_feedback": "Excellent work!",
            "is_published": True,
        },
    )
    assert graded.status_code == 200, graded.text
    assert graded.json()["auto_score"] == 10.0
    assert graded.json()["manual_score"] == 18.0
    assert graded.json()["total_score"] == 28.0
    assert graded.json()["is_published"] is True
