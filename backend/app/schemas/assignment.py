import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.lesson import StoredFileSummary

AssignmentStatus = Literal["draft", "published"]


class AssignmentCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    instructions: str = Field(min_length=1, max_length=50000)
    due_at: datetime | None = None
    max_score: float = Field(default=100.0, gt=0, le=10000)
    allow_late_submissions: bool = True
    allow_resubmissions: bool = True
    status: AssignmentStatus = "published"


class AssignmentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    instructions: str | None = Field(default=None, min_length=1, max_length=50000)
    due_at: datetime | None = None
    max_score: float | None = Field(default=None, gt=0, le=10000)
    allow_late_submissions: bool | None = None
    allow_resubmissions: bool | None = None
    status: AssignmentStatus | None = None


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    subject_offering_id: uuid.UUID
    created_by_user_id: uuid.UUID | None
    author_full_name: str | None = None
    title: str
    instructions: str
    due_at: datetime | None
    max_score: float
    allow_late_submissions: bool
    allow_resubmissions: bool
    status: str
    published_at: datetime | None
    attachments: list[StoredFileSummary] = []
    created_at: datetime
    updated_at: datetime


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    assignment_id: uuid.UUID
    student_user_id: uuid.UUID
    student_full_name: str | None = None
    student_email: str | None = None
    version_number: int
    is_latest: bool
    text_content: str | None
    is_late: bool
    submitted_at: datetime
    attachments: list[StoredFileSummary] = []
    created_at: datetime
