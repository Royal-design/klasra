"""Add optional video_url to lessons

Revision ID: 0011_lesson_video_url
Revises: 0010_slice9_attendance
Create Date: 2026-11-26 15:10:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_lesson_video_url"
down_revision: Union[str, None] = "0010_slice9_attendance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("lessons", sa.Column("video_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("lessons", "video_url")
