import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assignment import Assignment, Submission
from app.models.grade import Grade
from app.models.guardian import GuardianLink
from app.models.school import School
from app.repositories.pagination import count_and_paginate_scalars, escape_like


def get_submission_by_id(db: Session, *, submission_id: uuid.UUID) -> Submission | None:
    return db.get(Submission, submission_id)


def get_grade_by_submission_id(db: Session, *, submission_id: uuid.UUID) -> Grade | None:
    return db.scalar(select(Grade).where(Grade.submission_id == submission_id))


def list_grades_for_assignment(
    db: Session,
    *,
    school_id: uuid.UUID,
    assignment_id: uuid.UUID,
    is_published: bool | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Grade], int]:
    stmt = select(Grade).where(
        Grade.school_id == school_id,
        Grade.assignment_id == assignment_id,
    )
    if is_published is not None:
        stmt = stmt.where(Grade.is_published == is_published)
    stmt = stmt.order_by(Grade.graded_at.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


def list_published_grades_for_student(
    db: Session,
    *,
    student_user_id: uuid.UUID,
    school_id: uuid.UUID | None = None,
    subject_offering_id: uuid.UUID | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Grade], int]:
    """PROG-01 & PROG-02: Return ONLY published grades for a student."""
    stmt = (
        select(Grade)
        .join(Assignment, Assignment.id == Grade.assignment_id)
        .where(
            Grade.student_user_id == student_user_id,
            Grade.is_published.is_(True),
        )
    )
    if school_id is not None:
        stmt = stmt.where(Grade.school_id == school_id)
    if subject_offering_id is not None:
        stmt = stmt.where(Assignment.subject_offering_id == subject_offering_id)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(Assignment.title.ilike(pattern, escape="\\"))
    stmt = stmt.order_by(Grade.published_at.desc(), Grade.graded_at.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


def get_approved_guardian_link_for_child(
    db: Session, *, parent_user_id: uuid.UUID, student_user_id: uuid.UUID
) -> GuardianLink | None:
    return db.scalar(
        select(GuardianLink)
        .join(School, School.id == GuardianLink.school_id)
        .where(
            GuardianLink.parent_user_id == parent_user_id,
            GuardianLink.student_user_id == student_user_id,
            GuardianLink.status == "approved",
            School.status == "active",
        )
    )
