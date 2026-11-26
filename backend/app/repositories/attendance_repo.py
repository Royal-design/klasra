import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord
from app.repositories.pagination import count_and_paginate_scalars


def get_record(
    db: Session,
    *,
    school_id: uuid.UUID,
    offering_id: uuid.UUID,
    student_user_id: uuid.UUID,
    attendance_date: date,
) -> AttendanceRecord | None:
    return db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.school_id == school_id,
            AttendanceRecord.subject_offering_id == offering_id,
            AttendanceRecord.student_user_id == student_user_id,
            AttendanceRecord.attendance_date == attendance_date,
        )
    )


def list_for_offering(
    db: Session,
    *,
    school_id: uuid.UUID,
    offering_id: uuid.UUID,
    attendance_date: date | None = None,
    student_user_id: uuid.UUID | None = None,
    status: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[AttendanceRecord], int]:
    stmt = select(AttendanceRecord).where(
        AttendanceRecord.school_id == school_id,
        AttendanceRecord.subject_offering_id == offering_id,
    )
    if attendance_date is not None:
        stmt = stmt.where(AttendanceRecord.attendance_date == attendance_date)
    if student_user_id is not None:
        stmt = stmt.where(AttendanceRecord.student_user_id == student_user_id)
    if status is not None:
        stmt = stmt.where(AttendanceRecord.status == status)
    stmt = stmt.order_by(
        AttendanceRecord.attendance_date.desc(), AttendanceRecord.updated_at.desc()
    )
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)


def list_for_student(
    db: Session,
    *,
    student_user_id: uuid.UUID,
    school_id: uuid.UUID | None = None,
    subject_offering_id: uuid.UUID | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[AttendanceRecord], int]:
    stmt = select(AttendanceRecord).where(
        AttendanceRecord.student_user_id == student_user_id
    )
    if school_id is not None:
        stmt = stmt.where(AttendanceRecord.school_id == school_id)
    if subject_offering_id is not None:
        stmt = stmt.where(AttendanceRecord.subject_offering_id == subject_offering_id)
    if status is not None:
        stmt = stmt.where(AttendanceRecord.status == status)
    if date_from is not None:
        stmt = stmt.where(AttendanceRecord.attendance_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(AttendanceRecord.attendance_date <= date_to)
    stmt = stmt.order_by(
        AttendanceRecord.attendance_date.desc(), AttendanceRecord.updated_at.desc()
    )
    return count_and_paginate_scalars(db, stmt, offset=offset, limit=limit)
