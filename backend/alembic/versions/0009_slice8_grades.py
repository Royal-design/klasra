"""Slice 8: grades table for teacher grading, feedback, and progress views

Revision ID: 0009_slice8_grades
Revises: 0008_slice7_assignments
Create Date: 2026-11-26 14:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_slice8_grades"
down_revision: str | Sequence[str] | None = "0008_slice7_assignments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "grades",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("graded_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("max_score", sa.Float(), nullable=False),
        sa.Column("letter_grade", sa.String(length=10), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignments.id"],
            name=op.f("fk_grades_assignment_id_assignments"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["graded_by_user_id"],
            ["users.id"],
            name=op.f("fk_grades_graded_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_grades_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_user_id"],
            ["users.id"],
            name=op.f("fk_grades_student_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["submissions.id"],
            name=op.f("fk_grades_submission_id_submissions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_grades")),
    )
    op.create_index(
        op.f("ix_grades_assignment_id"), "grades", ["assignment_id"], unique=False
    )
    op.create_index(
        op.f("ix_grades_is_published"), "grades", ["is_published"], unique=False
    )
    op.create_index(op.f("ix_grades_school_id"), "grades", ["school_id"], unique=False)
    op.create_index(
        op.f("ix_grades_student_user_id"), "grades", ["student_user_id"], unique=False
    )
    op.create_index(
        op.f("ix_grades_submission_id"), "grades", ["submission_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_grades_submission_id"), table_name="grades")
    op.drop_index(op.f("ix_grades_student_user_id"), table_name="grades")
    op.drop_index(op.f("ix_grades_school_id"), table_name="grades")
    op.drop_index(op.f("ix_grades_is_published"), table_name="grades")
    op.drop_index(op.f("ix_grades_assignment_id"), table_name="grades")
    op.drop_table("grades")
