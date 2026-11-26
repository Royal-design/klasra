import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.normalizers import normalize_enum_str, normalize_required_text

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class InitialSchoolAdminInput(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value: str) -> str:
        return normalize_required_text(value)


class SchoolCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=100)
    initial_admin: InitialSchoolAdminInput

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return normalize_required_text(value)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not SLUG_PATTERN.match(normalized):
            raise ValueError("Slug must contain lowercase letters, numbers, and hyphens only.")
        return normalized


class SchoolUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    status: Literal["active", "suspended"] | None = None
    terminology_config: dict[str, str] | None = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        return normalize_required_text(value) if value is not None else None

    @field_validator("status", mode="before")
    @classmethod
    def clean_status(cls, value: object) -> object:
        return normalize_enum_str(value)


class SchoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    status: str
    terminology_config: dict[str, str] = {}
    created_at: datetime
    updated_at: datetime


class SchoolCreateResponse(BaseModel):
    school: SchoolResponse
    initial_admin_user_id: uuid.UUID
    initial_admin_membership_id: uuid.UUID
