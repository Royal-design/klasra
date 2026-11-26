import html
import logging
import secrets
import uuid
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import generate_token, hash_password, hash_token
from app.models.academic import Enrollment
from app.models.registration import StudentInvite, StudentRegistrationRequest
from app.models.user import User
from app.repositories import (
    academic_repo,
    membership_repo,
    registration_repo,
    school_repo,
    user_repo,
)
from app.schemas.registration import (
    RegistrationCodeCreateRequest,
    StudentEmailInviteCreateRequest,
    StudentRegistrationApproveRequest,
    StudentRegistrationRejectRequest,
    StudentSelfRegisterRequest,
)
from app.services.audit import record_audit_event
from app.services.auth import revoke_all_user_sessions
from app.services.email import EmailMessage, EmailProvider

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _generate_short_code() -> str:
    # Human-shareable high-entropy code (e.g., 12 uppercase alphanumeric chars)
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(12))


def create_registration_code(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: RegistrationCodeCreateRequest,
    actor_user_id: uuid.UUID,
) -> tuple[StudentInvite, str]:
    raw_code = _generate_short_code()
    now = _utcnow()
    invite = StudentInvite(
        school_id=school_id,
        invite_type="registration_code",
        token_hash=hash_token(raw_code),
        invited_email=None,
        label=payload.label.strip() if payload.label else None,
        max_uses=payload.max_uses,
        use_count=0,
        expires_at=now + timedelta(hours=payload.expires_in_hours),
        created_by_user_id=actor_user_id,
        created_at=now,
    )
    db.add(invite)
    db.flush()

    record_audit_event(
        db,
        action="student_registration_code.created",
        target_type="student_invite",
        target_id=invite.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"label": invite.label, "max_uses": invite.max_uses},
    )
    db.commit()
    db.refresh(invite)
    return invite, raw_code


def create_student_email_invitation(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: StudentEmailInviteCreateRequest,
    actor_user_id: uuid.UUID,
    frontend_base_url: str,
    email_provider: EmailProvider,
) -> StudentInvite:
    normalized_email = str(payload.email).strip().lower()
    raw_token = generate_token(32)
    now = _utcnow()
    invite = StudentInvite(
        school_id=school_id,
        invite_type="email_invitation",
        token_hash=hash_token(raw_token),
        invited_email=normalized_email,
        label=payload.label.strip() if payload.label else None,
        max_uses=1,
        use_count=0,
        expires_at=now + timedelta(hours=payload.expires_in_hours),
        created_by_user_id=actor_user_id,
        created_at=now,
    )
    db.add(invite)
    db.flush()

    record_audit_event(
        db,
        action="student_invitation.created",
        target_type="student_invite",
        target_id=invite.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"invited_email": normalized_email, "label": invite.label},
    )
    db.commit()
    db.refresh(invite)

    school = school_repo.get_school_by_id(db, school_id=school_id)
    school_name = school.name if school else "your school"
    base = frontend_base_url.rstrip("/")
    register_url = f"{base}/register/student?{urlencode({'token': raw_token})}"

    safe_school = html.escape(school_name)
    safe_url = html.escape(register_url, quote=True)
    message = EmailMessage(
        to=normalized_email,
        subject=f"Invitation to register at {school_name}",
        text=(
            f"You have been invited to register as a student at {school_name}.\n\n"
            f"Complete your registration here (expires in {payload.expires_in_hours} hours):\n"
            f"{register_url}\n\n"
            "Your account will remain pending until a school administrator approves it."
        ),
        html=(
            f"<p>You have been invited to register as a student at <strong>{safe_school}</strong>.</p>"
            f'<p><a href="{safe_url}">Complete Student Registration</a></p>'
            "<p>Your account will remain pending until a school administrator approves it.</p>"
        ),
    )
    try:
        email_provider.send_email(message)
    except Exception:
        logger.exception("Failed to deliver student invitation email")

    return invite


