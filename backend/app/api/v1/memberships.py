import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    SchoolAuthContext,
    get_app_settings,
    get_email_provider,
    require_school_role,
)
from app.core.config import Settings
from app.db.session import get_db
from app.services.email import EmailProvider
from app.schemas.membership import (
    MembershipUpdateRequest,
    SchoolUserCreateRequest,
    SchoolUserResponse,
)
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
    get_pagination_params,
)
from app.services.membership import (
    create_school_user,
    list_school_users,
    update_school_membership,
)

router = APIRouter(prefix="/schools/{school_id}", tags=["school-users"])

require_school_admin = require_school_role({"school_admin"})


def _to_school_user_response(user, membership) -> SchoolUserResponse:
    return SchoolUserResponse(
        membership_id=membership.id,
        school_id=membership.school_id,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role=membership.role,
        status=membership.status,
        created_at=membership.created_at,
        updated_at=membership.updated_at,
    )


@router.post(
    "/users",
    response_model=SchoolUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a school user and assign a role (School Admin)",
)
def create_school_user_endpoint(
    payload: SchoolUserCreateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> SchoolUserResponse:
    user, membership = create_school_user(
        db,
        school_id=school_auth.school.id,
        payload=payload,
        actor_user_id=school_auth.user.id,
        email_provider=email_provider,
        frontend_base_url=settings.frontend_base_url,
    )
    return _to_school_user_response(user, membership)


@router.get(
    "/users",
    response_model=PaginatedResponse[SchoolUserResponse],
    summary="List users belonging to this school with pagination and filtering (School Admin)",
)
def list_school_users_endpoint(
    role: str | None = Query(default=None),
    membership_status: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=100, description="Search by email or name"),
    pagination: PaginationParams = Depends(get_pagination_params),
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[SchoolUserResponse]:
    rows, total = list_school_users(
        db,
        school_id=school_auth.school.id,
        role=role,
        status=membership_status,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_school_user_response(user, membership) for user, membership in rows],
        total=total,
        pagination=pagination,
    )


@router.patch(
    "/memberships/{membership_id}",
    response_model=SchoolUserResponse,
    summary="Update or revoke a school membership (School Admin)",
)
def update_school_membership_endpoint(
    membership_id: uuid.UUID,
    payload: MembershipUpdateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> SchoolUserResponse:
    user, membership = update_school_membership(
        db,
        school_id=school_auth.school.id,
        membership_id=membership_id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return _to_school_user_response(user, membership)
