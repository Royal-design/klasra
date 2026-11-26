import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.school import School
from app.repositories.pagination import count_and_paginate_scalars, escape_like


def get_school_by_id(db: Session, *, school_id: uuid.UUID) -> School | None:
    return db.get(School, school_id)


def get_school_by_slug(db: Session, *, slug: str) -> School | None:
    return db.scalar(select(School).where(School.slug == slug))


def list_schools(
    db: Session,
    *,
    status: str | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[School], int]:
    stmt = select(School)
    if status is not None:
        stmt = stmt.where(School.status == status)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(
            or_(
                School.name.ilike(pattern, escape="\\"),
                School.slug.ilike(pattern, escape="\\"),
            )
        )
    stmt = stmt.order_by(School.created_at.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


def create_school(
    db: Session, *, name: str, slug: str, status: str = "active"
) -> School:
    school = School(name=name.strip(), slug=slug, status=status)
    db.add(school)
    return school