def submit_student_self_registration(
    db: Session,
    *,
    payload: StudentSelfRegisterRequest,
) -> tuple[StudentRegistrationRequest, User]:
    """AUTH-02: Create a pending student account & registration request.

    A code or invitation token never grants immediate school access or elevated roles.
    """
    raw_code = payload.code_or_token.strip()
    invite = registration_repo.get_invite_by_token_hash(
        db, token_hash=hash_token(raw_code)
    )
    now = _utcnow()
    if (
        invite is None
        or invite.revoked_at is not None
        or _as_utc(invite.expires_at) <= now
        or invite.use_count >= invite.max_uses
    ):
        raise AppError(
            status_code=410,
            code="TOKEN_INVALID_OR_EXPIRED",
            message="Registration code or invitation is invalid, expired, or has been used.",
        )

    school = school_repo.get_school_by_id(db, school_id=invite.school_id)
    if school is None or school.status != "active":
        raise AppError(
            status_code=403,
            code="SCHOOL_INACTIVE",
            message="This school is not currently accepting registrations.",
        )

    normalized_email = str(payload.email).strip().lower()
    if invite.invite_type == "email_invitation" and invite.invited_email != normalized_email:
        raise AppError(
            status_code=403,
            code="INVITATION_EMAIL_MISMATCH",
            message="This invitation was issued for a different email address.",
        )

    if user_repo.get_user_by_email(db, email=normalized_email) is not None:
        raise AppError(
            status_code=409,
            code="USER_EMAIL_EXISTS",
            message="An account with this email already exists.",
        )

    user = user_repo.create_user(
        db,
        email=normalized_email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        is_platform_admin=False,
        is_active=True,
    )
    db.flush()

    # Always student role, always pending until school admin approves (AUTH-02)
    membership = membership_repo.create_membership(
        db,
        user_id=user.id,
        school_id=invite.school_id,
        role="student",
        status="pending",
    )
    db.flush()

    reg_request = StudentRegistrationRequest(
        school_id=invite.school_id,
        user_id=user.id,
        membership_id=membership.id,
        invite_id=invite.id,
        status="pending",
        student_reference=(
            payload.student_reference.strip() if payload.student_reference else None
        ),
    )
    invite.use_count += 1
    db.add(reg_request)
    db.flush()

    record_audit_event(
        db,
        action="student_registration.submitted",
        target_type="student_registration_request",
        target_id=reg_request.id,
        actor_user_id=user.id,
        school_id=invite.school_id,
        metadata={
            "invite_id": str(invite.id),
            "invite_type": invite.invite_type,
        },
    )
    db.commit()
    db.refresh(reg_request)
    db.refresh(user)
    return reg_request, user


