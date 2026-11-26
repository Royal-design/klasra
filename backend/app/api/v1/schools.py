import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_platform_admin
from app.db.session import get_db
from app.schemas.school import (
    SchoolCreateRequest,
    SchoolCreateResponse,
    SchoolResponse,
    SchoolUpdateRequest,
)
from app.services.school import create_school_with_admin, list_schools, update_school

router = APIRouter(prefix="/schools", tags=["schools"])


@router.post(
    "",
    response_model=SchoolCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a school and its initial school administrator (Platform Admin)",
)
def create_school_endpoint(
    payload: SchoolCreateRequest,
    auth: AuthContext = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> SchoolCreateResponse:
    school, admin_user, membership = create_school_with_admin(
        db, payload=payload, actor_user_id=auth.user.id
    )
    return SchoolCreateResponse(
        school=SchoolResponse.model_validate(school),
        initial_admin_user_id=admin_user.id,
        initial_admin_membership_id=membership.id,
    )


@router.get(
    "",
    response_model=list[SchoolResponse],
    summary="List all schools (Platform Admin)",
)
def list_schools_endpoint(
    _auth: AuthContext = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[SchoolResponse]:
    schools = list_schools(db)
    return [SchoolResponse.model_validate(s) for s in schools]


@router.patch(
    "/{school_id}",
    response_model=SchoolResponse,
    summary="Update a school's name or status (Platform Admin)",
)
def update_school_endpoint(
    school_id: uuid.UUID,
    payload: SchoolUpdateRequest,
    auth: AuthContext = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> SchoolResponse:
    school = update_school(
        db, school_id=school_id, payload=payload, actor_user_id=auth.user.id
    )
    return SchoolResponse.model_validate(school)
