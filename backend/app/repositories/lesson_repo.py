import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.academic import Enrollment, OfferingTeacher, SubjectOffering
from app.models.lesson import Lesson, StoredFile
from app.repositories.pagination import count_and_paginate_scalars, escape_like


def get_offering_by_id(db: Session, *, offering_id: uuid.UUID) -> SubjectOffering | None:
    return db.get(SubjectOffering, offering_id)


def is_teacher_assigned_to_offering(
    db: Session, *, school_id: uuid.UUID, offering_id: uuid.UUID, teacher_user_id: uuid.UUID
) -> bool:
    row = db.scalar(
        select(OfferingTeacher.id).where(
            OfferingTeacher.school_id == school_id,
            OfferingTeacher.subject_offering_id == offering_id,
            OfferingTeacher.teacher_user_id == teacher_user_id,
        )
    )
    return row is not None


def is_student_enrolled_in_offering(
    db: Session,
    *,
    school_id: uuid.UUID,
    class_group_id: uuid.UUID,
    offering_id: uuid.UUID,
    student_user_id: uuid.UUID,
) -> bool:
    row = db.scalar(
        select(Enrollment.id).where(
            Enrollment.school_id == school_id,
            Enrollment.student_user_id == student_user_id,
            Enrollment.class_group_id == class_group_id,
            Enrollment.status == "active",
            or_(
                Enrollment.subject_offering_id.is_(None),
                Enrollment.subject_offering_id == offering_id,
            ),
        )
    )
    return row is not None


def get_lesson_for_offering(
    db: Session, *, school_id: uuid.UUID, offering_id: uuid.UUID, lesson_id: uuid.UUID
) -> Lesson | None:
    return db.scalar(
        select(Lesson).where(
            Lesson.id == lesson_id,
            Lesson.school_id == school_id,
            Lesson.subject_offering_id == offering_id,
        )
    )


def list_lessons_for_offering(
    db: Session,
    *,
    school_id: uuid.UUID,
    offering_id: uuid.UUID,
    published_only: bool = False,
    status: str | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Lesson], int]:
    stmt = select(Lesson).where(
        Lesson.school_id == school_id,
        Lesson.subject_offering_id == offering_id,
    )
    if published_only:
        stmt = stmt.where(Lesson.status == "published")
    elif status is not None:
        stmt = stmt.where(Lesson.status == status)
    if q and q.strip():
        pattern = f"%{escape_like(q.strip())}%"
        stmt = stmt.where(Lesson.title.ilike(pattern, escape="\\"))
    stmt = stmt.order_by(Lesson.created_at.desc())
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


def get_stored_file_by_id(db: Session, *, file_id: uuid.UUID) -> StoredFile | None:
    return db.get(StoredFile, file_id)


def get_stored_file_by_storage_key(db: Session, *, storage_key: str) -> StoredFile | None:
    return db.scalar(select(StoredFile).where(StoredFile.storage_key == storage_key))
