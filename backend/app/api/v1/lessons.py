import uuid

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import (
    AuthContext,
    get_app_settings,
    get_current_auth,
    get_storage_backend,
    verify_csrf,
)
from app.core.config import Settings
from app.db.session import get_db
from app.schemas.lesson import (
    CompleteUploadRequest,
    DownloadUrlResponse,
    LessonCreateRequest,
    LessonResponse,
    LessonUpdateRequest,
    PresignUploadRequest,
    PresignUploadResponse,
    StoredFileSummary,
)
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
    get_pagination_params,
)
from app.services import lesson as lesson_service
from app.services.file_storage import StorageBackend

router = APIRouter(tags=["lessons-and-files"])


def _to_lesson_response(lesson) -> LessonResponse:
    return LessonResponse(
        id=lesson.id,
        school_id=lesson.school_id,
        subject_offering_id=lesson.subject_offering_id,
        created_by_user_id=lesson.created_by_user_id,
        author_full_name=lesson.author.full_name if lesson.author else None,
        title=lesson.title,
        content=lesson.content,
        video_url=lesson.video_url,
        status=lesson.status,
        published_at=lesson.published_at,
        attachments=[
            StoredFileSummary.model_validate(att) for att in (lesson.attachments or [])
        ],
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
    )


@router.post(
    "/offerings/{offering_id}/lessons",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or publish a lesson for an assigned subject offering (Assigned Teacher)",
)
def create_lesson_endpoint(
    offering_id: uuid.UUID,
    payload: LessonCreateRequest,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> LessonResponse:
    lesson = lesson_service.create_lesson(
        db,
        offering_id=offering_id,
        payload=payload,
        actor_user_id=auth.user.id,
    )
    return _to_lesson_response(lesson)


@router.get(
    "/offerings/{offering_id}/lessons",
    response_model=PaginatedResponse[LessonResponse],
    summary="List lessons for a subject offering (Assigned Teacher or Enrolled Student)",
)
def list_lessons_endpoint(
    offering_id: uuid.UUID,
    lesson_status: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=100),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[LessonResponse]:
    lessons, total = lesson_service.list_lessons(
        db,
        offering_id=offering_id,
        actor_user_id=auth.user.id,
        status=lesson_status,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_lesson_response(lesson) for lesson in lessons],
        total=total,
        pagination=pagination,
    )


@router.patch(
    "/offerings/{offering_id}/lessons/{lesson_id}",
    response_model=LessonResponse,
    summary="Update or publish/unpublish a lesson (Assigned Teacher)",
)
def update_lesson_endpoint(
    offering_id: uuid.UUID,
    lesson_id: uuid.UUID,
    payload: LessonUpdateRequest,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
) -> LessonResponse:
    lesson = lesson_service.update_lesson(
        db,
        offering_id=offering_id,
        lesson_id=lesson_id,
        payload=payload,
        actor_user_id=auth.user.id,
    )
    return _to_lesson_response(lesson)


@router.post(
    "/offerings/{offering_id}/lessons/{lesson_id}/attachments",
    response_model=StoredFileSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an allow-listed learning material or video attachment to a lesson (Assigned Teacher)",
)
async def upload_lesson_attachment_endpoint(
    offering_id: uuid.UUID,
    lesson_id: uuid.UUID,
    file: UploadFile = File(...),
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    storage_backend: StorageBackend = Depends(get_storage_backend),
) -> StoredFileSummary:
    content = await file.read()
    stored = lesson_service.attach_file_to_lesson(
        db,
        offering_id=offering_id,
        lesson_id=lesson_id,
        actor_user_id=auth.user.id,
        raw_filename=file.filename or "attachment",
        content=content,
        storage_backend=storage_backend,
        max_bytes=settings.max_upload_bytes,
        max_video_bytes=settings.max_video_upload_bytes,
    )
    return StoredFileSummary.model_validate(stored)


@router.post(
    "/offerings/{offering_id}/lessons/{lesson_id}/attachments/presign",
    response_model=PresignUploadResponse,
    summary="Request a short-lived S3 presigned PUT URL for direct lesson attachment/video upload (Assigned Teacher)",
)
def presign_lesson_attachment_endpoint(
    offering_id: uuid.UUID,
    lesson_id: uuid.UUID,
    payload: PresignUploadRequest,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    storage_backend: StorageBackend = Depends(get_storage_backend),
) -> PresignUploadResponse:
    return lesson_service.presign_lesson_attachment_upload(
        db,
        offering_id=offering_id,
        lesson_id=lesson_id,
        payload=payload,
        actor_user_id=auth.user.id,
        storage_backend=storage_backend,
        max_bytes=settings.max_upload_bytes,
        max_video_bytes=settings.max_video_upload_bytes,
        expires_in=settings.presigned_url_ttl_seconds,
    )


@router.post(
    "/offerings/{offering_id}/lessons/{lesson_id}/attachments/complete",
    response_model=StoredFileSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Verify and register a directly uploaded S3 lesson attachment/video (Assigned Teacher)",
)
def complete_lesson_attachment_endpoint(
    offering_id: uuid.UUID,
    lesson_id: uuid.UUID,
    payload: CompleteUploadRequest,
    auth: AuthContext = Depends(verify_csrf),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    storage_backend: StorageBackend = Depends(get_storage_backend),
) -> StoredFileSummary:
    stored = lesson_service.complete_lesson_attachment_upload(
        db,
        offering_id=offering_id,
        lesson_id=lesson_id,
        payload=payload,
        actor_user_id=auth.user.id,
        storage_backend=storage_backend,
        max_bytes=settings.max_upload_bytes,
        max_video_bytes=settings.max_video_upload_bytes,
    )
    return StoredFileSummary.model_validate(stored)


@router.get(
    "/files/{file_id}/download",
    summary="Download an authorized file attachment",
)
def download_file_endpoint(
    file_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
    storage_backend: StorageBackend = Depends(get_storage_backend),
) -> Response:
    stored, file_bytes = lesson_service.authorize_and_fetch_file_bytes(
        db,
        file_id=file_id,
        actor_user_id=auth.user.id,
        storage_backend=storage_backend,
    )
    return Response(
        content=file_bytes,
        media_type=stored.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{stored.original_filename}"'
        },
    )


@router.get(
    "/files/{file_id}/download-url",
    response_model=DownloadUrlResponse,
    summary="Get a short-lived signed download/playback URL (S3) or proxy download path (local)",
)
def get_file_download_url_endpoint(
    file_id: uuid.UUID,
    inline: bool = Query(default=False, description="Set true for inline video/PDF playback"),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    storage_backend: StorageBackend = Depends(get_storage_backend),
) -> DownloadUrlResponse:
    return lesson_service.authorize_and_get_download_url(
        db,
        file_id=file_id,
        actor_user_id=auth.user.id,
        storage_backend=storage_backend,
        expires_in=settings.presigned_url_ttl_seconds,
        inline=inline,
    )
