import html
import logging
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import generate_token, hash_password, hash_token, verify_password
from app.models.membership import SchoolMembership
from app.models.staff_invite import StaffInvitation
from app.models.user import User
from app.repositories import membership_repo, school_repo, staff_invite_repo, user_repo
from app.schemas.staff_invite import StaffInviteAcceptRequest, StaffInviteCreateRequest
from app.services.audit import record_audit_event
from app.services.email import EmailMessage, EmailProvider

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def compute_invite_status(invite: StaffInvitation) -> str:
    if invite.accepted_at is not None:
        return "accepted"
    if invite.revoked_at is not None:
        return "revoked"
    if _as_utc(invite.expires_at) <= _utcnow():
        return "expired"
    return "pending"


def create_staff_invitation(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: StaffInviteCreateRequest,
    actor_user_id: uuid.UUID,
    frontend_base_url: str,
    email_provider: EmailProvider,
) -> StaffInvitation:
    """Invite a teacher or school_admin by email; they set their own password on accept."""
    normalized_email = str(payload.email).strip().lower()
    existing_user = user_repo.get_user_by_email(db, email=normalized_email)
    if existing_user is not None:
        if membership_repo.get_user_membership_in_school(
            db, user_id=existing_user.id, school_id=school_id
        ):
            raise AppError(
                status_code=409,
                code="MEMBERSHIP_EXISTS",
                message="This user already has a membership in this school.",
            )
        if payload.role == "teacher":
            other_teacher = membership_repo.get_active_teacher_membership_elsewhere(
                db, user_id=existing_user.id, exclude_school_id=school_id
            )
            if other_teacher is not None:
                raise AppError(
                    status_code=409,
                    code="TEACHER_SINGLE_SCHOOL_VIOLATION",
                    message="A teacher can only be actively associated with one school.",
                )

    now = _utcnow()
    staff_invite_repo.revoke_pending_for_email_in_school(
        db, school_id=school_id, email=normalized_email, revoked_at=now
    )

    raw_token = generate_token(32)
    invite = StaffInvitation(
        school_id=school_id,
        email=normalized_email,
        full_name=payload.full_name.strip(),
        role=payload.role,
        token_hash=hash_token(raw_token),
        expires_at=now + timedelta(hours=payload.expires_in_hours),
        created_by_user_id=actor_user_id,
        created_at=now,
    )
    db.add(invite)
    db.flush()

    record_audit_event(
        db,
        action="staff_invitation.created",
        target_type="staff_invitation",
        target_id=invite.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={"email": normalized_email, "role": invite.role},
    )
    db.commit()
    db.refresh(invite)

    school = school_repo.get_school_by_id(db, school_id=school_id)
    school_name = school.name if school else "your school"
    base = frontend_base_url.rstrip("/")
    accept_url = f"{base}/accept-staff-invite?{urlencode({'token': raw_token})}"

    message = EmailMessage(
        to=normalized_email,
        subject=f"You're invited to join {school_name} as {invite.role.replace('_', ' ')}",
        text=(
            f"Hello {invite.full_name},\n\n"
            f"You have been invited to join {school_name} as a {invite.role.replace('_', ' ')}.\n"
            f"Set your password and activate your account here (expires in {payload.expires_in_hours} hours):\n"
            f"{accept_url}\n"
        ),
        html=(
            f"<p>Hello {html.escape(invite.full_name)},</p>"
            f"<p>You have been invited to join <strong>{html.escape(school_name)}</strong> "
            f"as a <strong>{html.escape(invite.role.replace('_', ' '))}</strong>.</p>"
            f'<p><a href="{html.escape(accept_url, quote=True)}">Activate Staff Account</a></p>'
        ),
    )
    try:
        email_provider.send_email(message)
    except Exception:
        logger.exception("Failed to send staff invitation email")

    return invite


def accept_staff_invitation(
    db: Session,
    *,
    payload: StaffInviteAcceptRequest,
) -> tuple[User, SchoolMembership]:
    invite = staff_invite_repo.get_by_token_hash(
        db, token_hash=hash_token(payload.token.strip())
    )
    now = _utcnow()
    if (
        invite is None
        or invite.accepted_at is not None
        or invite.revoked_at is not None
        or _as_utc(invite.expires_at) <= now
    ):
        raise AppError(
            status_code=410,
            code="TOKEN_INVALID_OR_EXPIRED",
            message="Staff invitation token is invalid, expired, or already used.",
        )

    school = school_repo.get_school_by_id(db, school_id=invite.school_id)
    if school is None or school.status != "active":
        raise AppError(
            status_code=403,
            code="SCHOOL_INACTIVE",
            message="This school is not currently active.",
        )

    user = user_repo.get_user_by_email(db, email=invite.email)
    if user is None:
        user = user_repo.create_user(
            db,
            email=invite.email,
            full_name=invite.full_name,
            password_hash=hash_password(payload.password),
            is_platform_admin=False,
            is_active=True,
        )
        db.flush()
    else:
        # Existing user (e.g., parent account): verify their existing password so account cannot be hijacked
        if not verify_password(user.password_hash, payload.password):
            raise AppError(
                status_code=401,
                code="INVALID_CREDENTIALS",
                message="An account with this email already exists. Provide your existing password to accept.",
            )
        if membership_repo.get_user_membership_in_school(
            db, user_id=user.id, school_id=invite.school_id
        ):
            raise AppError(
                status_code=409,
                code="MEMBERSHIP_EXISTS",
                message="This user already has a membership in this school.",
            )

    if invite.role == "teacher":
        other_teacher = membership_repo.get_active_teacher_membership_elsewhere(
            db, user_id=user.id, exclude_school_id=invite.school_id
        )
        if other_teacher is not None:
            raise AppError(
                status_code=409,
                code="TEACHER_SINGLE_SCHOOL_VIOLATION",
                message="A teacher can only be actively associated with one school.",
            )

    membership = membership_repo.create_membership(
        db,
        user_id=user.id,
        school_id=invite.school_id,
        role=invite.role,
        status="active",
    )
    invite.accepted_at = now
    db.flush()

    record_audit_event(
        db,
        action="staff_invitation.accepted",
        target_type="school_membership",
        target_id=membership.id,
        actor_user_id=user.id,
        school_id=invite.school_id,
        metadata={"invite_id": str(invite.id), "role": invite.role},
    )
    db.commit()
    db.refresh(user)
    db.refresh(membership)
    return user, membership
