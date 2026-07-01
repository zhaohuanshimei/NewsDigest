"""add image_url and video_url to articles

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("image_url", sa.Text(), nullable=True))
    op.add_column("articles", sa.Column("video_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("articles", "video_url")
    op.drop_column("articles", "image_url")
