import uuid
from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.normalizers import normalize_enum_str

LessonStatus = Literal["draft", "published"]

ALLOWED_VIDEO_HOSTS = frozenset(
    {
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
        "vimeo.com",
        "player.vimeo.com",
        "loom.com",
        "www.loom.com",
    }
)


def _validate_video_url(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    parsed = urlparse(cleaned)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https":
        raise ValueError("Video URL must use https://.")
    if host not in ALLOWED_VIDEO_HOSTS:
        raise ValueError(
            "Video URL must be hosted on YouTube, Vimeo, or Loom."
        )
    if not parsed.path or parsed.path == "/":
        raise ValueError("Video URL must point to a specific video resource.")
    return cleaned


class LessonCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    content: str = Field(min_length=1, max_length=50000)
    video_url: str | None = Field(default=None, max_length=500)
    status: LessonStatus = "published"

    @field_validator("status", mode="before")
    @classmethod
    def clean_status(cls, value: object) -> object:
        return normalize_enum_str(value)

    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, value: str | None) -> str | None:
        return _validate_video_url(value)


class LessonUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=50000)
    video_url: str | None = Field(default=None, max_length=500)
    status: LessonStatus | None = None

    @field_validator("status", mode="before")
    @classmethod
    def clean_status(cls, value: object) -> object:
        return normalize_enum_str(value)

    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, value: str | None) -> str | None:
        return _validate_video_url(value)


class StoredFileSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    subject_offering_id: uuid.UUID
    created_by_user_id: uuid.UUID | None
    author_full_name: str | None = None
    title: str
    content: str
    video_url: str | None = None
    status: str
    published_at: datetime | None
    attachments: list[StoredFileSummary] = []
    created_at: datetime
    updated_at: datetime


class PresignUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)


class PresignUploadResponse(BaseModel):
    upload_url: str
    storage_key: str
    original_filename: str
    content_type: str
    expires_in_seconds: int


class CompleteUploadRequest(BaseModel):
    storage_key: str = Field(min_length=34, max_length=64)
    original_filename: str = Field(min_length=1, max_length=255)


class DownloadUrlResponse(BaseModel):
    file_id: uuid.UUID
    url: str
    expires_in_seconds: int
    content_type: str
    original_filename: str
    mode: Literal["presigned", "proxy"]
