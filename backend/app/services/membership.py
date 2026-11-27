import html
import logging
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import generate_token, hash_password, hash_token
from app.models.membership import SchoolMembership
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.repositories import membership_repo, school_repo, user_repo
from app.schemas.membership import MembershipUpdateRequest, SchoolUserCreateRequest
from app.services.audit import record_audit_event
from app.services.auth import revoke_all_user_sessions
from app.services.email import EmailMessage, EmailProvider

logger = logging.getLogger(__name__)


def _assert_teacher_single_school(
    db: Session,
    *,
    user_id: uuid.UUID,
    target_school_id: uuid.UUID,
) -> None:
    """AUTH-03: Enforce that a teacher has at most one active school membership."""
    existing = membership_repo.get_active_teacher_membership_elsewhere(
        db, user_id=user_id, exclude_school_id=target_school_id
    )
    if existing is not None:
        raise AppError(
            status_code=409,
            code="TEACHER_SINGLE_SCHOOL_VIOLATION",
            message="A teacher can only be actively associated with one school.",
        )


def create_school_user(
    db: Session,
    *,
    school_id: uuid.UUID,
    payload: SchoolUserCreateRequest,
    actor_user_id: uuid.UUID,
    email_provider: EmailProvider | None = None,
    frontend_base_url: str = "http://localhost:3000",
) -> tuple[User, SchoolMembership]:
    """Create a user account (or attach existing) with a role inside one school."""
    user = user_repo.get_user_by_email(db, email=str(payload.email))
    created_new_user = False

    if user is None:
        raw_pw = payload.password or generate_token(32)
        user = user_repo.create_user(
            db,
            email=str(payload.email),
            full_name=payload.full_name,
            password_hash=hash_password(raw_pw),
            is_platform_admin=False,
            is_active=True,
        )
        db.flush()
        created_new_user = True
    else:
        existing_in_school = membership_repo.get_user_membership_in_school(
            db, user_id=user.id, school_id=school_id
        )
        if existing_in_school is not None:
            raise AppError(
                status_code=409,
                code="MEMBERSHIP_EXISTS",
                message="This user already has a membership in this school.",
            )

    if payload.role == "teacher":
        _assert_teacher_single_school(db, user_id=user.id, target_school_id=school_id)

    membership = membership_repo.create_membership(
        db,
        user_id=user.id,
        school_id=school_id,
        role=payload.role,
        status="active",
    )
    db.flush()

    raw_setup_token: str | None = None
    if created_new_user:
        raw_setup_token = generate_token(32)
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token(raw_setup_token),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            )
        )

    record_audit_event(
        db,
        action="membership.created",
        target_type="school_membership",
        target_id=membership.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "user_id": str(user.id),
            "role": membership.role,
            "status": membership.status,
            "created_new_user": created_new_user,
        },
    )

    db.commit()
    db.refresh(user)
    db.refresh(membership)

    if email_provider is not None and created_new_user and raw_setup_token is not None:
        school = school_repo.get_school_by_id(db, school_id=school_id)
        school_name = school.name if school else "your school"
        base = frontend_base_url.rstrip("/")
        set_pw_url = f"{base}/reset-password?{urlencode({'token': raw_setup_token})}"
        role_display = membership.role.replace("_", " ").title()
        msg = EmailMessage(
            to=user.email,
            subject=f"Welcome to {school_name} on Klasra — Set your password",
            text=(
                f"Hello {user.full_name},\n\n"
                f"An account has been created for you at {school_name} as {role_display}.\n\n"
                f"Set your private password using this 24-hour single-use link:\n{set_pw_url}\n"
            ),
            html=(
                f"<p>Hello {html.escape(user.full_name)},</p>"
                f"<p>An account has been created for you at <strong>{html.escape(school_name)}</strong> "
                f"as <strong>{html.escape(role_display)}</strong>.</p>"
                f'<p><a href="{html.escape(set_pw_url)}">Set your private password (24h link)</a></p>'
            ),
        )
        try:
            email_provider.send_email(msg)
        except Exception:
            logger.exception("Failed to send welcome email to user %s", user.id)

    return user, membership


def list_school_users(
    db: Session,
    *,
    school_id: uuid.UUID,
    role: str | None = None,
    status: str | None = None,
    q: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[tuple[User, SchoolMembership]], int]:
    return membership_repo.list_school_users_with_memberships(
        db,
        school_id=school_id,
        role=role,
        status=status,
        q=q,
        offset=offset,
        limit=limit,
    )


def update_school_membership(
    db: Session,
    *,
    school_id: uuid.UUID,
    membership_id: uuid.UUID,
    payload: MembershipUpdateRequest,
    actor_user_id: uuid.UUID,
) -> tuple[User, SchoolMembership]:
    membership = membership_repo.get_membership_for_school(
        db, school_id=school_id, membership_id=membership_id
    )
    if membership is None:
        raise AppError(
            status_code=404,
            code="MEMBERSHIP_NOT_FOUND",
            message="School membership not found.",
        )

    new_role = payload.role or membership.role
    new_status = payload.status or membership.status

    if new_role == membership.role and new_status == membership.status:
        user = user_repo.get_user_by_id(db, user_id=membership.user_id)
        assert user is not None
        return user, membership

    if membership.status == "revoked" and payload.status == "revoked" and payload.role is None:
        raise AppError(
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message="Membership is already revoked.",
        )

    if membership.role == "school_admin" and membership.status == "active":
        losing_admin = new_role != "school_admin" or new_status != "active"
        if losing_admin:
            active_admins_count = membership_repo.count_active_school_admins(
                db, school_id=school_id
            )
            if active_admins_count <= 1:
                raise AppError(
                    status_code=409,
                    code="LAST_SCHOOL_ADMIN",
                    message="Cannot remove or demote the last active school administrator.",
                )

    if new_role == "teacher" and new_status == "active":
        _assert_teacher_single_school(
            db, user_id=membership.user_id, target_school_id=school_id
        )

    previous_role = membership.role
    previous_status = membership.status
    membership.role = new_role
    membership.status = new_status

    if new_status == "revoked":
        revoke_all_user_sessions(db, user_id=membership.user_id)

    record_audit_event(
        db,
        action="membership.updated",
        target_type="school_membership",
        target_id=membership.id,
        actor_user_id=actor_user_id,
        school_id=school_id,
        metadata={
            "user_id": str(membership.user_id),
            "previous_role": previous_role,
            "new_role": new_role,
            "previous_status": previous_status,
            "new_status": new_status,
        },
    )

    db.commit()
    db.refresh(membership)
    user = user_repo.get_user_by_id(db, user_id=membership.user_id)
    assert user is not None
    return user, membership
