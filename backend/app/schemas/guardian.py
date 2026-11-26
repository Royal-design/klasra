import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class GuardianInviteCreateRequest(BaseModel):
    student_user_id: uuid.UUID
    guardian_email: EmailStr
    guardian_full_name: str = Field(min_length=2, max_length=200)
    relationship_label: str = Field(default="Guardian", min_length=2, max_length=50)
    expires_in_hours: int = Field(default=72, ge=1, le=720)


class GuardianVerifyRequest(BaseModel):
    token: str = Field(min_length=16, max_length=256)
    password: str = Field(min_length=12, max_length=128)


class GuardianDecisionRequest(BaseModel):
    decision_notes: str | None = Field(default=None, max_length=500)


class GuardianLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    school_name: str | None = None
    student_user_id: uuid.UUID
    student_full_name: str | None = None
    student_email: str | None = None
    parent_user_id: uuid.UUID | None
    guardian_email: str
    guardian_full_name: str
    relationship_label: str
    status: str
    verified_at: datetime | None
    approved_by_user_id: uuid.UUID | None
    approved_at: datetime | None
    revoked_by_user_id: uuid.UUID | None
    revoked_at: datetime | None
    decision_notes: str | None
    created_at: datetime
    updated_at: datetime


class ParentChildSummary(BaseModel):
    link_id: uuid.UUID
    school_id: uuid.UUID
    school_name: str
    school_slug: str
    student_user_id: uuid.UUID
    student_full_name: str
    relationship_label: str
    approved_at: datetime | None
