import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.assignment import Assignment, Submission
from app.repositories.pagination import count_and_paginate_scalars, escape_like


def get_assignment_by_id(db: Session, *, assignment_id: uuid.UUID) -> Assignment | None:
    return db.get(Assignment, assignment_id)


def get_assignment_for_offering(
    db: Session,
    *,
    school_id: uuid.UUID,
    offering_id: uuid.UUID,
    assignment_id: uuid.UUID,
) -> Assignment | None:
    return db.scalar(
        select(Assignment).where(
            Assignment.id == assignment_id,
            Assignment.school_id == school_id,
            Assignment.subject_offering_id == offering_id,
        )
    )


def list_assignments_for_offering(
    db: Session,
    *,
    school_id: uuid.UUID,
    offering_id: uuid.UUID,
    published_only: bool = False,
    status: str | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Assignment], int]:
    stmt = select(Assignment).where(
        Assignment.school_id == school_id,
        Assignment.subject_offering_id == offering_id,
    )
    if published_only:
        stmt = stmt.where(Assignment.status == "published")
    elif status is not None:
        stmt = stmt.where(Assignment.status == status)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(Assignment.title.ilike(pattern, escape="\\"))
    stmt = stmt.order_by(Assignment.created_at.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


def get_latest_submission_version(
    db: Session,
    *,
    school_id: uuid.UUID,
    assignment_id: uuid.UUID,
    student_user_id: uuid.UUID,
) -> int:
    max_ver = db.scalar(
        select(func.max(Submission.version_number)).where(
            Submission.school_id == school_id,
            Submission.assignment_id == assignment_id,
            Submission.student_user_id == student_user_id,
        )
    )
    return int(max_ver or 0)


def mark_previous_submissions_not_latest(
    db: Session,
    *,
    school_id: uuid.UUID,
    assignment_id: uuid.UUID,
    student_user_id: uuid.UUID,
) -> None:
    db.execute(
        update(Submission)
        .where(
            Submission.school_id == school_id,
            Submission.assignment_id == assignment_id,
            Submission.student_user_id == student_user_id,
            Submission.is_latest.is_(True),
        )
        .values(is_latest=False)
    )


def list_submissions_for_assignment(
    db: Session,
    *,
    school_id: uuid.UUID,
    assignment_id: uuid.UUID,
    student_user_id: uuid.UUID | None = None,
    latest_only: bool = False,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Submission], int]:
    stmt = select(Submission).where(
        Submission.school_id == school_id,
        Submission.assignment_id == assignment_id,
    )
    if student_user_id is not None:
        stmt = stmt.where(Submission.student_user_id == student_user_id)
    if latest_only:
        stmt = stmt.where(Submission.is_latest.is_(True))
    stmt = stmt.order_by(Submission.submitted_at.desc(), Submission.version_number.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)
