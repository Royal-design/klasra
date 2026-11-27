import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Assessment(Base):
    """Slice 11 (ASSESS-01): School-scoped quiz, test (CA), or exam for a subject offering."""

    __tablename__ = "assessments"

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
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    # quiz | test | exam
    assessment_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="quiz", index=True
    )
    # draft | published | closed
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )
    available_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    available_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    shuffle_options: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    show_results_immediately: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    total_points: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    school = relationship("School", lazy="joined")
    subject_offering = relationship("SubjectOffering", lazy="joined")
    author = relationship("User", lazy="joined")
    questions = relationship(
        "AssessmentQuestion",
        back_populates="assessment",
        lazy="selectin",
        order_by="AssessmentQuestion.display_order.asc()",
        cascade="all, delete-orphan",
    )


class AssessmentQuestion(Base):
    """Question belonging to an assessment (objective auto-graded or teacher-graded essay)."""

    __tablename__ = "assessment_questions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # single_choice | true_false | multi_select | short_answer
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # List of {"key": "A", "label": "Option text"} for objective questions; null for short_answer
    options: Mapped[list[dict[str, str]] | None] = mapped_column(JSON, nullable=True)
    # List of correct option keys (e.g. ["A"] or ["A", "C"]); null for short_answer
    correct_answers: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    points: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    assessment = relationship("Assessment", back_populates="questions")


class AssessmentAttempt(Base):
    """A student's timed attempt on a published assessment."""

    __tablename__ = "assessment_attempts"
    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "student_user_id",
            "attempt_number",
            name="uq_assessment_student_attempt_num",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # in_progress | submitted | graded
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_progress", index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    deadline_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    auto_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    manual_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    teacher_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    graded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    school = relationship("School", lazy="joined")
    assessment = relationship("Assessment", lazy="joined")
    student = relationship("User", foreign_keys=[student_user_id], lazy="joined")
    graded_by = relationship("User", foreign_keys=[graded_by_user_id], lazy="joined")
    answers = relationship(
        "AssessmentAnswer",
        back_populates="attempt",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class AssessmentAnswer(Base):
    """Individual student answer to a question inside an attempt."""

    __tablename__ = "assessment_answers"
    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "question_id",
            name="uq_attempt_question_answer",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("assessment_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    selected_options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    text_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    points_awarded: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    attempt = relationship("AssessmentAttempt", back_populates="answers")
    question = relationship("AssessmentQuestion", lazy="joined")
