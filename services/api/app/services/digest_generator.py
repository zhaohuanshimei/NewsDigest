from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.cluster import Cluster
from app.models.digest import Digest
from app.repositories.digest_repository import DigestRepository

DEFAULT_ENTRY_COUNT = 15


class DigestGenerator:
    """Generates daily digests from clusters based on score and recency."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = DigestRepository(db)

    def generate(self, target_date: date) -> Digest:
        # Idempotent: remove existing digest for this date before rebuilding
        self.repo.delete_by_date(target_date)

        clusters = self._get_clusters_for_date(target_date)
        if not clusters:
            return self.repo.create_digest(target_date)

        # Bulk-fetch all articles for scoring / source counting
        all_article_ids: set[int] = set()
        cluster_article_map: dict[int, list[int]] = {}
        for c in clusters:
            aids = [m.article_id for m in (c.members or [])]
            cluster_article_map[c.id] = aids
            all_article_ids.update(aids)

        articles: list[Article] = (
            self.db.query(Article)
            .filter(Article.id.in_(all_article_ids))
            .all()
        ) if all_article_ids else []
        article_by_id: dict[int, Article] = {a.id: a for a in articles}

        # Score and rank clusters
        scored = [
            (self._compute_score(c, cluster_article_map, article_by_id), c)
            for c in clusters
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:DEFAULT_ENTRY_COUNT]

        # Build a digest and its entries
        digest = self.repo.create_digest(target_date)

        for rank, (_score, cluster) in enumerate(top, start=1):
            headline, summary = self._get_representative_content(cluster)
            article_ids = cluster_article_map.get(cluster.id, [])
            source_count = self._count_sources(article_ids, article_by_id)

            self.repo.create_entry(
                digest_id=digest.id,
                cluster_id=cluster.id,
                rank=rank,
                category=None,
                headline=headline,
                summary=summary,
                source_count=source_count,
            )

        # Refresh to populate the entries relationship
        self.db.refresh(digest)
        return digest

    def _get_clusters_for_date(self, target_date: date) -> list[Cluster]:
        """Return clusters whose first_seen_at falls on target_date,
        or the most recent clusters if none exist for that date."""
        start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        clusters: list[Cluster] = (
            self.db.query(Cluster)
            .filter(
                Cluster.first_seen_at >= start,
                Cluster.first_seen_at < end,
            )
            .all()
        )

        if clusters:
            return clusters

        # Fall back to most recent clusters
        return (
            self.db.query(Cluster)
            .order_by(Cluster.first_seen_at.desc())
            .limit(DEFAULT_ENTRY_COUNT)
            .all()
        )

    def _compute_score(
        self,
        cluster: Cluster,
        cluster_article_map: dict[int, list[int]],
        article_by_id: dict[int, Article],
    ) -> float:
        """Score = cluster.score * 0.6 + cluster.size * 0.3 + num_sources * 0.1."""
        article_ids = cluster_article_map.get(cluster.id, [])
        source_ids = {
            article_by_id[aid].source_id
            for aid in article_ids
            if aid in article_by_id
        }
        num_sources = len(source_ids)
        return cluster.score * 0.6 + cluster.size * 0.3 + num_sources * 0.1

    def _get_representative_content(
        self, cluster: Cluster
    ) -> tuple[str, str | None]:
        """Retrieve headline and summary from the cluster's representative article."""
        if cluster.representative_article_id is None:
            return "Untitled", None
        article = self.db.get(Article, cluster.representative_article_id)
        if article is None:
            return "Untitled", None
        return article.title or "Untitled", article.summary

    def _count_sources(
        self,
        article_ids: list[int],
        article_by_id: dict[int, Article],
    ) -> int:
        """Count distinct source_ids among the given article_ids."""
        source_ids = {
            article_by_id[aid].source_id
            for aid in article_ids
            if aid in article_by_id
        }
        return len(source_ids)
