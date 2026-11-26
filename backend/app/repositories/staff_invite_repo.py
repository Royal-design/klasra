import uuid
from datetime import datetime

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.models.staff_invite import StaffInvitation
from app.repositories.pagination import count_and_paginate_scalars, escape_like


def get_by_token_hash(db: Session, *, token_hash: str) -> StaffInvitation | None:
    return db.scalar(
        select(StaffInvitation).where(StaffInvitation.token_hash == token_hash)
    )


def revoke_pending_for_email_in_school(
    db: Session, *, school_id: uuid.UUID, email: str, revoked_at: datetime
) -> None:
    db.execute(
        update(StaffInvitation)
        .where(
            StaffInvitation.school_id == school_id,
            StaffInvitation.email == email.strip().lower(),
            StaffInvitation.accepted_at.is_(None),
            StaffInvitation.revoked_at.is_(None),
        )
        .values(revoked_at=revoked_at)
    )


def list_for_school(
    db: Session,
    *,
    school_id: uuid.UUID,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[StaffInvitation], int]:
    stmt = select(StaffInvitation).where(StaffInvitation.school_id == school_id)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(
            or_(
                StaffInvitation.email.ilike(pattern, escape="\\"),
                StaffInvitation.full_name.ilike(pattern, escape="\\"),
            )
        )
    stmt = stmt.order_by(StaffInvitation.created_at.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)
