import uuid
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.attendance import AttendanceRecord
from app.repositories import attendance_repo, grade_repo, lesson_repo, membership_repo
from app.schemas.attendance import AttendanceBatchUpsertRequest
from app.services.audit import record_audit_event
from app.services.lesson import _get_offering_and_check_teacher


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def record_offering_attendance(
    db: Session,
    *,
    offering_id: uuid.UUID,
    payload: AttendanceBatchUpsertRequest,
    actor_user_id: uuid.UUID,
) -> list[AttendanceRecord]:
    """ATT-01 & ATT-02: Assigned Teacher records/updates attendance with attribution & audit."""
    offering = _get_offering_and_check_teacher(
        db, offering_id=offering_id, user_id=actor_user_id
    )

    seen_students: set[uuid.UUID] = set()
    for entry in payload.entries:
        if entry.student_user_id in seen_students:
            raise AppError(
                422,
                "DUPLICATE_STUDENT_IN_BATCH",
                "Each student may only appear once per attendance submission.",
            )
        seen_students.add(entry.student_user_id)

        if not lesson_repo.is_student_enrolled_in_offering(
            db,
            school_id=offering.school_id,
            class_group_id=offering.class_group_id,
            offering_id=offering.id,
            student_user_id=entry.student_user_id,
        ):
            raise AppError(
                422,
                "STUDENT_NOT_ENROLLED",
                "All students in an attendance batch must be actively enrolled in this offering.",
            )

    now = _utcnow()
    saved_records: list[AttendanceRecord] = []

    for entry in payload.entries:
        existing = attendance_repo.get_record(
            db,
            school_id=offering.school_id,
            offering_id=offering.id,
            student_user_id=entry.student_user_id,
            attendance_date=payload.attendance_date,
        )
        cleaned_notes = entry.notes.strip() if entry.notes else None
        if existing is None:
            record = AttendanceRecord(
                school_id=offering.school_id,
                subject_offering_id=offering.id,
                student_user_id=entry.student_user_id,
                attendance_date=payload.attendance_date,
                status=entry.status,
                notes=cleaned_notes,
                recorded_by_user_id=actor_user_id,
                updated_by_user_id=actor_user_id,
                recorded_at=now,
                updated_at=now,
            )
            db.add(record)
            db.flush()
            record_audit_event(
                db,
                action="attendance.recorded",
                target_type="attendance_record",
                target_id=record.id,
                actor_user_id=actor_user_id,
                school_id=offering.school_id,
                metadata={
                    "subject_offering_id": str(offering.id),
                    "student_user_id": str(entry.student_user_id),
                    "attendance_date": payload.attendance_date.isoformat(),
                    "status": record.status,
                },
            )
            saved_records.append(record)
        else:
            previous_status = existing.status
            existing.status = entry.status
            existing.notes = cleaned_notes
            existing.updated_by_user_id = actor_user_id
            existing.updated_at = now
            record_audit_event(
                db,
                action="attendance.updated",
                target_type="attendance_record",
                target_id=existing.id,
                actor_user_id=actor_user_id,
                school_id=offering.school_id,
                metadata={
                    "subject_offering_id": str(offering.id),
                    "student_user_id": str(entry.student_user_id),
                    "attendance_date": payload.attendance_date.isoformat(),
                    "previous_status": previous_status,
                    "new_status": existing.status,
                },
            )
            saved_records.append(existing)

    db.commit()
    for rec in saved_records:
        db.refresh(rec)
    return saved_records


def list_offering_attendance(
    db: Session,
    *,
    offering_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    attendance_date: date | None = None,
    student_user_id: uuid.UUID | None = None,
    status: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[AttendanceRecord], int]:
    """Allow Assigned Teacher or active School Admin of the offering's school."""
    offering = lesson_repo.get_offering_by_id(db, offering_id=offering_id)
    if offering is None:
        raise AppError(404, "SUBJECT_OFFERING_NOT_FOUND", "Subject offering not found.")

    membership = membership_repo.get_user_membership_in_school(
        db, user_id=actor_user_id, school_id=offering.school_id
    )
    if membership is None or membership.status != "active":
        raise AppError(403, "FORBIDDEN", "You do not have access to this offering's attendance.")

    is_school_admin = membership.role == "school_admin"
    is_assigned_teacher = (
        membership.role == "teacher"
        and lesson_repo.is_teacher_assigned_to_offering(
            db,
            school_id=offering.school_id,
            offering_id=offering.id,
            teacher_user_id=actor_user_id,
        )
    )
    if not (is_school_admin or is_assigned_teacher):
        raise AppError(403, "FORBIDDEN", "You do not have access to this offering's attendance.")

    return attendance_repo.list_for_offering(
        db,
        school_id=offering.school_id,
        offering_id=offering.id,
        attendance_date=attendance_date,
        student_user_id=student_user_id,
        status=status,
        offset=offset,
        limit=limit,
    )


def list_child_attendance_for_parent(
    db: Session,
    *,
    parent_user_id: uuid.UUID,
    student_user_id: uuid.UUID,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[AttendanceRecord], int]:
    """PROG-02: Enforce approved guardian_link before returning child's attendance."""
    link = grade_repo.get_approved_guardian_link_for_child(
        db, parent_user_id=parent_user_id, student_user_id=student_user_id
    )
    if link is None:
        raise AppError(
            403,
            "FORBIDDEN",
            "You do not have an approved guardian link for this student.",
        )

    return attendance_repo.list_for_student(
        db,
        student_user_id=student_user_id,
        school_id=link.school_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        offset=offset,
        limit=limit,
    )
