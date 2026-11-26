import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.registration import StudentInvite, StudentRegistrationRequest
from app.models.user import User
from app.repositories.pagination import count_and_paginate_rows, escape_like


def get_invite_by_token_hash(
    db: Session, *, token_hash: str
) -> StudentInvite | None:
    return db.scalar(
        select(StudentInvite).where(StudentInvite.token_hash == token_hash)
    )


def get_registration_request_for_school(
    db: Session, *, school_id: uuid.UUID, request_id: uuid.UUID
) -> StudentRegistrationRequest | None:
    return db.scalar(
        select(StudentRegistrationRequest).where(
            StudentRegistrationRequest.id == request_id,
            StudentRegistrationRequest.school_id == school_id,
        )
    )


def list_registration_requests_for_school(
    db: Session,
    *,
    school_id: uuid.UUID,
    status: str | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[tuple[StudentRegistrationRequest, User]], int]:
    stmt = (
        select(StudentRegistrationRequest, User)
        .join(User, User.id == StudentRegistrationRequest.user_id)
        .where(StudentRegistrationRequest.school_id == school_id)
    )
    if status is not None:
        stmt = stmt.where(StudentRegistrationRequest.status == status)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(
            or_(
                User.email.ilike(pattern, escape="\\"),
                User.full_name.ilike(pattern, escape="\\"),
                StudentRegistrationRequest.student_reference.ilike(
                    pattern, escape="\\"
                ),
            )
        )
    stmt = stmt.order_by(StudentRegistrationRequest.created_at.desc())
    rows, total = count_and_paginate_rows(db, stmt, offset=offset, limit=limit)
    return [(row[0], row[1]) for row in rows], total
