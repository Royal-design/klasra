import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    AuthContext,
    get_app_settings,
    get_email_provider,
    require_platform_admin,
)
from app.core.config import Settings
from app.db.session import get_db
from app.services.email import EmailProvider
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
    get_pagination_params,
)
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
    settings: Settings = Depends(get_app_settings),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> SchoolCreateResponse:
    school, admin_user, membership = create_school_with_admin(
        db,
        payload=payload,
        actor_user_id=auth.user.id,
        email_provider=email_provider,
        frontend_base_url=settings.frontend_base_url,
    )
    return SchoolCreateResponse(
        school=SchoolResponse.model_validate(school),
        initial_admin_user_id=admin_user.id,
        initial_admin_membership_id=membership.id,
    )


@router.get(
    "",
    response_model=PaginatedResponse[SchoolResponse],
    summary="List all schools with pagination and filtering (Platform Admin)",
)
def list_schools_endpoint(
    school_status: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=100, description="Search by name or slug"),
    pagination: PaginationParams = Depends(get_pagination_params),
    _auth: AuthContext = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[SchoolResponse]:
    schools, total = list_schools(
        db,
        status=school_status,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [SchoolResponse.model_validate(s) for s in schools],
        total=total,
        pagination=pagination,
    )


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
