import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.guardian import GuardianLink
from app.models.school import School
from app.models.user import User
from app.repositories.pagination import count_and_paginate_scalars, escape_like


def get_link_for_school(
    db: Session, *, school_id: uuid.UUID, link_id: uuid.UUID
) -> GuardianLink | None:
    return db.scalar(
        select(GuardianLink).where(
            GuardianLink.id == link_id,
            GuardianLink.school_id == school_id,
        )
    )


def get_link_by_token_hash(
    db: Session, *, token_hash: str
) -> GuardianLink | None:
    return db.scalar(
        select(GuardianLink).where(GuardianLink.verification_token_hash == token_hash)
    )


def get_active_or_pending_link(
    db: Session,
    *,
    school_id: uuid.UUID,
    student_user_id: uuid.UUID,
    guardian_email: str,
) -> GuardianLink | None:
    return db.scalar(
        select(GuardianLink).where(
            GuardianLink.school_id == school_id,
            GuardianLink.student_user_id == student_user_id,
            GuardianLink.guardian_email == guardian_email.strip().lower(),
            GuardianLink.status.in_(["invited", "pending_approval", "approved"]),
        )
    )


def list_links_for_school(
    db: Session,
    *,
    school_id: uuid.UUID,
    student_user_id: uuid.UUID | None = None,
    status: str | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[GuardianLink], int]:
    stmt = (
        select(GuardianLink)
        .join(User, User.id == GuardianLink.student_user_id)
        .where(GuardianLink.school_id == school_id)
    )
    if student_user_id is not None:
        stmt = stmt.where(GuardianLink.student_user_id == student_user_id)
    if status is not None:
        stmt = stmt.where(GuardianLink.status == status)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(
            or_(
                GuardianLink.guardian_email.ilike(pattern, escape="\\"),
                GuardianLink.guardian_full_name.ilike(pattern, escape="\\"),
                User.full_name.ilike(pattern, escape="\\"),
                User.email.ilike(pattern, escape="\\"),
            )
        )
    stmt = stmt.order_by(GuardianLink.created_at.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


def list_approved_children_for_parent(
    db: Session,
    *,
    parent_user_id: uuid.UUID,
    school_id: uuid.UUID | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[GuardianLink], int]:
    """AUTH-04 / PROG-02: Return ONLY approved links across active schools."""
    stmt = (
        select(GuardianLink)
        .join(School, School.id == GuardianLink.school_id)
        .join(User, User.id == GuardianLink.student_user_id)
        .where(
            GuardianLink.parent_user_id == parent_user_id,
            GuardianLink.status == "approved",
            School.status == "active",
        )
    )
    if school_id is not None:
        stmt = stmt.where(GuardianLink.school_id == school_id)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(
            or_(
                User.full_name.ilike(pattern, escape="\\"),
                School.name.ilike(pattern, escape="\\"),
            )
        )
    stmt = stmt.order_by(GuardianLink.approved_at.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)
