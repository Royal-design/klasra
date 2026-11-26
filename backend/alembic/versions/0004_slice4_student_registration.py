"""Slice 4: student invites and student registration requests

Revision ID: 0004_slice4_student_registration
Revises: 0003_password_reset_tokens
Create Date: 2026-11-26 12:55:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_slice4_student_registration"
down_revision: str | Sequence[str] | None = "0003_password_reset_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "student_invites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("invite_type", sa.String(length=30), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("invited_email", sa.String(length=255), nullable=True),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=False),
        sa.Column("use_count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_student_invites_created_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_student_invites_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_student_invites")),
    )
    op.create_index(
        op.f("ix_student_invites_school_id"),
        "student_invites",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_student_invites_token_hash"),
        "student_invites",
        ["token_hash"],
        unique=True,
    )

    op.create_table(
        "student_registration_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column("invite_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("student_reference", sa.String(length=100), nullable=True),
        sa.Column("decision_notes", sa.String(length=500), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["invite_id"],
            ["student_invites.id"],
            name=op.f("fk_student_registration_requests_invite_id_student_invites"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["membership_id"],
            ["school_memberships.id"],
            name=op.f(
                "fk_student_registration_requests_membership_id_school_memberships"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            name=op.f("fk_student_registration_requests_reviewed_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name=op.f("fk_student_registration_requests_school_id_schools"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_student_registration_requests_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_student_registration_requests")),
        sa.UniqueConstraint(
            "membership_id", name=op.f("uq_student_registration_requests_membership_id")
        ),
    )
    op.create_index(
        op.f("ix_student_registration_requests_school_id"),
        "student_registration_requests",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_student_registration_requests_status"),
        "student_registration_requests",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_student_registration_requests_user_id"),
        "student_registration_requests",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_student_registration_requests_user_id"),
        table_name="student_registration_requests",
    )
    op.drop_index(
        op.f("ix_student_registration_requests_status"),
        table_name="student_registration_requests",
    )
    op.drop_index(
        op.f("ix_student_registration_requests_school_id"),
        table_name="student_registration_requests",
    )
    op.drop_table("student_registration_requests")

    op.drop_index(
        op.f("ix_student_invites_token_hash"), table_name="student_invites"
    )
    op.drop_index(op.f("ix_student_invites_school_id"), table_name="student_invites")
    op.drop_table("student_invites")
