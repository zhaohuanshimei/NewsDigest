from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.cluster import Cluster
from app.models.digest import Digest
from app.models.source import Source
from app.repositories.digest_repository import DigestRepository
from app.services.importance_scorer import score_cluster

# ── digest generation parameters ──────────────────────────────────────
MAX_ENTRIES = 20
MAX_ENTRIES_PER_TOPIC = 5
MIN_TOPIC_REPRESENTATION = 3


class DigestGenerator:
    """Generates daily digests from clusters.

    Clusters are scored using ``importance_scorer.score_cluster``, then
    partitioned by topic, sorted within each topic, and combined with
    diversity constraints.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = DigestRepository(db)

    def generate(self, target_date: date) -> Digest:
        # Idempotent: remove existing digest for this date before rebuilding
        self.repo.delete_by_date(target_date)

        clusters = self._get_clusters_for_date(target_date)
        if not clusters:
            return self.repo.create_digest(target_date)

        # Bulk-fetch articles, source quality/tier maps
        source_quality_map, source_tier_map = self._build_source_maps()
        all_articles, cluster_article_map = self._build_article_maps(clusters)
        article_by_id: dict[int, Article] = {a.id: a for a in all_articles}

        # Score clusters using the importance scorer
        scored: list[tuple[float, Cluster]] = []
        for c in clusters:
            members = [
                article_by_id[aid]
                for aid in cluster_article_map.get(c.id, [])
                if aid in article_by_id
            ]
            imp = score_cluster(
                c,
                members,
                source_quality_map=source_quality_map,
                source_tier_map=source_tier_map,
            )
            scored.append((imp, c))

        scored.sort(key=lambda x: x[0], reverse=True)

        # ── Topic partition ──────────────────────────────────────────
        topic_groups: dict[str, list[tuple[float, Cluster]]] = defaultdict(list)
        for imp, c in scored:
            t = c.topic or "general"
            topic_groups[t].append((imp, c))

        # Select entries: top `MAX_ENTRIES_PER_TOPIC` from each topic,
        # ensuring at least MIN_TOPIC_REPRESENTATION topics are represented.
        selected: list[tuple[float, Cluster, str]] = []

        # First pass: take the top entry from each topic
        for topic, group in sorted(topic_groups.items()):
            selected.append((group[0][0], group[0][1], topic))

        # Second pass: fill remaining slots respecting per-topic cap
        remaining_slots = MAX_ENTRIES - len(selected)
        if remaining_slots > 0:
            # Flatten remaining entries (skipping the first from each topic)
            pool: list[tuple[float, Cluster, str]] = []
            for topic, group in sorted(topic_groups.items()):
                pool.extend(
                    (imp, c, topic)
                    for imp, c in group[1:]
                )
            pool.sort(key=lambda x: x[0], reverse=True)

            topic_counts: dict[str, int] = defaultdict(int)
            for _, _, t in selected:
                topic_counts[t] += 1

            for imp, c, topic in pool:
                if topic_counts[topic] >= MAX_ENTRIES_PER_TOPIC:
                    continue
                if len(selected) >= MAX_ENTRIES:
                    break
                selected.append((imp, c, topic))
                topic_counts[topic] += 1

        # Build the digest
        digest = self.repo.create_digest(target_date)

        for rank, (imp, cluster, topic) in enumerate(selected, start=1):
            headline, summary = self._get_representative_content(cluster)
            article_ids = cluster_article_map.get(cluster.id, [])
            source_count = self._count_sources(article_ids, article_by_id)

            self.repo.create_entry(
                digest_id=digest.id,
                cluster_id=cluster.id,
                rank=rank,
                category=topic,
                headline=headline,
                summary=summary,
                source_count=source_count,
            )

        self.db.refresh(digest)
        return digest

    def _build_source_maps(
        self,
    ) -> tuple[dict[int, float], dict[int, str]]:
        """Fetch quality_score and tier for all sources."""
        sources = self.db.query(Source).all()
        quality_map: dict[int, float] = {s.id: s.quality_score for s in sources}
        tier_map: dict[int, str] = {s.id: s.tier for s in sources}
        return quality_map, tier_map

    def _build_article_maps(
        self,
        clusters: list[Cluster],
    ) -> tuple[list[Article], dict[int, list[int]]]:
        """Fetch all articles referenced by the given clusters."""
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

        return articles, cluster_article_map

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
            .limit(MAX_ENTRIES)
            .all()
        )

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
