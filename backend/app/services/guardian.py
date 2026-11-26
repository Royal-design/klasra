import html
import logging
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import generate_token, hash_password, hash_token, verify_password
from app.models.guardian import GuardianLink
from app.repositories import guardian_repo, membership_repo, school_repo, user_repo
from app.schemas.guardian import (
    GuardianDecisionRequest,
    GuardianInviteCreateRequest,
    GuardianVerifyRequest,
)
from app.services.audit import record_audit_event
from app.services.email import EmailMessage, EmailProvider

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def invite_guardian(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: GuardianInviteCreateRequest,
    actor_user_id: uuid.UUID,
    frontend_base_url: str,
    email_provider: EmailProvider,
) -> GuardianLink:
    """Slice 5 Step 1–2: School records parent/student link and emails verification token."""
    student_membership = membership_repo.get_user_membership_in_school(
        db, user_id=payload.student_user_id, school_id=school_id
    )
    if (
        student_membership is None
        or student_membership.role != "student"
        or student_membership.status != "active"
    ):
        raise AppError(
            status_code=422,
            code="INVALID_STUDENT",
            message="Target user must be an active student in this school.",
        )

    normalized_email = str(payload.guardian_email).strip().lower()
    if guardian_repo.get_active_or_pending_link(
        db,
        school_id=school_id,
        student_user_id=payload.student_user_id,
        guardian_email=normalized_email,
    ):
        raise AppError(
            status_code=409,
            code="GUARDIAN_LINK_EXISTS",
            message="An active or pending guardian link already exists for this email and student.",
        )

    now = _utcnow()
    raw_token = generate_token(32)
    link = GuardianLink(
        school_id=school_id,
        student_user_id=payload.student_user_id,
        guardian_email=normalized_email,
        guardian_full_name=payload.guardian_full_name.strip(),
        relationship_label=payload.relationship_label.strip(),
        status="invited",
        verification_token_hash=hash_token(raw_token),
        token_expires_at=now + timedelta(hours=payload.expires_in_hours),
        created_by_user_id=actor_user_id,
    )
    db.add(link)
    db.flush()

    record_audit_event(
        db,
        action="guardian_link.invited",
        target_type="guardian_link",
        target_id=link.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "student_user_id": str(payload.student_user_id),
            "guardian_email": normalized_email,
            "relationship_label": link.relationship_label,
        },
    )
    db.commit()
    db.refresh(link)

    school = school_repo.get_school_by_id(db, school_id=school_id)
    school_name = school.name if school else "your child's school"
    student_name = link.student.full_name if link.student else "your child"
    base = frontend_base_url.rstrip("/")
    verify_url = f"{base}/parent/verify?{urlencode({'token': raw_token})}"

    message = EmailMessage(
        to=normalized_email,
        subject=f"Parent portal invitation from {school_name}",
        text=(
            f"Hello {link.guardian_full_name},\n\n"
            f"{school_name} has invited you to link your parent account to {student_name}.\n"
            f"Verify your email and complete setup here (expires in {payload.expires_in_hours} hours):\n"
            f"{verify_url}\n\n"
            "After verification, a school administrator will approve the link before progress records are visible."
        ),
        html=(
            f"<p>Hello {html.escape(link.guardian_full_name)},</p>"
            f"<p><strong>{html.escape(school_name)}</strong> has invited you to link your parent account "
            f"to <strong>{html.escape(student_name)}</strong>.</p>"
            f'<p><a href="{html.escape(verify_url, quote=True)}">Verify Parent Invitation</a></p>'
            "<p>After verification, a school administrator will approve the link before progress records are visible.</p>"
        ),
    )
    try:
        email_provider.send_email(message)
    except Exception:
        logger.exception("Failed to send guardian invitation email")

    return link


def verify_guardian_invitation(
    db: Session,
    *,
    payload: GuardianVerifyRequest,
) -> GuardianLink:
    """Slice 5 Step 3–4: Parent verifies email token, creates/links single parent account, waits for admin approval."""
    link = guardian_repo.get_link_by_token_hash(
        db, token_hash=hash_token(payload.token.strip())
    )
    now = _utcnow()
    if (
        link is None
        or link.status != "invited"
        or link.token_expires_at is None
        or _as_utc(link.token_expires_at) <= now
    ):
        raise AppError(
            status_code=410,
            code="TOKEN_INVALID_OR_EXPIRED",
            message="Guardian verification token is invalid, expired, or already used.",
        )

    school = school_repo.get_school_by_id(db, school_id=link.school_id)
    if school is None or school.status != "active":
        raise AppError(
            status_code=403,
            code="SCHOOL_INACTIVE",
            message="This school is not currently active.",
        )

    # AUTH-04: Reuse existing parent account across multiple schools (verifying existing password)
    parent_user = user_repo.get_user_by_email(db, email=link.guardian_email)
    if parent_user is None:
        parent_user = user_repo.create_user(
            db,
            email=link.guardian_email,
            full_name=link.guardian_full_name,
            password_hash=hash_password(payload.password),
            is_platform_admin=False,
            is_active=True,
        )
        db.flush()
    else:
        if not parent_user.is_active:
            raise AppError(403, "ACCOUNT_INACTIVE", "This account is inactive.")
        if not verify_password(parent_user.password_hash, payload.password):
            raise AppError(
                status_code=401,
                code="INVALID_CREDENTIALS",
                message="An account with this email already exists. Enter your existing password to link this child.",
            )

    link.parent_user_id = parent_user.id
    link.status = "pending_approval"
    link.verified_at = now
    link.verification_token_hash = None  # Single-use: clear token hash after validation
    link.token_expires_at = None

    record_audit_event(
        db,
        action="guardian_link.verified",
        target_type="guardian_link",
        target_id=link.id,
        actor_user_id=parent_user.id,
        school_id=link.school_id,
        metadata={
            "student_user_id": str(link.student_user_id),
            "parent_user_id": str(parent_user.id),
        },
    )
    db.commit()
    db.refresh(link)
    return link


