"""add topic fields to articles and clusters

Revision ID: e3b1d2c4f5a6
Revises: 8888aea78ba4
Create Date: 2026-06-30 12:00:00.000000

"""
from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e3b1d2c4f5a6"
down_revision: str | None = "8888aea78ba4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("topic", sa.String(32), nullable=True),
    )
    op.add_column(
        "clusters",
        sa.Column("topic", sa.String(32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("clusters", "topic")
    op.drop_column("articles", "topic")
