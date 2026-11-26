import csv
import io
import uuid
from dataclasses import dataclass
from datetime import date

import openpyxl
from email_validator import EmailNotValidError, validate_email
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import generate_token, hash_password
from app.models.academic import ClassGroup, Enrollment
from app.repositories import academic_repo, membership_repo, user_repo
from app.schemas.imports import (
    ImportCommitResponse,
    ImportPreviewRow,
    ImportRowError,
    ImportValidationResponse,
)
from app.services.audit import record_audit_event

MAX_SPREADSHEET_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
ALLOWED_IMPORT_ROLES = {"teacher", "student"}
REQUIRED_COLUMNS = {"email", "full_name", "role"}
XLSX_MAGIC_BYTES = b"PK\x03\x04"


@dataclass
class _ValidatedImportRow:
    row_number: int
    email: str
    full_name: str
    role: str
    class_group: ClassGroup | None


def _parse_rows(filename: str, content: bytes) -> list[tuple[int, dict[str, str]]]:
    if len(content) > MAX_SPREADSHEET_BYTES:
        raise AppError(
            status_code=413,
            code="FILE_TOO_LARGE",
            message="Spreadsheet exceeds the 5 MB size limit.",
        )

    lower_name = (filename or "").lower()
    ext = ".csv" if lower_name.endswith(".csv") else (".xlsx" if lower_name.endswith(".xlsx") else "")
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError(
            status_code=415,
            code="UNSUPPORTED_FILE_TYPE",
            message="Only .csv and .xlsx spreadsheet files are supported.",
        )

    if ext == ".csv":
        try:
            text_content = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise AppError(
                status_code=400,
                code="INVALID_CSV_ENCODING",
                message="CSV file must be UTF-8 encoded.",
            ) from exc

        reader = csv.DictReader(io.StringIO(text_content))
        if not reader.fieldnames:
            raise AppError(400, "EMPTY_SPREADSHEET", "Spreadsheet has no header row.")
        normalized_headers = {h.strip().lower() for h in reader.fieldnames if h}
        missing = REQUIRED_COLUMNS - normalized_headers
        if missing:
            raise AppError(
                422,
                "MISSING_COLUMNS",
                f"Missing required columns: {', '.join(sorted(missing))}.",
            )

        rows: list[tuple[int, dict[str, str]]] = []
        for idx, raw_row in enumerate(reader, start=2):
            normalized = {
                (k.strip().lower() if k else ""): (v.strip() if isinstance(v, str) else "")
                for k, v in raw_row.items()
            }
            if not any(normalized.values()):
                continue
            rows.append((idx, normalized))
        return rows

    # .xlsx magic byte check + read-only safe parse (defusedxml is installed)
    if not content.startswith(XLSX_MAGIC_BYTES):
        raise AppError(
            status_code=415,
            code="INVALID_XLSX_CONTENT",
            message="File content does not match a valid .xlsx workbook.",
        )

    try:
        wb = openpyxl.load_workbook(
            filename=io.BytesIO(content), read_only=True, data_only=True
        )
    except Exception as exc:
        raise AppError(
            status_code=400,
            code="INVALID_XLSX_WORKBOOK",
            message="Could not parse the uploaded .xlsx workbook.",
        ) from exc

    try:
        ws = wb.active
        if ws is None:
            raise AppError(400, "EMPTY_SPREADSHEET", "Workbook contains no active sheet.")

        iterator = ws.iter_rows(values_only=True)
        header_row = next(iterator, None)
        if not header_row:
            raise AppError(400, "EMPTY_SPREADSHEET", "Spreadsheet has no header row.")

        headers = [str(cell).strip().lower() if cell is not None else "" for cell in header_row]
        missing = REQUIRED_COLUMNS - set(headers)
        if missing:
            raise AppError(
                422,
                "MISSING_COLUMNS",
                f"Missing required columns: {', '.join(sorted(missing))}.",
            )

        rows = []
        for idx, values in enumerate(iterator, start=2):
            normalized = {
                headers[i]: (str(values[i]).strip() if i < len(values) and values[i] is not None else "")
                for i in range(len(headers))
                if headers[i]
            }
            if not any(normalized.values()):
                continue
            rows.append((idx, normalized))
        return rows
    finally:
        wb.close()