def approve_guardian_link(
    db: Session,
    *,
    school_id: uuid.UUID,
    link_id: uuid.UUID,
    payload: GuardianDecisionRequest,
    actor_user_id: uuid.UUID,
    email_provider: EmailProvider,
) -> GuardianLink:
    """Slice 5 Step 5: School Admin approves verified parent-student link."""
    link = guardian_repo.get_link_for_school(db, school_id=school_id, link_id=link_id)
    if link is None:
        raise AppError(404, "GUARDIAN_LINK_NOT_FOUND", "Guardian link not found.")

    if link.status != "pending_approval":
        raise AppError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Only a verified guardian link awaiting approval can be approved.",
        )

    now = _utcnow()
    link.status = "approved"
    link.approved_by_user_id = actor_user_id
    link.approved_at = now
    link.decision_notes = (
        payload.decision_notes.strip() if payload.decision_notes else None
    )

    record_audit_event(
        db,
        action="guardian_link.approved",
        target_type="guardian_link",
        target_id=link.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "student_user_id": str(link.student_user_id),
            "parent_user_id": str(link.parent_user_id) if link.parent_user_id else None,
        },
    )
    db.commit()
    db.refresh(link)

    school_name = link.school.name if link.school else "the school"
    student_name = link.student.full_name if link.student else "your child"
    try:
        email_provider.send_email(
            EmailMessage(
                to=link.guardian_email,
                subject=f"Parent link approved at {school_name}",
                text=(
                    f"Hello {link.guardian_full_name},\n\n"
                    f"Your parent link to {student_name} at {school_name} has been approved. "
                    "You can now sign in to view their grades, attendance, and teacher feedback."
                ),
                html=(
                    f"<p>Hello {html.escape(link.guardian_full_name)},</p>"
                    f"<p>Your parent link to <strong>{html.escape(student_name)}</strong> at "
                    f"<strong>{html.escape(school_name)}</strong> has been approved.</p>"
                ),
            )
        )
    except Exception:
        logger.exception("Failed to send guardian approval email")

    return link


def revoke_guardian_link(
    db: Session,
    *,
    school_id: uuid.UUID,
    link_id: uuid.UUID,
    payload: GuardianDecisionRequest,
    actor_user_id: uuid.UUID,
    email_provider: EmailProvider,
) -> GuardianLink:
    """Slice 5 Step 6: School Admin revokes a guardian link (audited)."""
    link = guardian_repo.get_link_for_school(db, school_id=school_id, link_id=link_id)
    if link is None:
        raise AppError(404, "GUARDIAN_LINK_NOT_FOUND", "Guardian link not found.")

    if link.status == "revoked":
        raise AppError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Guardian link is already revoked.",
        )

    now = _utcnow()
    link.status = "revoked"
    link.revoked_by_user_id = actor_user_id
    link.revoked_at = now
    link.verification_token_hash = None
    link.token_expires_at = None
    link.decision_notes = (
        payload.decision_notes.strip() if payload.decision_notes else None
    )

    record_audit_event(
        db,
        action="guardian_link.revoked",
        target_type="guardian_link",
        target_id=link.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "student_user_id": str(link.student_user_id),
            "parent_user_id": str(link.parent_user_id) if link.parent_user_id else None,
            "decision_notes": link.decision_notes,
        },
    )
    db.commit()
    db.refresh(link)

    school_name = link.school.name if link.school else "the school"
    try:
        email_provider.send_email(
            EmailMessage(
                to=link.guardian_email,
                subject=f"Update to your parent access at {school_name}",
                text=(
                    f"Hello {link.guardian_full_name},\n\n"
                    f"Your parent link at {school_name} has been revoked by a school administrator. "
                    "Please contact the school office if you have questions."
                ),
                html=(
                    f"<p>Hello {html.escape(link.guardian_full_name)},</p>"
                    f"<p>Your parent link at <strong>{html.escape(school_name)}</strong> has been revoked "
                    "by a school administrator.</p>"
                ),
            )
        )
    except Exception:
        logger.exception("Failed to send guardian revocation email")

    return link
