import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.assignment import Assignment, Submission
from app.models.lesson import StoredFile
from app.repositories import assignment_repo
from app.schemas.assignment import AssignmentCreateRequest, AssignmentUpdateRequest
from app.services.audit import record_audit_event
from app.services.file_storage import StorageBackend, save_uploaded_file
from app.services.lesson import (
    _check_offering_read_access,
    _get_offering_and_check_teacher,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def create_assignment(
    db: Session,
    *,
    offering_id: uuid.UUID,
    payload: AssignmentCreateRequest,
    actor_user_id: uuid.UUID,
) -> Assignment:
    offering = _get_offering_and_check_teacher(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    now = _utcnow()
    assignment = Assignment(
        school_id=offering.school_id,
        subject_offering_id=offering.id,
        created_by_user_id=actor_user_id,
        title=payload.title.strip(),
        instructions=payload.instructions,
        due_at=payload.due_at,
        max_score=payload.max_score,
        allow_late_submissions=payload.allow_late_submissions,
        allow_resubmissions=payload.allow_resubmissions,
        status=payload.status,
        published_at=now if payload.status == "published" else None,
    )
    db.add(assignment)
    db.flush()

    record_audit_event(
        db,
        action="assignment.created",
        target_type="assignment",
        target_id=assignment.id,
        actor_user_id=actor_user_id,
        school_id=offering.school_id,
        metadata={"subject_offering_id": str(offering.id), "status": assignment.status},
    )
    db.commit()
    db.refresh(assignment)
    return assignment


def list_assignments(
    db: Session,
    *,
    offering_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    status: str | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Assignment], int]:
    offering, is_teacher = _check_offering_read_access(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    return assignment_repo.list_assignments_for_offering(
        db,
        school_id=offering.school_id,
        offering_id=offering.id,
        published_only=not is_teacher,
        status=status if is_teacher else None,
        q=q,
        offset=offset,
        limit=limit,
    )


def update_assignment(
    db: Session,
    *,
    offering_id: uuid.UUID,
    assignment_id: uuid.UUID,
    payload: AssignmentUpdateRequest,
    actor_user_id: uuid.UUID,
) -> Assignment:
    offering = _get_offering_and_check_teacher(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    assignment = assignment_repo.get_assignment_for_offering(
        db,
        school_id=offering.school_id,
        offering_id=offering.id,
        assignment_id=assignment_id,
    )
    if assignment is None:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "Assignment not found.")

    if payload.title is not None:
        assignment.title = payload.title.strip()
    if payload.instructions is not None:
        assignment.instructions = payload.instructions
    if payload.due_at is not None:
        assignment.due_at = payload.due_at
    if payload.max_score is not None:
        assignment.max_score = payload.max_score
    if payload.allow_late_submissions is not None:
        assignment.allow_late_submissions = payload.allow_late_submissions
    if payload.allow_resubmissions is not None:
        assignment.allow_resubmissions = payload.allow_resubmissions
    if payload.status is not None:
        assignment.status = payload.status
        if payload.status == "published" and assignment.published_at is None:
            assignment.published_at = _utcnow()

    record_audit_event(
        db,
        action="assignment.updated",
        target_type="assignment",
        target_id=assignment.id,
        actor_user_id=actor_user_id,
        school_id=offering.school_id,
        metadata={"status": assignment.status},
    )
    db.commit()
    db.refresh(assignment)
    return assignment


def attach_file_to_assignment(
    db: Session,
    *,
    offering_id: uuid.UUID,
    assignment_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    raw_filename: str,
    content: bytes,
    storage_backend: StorageBackend,
    max_bytes: int,
) -> StoredFile:
    offering = _get_offering_and_check_teacher(
        db, offering_id=offering_id, user_id=actor_user_id
    )
    assignment = assignment_repo.get_assignment_for_offering(
        db,
        school_id=offering.school_id,
        offering_id=offering.id,
        assignment_id=assignment_id,
    )
    if assignment is None:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "Assignment not found.")

    saved = save_uploaded_file(
        storage_backend=storage_backend,
        raw_filename=raw_filename,
        content=content,
        max_bytes=max_bytes,
    )
    stored = StoredFile(
        school_id=offering.school_id,
        uploaded_by_user_id=actor_user_id,
        assignment_id=assignment.id,
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
        action="assignment_attachment.uploaded",
        target_type="stored_file",
        target_id=stored.id,
        actor_user_id=actor_user_id,
        school_id=offering.school_id,
        metadata={"assignment_id": str(assignment.id), "size_bytes": stored.size_bytes},
    )
    db.commit()
    db.refresh(stored)
    return stored


def create_student_submission(
    db: Session,
    *,
    assignment_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    text_content: str | None,
    uploaded_files: list[tuple[str, bytes]],
    storage_backend: StorageBackend,
    max_bytes: int,
) -> Submission:
    """ASSIGN-02 & ASSIGN-03: Enrolled student submits text and/or files with version history."""
    assignment = assignment_repo.get_assignment_by_id(db, assignment_id=assignment_id)
    if assignment is None:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "Assignment not found.")

    _offering, is_teacher = _check_offering_read_access(
        db, offering_id=assignment.subject_offering_id, user_id=actor_user_id
    )
    if is_teacher:
        raise AppError(403, "FORBIDDEN", "Only enrolled students can submit assignments.")

    if assignment.status != "published":
        raise AppError(403, "FORBIDDEN", "This assignment is not open for submission.")

    cleaned_text = text_content.strip() if text_content and text_content.strip() else None
    if cleaned_text is None and not uploaded_files:
        raise AppError(
            422,
            "EMPTY_SUBMISSION",
            "Submission must include typed text, at least one file attachment, or both.",
        )

    now = _utcnow()
    is_late = assignment.due_at is not None and now > _as_utc(assignment.due_at)
    if is_late and not assignment.allow_late_submissions:
        raise AppError(
            409,
            "LATE_SUBMISSION_NOT_ALLOWED",
            "Late submissions are not allowed for this assignment.",
        )

    previous_version = assignment_repo.get_latest_submission_version(
        db,
        school_id=assignment.school_id,
        assignment_id=assignment.id,
        student_user_id=actor_user_id,
    )
    if previous_version > 0 and not assignment.allow_resubmissions:
        raise AppError(
            409,
            "RESUBMISSION_NOT_ALLOWED",
            "Resubmissions are not allowed for this assignment.",
        )

    # Validate & store all uploaded files before committing submission row
    saved_uploads = [
        save_uploaded_file(
            storage_backend=storage_backend,
            raw_filename=fname,
            content=fbytes,
            max_bytes=max_bytes,
        )
        for fname, fbytes in uploaded_files
    ]

    if previous_version > 0:
        assignment_repo.mark_previous_submissions_not_latest(
            db,
            school_id=assignment.school_id,
            assignment_id=assignment.id,
            student_user_id=actor_user_id,
        )

    submission = Submission(
        school_id=assignment.school_id,
        assignment_id=assignment.id,
        student_user_id=actor_user_id,
        version_number=previous_version + 1,
        is_latest=True,
        text_content=cleaned_text,
        is_late=is_late,
        submitted_at=now,
    )
    db.add(submission)
    db.flush()

    for saved in saved_uploads:
        db.add(
            StoredFile(
                school_id=assignment.school_id,
                uploaded_by_user_id=actor_user_id,
                submission_id=submission.id,
                original_filename=saved.original_filename,
                storage_key=saved.storage_key,
                content_type=saved.content_type,
                size_bytes=saved.size_bytes,
                sha256_checksum=saved.sha256_checksum,
            )
        )

    record_audit_event(
        db,
        action="submission.created",
        target_type="submission",
        target_id=submission.id,
        actor_user_id=actor_user_id,
        school_id=assignment.school_id,
        metadata={
            "assignment_id": str(assignment.id),
            "version_number": submission.version_number,
            "is_late": submission.is_late,
            "file_count": len(saved_uploads),
        },
    )
    db.commit()
    db.refresh(submission)
    return submission


def list_submissions(
    db: Session,
    *,
    assignment_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    student_user_id: uuid.UUID | None = None,
    latest_only: bool = False,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Submission], int]:
    assignment = assignment_repo.get_assignment_by_id(db, assignment_id=assignment_id)
    if assignment is None:
        raise AppError(404, "ASSIGNMENT_NOT_FOUND", "Assignment not found.")

    _offering, is_teacher = _check_offering_read_access(
        db, offering_id=assignment.subject_offering_id, user_id=actor_user_id
    )

    # Enrolled students can ONLY view their own submissions (never other students')
    scoped_student_id = student_user_id if is_teacher else actor_user_id
    return assignment_repo.list_submissions_for_assignment(
        db,
        school_id=assignment.school_id,
        assignment_id=assignment.id,
        student_user_id=scoped_student_id,
        latest_only=latest_only,
        offset=offset,
        limit=limit,
    )
