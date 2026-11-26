import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.session import UserSession


def create_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    token_hash: str,
    csrf_token_hash: str,
    expires_at: datetime,
    now: datetime,
) -> UserSession:
    session = UserSession(
        user_id=user_id,
        token_hash=token_hash,
        csrf_token_hash=csrf_token_hash,
        expires_at=expires_at,
        created_at=now,
        last_seen_at=now,
    )
    db.add(session)
    return session


def get_session_by_token_hash(db: Session, *, token_hash: str) -> UserSession | None:
    return db.scalar(select(UserSession).where(UserSession.token_hash == token_hash))


def revoke_active_sessions_for_user(
    db: Session, *, user_id: uuid.UUID, revoked_at: datetime
) -> None:
    db.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .values(revoked_at=revoked_at)
    )
