"""Service for digest query operations."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.cluster_member import ClusterMember
from app.models.source import Source
from app.repositories.digest_query_repository import DigestQueryRepository
from app.repositories.translation_repository import TranslationRepository
from app.schemas.digest import DigestResource, DigestEntryResource


TARGET_LANGUAGE = "zh"


class DigestQueryService:
    """Service for querying digests, aligned with shared-types DigestResource."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = DigestQueryRepository(db)
        self.translation_repo = TranslationRepository(db)

    def get_latest(self) -> DigestResource | None:
        """Get the latest digest as DigestResource."""
        digest = self.repo.get_latest_digest()
        if digest is None:
            return None

        return self._to_resource(digest)

    def get_by_date(self, target_date: date) -> DigestResource | None:
        """Get digest for a specific date as DigestResource."""
        digest = self.repo.get_digest_by_date(target_date)
        if digest is None:
            return None

        return self._to_resource(digest)

    def get_available_dates(self, limit: int = 30) -> list[date]:
        """Get list of dates with digests, in descending order."""
        return self.repo.get_available_dates(limit)

    def _get_cluster_media_and_sources(self, cluster_id: int) -> tuple[str, str, list[str]]:
        """Fetch image_url, video_url, and source names for a cluster.

        Returns (image_url, video_url, source_names).
        """
        # Get representative article for media
        from app.models.cluster import Cluster
        cluster = self.db.query(Cluster).filter(Cluster.id == cluster_id).first()
        image_url = ""
        video_url = ""
        if cluster and cluster.representative_article_id:
            rep_article = self.db.query(Article).filter(
                Article.id == cluster.representative_article_id
            ).first()
            if rep_article:
                image_url = rep_article.image_url or ""
                video_url = rep_article.video_url or ""

        # Get source names from member articles
        source_rows = (
            self.db.query(Source.name)
            .join(Article, Article.source_id == Source.id)
            .join(ClusterMember, ClusterMember.article_id == Article.id)
            .filter(ClusterMember.cluster_id == cluster_id)
            .distinct()
            .all()
        )
        source_names = [row[0] for row in source_rows if row[0]]

        return image_url, video_url, source_names

    def _to_resource(self, digest) -> DigestResource:
        """Convert Digest model to DigestResource schema."""
        entries = []
        if digest.entries:
            for entry in digest.entries:
                translation = self.translation_repo.get_completed_translation(
                    entry.id, TARGET_LANGUAGE
                )
                image_url, video_url, sources = self._get_cluster_media_and_sources(
                    entry.cluster_id
                )
                entries.append(
                    DigestEntryResource(
                        cluster_id=str(entry.cluster_id),
                        rank=entry.rank,
                        category=entry.category or "",
                        headline=entry.headline,
                        summary=entry.summary or "",
                        source_count=entry.source_count,
                        sources=sources,
                        image_url=image_url,
                        video_url=video_url,
                        headline_translated=translation.translated_title if translation else "",
                        summary_translated=translation.translated_summary if translation else "",
                    )
                )

        published_at = ""
        if digest.published_at:
            published_at = digest.published_at.isoformat()
        elif digest.created_at:
            published_at = digest.created_at.isoformat()

        return DigestResource(
            date=digest.date.isoformat(),
            published_at=published_at,
            entries=entries,
        )
