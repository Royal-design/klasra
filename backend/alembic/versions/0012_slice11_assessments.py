"""Add Slice 11 assessments (quizzes, tests, and exams)

Revision ID: 0012_slice11_assessments
Revises: 0011_lesson_video_url
Create Date: 2026-11-27 12:40:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_slice11_assessments"
down_revision: Union[str, None] = "0011_lesson_video_url"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assessments",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "subject_offering_id",
            sa.Uuid(),
            sa.ForeignKey("subject_offerings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("assessment_type", sa.String(length=20), nullable=False, server_default="quiz"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("available_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("available_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_limit_minutes", sa.Integer(), nullable=True),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("shuffle_questions", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("shuffle_options", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("show_results_immediately", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("total_points", sa.Float(), nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assessments_school_id", "assessments", ["school_id"])
    op.create_index("ix_assessments_subject_offering_id", "assessments", ["subject_offering_id"])
    op.create_index("ix_assessments_assessment_type", "assessments", ["assessment_type"])
    op.create_index("ix_assessments_status", "assessments", ["status"])

    op.create_table(
        "assessment_questions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_type", sa.String(length=30), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("correct_answers", sa.JSON(), nullable=True),
        sa.Column("points", sa.Float(), nullable=False, server_default="1"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assessment_questions_school_id", "assessment_questions", ["school_id"])
    op.create_index("ix_assessment_questions_assessment_id", "assessment_questions", ["assessment_id"])

    op.create_table(
        "assessment_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="in_progress"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("auto_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("manual_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("max_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("teacher_feedback", sa.Text(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("graded_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "assessment_id",
            "student_user_id",
            "attempt_number",
            name="uq_assessment_student_attempt_num",
        ),
    )
    op.create_index("ix_assessment_attempts_school_id", "assessment_attempts", ["school_id"])
    op.create_index("ix_assessment_attempts_assessment_id", "assessment_attempts", ["assessment_id"])
    op.create_index("ix_assessment_attempts_student_user_id", "assessment_attempts", ["student_user_id"])
    op.create_index("ix_assessment_attempts_status", "assessment_attempts", ["status"])
    op.create_index("ix_assessment_attempts_is_published", "assessment_attempts", ["is_published"])

    op.create_table(
        "assessment_answers",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "question_id",
            sa.Uuid(),
            sa.ForeignKey("assessment_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("selected_options", sa.JSON(), nullable=True),
        sa.Column("text_answer", sa.Text(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("points_awarded", sa.Float(), nullable=False, server_default="0"),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question_answer"),
    )
    op.create_index("ix_assessment_answers_school_id", "assessment_answers", ["school_id"])
    op.create_index("ix_assessment_answers_attempt_id", "assessment_answers", ["attempt_id"])
    op.create_index("ix_assessment_answers_question_id", "assessment_answers", ["question_id"])


def downgrade() -> None:
    op.drop_table("assessment_answers")
    op.drop_table("assessment_attempts")
    op.drop_table("assessment_questions")
    op.drop_table("assessments")