def _validate_rows(
    db: Session, *, school_id: uuid.UUID, filename: str, content: bytes
) -> tuple[list[_ValidatedImportRow], list[ImportRowError], list[ImportPreviewRow]]:
    raw_rows = _parse_rows(filename, content)
    validated: list[_ValidatedImportRow] = []
    errors: list[ImportRowError] = []
    preview: list[ImportPreviewRow] = []
    seen_emails: set[str] = set()

    for row_num, row in raw_rows:
        row_has_error = False
        raw_email = row.get("email", "").strip().lower()
        full_name = row.get("full_name", "").strip()
        role = row.get("role", "").strip().lower()
        academic_year_name = row.get("academic_year", "").strip() or None
        class_group_name = row.get("class_group", "").strip() or None

        # Validate email
        if not raw_email:
            errors.append(
                ImportRowError(
                    row=row_num, field="email", code="REQUIRED", message="Email is required."
                )
            )
            row_has_error = True
        else:
            try:
                validate_email(raw_email, check_deliverability=False)
            except EmailNotValidError:
                errors.append(
                    ImportRowError(
                        row=row_num,
                        field="email",
                        code="INVALID_EMAIL",
                        message="Email address is not valid.",
                    )
                )
                row_has_error = True

        if raw_email and raw_email in seen_emails:
            errors.append(
                ImportRowError(
                    row=row_num,
                    field="email",
                    code="DUPLICATE_IN_FILE",
                    message="Duplicate email address within spreadsheet.",
                )
            )
            row_has_error = True
        elif raw_email:
            seen_emails.add(raw_email)

        if len(full_name) < 2:
            errors.append(
                ImportRowError(
                    row=row_num,
                    field="full_name",
                    code="INVALID_NAME",
                    message="Full name must be at least 2 characters.",
                )
            )
            row_has_error = True

        if role not in ALLOWED_IMPORT_ROLES:
            errors.append(
                ImportRowError(
                    row=row_num,
                    field="role",
                    code="INVALID_ROLE",
                    message="Role must be 'teacher' or 'student'.",
                )
            )
            row_has_error = True

        # Database checks
        if not row_has_error:
            existing_user = user_repo.get_user_by_email(db, email=raw_email)
            if existing_user is not None:
                existing_membership = membership_repo.get_user_membership_in_school(
                    db, user_id=existing_user.id, school_id=school_id
                )
                if existing_membership is not None:
                    errors.append(
                        ImportRowError(
                            row=row_num,
                            field="email",
                            code="MEMBERSHIP_EXISTS",
                            message="User already has a membership in this school.",
                        )
                    )
                    row_has_error = True
                elif role == "teacher":
                    other_teacher = membership_repo.get_active_teacher_membership_elsewhere(
                        db, user_id=existing_user.id, exclude_school_id=school_id
                    )
                    if other_teacher is not None:
                        errors.append(
                            ImportRowError(
                                row=row_num,
                                field="role",
                                code="TEACHER_SINGLE_SCHOOL_VIOLATION",
                                message="Teacher is already actively associated with another school.",
                            )
                        )
                        row_has_error = True

        # Optional class_group lookup for students
        resolved_group: ClassGroup | None = None
        if class_group_name:
            if role != "student":
                errors.append(
                    ImportRowError(
                        row=row_num,
                        field="class_group",
                        code="CLASS_GROUP_STUDENTS_ONLY",
                        message="class_group enrollment is only valid for student rows.",
                    )
                )
                row_has_error = True
            else:
                if not academic_year_name:
                    errors.append(
                        ImportRowError(
                            row=row_num,
                            field="academic_year",
                            code="ACADEMIC_YEAR_REQUIRED",
                            message="academic_year is required when class_group is provided.",
                        )
                    )
                    row_has_error = True
                else:
                    year = academic_repo.get_academic_year_by_name(
                        db, school_id=school_id, name=academic_year_name
                    )
                    if year is None:
                        errors.append(
                            ImportRowError(
                                row=row_num,
                                field="academic_year",
                                code="ACADEMIC_YEAR_NOT_FOUND",
                                message=f"Academic year '{academic_year_name}' not found.",
                            )
                        )
                        row_has_error = True
                    else:
                        resolved_group = academic_repo.get_class_group_by_year_and_name(
                            db,
                            school_id=school_id,
                            academic_year_id=year.id,
                            name=class_group_name,
                        )
                        if resolved_group is None:
                            errors.append(
                                ImportRowError(
                                    row=row_num,
                                    field="class_group",
                                    code="CLASS_GROUP_NOT_FOUND",
                                    message=f"Class group '{class_group_name}' not found in '{academic_year_name}'.",
                                )
                            )
                            row_has_error = True

        if not row_has_error:
            validated.append(
                _ValidatedImportRow(
                    row_number=row_num,
                    email=raw_email,
                    full_name=full_name,
                    role=role,
                    class_group=resolved_group,
                )
            )
            preview.append(
                ImportPreviewRow(
                    row=row_num,
                    email=raw_email,
                    full_name=full_name,
                    role=role,
                    academic_year=academic_year_name,
                    class_group=class_group_name,
                )
            )

    return validated, errors, preview


