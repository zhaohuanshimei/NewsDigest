"""add importance_score to clusters, topic to digest_entries

Revision ID: a1b2c3d4e5f6
Revises: f7a8b9c0d1e2
Create Date: 2026-06-30 13:00:00.000000

"""
from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "f7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clusters",
        sa.Column("importance_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "digest_entries",
        sa.Column("topic", sa.String(32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("digest_entries", "topic")
    op.drop_column("clusters", "importance_score")
