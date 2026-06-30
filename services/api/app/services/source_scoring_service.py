from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.cluster import Cluster
from app.models.cluster_member import ClusterMember
from app.models.digest import Digest
from app.models.digest_entry import DigestEntry
from app.models.source import Source
from app.repositories.source_repository import SourceRepository

# Look-back window for statistics
STATS_WINDOW_DAYS = 30

# Scoring adjustments
DIGEST_ENTRY_RATE_THRESHOLD = 0.30
DIGEST_ENTRY_BONUS = 0.10

DEDUP_ELIMINATION_RATE_THRESHOLD = 0.70
DEDUP_ELIMINATION_PENALTY = 0.10


class SourceScoringService:
    """Recalculates quality_score for every source based on recent
    statistical performance.

    This is a pure-statistical scoring mechanism (no AI).  It examines the
    past 30 days of article and digest data for each source and adjusts its
    quality_score up or down.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = SourceRepository(db)

    def recalculate_all(self) -> int:
        """Recalculate quality_score for every active source.

        Returns:
            Number of sources whose score was adjusted.
        """
        sources = self.repository.get_enabled_sources()
        adjusted = 0
        cutoff = datetime.now(timezone.utc) - timedelta(days=STATS_WINDOW_DAYS)

        for source in sources:
            old_score = source.quality_score
            new_score = self._calculate_score(source, cutoff)
            if abs(new_score - old_score) > 0.001:
                source.quality_score = min(1.0, max(0.1, new_score))
                adjusted += 1

        self.db.commit()
        return adjusted

    def _calculate_score(self, source: Source, cutoff: datetime) -> float:
        """Calculate adjusted quality_score for a single source."""
        source_id = source.id

        # Total articles from this source in the window
        total = (
            self.db.query(func.count(Article.id))
            .filter(
                Article.source_id == source_id,
                Article.created_at >= cutoff,
            )
            .scalar()
            or 0
        )

        if total == 0:
            return source.quality_score

        # Articles that entered a digest (via cluster → digest_entry)
        in_digest = (
            self.db.query(func.count(Article.id))
            .join(ClusterMember, ClusterMember.article_id == Article.id)
            .join(Cluster, Cluster.id == ClusterMember.cluster_id)
            .join(DigestEntry, DigestEntry.cluster_id == Cluster.id)
            .join(Digest, Digest.id == DigestEntry.digest_id)
            .filter(
                Article.source_id == source_id,
                Article.created_at >= cutoff,
            )
            .scalar()
            or 0
        )

        # Articles in any cluster at all (proxy for "not dedup-eliminated")
        in_cluster = (
            self.db.query(func.count(Article.id))
            .join(ClusterMember, ClusterMember.article_id == Article.id)
            .filter(
                Article.source_id == source_id,
                Article.created_at >= cutoff,
            )
            .scalar()
            or 0
        )

        digest_rate = in_digest / total if total > 0 else 0.0
        dedup_rate = (total - in_cluster) / total if total > 0 else 0.0

        # Start from current score
        score = source.quality_score

        # Bonus for sources whose articles frequently make the digest
        if digest_rate > DIGEST_ENTRY_RATE_THRESHOLD:
            score += DIGEST_ENTRY_BONUS

        # Penalty for sources whose articles are frequently deduplicated away
        if dedup_rate > DEDUP_ELIMINATION_RATE_THRESHOLD:
            score -= DEDUP_ELIMINATION_PENALTY

        return score

    def get_quality_score(self, source_name: str) -> float:
        """Convenience: get the current quality_score for a named source."""
        source = self.repository.get_by_name(source_name)
        if source is None:
            return 0.5
        return source.quality_score

    def get_tier(self, source_name: str) -> str:
        """Convenience: get the current tier for a named source."""
        source = self.repository.get_by_name(source_name)
        if source is None:
            return "pending"
        return source.tier
