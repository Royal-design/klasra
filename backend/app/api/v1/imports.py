from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import SchoolAuthContext, require_school_role
from app.db.session import get_db
from app.schemas.imports import ImportCommitResponse, ImportValidationResponse
from app.services.imports import commit_spreadsheet_import, validate_spreadsheet_import

router = APIRouter(prefix="/schools/{school_id}/imports", tags=["imports"])

require_school_admin = require_school_role({"school_admin"})


@router.post(
    "/validate",
    response_model=ImportValidationResponse,
    summary="Dry-run validate a CSV or XLSX student/staff spreadsheet",
)
async def validate_import_endpoint(
    file: UploadFile = File(...),
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> ImportValidationResponse:
    content = await file.read()
    return validate_spreadsheet_import(
        db,
        school_id=school_auth.school.id,
        filename=file.filename or "",
        content=content,
    )


@router.post(
    "/commit",
    response_model=ImportCommitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Validate and commit a CSV or XLSX student/staff spreadsheet",
)
async def commit_import_endpoint(
    file: UploadFile = File(...),
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> ImportCommitResponse:
    content = await file.read()
    return commit_spreadsheet_import(
        db,
        school_id=school_auth.school.id,
        filename=file.filename or "",
        content=content,
        actor_user_id=school_auth.user.id,
    )
