import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LessonStatus = Literal["draft", "published"]


class LessonCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    content: str = Field(min_length=1, max_length=50000)
    status: LessonStatus = "published"


class LessonUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=50000)
    status: LessonStatus | None = None


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
    status: str
    published_at: datetime | None
    attachments: list[StoredFileSummary] = []
    created_at: datetime
    updated_at: datetime
