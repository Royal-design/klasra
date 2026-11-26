import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

SchoolRole = Literal["school_admin", "teacher", "student"]
MembershipStatus = Literal["pending", "active", "revoked"]


class SchoolUserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=12, max_length=128)
    role: SchoolRole


class MembershipUpdateRequest(BaseModel):
    role: SchoolRole | None = None
    status: MembershipStatus | None = None


class SchoolUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    membership_id: uuid.UUID
    school_id: uuid.UUID
    user_id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    role: str
    status: str
    created_at: datetime
    updated_at: datetime
