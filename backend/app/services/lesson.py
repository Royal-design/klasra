import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.academic import SubjectOffering
from app.models.lesson import Lesson, StoredFile
from app.repositories import lesson_repo, membership_repo
from app.schemas.lesson import (
    CompleteUploadRequest,
    DownloadUrlResponse,
    LessonCreateRequest,
    LessonUpdateRequest,
    PresignUploadRequest,
    PresignUploadResponse,
)
from app.services.audit import record_audit_event
from app.services.file_storage import (
    ALLOWED_FILE_TYPES,
    ALLOWED_VIDEO_TYPES,
    STORAGE_KEY_PATTERN,
    StorageBackend,
    prepare_presigned_upload,
    sanitize_display_filename,
    save_uploaded_file,
    validate_magic_bytes,
)


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


def _authorize_file_access(
    db: Session, *, file_id: uuid.UUID, actor_user_id: uuid.UUID
) -> StoredFile:
    stored = lesson_repo.get_stored_file_by_id(db, file_id=file_id)
    if stored is None:
        raise AppError(404, "FILE_NOT_FOUND", "File not found.")

    if stored.lesson_id is not None and stored.lesson is not None:
        _offering, is_teacher = _check_offering_read_access(
            db,
            offering_id=stored.lesson.subject_offering_id,
            user_id=actor_user_id,
        )
        if not is_teacher and stored.lesson.status != "published":
            raise AppError(403, "FORBIDDEN", "You do not have permission to download this file.")
    elif stored.assignment_id is not None and stored.assignment is not None:
        _offering, is_teacher = _check_offering_read_access(
            db,
            offering_id=stored.assignment.subject_offering_id,
            user_id=actor_user_id,
        )
        if not is_teacher and stored.assignment.status != "published":
            raise AppError(403, "FORBIDDEN", "You do not have permission to download this file.")
    elif stored.submission_id is not None and stored.submission is not None:
        assignment = stored.submission.assignment
        if assignment is None:
            raise AppError(403, "FORBIDDEN", "You do not have permission to download this file.")
        _offering, is_teacher = _check_offering_read_access(
            db,
            offering_id=assignment.subject_offering_id,
            user_id=actor_user_id,
        )
        if not is_teacher and stored.submission.student_user_id != actor_user_id:
            raise AppError(403, "FORBIDDEN", "You do not have permission to download this file.")
    else:
        raise AppError(403, "FORBIDDEN", "You do not have permission to download this file.")

    return stored


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
        video_url=payload.video_url,
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
    if "video_url" in payload.model_fields_set:
        lesson.video_url = payload.video_url
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
    storage_backend: StorageBackend,
    max_bytes: int,
    max_video_bytes: int,
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
        storage_backend=storage_backend,
        raw_filename=raw_filename,
        content=content,
        max_bytes=max_bytes,
        allow_video=True,
        max_video_bytes=max_video_bytes,
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


