"""Add staff_invitations table for teacher/staff email activation

Revision ID: 0005_staff_invitations
Revises: 0004_slice4_student_registration
Create Date: 2026-11-26 13:35:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_staff_invitations"
down_revision: str | Sequence[str] | None = "0004_slice4_student_registration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "staff_invitations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_staff_invitations_created_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_staff_invitations_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_staff_invitations")),
    )
    op.create_index(
        op.f("ix_staff_invitations_email"), "staff_invitations", ["email"], unique=False
    )
    op.create_index(
        op.f("ix_staff_invitations_school_id"),
        "staff_invitations",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_staff_invitations_token_hash"),
        "staff_invitations",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_staff_invitations_token_hash"), table_name="staff_invitations"
    )
    op.drop_index(
        op.f("ix_staff_invitations_school_id"), table_name="staff_invitations"
    )
    op.drop_index(op.f("ix_staff_invitations_email"), table_name="staff_invitations")
    op.drop_table("staff_invitations")
