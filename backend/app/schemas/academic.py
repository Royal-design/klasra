import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# --- Academic Years ---
class AcademicYearCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_dates(self) -> "AcademicYearCreateRequest":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date.")
        return self


class AcademicYearUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    status: Literal["active", "archived"] | None = None


class AcademicYearResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    name: str
    start_date: date
    end_date: date
    status: str
    created_at: datetime
    updated_at: datetime


# --- Terms ---
class TermCreateRequest(BaseModel):
    academic_year_id: uuid.UUID
    name: str = Field(min_length=2, max_length=100)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_dates(self) -> "TermCreateRequest":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date.")
        return self


class TermUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    start_date: date | None = None
    end_date: date | None = None


class TermResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    academic_year_id: uuid.UUID
    name: str
    start_date: date
    end_date: date
    created_at: datetime
    updated_at: datetime


# --- Year Levels ---
class YearLevelCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    display_order: int = Field(default=0, ge=0, le=1000)


class YearLevelUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    display_order: int | None = Field(default=None, ge=0, le=1000)


class YearLevelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    name: str
    display_order: int
    created_at: datetime
    updated_at: datetime


# --- Class Groups ---
class ClassGroupCreateRequest(BaseModel):
    academic_year_id: uuid.UUID
    year_level_id: uuid.UUID
    name: str = Field(min_length=1, max_length=100)


class ClassGroupUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class ClassGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    academic_year_id: uuid.UUID
    year_level_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime


# --- Subjects ---
class SubjectCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=2, max_length=150)


class SubjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    code: str
    name: str
    created_at: datetime
    updated_at: datetime


# --- Subject Offerings ---
class SubjectOfferingCreateRequest(BaseModel):
    class_group_id: uuid.UUID
    subject_id: uuid.UUID
    term_id: uuid.UUID | None = None
    teacher_user_ids: list[uuid.UUID] = Field(default_factory=list)


class SubjectOfferingUpdateRequest(BaseModel):
    status: Literal["active", "archived"] | None = None


class OfferingTeacherAssignRequest(BaseModel):
    teacher_user_id: uuid.UUID


class SubjectOfferingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    class_group_id: uuid.UUID
    subject_id: uuid.UUID
    term_id: uuid.UUID | None
    status: str
    teacher_user_ids: list[uuid.UUID] = []
    created_at: datetime
    updated_at: datetime


# --- Enrollments ---
class EnrollmentCreateRequest(BaseModel):
    student_user_id: uuid.UUID
    class_group_id: uuid.UUID
    subject_offering_id: uuid.UUID | None = None
    effective_from: date


class EnrollmentTransferRequest(BaseModel):
    target_class_group_id: uuid.UUID
    target_subject_offering_id: uuid.UUID | None = None
    effective_date: date


class EnrollmentWithdrawRequest(BaseModel):
    effective_date: date


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    student_user_id: uuid.UUID
    academic_year_id: uuid.UUID
    class_group_id: uuid.UUID
    subject_offering_id: uuid.UUID | None
    status: str
    effective_from: date
    effective_to: date | None
    created_at: datetime
    updated_at: datetime


class EnrollmentTransferResponse(BaseModel):
    previous_enrollment: EnrollmentResponse
    new_enrollment: EnrollmentResponse
