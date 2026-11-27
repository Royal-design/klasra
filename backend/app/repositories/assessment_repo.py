import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.assessment import (
    Assessment,
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentQuestion,
)
from app.repositories.pagination import count_and_paginate_scalars, escape_like


def get_assessment_by_id(
    db: Session, *, assessment_id: uuid.UUID
) -> Assessment | None:
    return db.get(Assessment, assessment_id)


def get_assessment_for_offering(
    db: Session,
    *,
    school_id: uuid.UUID,
    offering_id: uuid.UUID,
    assessment_id: uuid.UUID,
) -> Assessment | None:
    return db.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id,
            Assessment.school_id == school_id,
            Assessment.subject_offering_id == offering_id,
        )
    )


def list_assessments_for_offering(
    db: Session,
    *,
    school_id: uuid.UUID,
    offering_id: uuid.UUID,
    published_only: bool = False,
    assessment_type: str | None = None,
    status: str | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Assessment], int]:
    stmt = select(Assessment).where(
        Assessment.school_id == school_id,
        Assessment.subject_offering_id == offering_id,
    )
    if published_only:
        stmt = stmt.where(Assessment.status.in_(["published", "closed"]))
    elif status is not None:
        stmt = stmt.where(Assessment.status == status)
    if assessment_type is not None:
        stmt = stmt.where(Assessment.assessment_type == assessment_type)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(Assessment.title.ilike(pattern, escape="\\"))
    stmt = stmt.order_by(Assessment.created_at.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


def get_question_for_assessment(
    db: Session,
    *,
    school_id: uuid.UUID,
    assessment_id: uuid.UUID,
    question_id: uuid.UUID,
) -> AssessmentQuestion | None:
    return db.scalar(
        select(AssessmentQuestion).where(
            AssessmentQuestion.id == question_id,
            AssessmentQuestion.school_id == school_id,
            AssessmentQuestion.assessment_id == assessment_id,
        )
    )


def recalculate_total_points(
    db: Session, *, school_id: uuid.UUID, assessment_id: uuid.UUID
) -> float:
    total = db.scalar(
        select(func.coalesce(func.sum(AssessmentQuestion.points), 0.0)).where(
            AssessmentQuestion.school_id == school_id,
            AssessmentQuestion.assessment_id == assessment_id,
        )
    )
    return float(total or 0.0)


def count_student_attempts(
    db: Session,
    *,
    school_id: uuid.UUID,
    assessment_id: uuid.UUID,
    student_user_id: uuid.UUID,
) -> int:
    count = db.scalar(
        select(func.count(AssessmentAttempt.id)).where(
            AssessmentAttempt.school_id == school_id,
            AssessmentAttempt.assessment_id == assessment_id,
            AssessmentAttempt.student_user_id == student_user_id,
        )
    )
    return int(count or 0)


def get_in_progress_attempt(
    db: Session,
    *,
    school_id: uuid.UUID,
    assessment_id: uuid.UUID,
    student_user_id: uuid.UUID,
) -> AssessmentAttempt | None:
    return db.scalar(
        select(AssessmentAttempt).where(
            AssessmentAttempt.school_id == school_id,
            AssessmentAttempt.assessment_id == assessment_id,
            AssessmentAttempt.student_user_id == student_user_id,
            AssessmentAttempt.status == "in_progress",
        )
    )


def get_attempt_by_id(
    db: Session, *, attempt_id: uuid.UUID
) -> AssessmentAttempt | None:
    return db.get(AssessmentAttempt, attempt_id)


def list_attempts_for_assessment(
    db: Session,
    *,
    school_id: uuid.UUID,
    assessment_id: uuid.UUID,
    student_user_id: uuid.UUID | None = None,
    status: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[AssessmentAttempt], int]:
    stmt = select(AssessmentAttempt).where(
        AssessmentAttempt.school_id == school_id,
        AssessmentAttempt.assessment_id == assessment_id,
    )
    if student_user_id is not None:
        stmt = stmt.where(AssessmentAttempt.student_user_id == student_user_id)
    if status is not None:
        stmt = stmt.where(AssessmentAttempt.status == status)
    stmt = stmt.order_by(AssessmentAttempt.created_at.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


def list_published_attempts_for_student(
    db: Session,
    *,
    student_user_id: uuid.UUID,
    school_id: uuid.UUID | None = None,
    assessment_type: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[AssessmentAttempt], int]:
    stmt = (
        select(AssessmentAttempt)
        .join(Assessment, AssessmentAttempt.assessment_id == Assessment.id)
        .where(
            AssessmentAttempt.student_user_id == student_user_id,
            AssessmentAttempt.is_published.is_(True),
        )
    )
    if school_id is not None:
        stmt = stmt.where(AssessmentAttempt.school_id == school_id)
    if assessment_type is not None:
        stmt = stmt.where(Assessment.assessment_type == assessment_type)
    stmt = stmt.order_by(AssessmentAttempt.submitted_at.desc(), AssessmentAttempt.created_at.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


def get_answer_for_attempt_question(
    db: Session,
    *,
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
) -> AssessmentAnswer | None:
    return db.scalar(
        select(AssessmentAnswer).where(
            AssessmentAnswer.attempt_id == attempt_id,
            AssessmentAnswer.question_id == question_id,
        )
    )
