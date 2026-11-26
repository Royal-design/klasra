import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GradeUpsertRequest(BaseModel):
    score: float = Field(ge=0)
    letter_grade: str | None = Field(default=None, max_length=10)
    feedback: str | None = Field(default=None, max_length=10000)
    is_published: bool = True


class GradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    school_name: str | None = None
    submission_id: uuid.UUID
    assignment_id: uuid.UUID
    assignment_title: str | None = None
    subject_name: str | None = None
    subject_code: str | None = None
    class_group_name: str | None = None
    student_user_id: uuid.UUID
    student_full_name: str | None = None
    graded_by_user_id: uuid.UUID | None
    graded_by_full_name: str | None = None
    score: float
    max_score: float
    letter_grade: str | None
    feedback: str | None
    is_published: bool
    published_at: datetime | None
    graded_at: datetime
    created_at: datetime
    updated_at: datetime