def approve_student_registration(
    db: Session,
    *,
    school_id: uuid.UUID,
    request_id: uuid.UUID,
    payload: StudentRegistrationApproveRequest,
    actor_user_id: uuid.UUID,
    email_provider: EmailProvider,
) -> tuple[StudentRegistrationRequest, User]:
    reg_request = registration_repo.get_registration_request_for_school(
        db, school_id=school_id, request_id=request_id
    )
    if reg_request is None:
        raise AppError(
            status_code=404,
            code="REGISTRATION_REQUEST_NOT_FOUND",
            message="Student registration request not found.",
        )

    if reg_request.status != "pending":
        raise AppError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="This registration request has already been processed.",
        )

    membership = membership_repo.get_membership_for_school(
        db, school_id=school_id, membership_id=reg_request.membership_id
    )
    if membership is None:
        raise AppError(404, "MEMBERSHIP_NOT_FOUND", "Associated membership not found.")

    enrollment_id: uuid.UUID | None = None
    if payload.class_group_id is not None:
        group = academic_repo.get_class_group(
            db, school_id=school_id, class_group_id=payload.class_group_id
        )
        if group is None:
            raise AppError(404, "CLASS_GROUP_NOT_FOUND", "Class group not found.")
        enrollment = Enrollment(
            school_id=school_id,
            student_user_id=reg_request.user_id,
            academic_year_id=group.academic_year_id,
            class_group_id=group.id,
            subject_offering_id=None,
            status="active",
            effective_from=payload.effective_from or date.today(),
        )
        db.add(enrollment)
        db.flush()
        enrollment_id = enrollment.id

    now = _utcnow()
    membership.status = "active"
    reg_request.status = "approved"
    reg_request.decision_notes = (
        payload.decision_notes.strip() if payload.decision_notes else None
    )
    reg_request.reviewed_by_user_id = actor_user_id
    reg_request.reviewed_at = now

    record_audit_event(
        db,
        action="student_registration.approved",
        target_type="student_registration_request",
        target_id=reg_request.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "student_user_id": str(reg_request.user_id),
            "membership_id": str(membership.id),
            "enrollment_id": str(enrollment_id) if enrollment_id else None,
        },
    )
    db.commit()
    db.refresh(reg_request)

    user = user_repo.get_user_by_id(db, user_id=reg_request.user_id)
    assert user is not None
    school = school_repo.get_school_by_id(db, school_id=school_id)
    school_name = school.name if school else "your school"

    try:
        email_provider.send_email(
            EmailMessage(
                to=user.email,
                subject=f"Your registration at {school_name} was approved",
                text=(
                    f"Hello {user.full_name},\n\n"
                    f"Your student registration at {school_name} has been approved. "
                    "You can now sign in to access your classes."
                ),
                html=(
                    f"<p>Hello {html.escape(user.full_name)},</p>"
                    f"<p>Your student registration at <strong>{html.escape(school_name)}</strong> "
                    "has been approved. You can now sign in to access your classes.</p>"
                ),
            )
        )
    except Exception:
        logger.exception("Failed to send student approval notification email")

    return reg_request, user


def reject_student_registration(
    db: Session,
    *,
    school_id: uuid.UUID,
    request_id: uuid.UUID,
    payload: StudentRegistrationRejectRequest,
    actor_user_id: uuid.UUID,
    email_provider: EmailProvider,
) -> tuple[StudentRegistrationRequest, User]:
    reg_request = registration_repo.get_registration_request_for_school(
        db, school_id=school_id, request_id=request_id
    )
    if reg_request is None:
        raise AppError(
            status_code=404,
            code="REGISTRATION_REQUEST_NOT_FOUND",
            message="Student registration request not found.",
        )

    if reg_request.status != "pending":
        raise AppError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="This registration request has already been processed.",
        )

    membership = membership_repo.get_membership_for_school(
        db, school_id=school_id, membership_id=reg_request.membership_id
    )
    if membership is not None:
        membership.status = "revoked"

    now = _utcnow()
    reg_request.status = "rejected"
    reg_request.decision_notes = (
        payload.decision_notes.strip() if payload.decision_notes else None
    )
    reg_request.reviewed_by_user_id = actor_user_id
    reg_request.reviewed_at = now
    revoke_all_user_sessions(db, user_id=reg_request.user_id)

    record_audit_event(
        db,
        action="student_registration.rejected",
        target_type="student_registration_request",
        target_id=reg_request.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "student_user_id": str(reg_request.user_id),
            "decision_notes": reg_request.decision_notes,
        },
    )
    db.commit()
    db.refresh(reg_request)

    user = user_repo.get_user_by_id(db, user_id=reg_request.user_id)
    assert user is not None
    school = school_repo.get_school_by_id(db, school_id=school_id)
    school_name = school.name if school else "the school"

    try:
        email_provider.send_email(
            EmailMessage(
                to=user.email,
                subject=f"Update on your registration at {school_name}",
                text=(
                    f"Hello {user.full_name},\n\n"
                    f"Your student registration request for {school_name} was not approved. "
                    "Please contact the school office if you believe this is a mistake."
                ),
                html=(
                    f"<p>Hello {html.escape(user.full_name)},</p>"
                    f"<p>Your student registration request for <strong>{html.escape(school_name)}</strong> "
                    "was not approved. Please contact the school office if you believe this is a mistake.</p>"
                ),
            )
        )
    except Exception:
        logger.exception("Failed to send student rejection notification email")

    return reg_request, user
