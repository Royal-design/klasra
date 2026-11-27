"""Scope class_groups uniqueness per year level.

Revision ID: 0013_class_group_level_uq
Revises: 0012_slice11_assessments
Create Date: 2026-11-27 16:40:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0013_class_group_level_uq"
down_revision: str | None = "0012_slice11_assessments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_class_groups_school_year_name", "class_groups", type_="unique"
    )
    op.create_unique_constraint(
        "uq_class_groups_school_year_level_name",
        "class_groups",
        ["school_id", "academic_year_id", "year_level_id", "name"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_class_groups_school_year_level_name", "class_groups", type_="unique"
    )
    op.create_unique_constraint(
        "uq_class_groups_school_year_name",
        "class_groups",
        ["school_id", "academic_year_id", "name"],
    )
