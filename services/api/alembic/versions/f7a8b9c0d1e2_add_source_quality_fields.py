"""add quality_score and tier fields to sources

Revision ID: f7a8b9c0d1e2
Revises: e3b1d2c4f5a6
Create Date: 2026-06-30 12:30:00.000000

"""
from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f7a8b9c0d1e2"
down_revision: str | None = "e3b1d2c4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sources",
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.5"),
    )
    op.add_column(
        "sources",
        sa.Column("tier", sa.String(16), nullable=False, server_default="tier-2"),
    )


def downgrade() -> None:
    op.drop_column("sources", "tier")
    op.drop_column("sources", "quality_score")
