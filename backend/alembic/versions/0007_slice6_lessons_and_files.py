"""Slice 6: lessons and stored_files tables

Revision ID: 0007_slice6_lessons_and_files
Revises: 0006_slice5_guardian_links
Create Date: 2026-11-26 13:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_slice6_lessons_and_files"
down_revision: str | Sequence[str] | None = "0006_slice5_guardian_links"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lessons",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("subject_offering_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_lessons_created_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_lessons_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subject_offering_id"],
            ["subject_offerings.id"],
            name=op.f("fk_lessons_subject_offering_id_subject_offerings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lessons")),
    )
    op.create_index(op.f("ix_lessons_school_id"), "lessons", ["school_id"], unique=False)
    op.create_index(op.f("ix_lessons_status"), "lessons", ["status"], unique=False)
    op.create_index(
        op.f("ix_lessons_subject_offering_id"),
        "lessons",
        ["subject_offering_id"],
        unique=False,
    )

    op.create_table(
        "stored_files",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("lesson_id", sa.Uuid(), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_checksum", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["lessons.id"],
            name=op.f("fk_stored_files_lesson_id_lessons"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_stored_files_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_user_id"],
            ["users.id"],
            name=op.f("fk_stored_files_uploaded_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stored_files")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_stored_files_storage_key")),
    )
    op.create_index(
        op.f("ix_stored_files_lesson_id"), "stored_files", ["lesson_id"], unique=False
    )
    op.create_index(
        op.f("ix_stored_files_school_id"), "stored_files", ["school_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_stored_files_school_id"), table_name="stored_files")
    op.drop_index(op.f("ix_stored_files_lesson_id"), table_name="stored_files")
    op.drop_table("stored_files")

    op.drop_index(op.f("ix_lessons_subject_offering_id"), table_name="lessons")
    op.drop_index(op.f("ix_lessons_status"), table_name="lessons")
    op.drop_index(op.f("ix_lessons_school_id"), table_name="lessons")
    op.drop_table("lessons")
