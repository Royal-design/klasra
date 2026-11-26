import uuid

from pydantic import BaseModel


class ImportRowError(BaseModel):
    row: int
    field: str
    code: str
    message: str


class ImportPreviewRow(BaseModel):
    row: int
    email: str
    full_name: str
    role: str
    academic_year: str | None = None
    class_group: str | None = None


class ImportValidationResponse(BaseModel):
    total_rows: int
    valid_rows: int
    error_count: int
    errors: list[ImportRowError]
    preview: list[ImportPreviewRow]


class ImportCommitResponse(BaseModel):
    imported_users: int
    imported_memberships: int
    imported_enrollments: int
    created_user_ids: list[uuid.UUID]
