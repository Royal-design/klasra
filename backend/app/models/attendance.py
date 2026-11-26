import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AttendanceRecord(Base):
    """ATT-01 & ATT-02: Per-offering, per-date student attendance with staff attribution."""

    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint(
            "subject_offering_id",
            "student_user_id",
            "attendance_date",
            name="uq_attendance_offering_student_date",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_offering_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("subject_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    school = relationship("School", lazy="joined")
    subject_offering = relationship("SubjectOffering", lazy="joined")
    student = relationship("User", foreign_keys=[student_user_id], lazy="joined")
    recorded_by = relationship("User", foreign_keys=[recorded_by_user_id], lazy="joined")
    updated_by = relationship("User", foreign_keys=[updated_by_user_id], lazy="joined")
