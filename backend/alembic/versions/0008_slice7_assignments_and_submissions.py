"""Slice 7: assignments, submissions, and stored_files links

Revision ID: 0008_slice7_assignments_and_submissions
Revises: 0007_slice6_lessons_and_files
Create Date: 2026-11-26 14:05:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_slice7_assignments"
down_revision: str | Sequence[str] | None = "0007_slice6_lessons_and_files"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("subject_offering_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_score", sa.Float(), nullable=False),
        sa.Column("allow_late_submissions", sa.Boolean(), nullable=False),
        sa.Column("allow_resubmissions", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_assignments_created_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_assignments_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subject_offering_id"],
            ["subject_offerings.id"],
            name=op.f("fk_assignments_subject_offering_id_subject_offerings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assignments")),
    )
    op.create_index(
        op.f("ix_assignments_school_id"), "assignments", ["school_id"], unique=False
    )
    op.create_index(
        op.f("ix_assignments_status"), "assignments", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_assignments_subject_offering_id"),
        "assignments",
        ["subject_offering_id"],
        unique=False,
    )

    op.create_table(
        "submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("is_latest", sa.Boolean(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("is_late", sa.Boolean(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["assignments.id"],
            name=op.f("fk_submissions_assignment_id_assignments"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_submissions_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_user_id"],
            ["users.id"],
            name=op.f("fk_submissions_student_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_submissions")),
        sa.UniqueConstraint(
            "assignment_id",
            "student_user_id",
            "version_number",
            name="uq_submissions_assignment_student_version",
        ),
    )
    op.create_index(
        op.f("ix_submissions_assignment_id"),
        "submissions",
        ["assignment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_submissions_is_latest"), "submissions", ["is_latest"], unique=False
    )
    op.create_index(
        op.f("ix_submissions_school_id"), "submissions", ["school_id"], unique=False
    )
    op.create_index(
        op.f("ix_submissions_student_user_id"),
        "submissions",
        ["student_user_id"],
        unique=False,
    )

    op.add_column("stored_files", sa.Column("assignment_id", sa.Uuid(), nullable=True))
    op.add_column("stored_files", sa.Column("submission_id", sa.Uuid(), nullable=True))
    op.create_index(
        op.f("ix_stored_files_assignment_id"),
        "stored_files",
        ["assignment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_stored_files_submission_id"),
        "stored_files",
        ["submission_id"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_stored_files_assignment_id_assignments"),
        "stored_files",
        "assignments",
        ["assignment_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_stored_files_submission_id_submissions"),
        "stored_files",
        "submissions",
        ["submission_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_stored_files_submission_id_submissions"),
        "stored_files",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_stored_files_assignment_id_assignments"),
        "stored_files",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_stored_files_submission_id"), table_name="stored_files")
    op.drop_index(op.f("ix_stored_files_assignment_id"), table_name="stored_files")
    op.drop_column("stored_files", "submission_id")
    op.drop_column("stored_files", "assignment_id")

    op.drop_index(op.f("ix_submissions_student_user_id"), table_name="submissions")
    op.drop_index(op.f("ix_submissions_school_id"), table_name="submissions")
    op.drop_index(op.f("ix_submissions_is_latest"), table_name="submissions")
    op.drop_index(op.f("ix_submissions_assignment_id"), table_name="submissions")
    op.drop_table("submissions")

    op.drop_index(op.f("ix_assignments_subject_offering_id"), table_name="assignments")
    op.drop_index(op.f("ix_assignments_status"), table_name="assignments")
    op.drop_index(op.f("ix_assignments_school_id"), table_name="assignments")
    op.drop_table("assignments")