def validate_spreadsheet_import(
    db: Session, *, school_id: uuid.UUID, filename: str, content: bytes
) -> ImportValidationResponse:
    validated, errors, preview = _validate_rows(
        db, school_id=school_id, filename=filename, content=content
    )
    total_rows = len(validated) + len({e.row for e in errors})
    return ImportValidationResponse(
        total_rows=total_rows,
        valid_rows=len(validated),
        error_count=len(errors),
        errors=errors,
        preview=preview,
    )


def commit_spreadsheet_import(
    db: Session,
    *,
    school_id: uuid.UUID,
    filename: str,
    content: bytes,
    actor_user_id: uuid.UUID,
) -> ImportCommitResponse:
    validated, errors, _preview = _validate_rows(
        db, school_id=school_id, filename=filename, content=content
    )
    if errors:
        raise AppError(
            status_code=422,
            code="IMPORT_VALIDATION_FAILED",
            message="Spreadsheet contains validation errors. Fix all errors before committing.",
            details=[e.model_dump() for e in errors],
        )

    created_user_ids: list[uuid.UUID] = []
    imported_memberships = 0
    imported_enrollments = 0
    today = date.today()

    for item in validated:
        user = user_repo.get_user_by_email(db, email=item.email)
        if user is None:
            # Cryptographically random password placeholder until account activation flow (Slice 4/5).
            placeholder_password = generate_token(24)
            user = user_repo.create_user(
                db,
                email=item.email,
                full_name=item.full_name,
                password_hash=hash_password(placeholder_password),
                is_platform_admin=False,
                is_active=True,
            )
            db.flush()
            created_user_ids.append(user.id)

        membership_repo.create_membership(
            db,
            user_id=user.id,
            school_id=school_id,
            role=item.role,
            status="active",
        )
        imported_memberships += 1

        if item.class_group is not None:
            db.add(
                Enrollment(
                    school_id=school_id,
                    student_user_id=user.id,
                    academic_year_id=item.class_group.academic_year_id,
                    class_group_id=item.class_group.id,
                    subject_offering_id=None,
                    status="active",
                    effective_from=today,
                )
            )
            imported_enrollments += 1

    record_audit_event(
        db,
        action="import.committed",
        target_type="school",
        target_id=school_id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "filename": filename,
            "imported_users": len(created_user_ids),
            "imported_memberships": imported_memberships,
            "imported_enrollments": imported_enrollments,
        },
    )
    db.commit()

    return ImportCommitResponse(
        imported_users=len(created_user_ids),
        imported_memberships=imported_memberships,
        imported_enrollments=imported_enrollments,
        created_user_ids=created_user_ids,
    )
