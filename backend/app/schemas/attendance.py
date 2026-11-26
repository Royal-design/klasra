import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.normalizers import normalize_enum_str

AttendanceStatus = Literal["present", "absent", "late", "excused"]


class AttendanceEntryInput(BaseModel):
    student_user_id: uuid.UUID
    status: AttendanceStatus
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("status", mode="before")
    @classmethod
    def clean_status(cls, value: object) -> object:
        return normalize_enum_str(value)


class AttendanceBatchUpsertRequest(BaseModel):
    attendance_date: date
    entries: list[AttendanceEntryInput] = Field(min_length=1, max_length=200)


class AttendanceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    school_name: str | None = None
    subject_offering_id: uuid.UUID
    subject_name: str | None = None
    subject_code: str | None = None
    class_group_name: str | None = None
    student_user_id: uuid.UUID
    student_full_name: str | None = None
    attendance_date: date
    status: str
    notes: str | None
    recorded_by_user_id: uuid.UUID | None
    recorded_by_full_name: str | None = None
    updated_by_user_id: uuid.UUID | None
    updated_by_full_name: str | None = None
    recorded_at: datetime
    updated_at: datetime
