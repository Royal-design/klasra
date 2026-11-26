import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


def record_audit_event(
    db: Session,
    *,
    action: str,
    target_type: str,
    target_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
    school_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    """Append an immutable audit event within the caller's database transaction."""
    event = AuditEvent(
        school_id=school_id,
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_json=metadata or {},
    )
    db.add(event)
    return event
