import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GuardianLink(Base):
    """AUTH-04: Multi-school parent/guardian to student relationship with approval workflow."""

    __tablename__ = "guardian_links"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    guardian_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    guardian_full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    relationship_label: Mapped[str] = mapped_column(String(50), nullable=False, default="Guardian")
    # invited -> pending_approval -> approved | revoked
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="invited", index=True)
    verification_token_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    school = relationship("School", lazy="joined")
    student = relationship("User", foreign_keys=[student_user_id], lazy="joined")
    parent = relationship("User", foreign_keys=[parent_user_id], lazy="joined")
