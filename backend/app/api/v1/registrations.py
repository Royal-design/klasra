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
from app.repositories import registration_repo
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
    get_pagination_params,
)
from app.schemas.registration import (
    RegistrationCodeCreateRequest,
    RegistrationCodeCreateResponse,
    StudentEmailInviteCreateRequest,
    StudentEmailInviteCreateResponse,
    StudentRegistrationApproveRequest,
    StudentRegistrationRejectRequest,
    StudentRegistrationResponse,
    StudentSelfRegisterRequest,
)
from app.services import registration as registration_service
from app.services.email import EmailProvider

router = APIRouter(tags=["registrations"])

require_school_admin = require_school_role({"school_admin"})


def _to_registration_response(reg_request, user) -> StudentRegistrationResponse:
    return StudentRegistrationResponse(
        id=reg_request.id,
        school_id=reg_request.school_id,
        user_id=reg_request.user_id,
        membership_id=reg_request.membership_id,
        email=user.email,
        full_name=user.full_name,
        status=reg_request.status,
        student_reference=reg_request.student_reference,
        decision_notes=reg_request.decision_notes,
        reviewed_by_user_id=reg_request.reviewed_by_user_id,
        reviewed_at=reg_request.reviewed_at,
        created_at=reg_request.created_at,
        updated_at=reg_request.updated_at,
    )


@router.post(
    "/registrations/students",
    response_model=StudentRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a pending student self-registration using a school code or invitation",
)
def student_self_register_endpoint(
    payload: StudentSelfRegisterRequest,
    db: Session = Depends(get_db),
) -> StudentRegistrationResponse:
    reg_request, user = registration_service.submit_student_self_registration(
        db, payload=payload
    )
    return _to_registration_response(reg_request, user)


@router.post(
    "/schools/{school_id}/registrations/codes",
    response_model=RegistrationCodeCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a short-lived cohort registration code (School Admin)",
)
def create_registration_code_endpoint(
    payload: RegistrationCodeCreateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> RegistrationCodeCreateResponse:
    invite, raw_code = registration_service.create_registration_code(
        db,
        school_id=school_auth.school.id,
        payload=payload,
        actor_user_id=school_auth.user.id,
    )
    return RegistrationCodeCreateResponse(
        id=invite.id,
        school_id=invite.school_id,
        invite_type=invite.invite_type,
        code=raw_code,
        label=invite.label,
        max_uses=invite.max_uses,
        expires_at=invite.expires_at,
    )


@router.post(
    "/schools/{school_id}/registrations/invitations",
    response_model=StudentEmailInviteCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a single-use student email invitation via Resend (School Admin)",
)
def create_student_email_invite_endpoint(
    payload: StudentEmailInviteCreateRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> StudentEmailInviteCreateResponse:
    invite = registration_service.create_student_email_invitation(
        db,
        school_id=school_auth.school.id,
        payload=payload,
        actor_user_id=school_auth.user.id,
        frontend_base_url=settings.frontend_base_url,
        email_provider=email_provider,
    )
    assert invite.invited_email is not None
    return StudentEmailInviteCreateResponse(
        id=invite.id,
        school_id=invite.school_id,
        invite_type=invite.invite_type,
        invited_email=invite.invited_email,
        label=invite.label,
        expires_at=invite.expires_at,
    )


@router.get(
    "/schools/{school_id}/registrations/students",
    response_model=PaginatedResponse[StudentRegistrationResponse],
    summary="List student registration requests with pagination and filtering (School Admin)",
)
def list_student_registrations_endpoint(
    request_status: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=100, description="Search by email, name, or reference"),
    pagination: PaginationParams = Depends(get_pagination_params),
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[StudentRegistrationResponse]:
    rows, total = registration_repo.list_registration_requests_for_school(
        db,
        school_id=school_auth.school.id,
        status=request_status,
        q=q,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return build_paginated_response(
        [_to_registration_response(reg_req, user) for reg_req, user in rows],
        total=total,
        pagination=pagination,
    )


@router.post(
    "/schools/{school_id}/registrations/students/{request_id}/approve",
    response_model=StudentRegistrationResponse,
    summary="Approve a pending student registration and optionally enroll into a class group",
)
def approve_student_registration_endpoint(
    request_id: uuid.UUID,
    payload: StudentRegistrationApproveRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> StudentRegistrationResponse:
    reg_request, user = registration_service.approve_student_registration(
        db,
        school_id=school_auth.school.id,
        request_id=request_id,
        payload=payload,
        actor_user_id=school_auth.user.id,
        email_provider=email_provider,
    )
    return _to_registration_response(reg_request, user)


@router.post(
    "/schools/{school_id}/registrations/students/{request_id}/reject",
    response_model=StudentRegistrationResponse,
    summary="Reject a pending student registration request",
)
def reject_student_registration_endpoint(
    request_id: uuid.UUID,
    payload: StudentRegistrationRejectRequest,
    school_auth: SchoolAuthContext = Depends(require_school_admin),
    db: Session = Depends(get_db),
    email_provider: EmailProvider = Depends(get_email_provider),
) -> StudentRegistrationResponse:
    reg_request, user = registration_service.reject_student_registration(
        db,
        school_id=school_auth.school.id,
        request_id=request_id,
        payload=payload,
        actor_user_id=school_auth.user.id,
        email_provider=email_provider,
    )
    return _to_registration_response(reg_request, user)
