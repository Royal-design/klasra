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
from app.repositories import staff_invite_repo
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
    get_pagination_params,
)
from app.schemas.staff_invite import (
    StaffInviteAcceptRequest,
    StaffInviteAcceptResponse,
    StaffInviteCreateRequest,
    StaffInviteResponse,
)
from app.services import staff_invite as staff_invite_service
from app.services.email import EmailProvider

router = APIRouter(tags=["staff-invitations"])

require_school_admin = require_school_role({"school_admin"})


def _to_response(invite) -> StaffInviteResponse:
    return StaffInviteResponse(
        id=invite.id,
        school_id=invite.school_id,
        school_name=invite.school.name if invite.school else None,
        email=invite.email,
        full_name=invite.full_name,
        role=invite.role,
        status=staff_invite_service.compute_invite_status(invite),
        expires_at=invite.expires_at,
        accepted_at=invite.accepted_at,
        revoked_at=invite.revoked_at,
        created_at=invite.created_at,
    )


@router.post(
    "/schools/{school_id}/staff-invitations",
    response_model=StaffInviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a teacher or school admin by email to set their own password (School Admin)",
)
def create_staff_invitation_endpoint(
    payload: StaffInviteCreateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> StaffInviteResponse:
    invite = staff_invite_service.create_staff_invitation(
        db,
        school_id=school_auth.school.id,
        payload=payload,
        actor_user_id=school_auth.user.id,
        frontend_base_url=settings.frontend_base_url,
        email_provider=email_provider,
    )
    return _to_response(invite)


@router.get(
    "/schools/{school_id}/staff-invitations",
    response_model=PaginatedResponse[StaffInviteResponse],
    summary="List staff invitations for this school (School Admin)",
)
def list_staff_invitations_endpoint(
    q: str | None = Query(default=None, max_length=100),
    pagination: PaginationParams = Depends(get_pagination_params),
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[StaffInviteResponse]:
    items, total = staff_invite_repo.list_for_school(
        db,
        school_id=school_auth.school.id,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_response(inv) for inv in items], total=total, pagination=pagination
    )


@router.post(
    "/staff-invitations/accept",
    response_model=StaffInviteAcceptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Accept a single-use staff email invitation and set password",
)
def accept_staff_invitation_endpoint(
    payload: StaffInviteAcceptRequest,
    db: Session = Depends(get_db),
) -> StaffInviteAcceptResponse:
    user, membership = staff_invite_service.accept_staff_invitation(db, payload=payload)
    return StaffInviteAcceptResponse(
        user_id=user.id,
        membership_id=membership.id,
        school_id=membership.school_id,
        role=membership.role,
        status=membership.status,
    )
