"""Slice 5: guardian_links table for multi-school parent/guardian linking

Revision ID: 0006_slice5_guardian_links
Revises: 0005_staff_invitations
Create Date: 2026-11-26 13:36:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_slice5_guardian_links"
down_revision: str | Sequence[str] | None = "0005_staff_invitations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "guardian_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("parent_user_id", sa.Uuid(), nullable=True),
        sa.Column("guardian_email", sa.String(length=255), nullable=False),
        sa.Column("guardian_full_name", sa.String(length=200), nullable=False),
        sa.Column("relationship_label", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("verification_token_hash", sa.String(length=64), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_notes", sa.String(length=500), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"],
            ["users.id"],
            name=op.f("fk_guardian_links_approved_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_guardian_links_created_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["parent_user_id"],
            ["users.id"],
            name=op.f("fk_guardian_links_parent_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["revoked_by_user_id"],
            ["users.id"],
            name=op.f("fk_guardian_links_revoked_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_guardian_links_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_user_id"],
            ["users.id"],
            name=op.f("fk_guardian_links_student_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_guardian_links")),
    )
    op.create_index(
        op.f("ix_guardian_links_guardian_email"),
        "guardian_links",
        ["guardian_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_guardian_links_parent_user_id"),
        "guardian_links",
        ["parent_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_guardian_links_school_id"),
        "guardian_links",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_guardian_links_status"), "guardian_links", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_guardian_links_student_user_id"),
        "guardian_links",
        ["student_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_guardian_links_verification_token_hash"),
        "guardian_links",
        ["verification_token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_guardian_links_verification_token_hash"), table_name="guardian_links"
    )
    op.drop_index(
        op.f("ix_guardian_links_student_user_id"), table_name="guardian_links"
    )
    op.drop_index(op.f("ix_guardian_links_status"), table_name="guardian_links")
    op.drop_index(op.f("ix_guardian_links_school_id"), table_name="guardian_links")
    op.drop_index(
        op.f("ix_guardian_links_parent_user_id"), table_name="guardian_links"
    )
    op.drop_index(
        op.f("ix_guardian_links_guardian_email"), table_name="guardian_links"
    )
    op.drop_table("guardian_links")
