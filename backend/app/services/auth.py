import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import generate_token, hash_token, verify_password
from app.models.membership import SchoolMembership
from app.models.session import UserSession
from app.models.user import User
from app.repositories import membership_repo, session_repo, user_repo


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
