import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.academic import SubjectOffering
from app.models.lesson import Lesson, StoredFile
from app.repositories import lesson_repo, membership_repo
from app.schemas.lesson import LessonCreateRequest, LessonUpdateRequest
from app.services.audit import record_audit_event
from app.services.file_storage import resolve_stored_file_path, save_uploaded_file


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_offering_and_check_teacher(
    db: Session, *, offering_id: uuid.UUID, user_id: uuid.UUID
) -> SubjectOffering:
    offering = lesson_repo.get_offering_by_id(db, offering_id=offering_id)
    if offering is None:
        raise AppError(404, "SUBJECT_OFFERING_NOT_FOUND", "Subject offering not found.")

    membership = membership_repo.get_user_membership_in_school(
        db, user_id=user_id, school_id=offering.school_id
    )
    if (
        membership is None
        or membership.role != "teacher"
        or membership.status != "active"
        or not lesson_repo.is_teacher_assigned_to_offering(
            db,
            school_id=offering.school_id,
            offering_id=offering.id,
            teacher_user_id=user_id,
        )
    ):
        raise AppError(
            403,
            "FORBIDDEN",
            "Only teachers assigned to this subject offering can perform this action.",
        )
    return offering


def _check_offering_read_access(
    db: Session, *, offering_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[SubjectOffering, bool]:
    """Return (offering, is_teacher). Fail closed for parents, admins, unassigned teachers, unenrolled students."""
    offering = lesson_repo.get_offering_by_id(db, offering_id=offering_id)
    if offering is None:
        raise AppError(404, "SUBJECT_OFFERING_NOT_FOUND", "Subject offering not found.")

    membership = membership_repo.get_user_membership_in_school(
        db, user_id=user_id, school_id=offering.school_id
    )
    if membership is None or membership.status != "active":
        raise AppError(403, "FORBIDDEN", "You do not have access to this subject offering.")

    if membership.role == "teacher" and lesson_repo.is_teacher_assigned_to_offering(
        db,
        school_id=offering.school_id,
        offering_id=offering.id,
        teacher_user_id=user_id,
    ):
        return offering, True

    if membership.role == "student" and lesson_repo.is_student_enrolled_in_offering(
        db,
        school_id=offering.school_id,
        class_group_id=offering.class_group_id,
        offering_id=offering.id,
        student_user_id=user_id,
    ):
        return offering, False

    raise AppError(403, "FORBIDDEN", "You do not have access to this subject offering.")


def create_lesson(
    db: Session,
    *,
    offering_id: uuid.UUID,
    payload: LessonCreateRequest,
    actor_user_id: uuid.UUID,
) -> Lesson:
    offering = _get_offering_and_check_teacher(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    now = _utcnow()
    lesson = Lesson(
        school_id=offering.school_id,
        subject_offering_id=offering.id,
        created_by_user_id=actor_user_id,
        title=payload.title.strip(),
        content=payload.content,
        status=payload.status,
        published_at=now if payload.status == "published" else None,
    )
    db.add(lesson)
    db.flush()

    record_audit_event(
        db,
        action="lesson.created",
        target_type="lesson",
        target_id=lesson.id,
        actor_user_id=actor_user_id,
        school_id=offering.school_id,
        metadata={"subject_offering_id": str(offering.id), "status": lesson.status},
    )
    db.commit()
    db.refresh(lesson)
    return lesson


def list_lessons(
    db: Session,
    *,
    offering_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    status: str | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Lesson], int]:
    offering, is_teacher = _check_offering_read_access(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    return lesson_repo.list_lessons_for_offering(
        db,
        school_id=offering.school_id,
        offering_id=offering.id,
        published_only=not is_teacher,
        status=status if is_teacher else None,
        q=q,
        offset=offset,
        limit=limit,
    )


def update_lesson(
    db: Session,
    *,
    offering_id: uuid.UUID,
    lesson_id: uuid.UUID,
    payload: LessonUpdateRequest,
    actor_user_id: uuid.UUID,
) -> Lesson:
    offering = _get_offering_and_check_teacher(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    lesson = lesson_repo.get_lesson_for_offering(
        db, school_id=offering.school_id, offering_id=offering.id, lesson_id=lesson_id
    )
    if lesson is None:
        raise AppError(404, "LESSON_NOT_FOUND", "Lesson not found.")

    if payload.title is not None:
        lesson.title = payload.title.strip()
    if payload.content is not None:
        lesson.content = payload.content
    if payload.status is not None:
        lesson.status = payload.status
        if payload.status == "published" and lesson.published_at is None:
            lesson.published_at = _utcnow()

    record_audit_event(
        db,
        action="lesson.updated",
        target_type="lesson",
        target_id=lesson.id,
        actor_user_id=actor_user_id,
        school_id=offering.school_id,
        metadata={"status": lesson.status},
    )
    db.commit()
    db.refresh(lesson)
    return lesson


def attach_file_to_lesson(
    db: Session,
    *,
    offering_id: uuid.UUID,
    lesson_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    raw_filename: str,
    content: bytes,
    storage_dir: str,
    max_bytes: int,
) -> StoredFile:
    offering = _get_offering_and_check_teacher(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    lesson = lesson_repo.get_lesson_for_offering(
        db, school_id=offering.school_id, offering_id=offering.id, lesson_id=lesson_id
    )
    if lesson is None:
        raise AppError(404, "LESSON_NOT_FOUND", "Lesson not found.")

    saved = save_uploaded_file(
        storage_dir=storage_dir,
        raw_filename=raw_filename,
        content=content,
        max_bytes=max_bytes,
    )
    stored = StoredFile(
        school_id=offering.school_id,
        uploaded_by_user_id=actor_user_id,
        lesson_id=lesson.id,
        original_filename=saved.original_filename,
        storage_key=saved.storage_key,
        content_type=saved.content_type,
        size_bytes=saved.size_bytes,
        sha256_checksum=saved.sha256_checksum,
    )
    db.add(stored)
    db.flush()

    record_audit_event(
        db,
        action="lesson_attachment.uploaded",
        target_type="stored_file",
        target_id=stored.id,
        actor_user_id=actor_user_id,
        school_id=offering.school_id,
        metadata={"lesson_id": str(lesson.id), "size_bytes": stored.size_bytes},
    )
    db.commit()
    db.refresh(stored)
    return stored


def authorize_and_resolve_file_download(
    db: Session,
    *,
    file_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    storage_dir: str,
) -> tuple[StoredFile, Path]:
    stored = lesson_repo.get_stored_file_by_id(db, file_id=file_id)
    if stored is None:
        raise AppError(404, "FILE_NOT_FOUND", "File not found.")

    if stored.lesson_id is None or stored.lesson is None:
        raise AppError(403, "FORBIDDEN", "You do not have permission to download this file.")

    _offering, is_teacher = _check_offering_read_access(
        db,
        offering_id=stored.lesson.subject_offering_id,
        user_id=actor_user_id,
    )
    if not is_teacher and stored.lesson.status != "published":
        raise AppError(403, "FORBIDDEN", "You do not have permission to download this file.")

    path = resolve_stored_file_path(
        storage_dir=storage_dir, storage_key=stored.storage_key
    )
    return stored, path
