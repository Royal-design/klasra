import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

StaffRole = Literal["teacher", "school_admin"]


class StaffInviteCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    role: StaffRole = "teacher"
    expires_in_hours: int = Field(default=72, ge=1, le=720)


class StaffInviteAcceptRequest(BaseModel):
    token: str = Field(min_length=16, max_length=256)
    password: str = Field(min_length=12, max_length=128)


class StaffInviteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    school_name: str | None = None
    email: str
    full_name: str
    role: str
    status: str
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class StaffInviteAcceptResponse(BaseModel):
    user_id: uuid.UUID
    membership_id: uuid.UUID
    school_id: uuid.UUID
    role: str
    status: str
