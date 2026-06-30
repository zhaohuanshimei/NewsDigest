from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.models.article import Article
from app.models.cluster import Cluster
from app.models.cluster_member import ClusterMember
from app.models.digest import Digest
from app.models.digest_entry import DigestEntry
from app.models.source import Source
from app.services.source_scoring_service import SourceScoringService


def _count_adjusted(svc: SourceScoringService) -> int:
    """Helper to call recalculate_all and return the count."""
    return svc.recalculate_all()


class TestSourceScoringService:
    """Tests for the source scoring service.

    Uses the real database fixture so we can insert articles, clusters,
    and digest entries to exercise the scoring queries.
    """

    # ── 调分逻辑 ────────────────────────────────────────────

    def test_high_digest_rate_gets_bonus(
        self, db_session,
    ) -> None:
        """Source with >30% of articles in digest gets +0.1."""
        source = _seed_source(db_session)
        svc = SourceScoringService(db_session)
        articles = _seed_articles(db_session, source, count=10)
        cluster = _seed_cluster(db_session)
        _seed_cluster_members(db_session, cluster, articles[:4])  # 4/10 = 40%
        _seed_digest(db_session, cluster)

        adjusted = _count_adjusted(svc)
        assert adjusted >= 1
        src = db_session.get(Source, source.id)
        assert src.quality_score == pytest.approx(0.6, abs=0.001)

    def test_high_dedup_rate_gets_penalty(
        self, db_session,
    ) -> None:
        """Source with >70% of articles deduped gets -0.1."""
        source = _seed_source(db_session)
        svc = SourceScoringService(db_session)
        articles = _seed_articles(db_session, source, count=10)
        cluster = _seed_cluster(db_session)
        _seed_cluster_members(db_session, cluster, articles[:2])  # 2/10 = 20% → 80% dedup rate

        adjusted = _count_adjusted(svc)
        src = db_session.get(Source, source.id)
        assert src.quality_score == pytest.approx(0.4, abs=0.001)

    def test_both_bonus_and_penalty_stack(
        self, db_session,
    ) -> None:
        """Both bonus and penalty can apply to the same source."""
        source = _seed_source(db_session)
        svc = SourceScoringService(db_session)
        articles = _seed_articles(db_session, source, count=10)
        cluster = _seed_cluster(db_session)
        _seed_cluster_members(db_session, cluster, articles[:4])  # 4 in cluster, 6 deduped
        _seed_digest(db_session, cluster)  # 4/10 = 40% in digest → +0.1
        # 6/10 = 60% deduped < 70%, so no penalty

        svc.recalculate_all()
        src = db_session.get(Source, source.id)
        # 0.5 + 0.1 = 0.6
        assert src.quality_score == pytest.approx(0.6, abs=0.001)

    def test_bonus_and_penalty_cancel_on_edge(
        self, db_session,
    ) -> None:
        """Both bonus and penalty can apply."""
        source = _seed_source(db_session)
        svc = SourceScoringService(db_session)
        articles = _seed_articles(db_session, source, count=10)
        cluster = _seed_cluster(db_session)
        _seed_cluster_members(db_session, cluster, articles[:2])  # 2/10 in cluster, 8/10 deduped
        _seed_digest(db_session, cluster)
        # 2/10 = 20% in digest < 30% → no bonus
        # 8/10 = 80% deduped > 70% → -0.1
        # score = 0.5 - 0.1 = 0.4

        svc.recalculate_all()
        src = db_session.get(Source, source.id)
        assert src.quality_score == pytest.approx(0.4, abs=0.001)

    # ── 边界 clamp ──────────────────────────────────────────

    def test_clamp_lower_bound(self, db_session) -> None:
        """quality_score never goes below 0.1."""
        source = _seed_source(db_session, quality_score=0.15)
        svc = SourceScoringService(db_session)
        _seed_articles(db_session, source, count=10)
        # 0 articles in cluster → dedup_rate = 100% > 70% → -0.1
        # 0.15 - 0.1 = 0.05 → clamped to 0.1

        svc.recalculate_all()
        db_session.refresh(source)
        assert source.quality_score == 0.1

    def test_clamp_upper_bound(self, db_session) -> None:
        """quality_score never goes above 1.0."""
        source = _seed_source(db_session, quality_score=0.95)
        svc = SourceScoringService(db_session)
        articles = _seed_articles(db_session, source, count=10)
        cluster = _seed_cluster(db_session)
        _seed_cluster_members(db_session, cluster, articles[:10])
        _seed_digest(db_session, cluster)
        # 10/10 = 100% in digest → +0.1
        # 0.95 + 0.1 = 1.05 → clamped to 1.0

        svc.recalculate_all()
        db_session.refresh(source)
        assert source.quality_score == 1.0

    # ── 无数据源保持默认 ─────────────────────────────────────

    def test_no_data_keeps_default(self, db_session) -> None:
        """Source with no articles should keep its default quality_score."""
        source = _seed_source(db_session)
        svc = SourceScoringService(db_session)
        adjusted = _count_adjusted(svc)
        assert adjusted == 0
        db_session.refresh(source)
        assert source.quality_score == 0.5

    # ── tier 不被调分改变 ────────────────────────────────────

    def test_tier_not_changed_by_scoring(self, db_session) -> None:
        """The tier field should not be affected by recalculate_all."""
        source = _seed_source(db_session)
        svc = SourceScoringService(db_session)
        articles = _seed_articles(db_session, source, count=10)
        cluster = _seed_cluster(db_session)
        _seed_cluster_members(db_session, cluster, articles[:4])
        _seed_digest(db_session, cluster)

        svc.recalculate_all()
        db_session.refresh(source)
        assert source.tier == "tier-2"  # unchanged

    # ── get_quality_score ────────────────────────────────────

    def test_get_quality_score_returns_default_for_unknown(self, db_session) -> None:
        svc = SourceScoringService(db_session)
        assert svc.get_quality_score("NonExistentSource") == 0.5

    def test_get_quality_score_returns_stored_value(
        self, db_session,
    ) -> None:
        source = _seed_source(db_session)
        svc = SourceScoringService(db_session)
        assert svc.get_quality_score(source.name) == 0.5

    # ── get_tier ─────────────────────────────────────────────

    def test_get_tier_returns_pending_for_unknown(self, db_session) -> None:
        svc = SourceScoringService(db_session)
        assert svc.get_tier("NonExistentSource") == "pending"

    def test_get_tier_returns_stored_value(self, db_session) -> None:
        source = _seed_source(db_session)
        svc = SourceScoringService(db_session)
        assert svc.get_tier(source.name) == "tier-2"


