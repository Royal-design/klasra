import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.school import School


def get_school_by_id(db: Session, *, school_id: uuid.UUID) -> School | None:
    return db.get(School, school_id)


def get_school_by_slug(db: Session, *, slug: str) -> School | None:
    return db.scalar(select(School).where(School.slug == slug))


def list_schools(db: Session) -> list[School]:
    return list(db.scalars(select(School).order_by(School.created_at.desc())).all())


def create_school(
    db: Session, *, name: str, slug: str, status: str = "active"
) -> School:
    school = School(name=name.strip(), slug=slug, status=status)
    db.add(school)
    return school
