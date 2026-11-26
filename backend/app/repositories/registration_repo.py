import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.registration import StudentInvite, StudentRegistrationRequest
from app.models.user import User


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
    db: Session, *, school_id: uuid.UUID, status: str | None = None
) -> list[tuple[StudentRegistrationRequest, User]]:
    stmt = (
        select(StudentRegistrationRequest, User)
        .join(User, User.id == StudentRegistrationRequest.user_id)
        .where(StudentRegistrationRequest.school_id == school_id)
    )
    if status is not None:
        stmt = stmt.where(StudentRegistrationRequest.status == status)
    rows = db.execute(
        stmt.order_by(StudentRegistrationRequest.created_at.desc())
    ).all()
    return [(row[0], row[1]) for row in rows]