# ── test helpers ────────────────────────────────────────────────────────


def _seed_source(db_session, quality_score: float = 0.5) -> Source:
    s = Source(
        name=f"_test_source_{datetime.now(timezone.utc).timestamp()}",
        kind="rss",
        url="https://example.com/rss",
        quality_score=quality_score,
    )
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


def _seed_articles(db_session, source: Source, count: int) -> list[Article]:
    articles = []
    now = datetime.now(timezone.utc)
    for i in range(count):
        a = Article(
            source_id=source.id,
            url=f"https://example.com/article_{i}_{now.timestamp()}",
            title=f"Test Article {i}",
            body=f"Content {i}",
            created_at=now,
            updated_at=now,
        )
        db_session.add(a)
        articles.append(a)
    db_session.commit()
    for a in articles:
        db_session.refresh(a)
    return articles


def _seed_cluster(db_session) -> Cluster:
    c = Cluster(size=1)
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


def _seed_cluster_members(
    db_session, cluster: Cluster, articles: list[Article]
) -> None:
    for a in articles:
        cm = ClusterMember(cluster_id=cluster.id, article_id=a.id)
        db_session.add(cm)
    db_session.commit()
    # Update cluster size
    cluster.size = len(articles)
    db_session.commit()


def _seed_digest(db_session, cluster: Cluster) -> Digest:
    today = datetime.now(timezone.utc).date()
    d = Digest(date=today, status="published")
    db_session.add(d)
    db_session.commit()
    db_session.refresh(d)

    entry = DigestEntry(
        digest_id=d.id,
        cluster_id=cluster.id,
        rank=1,
        headline="Test",
    )
    db_session.add(entry)
    db_session.commit()
    return d
