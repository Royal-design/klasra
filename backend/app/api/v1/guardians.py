import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    AuthContext,
    SchoolAuthContext,
    get_app_settings,
    get_current_auth,
    get_email_provider,
    require_school_role,
)
from app.core.config import Settings
from app.db.session import get_db
from app.repositories import guardian_repo
from app.schemas.guardian import (
    GuardianDecisionRequest,
    GuardianInviteCreateRequest,
    GuardianLinkResponse,
    GuardianVerifyRequest,
    ParentChildSummary,
)
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
    get_pagination_params,
)
from app.services import guardian as guardian_service
from app.services.email import EmailProvider

router = APIRouter(tags=["guardians"])

require_school_admin = require_school_role({"school_admin"})


def _to_link_response(link) -> GuardianLinkResponse:
    return GuardianLinkResponse(
        id=link.id,
        school_id=link.school_id,
        school_name=link.school.name if link.school else None,
        student_user_id=link.student_user_id,
        student_full_name=link.student.full_name if link.student else None,
        student_email=link.student.email if link.student else None,
        parent_user_id=link.parent_user_id,
        guardian_email=link.guardian_email,
        guardian_full_name=link.guardian_full_name,
        relationship_label=link.relationship_label,
        status=link.status,
        verified_at=link.verified_at,
        approved_by_user_id=link.approved_by_user_id,
        approved_at=link.approved_at,
        revoked_by_user_id=link.revoked_by_user_id,
        revoked_at=link.revoked_at,
        decision_notes=link.decision_notes,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


@router.post(
    "/schools/{school_id}/guardian-links/invite",
    response_model=GuardianLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a parent/guardian relationship and email a verification link (School Admin)",
)
def invite_guardian_endpoint(
    payload: GuardianInviteCreateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> GuardianLinkResponse:
    link = guardian_service.invite_guardian(
        db,
        school_id=school_auth.school.id,
        payload=payload,
        actor_user_id=school_auth.user.id,
        frontend_base_url=settings.frontend_base_url,
        email_provider=email_provider,
    )
    return _to_link_response(link)


@router.get(
    "/schools/{school_id}/guardian-links",
    response_model=PaginatedResponse[GuardianLinkResponse],
    summary="List guardian links for this school with pagination and filtering (School Admin)",
)
def list_school_guardian_links_endpoint(
    student_user_id: uuid.UUID | None = Query(default=None),
    link_status: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=100),
    pagination: PaginationParams = Depends(get_pagination_params),
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[GuardianLinkResponse]:
    links, total = guardian_repo.list_links_for_school(
        db,
        school_id=school_auth.school.id,
        student_user_id=student_user_id,
        status=link_status,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_link_response(link) for link in links], total=total, pagination=pagination
    )


@router.post(
    "/guardian-links/verify",
    response_model=GuardianLinkResponse,
    summary="Verify parent email token and link to single parent account (remains pending approval)",
)
def verify_guardian_endpoint(
    payload: GuardianVerifyRequest,
    db: Session = Depends(get_db),
) -> GuardianLinkResponse:
    link = guardian_service.verify_guardian_invitation(db, payload=payload)
    return _to_link_response(link)


@router.post(
    "/schools/{school_id}/guardian-links/{link_id}/approve",
    response_model=GuardianLinkResponse,
    summary="Approve a verified parent/student link (School Admin)",
)
def approve_guardian_link_endpoint(
    link_id: uuid.UUID,
    payload: GuardianDecisionRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> GuardianLinkResponse:
    link = guardian_service.approve_guardian_link(
        db,
        school_id=school_auth.school.id,
        link_id=link_id,
        payload=payload,
        actor_user_id=school_auth.user.id,
        email_provider=email_provider,
    )
    return _to_link_response(link)


@router.post(
    "/schools/{school_id}/guardian-links/{link_id}/revoke",
    response_model=GuardianLinkResponse,
    summary="Revoke a parent/student link (School Admin)",
)
def revoke_guardian_link_endpoint(
    link_id: uuid.UUID,
    payload: GuardianDecisionRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> GuardianLinkResponse:
    link = guardian_service.revoke_guardian_link(
        db,
        school_id=school_auth.school.id,
        link_id=link_id,
        payload=payload,
        actor_user_id=school_auth.user.id,
        email_provider=email_provider,
    )
    return _to_link_response(link)


@router.get(
    "/parent/children",
    response_model=PaginatedResponse[ParentChildSummary],
    summary="List approved linked children across all schools for the signed-in parent",
)
def list_parent_children_endpoint(
    school_id: uuid.UUID | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    pagination: PaginationParams = Depends(get_pagination_params),
    auth: AuthContext = Depends(get_current_auth),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ParentChildSummary]:
    links, total = guardian_repo.list_approved_children_for_parent(
        db,
        parent_user_id=auth.user.id,
        school_id=school_id,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    items = [
        ParentChildSummary(
            link_id=link.id,
            school_id=link.school_id,
            school_name=link.school.name,
            school_slug=link.school.slug,
            student_user_id=link.student_user_id,
            student_full_name=link.student.full_name,
            relationship_label=link.relationship_label,
            approved_at=link.approved_at,
        )
        for link in links
        if link.school is not None and link.student is not None
    ]
    return build_paginated_response(items, total=total, pagination=pagination)