def presign_lesson_attachment_upload(
    db: Session,
    *,
    offering_id: uuid.UUID,
    lesson_id: uuid.UUID,
    payload: PresignUploadRequest,
    actor_user_id: uuid.UUID,
    storage_backend: StorageBackend,
    max_bytes: int,
    max_video_bytes: int,
    expires_in: int,
) -> PresignUploadResponse:
    offering = _get_offering_and_check_teacher(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    lesson = lesson_repo.get_lesson_for_offering(
        db, school_id=offering.school_id, offering_id=offering.id, lesson_id=lesson_id
    )
    if lesson is None:
        raise AppError(404, "LESSON_NOT_FOUND", "Lesson not found.")

    if not storage_backend.supports_presigned_urls:
        raise AppError(
            400,
            "PRESIGNED_URLS_UNSUPPORTED",
            "Direct presigned uploads require STORAGE_PROVIDER=s3. Use the multipart upload endpoint instead.",
        )

    display_name, storage_key, content_type, _limit = prepare_presigned_upload(
        raw_filename=payload.filename,
        size_bytes=payload.size_bytes,
        max_bytes=max_bytes,
        allow_video=True,
        max_video_bytes=max_video_bytes,
    )
    upload_url = storage_backend.generate_presigned_upload_url(
        storage_key=storage_key,
        content_type=content_type,
        expires_in=expires_in,
    )
    return PresignUploadResponse(
        upload_url=upload_url,
        storage_key=storage_key,
        original_filename=display_name,
        content_type=content_type,
        expires_in_seconds=expires_in,
    )


def complete_lesson_attachment_upload(
    db: Session,
    *,
    offering_id: uuid.UUID,
    lesson_id: uuid.UUID,
    payload: CompleteUploadRequest,
    actor_user_id: uuid.UUID,
    storage_backend: StorageBackend,
    max_bytes: int,
    max_video_bytes: int,
) -> StoredFile:
    offering = _get_offering_and_check_teacher(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    lesson = lesson_repo.get_lesson_for_offering(
        db, school_id=offering.school_id, offering_id=offering.id, lesson_id=lesson_id
    )
    if lesson is None:
        raise AppError(404, "LESSON_NOT_FOUND", "Lesson not found.")

    if not storage_backend.supports_presigned_urls:
        raise AppError(
            400,
            "PRESIGNED_URLS_UNSUPPORTED",
            "Direct presigned uploads require STORAGE_PROVIDER=s3.",
        )

    if not STORAGE_KEY_PATTERN.match(payload.storage_key):
        raise AppError(400, "INVALID_STORAGE_KEY", "Invalid storage key format.")

    if lesson_repo.get_stored_file_by_storage_key(db, storage_key=payload.storage_key) is not None:
        raise AppError(409, "DUPLICATE_STORAGE_KEY", "This uploaded file has already been registered.")

    display_name = sanitize_display_filename(payload.original_filename)
    ext = Path(display_name).suffix.lower()
    allowed = {**ALLOWED_FILE_TYPES, **ALLOWED_VIDEO_TYPES}
    if ext not in allowed or not payload.storage_key.endswith(ext):
        raise AppError(
            415,
            "UNSUPPORTED_FILE_TYPE",
            "File extension does not match an allow-listed type or storage key.",
        )

    actual_size, _stored_ct = storage_backend.head_object(storage_key=payload.storage_key)
    effective_limit = max_video_bytes if ext in ALLOWED_VIDEO_TYPES else max_bytes
    if actual_size <= 0:
        raise AppError(400, "EMPTY_FILE", "Uploaded file cannot be empty.")
    if actual_size > effective_limit:
        raise AppError(
            413,
            "FILE_TOO_LARGE",
            f"Uploaded object exceeds the maximum allowed size of {effective_limit // (1024 * 1024)} MB.",
        )

    header_bytes = storage_backend.read_head_bytes(storage_key=payload.storage_key, num_bytes=32)
    validate_magic_bytes(ext, header_bytes, header_only=True)

    stored = StoredFile(
        school_id=offering.school_id,
        uploaded_by_user_id=actor_user_id,
        lesson_id=lesson.id,
        original_filename=display_name,
        storage_key=payload.storage_key,
        content_type=allowed[ext],
        size_bytes=actual_size,
        sha256_checksum="s3-direct-upload",
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
        metadata={
            "lesson_id": str(lesson.id),
            "size_bytes": stored.size_bytes,
            "upload_mode": "presigned",
        },
    )
    db.commit()
    db.refresh(stored)
    return stored


def authorize_and_fetch_file_bytes(
    db: Session,
    *,
    file_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    storage_backend: StorageBackend,
) -> tuple[StoredFile, bytes]:
    stored = _authorize_file_access(db, file_id=file_id, actor_user_id=actor_user_id)
    content = storage_backend.get_bytes(storage_key=stored.storage_key)
    return stored, content


def authorize_and_get_download_url(
    db: Session,
    *,
    file_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    storage_backend: StorageBackend,
    expires_in: int,
    inline: bool = False,
) -> DownloadUrlResponse:
    stored = _authorize_file_access(db, file_id=file_id, actor_user_id=actor_user_id)
    if storage_backend.supports_presigned_urls:
        url = storage_backend.generate_presigned_download_url(
            storage_key=stored.storage_key,
            filename=stored.original_filename,
            content_type=stored.content_type,
            expires_in=expires_in,
            inline=inline,
        )
        return DownloadUrlResponse(
            file_id=stored.id,
            url=url,
            expires_in_seconds=expires_in,
            content_type=stored.content_type,
            original_filename=stored.original_filename,
            mode="presigned",
        )
    return DownloadUrlResponse(
        file_id=stored.id,
        url=f"/api/v1/files/{stored.id}/download",
        expires_in_seconds=0,
        content_type=stored.content_type,
        original_filename=stored.original_filename,
        mode="proxy",
    )
