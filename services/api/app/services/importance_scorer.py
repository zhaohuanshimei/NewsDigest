from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Sequence

from app.models.article import Article
from app.models.cluster import Cluster

# ── importance score weights ─────────────────────────────────────────
# Configurable weights for the rule-based importance scoring formula.
# These are module-level constants so they can be inspected and overridden
# by tests without touching production code.
WEIGHT_SOURCE_DIVERSITY = 0.30
WEIGHT_AVG_SOURCE_QUALITY = 0.25
WEIGHT_FRESHNESS = 0.20
WEIGHT_TIER_BONUS = 0.15
WEIGHT_CLUSTER_SIZE = 0.10

# Freshness half-life in hours — after 24 hours score decays to ~37%
FRESHNESS_DECAY_HOURS = 24

# Tier-1 source bonus threshold — cluster with at least one tier-1 source
# gets the full tier_bonus weight
TIER_BONUS_SOURCES = frozenset({
    "BBC News", "Reuters", "AP News", "NYT Home Page",
    "The Guardian International", "NPR News", "Washington Post",
    "Al Jazeera English", "DW (Deutsche Welle)", "France 24 English",
})


def score_cluster(
    cluster: Cluster,
    members: Sequence[Article],
    source_quality_map: dict[int, float] | None = None,
    source_tier_map: dict[int, str] | None = None,
) -> float:
    """Compute a rule-based importance score for a cluster (0–1).

    Formula:
      rule_score =
        0.30 * source_diversity       # unique sources / total sources in members
        0.25 * avg_source_quality     # mean quality_score of member sources
        0.20 * freshness_decay        # exp(-age_hours / 24)
        0.15 * tier_bonus             # 1.0 if any tier-1 source, else 0.0
        0.10 * cluster_size           # min(cluster.size / 10, 1.0)

    Weights are exposed as module-level constants (``WEIGHT_*``) and can
    be overridden or tested independently.
    """
    source_quality_map = source_quality_map or {}
    source_tier_map = source_tier_map or {}

    source_ids = {a.source_id for a in members if a is not None}
    total_possible_sources = max(len(source_ids), 1)

    # 1. Source diversity
    source_diversity = len(source_ids) / total_possible_sources

    # 2. Average source quality
    if source_ids and source_quality_map:
        scores = [
            source_quality_map.get(sid, 0.5)
            for sid in source_ids
        ]
        avg_source_quality = sum(scores) / len(scores) if scores else 0.5
    else:
        avg_source_quality = 0.5

    # 3. Freshness decay
    now = datetime.now(timezone.utc)
    ref_time = None
    if members and members[0] and members[0].published_at:
        ref_time = members[0].published_at
    elif cluster.first_seen_at:
        ref_time = cluster.first_seen_at

    if ref_time is not None:
        # SQLite may return offset-naive datetimes — treat them as UTC
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)
        age = (now - ref_time).total_seconds()
        age_hours = age / 3600
    else:
        age_hours = 0
    freshness_decay = math.exp(-age_hours / FRESHNESS_DECAY_HOURS)

    # 4. Tier bonus — any tier-1 source?
    has_tier1 = False
    for sid in source_ids:
        t = source_tier_map.get(sid, "tier-2")
        if t == "tier-1":
            has_tier1 = True
            break
    tier_bonus = 1.0 if has_tier1 else 0.0

    # 5. Cluster size (normalized to a cap of 10)
    size_score = min(cluster.size / 10.0, 1.0)

    return (
        WEIGHT_SOURCE_DIVERSITY * source_diversity
        + WEIGHT_AVG_SOURCE_QUALITY * avg_source_quality
        + WEIGHT_FRESHNESS * freshness_decay
        + WEIGHT_TIER_BONUS * tier_bonus
        + WEIGHT_CLUSTER_SIZE * size_score
    )
