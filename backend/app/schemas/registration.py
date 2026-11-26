import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegistrationCodeCreateRequest(BaseModel):
    label: str | None = Field(default=None, max_length=120)
    max_uses: int = Field(default=50, ge=1, le=1000)
    expires_in_hours: int = Field(default=72, ge=1, le=720)


class RegistrationCodeCreateResponse(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    invite_type: str
    code: str
    label: str | None
    max_uses: int
    expires_at: datetime


class StudentEmailInviteCreateRequest(BaseModel):
    email: EmailStr
    label: str | None = Field(default=None, max_length=120)
    expires_in_hours: int = Field(default=72, ge=1, le=720)


class StudentEmailInviteCreateResponse(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    invite_type: str
    invited_email: str
    label: str | None
    expires_at: datetime


class StudentSelfRegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=12, max_length=128)
    code_or_token: str = Field(min_length=6, max_length=256)
    student_reference: str | None = Field(default=None, max_length=100)


class StudentRegistrationApproveRequest(BaseModel):
    class_group_id: uuid.UUID | None = None
    effective_from: date | None = None
    decision_notes: str | None = Field(default=None, max_length=500)


class StudentRegistrationRejectRequest(BaseModel):
    decision_notes: str | None = Field(default=None, max_length=500)


class StudentRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    user_id: uuid.UUID
    membership_id: uuid.UUID
    email: str
    full_name: str
    status: str
    student_reference: str | None
    decision_notes: str | None
    reviewed_by_user_id: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
