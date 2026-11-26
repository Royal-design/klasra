"""Slice 9: attendance_records table with staff attribution

Revision ID: 0010_slice9_attendance
Revises: 0009_slice8_grades
Create Date: 2026-11-26 14:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_slice9_attendance"
down_revision: str | Sequence[str] | None = "0009_slice8_grades"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attendance_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("subject_offering_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("recorded_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["recorded_by_user_id"],
            ["users.id"],
            name=op.f("fk_attendance_records_recorded_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_attendance_records_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_user_id"],
            ["users.id"],
            name=op.f("fk_attendance_records_student_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subject_offering_id"],
            ["subject_offerings.id"],
            name=op.f("fk_attendance_records_subject_offering_id_subject_offerings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["users.id"],
            name=op.f("fk_attendance_records_updated_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attendance_records")),
        sa.UniqueConstraint(
            "subject_offering_id",
            "student_user_id",
            "attendance_date",
            name="uq_attendance_offering_student_date",
        ),
    )
    op.create_index(
        op.f("ix_attendance_records_attendance_date"),
        "attendance_records",
        ["attendance_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attendance_records_school_id"),
        "attendance_records",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attendance_records_status"),
        "attendance_records",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attendance_records_student_user_id"),
        "attendance_records",
        ["student_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attendance_records_subject_offering_id"),
        "attendance_records",
        ["subject_offering_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_attendance_records_subject_offering_id"),
        table_name="attendance_records",
    )
    op.drop_index(
        op.f("ix_attendance_records_student_user_id"), table_name="attendance_records"
    )
    op.drop_index(op.f("ix_attendance_records_status"), table_name="attendance_records")
    op.drop_index(
        op.f("ix_attendance_records_school_id"), table_name="attendance_records"
    )
    op.drop_index(
        op.f("ix_attendance_records_attendance_date"), table_name="attendance_records"
    )
    op.drop_table("attendance_records")
