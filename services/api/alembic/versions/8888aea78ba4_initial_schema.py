"""initial schema

Revision ID: 8888aea78ba4
Revises: 
Create Date: 2026-06-26 11:45:33.496265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8888aea78ba4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("language", sa.String(8), server_default="en", nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("fetch_interval_minutes", sa.Integer(), server_default="30", nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("language", sa.String(8), server_default="en", nullable=False),
        sa.Column("normalized_url", sa.Text(), nullable=True),
        sa.Column("dedupe_key", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
        sa.UniqueConstraint("dedupe_key"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name="fk_articles_source_id"),
    )
    op.create_index("ix_articles_source_id", "articles", ["source_id"])
    op.create_index("ix_articles_normalized_url", "articles", ["normalized_url"])
    op.create_index("ix_articles_dedupe_key", "articles", ["dedupe_key"])

    op.create_table(
        "clusters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("representative_article_id", sa.Integer(), nullable=True),
        sa.Column("size", sa.Integer(), server_default="1", nullable=False),
        sa.Column("score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["representative_article_id"], ["articles.id"],
            name="fk_clusters_representative_article_id",
        ),
    )

    op.create_table(
        "cluster_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], name="fk_cluster_members_cluster_id"),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], name="fk_cluster_members_article_id"),
        sa.UniqueConstraint("cluster_id", "article_id", name="uq_cluster_member_cluster_article"),
    )

    op.create_table(
        "digests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(16), server_default="draft", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date"),
    )

    op.create_table(
        "digest_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("digest_id", sa.Integer(), nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("source_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["digest_id"], ["digests.id"], name="fk_digest_entries_digest_id"),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], name="fk_digest_entries_cluster_id"),
    )

    op.create_table(
        "translations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=True),
        sa.Column("digest_entry_id", sa.Integer(), nullable=True),
        sa.Column("target_language", sa.String(8), nullable=False),
        sa.Column("translated_title", sa.Text(), nullable=True),
        sa.Column("translated_summary", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("review_state", sa.String(16), server_default="unreviewed", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], name="fk_translations_article_id"),
        sa.ForeignKeyConstraint(
            ["digest_entry_id"], ["digest_entries.id"],
            name="fk_translations_digest_entry_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("translations")
    op.drop_table("digest_entries")
    op.drop_table("digests")
    op.drop_table("cluster_members")
    op.drop_table("clusters")
    op.drop_table("articles")
    op.drop_table("sources")
