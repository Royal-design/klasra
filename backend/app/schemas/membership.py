import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.normalizers import normalize_enum_str, normalize_required_text

SchoolRole = Literal["school_admin", "teacher", "student"]
MembershipStatus = Literal["pending", "active", "revoked"]


class SchoolUserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=12, max_length=128)
    role: SchoolRole

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value: str) -> str:
        return normalize_required_text(value)

    @field_validator("role", mode="before")
    @classmethod
    def clean_role(cls, value: object) -> object:
        return normalize_enum_str(value)


class MembershipUpdateRequest(BaseModel):
    role: SchoolRole | None = None
    status: MembershipStatus | None = None

    @field_validator("role", "status", mode="before")
    @classmethod
    def clean_enums(cls, value: object) -> object:
        return normalize_enum_str(value)


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
