import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.membership import SchoolMembership
from app.models.user import User
from app.repositories.pagination import count_and_paginate_rows, escape_like


def get_membership_for_school(
    db: Session, *, school_id: uuid.UUID, membership_id: uuid.UUID
) -> SchoolMembership | None:
    return db.scalar(
        select(SchoolMembership).where(
            SchoolMembership.id == membership_id,
            SchoolMembership.school_id == school_id,
        )
    )


def get_user_membership_in_school(
    db: Session, *, user_id: uuid.UUID, school_id: uuid.UUID
) -> SchoolMembership | None:
    return db.scalar(
        select(SchoolMembership).where(
            SchoolMembership.user_id == user_id,
            SchoolMembership.school_id == school_id,
        )
    )


def get_active_teacher_membership_elsewhere(
    db: Session, *, user_id: uuid.UUID, exclude_school_id: uuid.UUID
) -> SchoolMembership | None:
    return db.scalar(
        select(SchoolMembership).where(
            SchoolMembership.user_id == user_id,
            SchoolMembership.role == "teacher",
            SchoolMembership.status == "active",
            SchoolMembership.school_id != exclude_school_id,
        )
    )


def count_active_school_admins(db: Session, *, school_id: uuid.UUID) -> int:
    count = db.scalar(
        select(func.count())
        .select_from(SchoolMembership)
        .where(
            SchoolMembership.school_id == school_id,
            SchoolMembership.role == "school_admin",
            SchoolMembership.status == "active",
        )
    )
    return int(count or 0)


def list_user_memberships(
    db: Session, *, user_id: uuid.UUID
) -> list[SchoolMembership]:
    return list(
        db.scalars(
            select(SchoolMembership)
            .where(SchoolMembership.user_id == user_id)
            .order_by(SchoolMembership.created_at.asc())
        ).all()
    )


def list_school_users_with_memberships(
    db: Session,
    *,
    school_id: uuid.UUID,
    role: str | None = None,
    status: str | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[tuple[User, SchoolMembership]], int]:
    stmt = (
        select(User, SchoolMembership)
        .join(SchoolMembership, SchoolMembership.user_id == User.id)
        .where(SchoolMembership.school_id == school_id)
    )
    if role is not None:
        stmt = stmt.where(SchoolMembership.role == role)
    if status is not None:
        stmt = stmt.where(SchoolMembership.status == status)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(
            or_(
                User.email.ilike(pattern, escape="\\"),
                User.full_name.ilike(pattern, escape="\\"),
            )
        )
    stmt = stmt.order_by(SchoolMembership.created_at.desc())
    rows, total = count_and_paginate_rows(db, stmt, offset=offset, limit=limit)
    return [(row[0], row[1]) for row in rows], total


def create_membership(
    db: Session,
    *,
    user_id: uuid.UUID,
    school_id: uuid.UUID,
    role: str,
    status: str = "active",
) -> SchoolMembership:
    membership = SchoolMembership(
        user_id=user_id,
        school_id=school_id,
        role=role,
        status=status,
    )
    db.add(membership)
    return membership
