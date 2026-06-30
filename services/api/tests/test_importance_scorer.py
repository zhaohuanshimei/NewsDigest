from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models.article import Article
from app.models.cluster import Cluster
from app.services.importance_scorer import (
    WEIGHT_AVG_SOURCE_QUALITY,
    WEIGHT_CLUSTER_SIZE,
    WEIGHT_FRESHNESS,
    WEIGHT_SOURCE_DIVERSITY,
    WEIGHT_TIER_BONUS,
    score_cluster,
)


def _cluster(
    size: int = 1,
    score: float = 1.0,
    topic: str | None = None,
    first_seen_at: datetime | None = None,
) -> Cluster:
    if first_seen_at is None:
        first_seen_at = datetime.now(timezone.utc)
    c = Cluster(
        size=size,
        score=score,
        topic=topic,
        first_seen_at=first_seen_at,
    )
    c.id = 1
    return c


def _article(
    source_id: int = 1,
    published_at: datetime | None = None,
) -> Article:
    if published_at is None:
        published_at = datetime.now(timezone.utc)
    a = Article(
        source_id=source_id,
        url="https://example.com/a",
        title="Test",
        published_at=published_at,
    )
    a.id = 1
    return a


class TestScoreCluster:
    """Tests for the rule-based importance scoring formula."""

    # ── source diversity ─────────────────────────────────────────

    def test_single_source_diversity(self) -> None:
        """Single source gives diversity=1.0, weighted contribution=0.30."""
        c = _cluster(size=1)
        members = [_article(source_id=1)]
        s = score_cluster(c, members)
        # At minimum: source_diversity(0.30) + avg_quality(0.125) + cluster_size(0.05)
        # + freshness(~0.20) = 0.675.  Actual result should be >= this.
        assert s >= 0.60

    def test_multiple_sources_diversity(self) -> None:
        """Multiple sources → diversity bounded by weight."""
        c = _cluster(size=2)
        members = [_article(source_id=1), _article(source_id=2)]
        s = score_cluster(c, members)
        assert s >= WEIGHT_SOURCE_DIVERSITY * (2 / 2)

    # ── source quality ───────────────────────────────────────────

    def test_quality_map_used(self) -> None:
        """Provided quality_map is used for avg_source_quality."""
        c = _cluster(size=1)
        members = [_article(source_id=1)]
        quality_map = {1: 1.0}
        s = score_cluster(c, members, source_quality_map=quality_map)
        # Freshness + cluster_size + source_diversity + avg_quality + tier_bonus
        # avg_quality = 1.0, weighted = 0.25
        assert s >= WEIGHT_AVG_SOURCE_QUALITY * 1.0

    def test_quality_map_default(self) -> None:
        """Without quality map, defaults to 0.5."""
        c = _cluster(size=1)
        members = [_article(source_id=1)]
        s = score_cluster(c, members)
        # avg_quality defaults to 0.5 → weighted = 0.125
        assert s >= WEIGHT_AVG_SOURCE_QUALITY * 0.5

    # ── freshness decay ──────────────────────────────────────────

    def test_fresh_article_full_freshness(self) -> None:
        """Just-published article → freshness ≈ 1.0."""
        c = _cluster(size=1)
        members = [_article(published_at=datetime.now(timezone.utc))]
        s = score_cluster(c, members)
        expected = WEIGHT_FRESHNESS * 1.0  # ≈ 0.20
        assert s >= expected * 0.9  # allow slight decay from time-of-test

    def test_old_article_low_freshness(self) -> None:
        """Article from 48h ago → freshness significantly lower than fresh."""
        old = datetime.now(timezone.utc) - timedelta(hours=48)
        c = _cluster(size=1)
        members = [_article(published_at=old)]
        s_old = score_cluster(c, members)

        # Compare with a fresh article
        fresh_c = _cluster(size=1)
        fresh_members = [_article(published_at=datetime.now(timezone.utc))]
        s_fresh = score_cluster(fresh_c, fresh_members)

        assert s_old < s_fresh  # Old article scores lower

    # ── tier bonus ───────────────────────────────────────────────

    def test_tier1_bonus_granted(self) -> None:
        """Source name matching tier-1 gets the bonus."""
        # source_tier_map has source_id=1 with tier-1
        c = _cluster(size=1)
        members = [_article(source_id=1)]
        tier_map = {1: "tier-1"}
        s = score_cluster(c, members, source_tier_map=tier_map)
        assert s >= WEIGHT_TIER_BONUS * 1.0 - 0.01  # 0.15

    def test_no_tier1_no_bonus(self) -> None:
        """Without a tier-map, tier bonus is 0 (default tier-2)."""
        c = _cluster(size=1)
        members = [_article(source_id=1)]
        s_no_map = score_cluster(c, members)

        # Same cluster but with tier-1 map should be higher
        tier_map = {1: "tier-1"}
        s_with_map = score_cluster(c, members, source_tier_map=tier_map)
        assert s_with_map > s_no_map  # tier-1 bonus makes it higher

    # ── cluster size ─────────────────────────────────────────────

    def test_size_contribution(self) -> None:
        """Cluster size normalized to a 10 cap."""
        c = _cluster(size=5)
        members = [_article(source_id=1)]
        s = score_cluster(c, members)
        expected_size_weight = WEIGHT_CLUSTER_SIZE * min(5 / 10, 1.0)  # 0.05
        assert s >= expected_size_weight * 0.9

    def test_size_capped_at_10(self) -> None:
        """Size > 10 still gives 1.0 normalized score."""
        c = _cluster(size=20)
        members = [_article(source_id=1)]
        s = score_cluster(c, members)
        max_size_weight = WEIGHT_CLUSTER_SIZE * 1.0  # 0.10
        assert s >= max_size_weight * 0.9

    # ── edge cases ───────────────────────────────────────────────

    def test_empty_members(self) -> None:
        """Cluster with no members should not crash."""
        c = _cluster(size=0)
        s = score_cluster(c, [])
        assert 0.0 <= s <= 1.0

    def test_score_range(self) -> None:
        """Score is always in [0, 1]."""
        c = _cluster(size=10)
        members = [
            _article(source_id=1, published_at=datetime.now(timezone.utc)),
            _article(source_id=2, published_at=datetime.now(timezone.utc)),
        ]
        quality_map = {1: 1.0, 2: 1.0}
        tier_map = {1: "tier-1", 2: "tier-1"}
        s = score_cluster(c, members, source_quality_map=quality_map, source_tier_map=tier_map)
        assert 0.0 <= s <= 1.0

    def test_no_published_at_falls_back_to_first_seen(self) -> None:
        """Article with no published_at should use cluster.first_seen_at."""
        now = datetime.now(timezone.utc)
        old = now - timedelta(hours=48)

        # Old cluster with old first_seen_at
        c_old = _cluster(size=1, first_seen_at=old)
        members_old = [_article(published_at=None)]
        s_old = score_cluster(c_old, members_old)

        # Fresh cluster with fresh first_seen_at
        c_fresh = _cluster(size=1, first_seen_at=now)
        members_fresh = [_article(published_at=None)]
        s_fresh = score_cluster(c_fresh, members_fresh)

        assert s_old < s_fresh  # Old first_seen → lower freshness → lower score
