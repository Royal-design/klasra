import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_app_settings, get_current_auth, verify_csrf
from app.core.config import Settings
from app.db.session import get_db
from app.schemas.assignment import (
    AssignmentCreateRequest,
    AssignmentResponse,
    AssignmentUpdateRequest,
    SubmissionResponse,
)
from app.schemas.lesson import StoredFileSummary
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
    get_pagination_params,
)
from app.services import assignment as assignment_service

router = APIRouter(tags=["assignments-and-submissions"])


def _to_assignment_response(assignment) -> AssignmentResponse:
    return AssignmentResponse(
        id=assignment.id,
        school_id=assignment.school_id,
        subject_offering_id=assignment.subject_offering_id,
        created_by_user_id=assignment.created_by_user_id,
        author_full_name=assignment.author.full_name if assignment.author else None,
        title=assignment.title,
        instructions=assignment.instructions,
        due_at=assignment.due_at,
        max_score=assignment.max_score,
        allow_late_submissions=assignment.allow_late_submissions,
        allow_resubmissions=assignment.allow_resubmissions,
        status=assignment.status,
        published_at=assignment.published_at,
        attachments=[
            StoredFileSummary.model_validate(att)
            for att in (assignment.attachments or [])
        ],
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
    )


def _to_submission_response(submission) -> SubmissionResponse:
    return SubmissionResponse(
        id=submission.id,
        school_id=submission.school_id,
        assignment_id=submission.assignment_id,
        student_user_id=submission.student_user_id,
        student_full_name=submission.student.full_name if submission.student else None,
        student_email=submission.student.email if submission.student else None,
        version_number=submission.version_number,
        is_latest=submission.is_latest,
        text_content=submission.text_content,
        is_late=submission.is_late,
        submitted_at=submission.submitted_at,
        attachments=[
            StoredFileSummary.model_validate(att)
            for att in (submission.attachments or [])
        ],
        created_at=submission.created_at,
    )


@router.post(
    "/offerings/{offering_id}/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an assignment for an assigned subject offering (Assigned Teacher)",
)
def create_assignment_endpoint(
    offering_id: uuid.UUID,
    payload: AssignmentCreateRequest,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    assignment = assignment_service.create_assignment(
        db,
        offering_id=offering_id,
        payload=payload,
        actor_user_id=auth.user.id,
    )
    return _to_assignment_response(assignment)


@router.get(
    "/offerings/{offering_id}/assignments",
    response_model=PaginatedResponse[AssignmentResponse],
    summary="List assignments for a subject offering (Assigned Teacher or Enrolled Student)",
)
def list_assignments_endpoint(
    offering_id: uuid.UUID,
    assignment_status: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=100),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AssignmentResponse]:
    items, total = assignment_service.list_assignments(
        db,
        offering_id=offering_id,
        actor_user_id=auth.user.id,
        status=assignment_status,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_assignment_response(a) for a in items], total=total, pagination=pagination
    )


@router.patch(
    "/offerings/{offering_id}/assignments/{assignment_id}",
    response_model=AssignmentResponse,
    summary="Update assignment details, policy, or publish status (Assigned Teacher)",
)
def update_assignment_endpoint(
    offering_id: uuid.UUID,
    assignment_id: uuid.UUID,
    payload: AssignmentUpdateRequest,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    assignment = assignment_service.update_assignment(
        db,
        offering_id=offering_id,
        assignment_id=assignment_id,
        payload=payload,
        actor_user_id=auth.user.id,
    )
    return _to_assignment_response(assignment)


@router.post(
    "/offerings/{offering_id}/assignments/{assignment_id}/attachments",
    response_model=StoredFileSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an attachment to an assignment (Assigned Teacher)",
)
async def upload_assignment_attachment_endpoint(
    offering_id: uuid.UUID,
    assignment_id: uuid.UUID,
    file: UploadFile = File(...),
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> StoredFileSummary:
    content = await file.read()
    stored = assignment_service.attach_file_to_assignment(
        db,
        offering_id=offering_id,
        assignment_id=assignment_id,
        actor_user_id=auth.user.id,
        raw_filename=file.filename or "attachment",
        content=content,
        storage_dir=settings.upload_storage_dir,
        max_bytes=settings.max_upload_bytes,
    )
    return StoredFileSummary.model_validate(stored)


@router.post(
    "/assignments/{assignment_id}/submissions",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit typed text and/or file uploads for an assignment (Enrolled Student)",
)
async def create_submission_endpoint(
    assignment_id: uuid.UUID,
    text_content: str | None = Form(default=None),
    files: list[UploadFile] = File(default=[]),
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> SubmissionResponse:
    uploaded: list[tuple[str, bytes]] = []
    for upload in files:
        data = await upload.read()
        uploaded.append((upload.filename or "submission", data))

    submission = assignment_service.create_student_submission(
        db,
        assignment_id=assignment_id,
        actor_user_id=auth.user.id,
        text_content=text_content,
        uploaded_files=uploaded,
        storage_dir=settings.upload_storage_dir,
        max_bytes=settings.max_upload_bytes,
    )
    return _to_submission_response(submission)


@router.get(
    "/assignments/{assignment_id}/submissions",
    response_model=PaginatedResponse[SubmissionResponse],
    summary="List submissions (Assigned Teacher sees all; Enrolled Student sees own history only)",
)
def list_submissions_endpoint(
    assignment_id: uuid.UUID,
    student_user_id: uuid.UUID | None = Query(default=None),
    latest_only: bool = Query(default=False),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[SubmissionResponse]:
    items, total = assignment_service.list_submissions(
        db,
        assignment_id=assignment_id,
        actor_user_id=auth.user.id,
        student_user_id=student_user_id,
        latest_only=latest_only,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_submission_response(s) for s in items], total=total, pagination=pagination
    )
