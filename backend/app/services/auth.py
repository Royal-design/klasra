import html
import logging
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import generate_token, hash_password, hash_token, verify_password
from app.models.membership import SchoolMembership
from app.models.session import UserSession
from app.models.user import User
from app.repositories import membership_repo, password_reset_repo, session_repo, user_repo
from app.services.audit import record_audit_event
from app.services.email import EmailMessage, EmailProvider

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def authenticate_user(db: Session, *, email: str, password: str) -> User:
    """Verify credentials without revealing whether an email address exists."""
    user = user_repo.get_user_by_email(db, email=email)
    if user is None or not verify_password(user.password_hash, password):
        raise AppError(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
        )
    if not user.is_active:
        raise AppError(
            status_code=403,
            code="ACCOUNT_INACTIVE",
            message="This account is inactive.",
        )
    return user


def create_user_session(
    db: Session,
    *,
    user: User,
    ttl_hours: int,
) -> tuple[UserSession, str, str]:
    """Create a server-side session storing only hashes of the session & CSRF tokens."""
    raw_session_token = generate_token(32)
    raw_csrf_token = generate_token(32)
    now = _utcnow()
    session = session_repo.create_session(
        db,
        user_id=user.id,
        token_hash=hash_token(raw_session_token),
        csrf_token_hash=hash_token(raw_csrf_token),
        expires_at=now + timedelta(hours=ttl_hours),
        now=now,
    )
    db.commit()
    db.refresh(session)
    return session, raw_session_token, raw_csrf_token


def revoke_all_user_sessions(db: Session, *, user_id: uuid.UUID) -> None:
    """Invalidate all active sessions for a user (logout, deactivation, revocation)."""
    session_repo.revoke_active_sessions_for_user(
        db, user_id=user_id, revoked_at=_utcnow()
    )


def get_active_session_and_user(
    db: Session, *, raw_session_token: str
) -> tuple[UserSession, User]:
    session = session_repo.get_session_by_token_hash(
        db, token_hash=hash_token(raw_session_token)
    )
    now = _utcnow()
    if session is None or session.revoked_at is not None or _as_utc(session.expires_at) <= now:
        raise AppError(
            status_code=401,
            code="SESSION_INVALID",
            message="Authentication required.",
        )

    user = user_repo.get_user_by_id(db, user_id=session.user_id)
    if user is None or not user.is_active:
        raise AppError(
            status_code=403,
            code="ACCOUNT_INACTIVE",
            message="This account is inactive.",
        )

    session.last_seen_at = now
    db.commit()
    return session, user


def get_user_memberships(db: Session, *, user_id: uuid.UUID) -> list[SchoolMembership]:
    return membership_repo.list_user_memberships(db, user_id=user_id)


def request_password_reset(
    db: Session,
    *,
    email: str,
    ttl_minutes: int,
    frontend_base_url: str,
    email_provider: EmailProvider,
) -> None:
    """Create a single-use hashed reset token and send it via EmailProvider.

    Always completes silently when the email is unknown or inactive to prevent
    account enumeration.
    """
    user = user_repo.get_user_by_email(db, email=email)
    if user is None or not user.is_active:
        return

    now = _utcnow()
    password_reset_repo.invalidate_unused_tokens_for_user(
        db, user_id=user.id, invalidated_at=now
    )

    raw_token = generate_token(32)
    password_reset_repo.create_reset_token(
        db,
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=now + timedelta(minutes=ttl_minutes),
        now=now,
    )
    record_audit_event(
        db,
        action="auth.password_reset_requested",
        target_type="user",
        target_id=user.id,
        actor_user_id=user.id,
    )
    db.commit()

    base = frontend_base_url.rstrip("/")
    reset_url = f"{base}/reset-password?{urlencode({'token': raw_token})}"
    safe_name = html.escape(user.full_name)
    safe_url = html.escape(reset_url, quote=True)

    message = EmailMessage(
        to=user.email,
        subject="Reset your School LMS password",
        text=(
            f"Hello {user.full_name},\n\n"
            f"We received a request to reset your password. Use the link below within "
            f"{ttl_minutes} minutes:\n{reset_url}\n\n"
            "If you did not request this, you can safely ignore this email."
        ),
        html=(
            f"<p>Hello {safe_name},</p>"
            f"<p>We received a request to reset your password. Use the link below within "
            f"{ttl_minutes} minutes:</p>"
            f'<p><a href="{safe_url}">Reset Password</a></p>'
            "<p>If you did not request this, you can safely ignore this email.</p>"
        ),
    )
    try:
        email_provider.send_email(message)
    except Exception:
        # Never leak provider failure or user existence to caller; log sanitized error.
        logger.exception("Failed to deliver password reset email")


def reset_password_with_token(
    db: Session,
    *,
    raw_token: str,
    new_password: str,
) -> None:
    """Validate single-use reset token, update Argon2id hash, and revoke all sessions."""
    token_record = password_reset_repo.get_by_token_hash(
        db, token_hash=hash_token(raw_token)
    )
    now = _utcnow()
    if (
        token_record is None
        or token_record.used_at is not None
        or _as_utc(token_record.expires_at) <= now
    ):
        raise AppError(
            status_code=410,
            code="TOKEN_INVALID_OR_EXPIRED",
            message="Password reset token is invalid or has expired.",
        )

    user = user_repo.get_user_by_id(db, user_id=token_record.user_id)
    if user is None or not user.is_active:
        raise AppError(
            status_code=410,
            code="TOKEN_INVALID_OR_EXPIRED",
            message="Password reset token is invalid or has expired.",
        )

    user.password_hash = hash_password(new_password)
    token_record.used_at = now
    revoke_all_user_sessions(db, user_id=user.id)

    record_audit_event(
        db,
        action="auth.password_reset_completed",
        target_type="user",
        target_id=user.id,
        actor_user_id=user.id,
    )
    db.commit()


def change_user_password(
    db: Session,
    *,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    """Verify current password, update Argon2id hash, and invalidate active sessions."""
    if not verify_password(user.password_hash, current_password):
        raise AppError(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message="Current password is incorrect.",
        )
    if current_password == new_password:
        raise AppError(
            status_code=422,
            code="SAME_PASSWORD",
            message="New password must be different from the current password.",
        )

    user.password_hash = hash_password(new_password)
    revoke_all_user_sessions(db, user_id=user.id)
    record_audit_event(
        db,
        action="auth.password_changed",
        target_type="user",
        target_id=user.id,
        actor_user_id=user.id,
    )
    db.commit()
