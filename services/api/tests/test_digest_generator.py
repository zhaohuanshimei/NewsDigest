from __future__ import annotations

from datetime import date, datetime, timezone

from app.models.article import Article
from app.models.cluster import Cluster
from app.models.cluster_member import ClusterMember
from app.models.digest import Digest
from app.models.digest_entry import DigestEntry
from app.models.source import Source
from app.services.digest_generator import DigestGenerator


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

_article_counter = 0


def _unique_url() -> str:
    global _article_counter
    _article_counter += 1
    return f"https://example.com/article/{_article_counter}"


def _create_source(db, name: str | None = None, kind: str = "rss") -> Source:
    tag = _create_source._counter = getattr(_create_source, "_counter", 0) + 1
    name = name or f"Source {tag}"
    source = Source(name=name, kind=kind, url=f"https://{name}.example.com/rss")
    db.add(source)
    db.flush()
    return source


def _create_article(
    db,
    source_id: int,
    title: str = "Test Headline",
    summary: str | None = "Test summary.",
) -> Article:
    article = Article(
        source_id=source_id,
        url=_unique_url(),
        title=title,
        summary=summary,
    )
    db.add(article)
    db.flush()
    return article


def _setup_cluster(
    db,
    article_ids: list[int],
    score: float = 1.0,
    first_seen_at: datetime | None = None,
) -> Cluster:
    if first_seen_at is None:
        first_seen_at = datetime.now(timezone.utc)
    cluster = Cluster(
        representative_article_id=article_ids[0],
        size=len(article_ids),
        score=score,
        first_seen_at=first_seen_at,
    )
    db.add(cluster)
    db.flush()
    for rank, aid in enumerate(article_ids):
        db.add(ClusterMember(cluster_id=cluster.id, article_id=aid, rank=rank))
    db.commit()
    db.refresh(cluster)
    return cluster


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDigestGenerator:

    def test_normal_generation(self, db_session) -> None:
        """Normal generation creates digest + entries from clusters."""
        src_a = _create_source(db_session, "Source A")
        src_b = _create_source(db_session, "Source B")

        today = date(2026, 6, 26)
        first_seen = datetime(2026, 6, 26, 8, 0, tzinfo=timezone.utc)

        art1 = _create_article(db_session, src_a.id, "Headline 1", "Summary 1")
        art2 = _create_article(db_session, src_a.id, "Headline 2", "Summary 2")
        art3 = _create_article(db_session, src_b.id, "Headline 3", "Summary 3")

        _setup_cluster(db_session, [art1.id, art2.id, art3.id],
                       score=5.0, first_seen_at=first_seen)

        gen = DigestGenerator(db_session)
        digest = gen.generate(today)

        assert digest.date == today
        assert digest.status == "draft"
        assert len(digest.entries) == 1

        entry = digest.entries[0]
        assert entry.headline == "Headline 1"
        assert entry.summary == "Summary 1"
        assert entry.rank == 1
        assert entry.source_count == 2  # two distinct sources
        assert entry.category == "general"  # cluster has no topic → general

    def test_idempotent_overwrite(self, db_session) -> None:
        """Re-generating for the same date replaces the old digest cleanly."""
        src = _create_source(db_session)
        today = date(2026, 6, 26)
        first_seen = datetime(2026, 6, 26, 8, 0, tzinfo=timezone.utc)

        art1 = _create_article(db_session, src.id, "Headline 1", "Summary 1")
        _setup_cluster(db_session, [art1.id], score=5.0, first_seen_at=first_seen)

        gen = DigestGenerator(db_session)
        gen.generate(today)

        assert db_session.query(Digest).count() == 1
        assert db_session.query(DigestEntry).count() == 1

        # Add another cluster and re-generate
        art2 = _create_article(db_session, src.id, "Headline 2", "Summary 2")
        _setup_cluster(db_session, [art2.id], score=3.0, first_seen_at=first_seen)

        gen.generate(today)

        assert db_session.query(Digest).count() == 1  # still one digest
        assert db_session.query(DigestEntry).count() == 2  # two entries now

    def test_empty_data_date(self, db_session) -> None:
        """Date with no clusters produces an empty-draft digest, not a 404."""
        today = date(2026, 6, 26)

        gen = DigestGenerator(db_session)
        digest = gen.generate(today)

        assert digest.date == today
        assert digest.status == "draft"
        assert len(digest.entries) == 0

    def test_boundary_date_with_clusters(self, db_session) -> None:
        """Clusters whose first_seen_at falls on the boundary date are included."""
        src = _create_source(db_session)
        target_date = date(2026, 6, 1)

        art = _create_article(db_session, src.id, "Boundary", "Boundary summary")
        first_seen = datetime(2026, 6, 1, 23, 59, 59, tzinfo=timezone.utc)
        _setup_cluster(db_session, [art.id], score=5.0, first_seen_at=first_seen)

        gen = DigestGenerator(db_session)
        digest = gen.generate(target_date)

        assert len(digest.entries) == 1
        assert digest.entries[0].headline == "Boundary"

    def test_score_ordering(self, db_session) -> None:
        """Clusters are sorted by computed importance score in descending order."""
        src1 = _create_source(db_session, "Source A")
        src2 = _create_source(db_session, "Source B")
        today = date(2026, 6, 26)
        first_seen = datetime(2026, 6, 26, 8, 0, tzinfo=timezone.utc)

        # High-scored cluster: 10 articles from 2 sources → larger size, better diversity
        high_articles = []
        for i in range(10):
            src = src1 if i < 5 else src2
            a = _create_article(db_session, src.id, f"High Article {i}", f"High {i}")
            high_articles.append(a)
        _setup_cluster(db_session, [a.id for a in high_articles], score=5.0, first_seen_at=first_seen)

        # Low-scored cluster: 1 source + 1 article
        art3 = _create_article(db_session, src2.id, "Low Score", "Low")
        _setup_cluster(db_session, [art3.id], score=1.0, first_seen_at=first_seen)

        gen = DigestGenerator(db_session)
        digest = gen.generate(today)

        assert len(digest.entries) == 2
        # High cluster has 10 articles from 2 sources → higher importance
        assert digest.entries[0].headline.startswith("High Article")
        assert digest.entries[1].headline == "Low Score"
