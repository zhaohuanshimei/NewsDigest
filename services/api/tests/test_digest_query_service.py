"""Unit tests for DigestQueryService."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.base import Base
from app.models.digest import Digest
from app.models.digest_entry import DigestEntry
from app.models.cluster import Cluster
from app.services.digest_query_service import DigestQueryService


@pytest.fixture
def db_session():
    """Create a fresh in-memory database for each test."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def service(db_session):
    """Create DigestQueryService instance."""
    return DigestQueryService(db_session)


def _create_test_digest(
    db_session,
    target_date: date,
    status: str = "published",
    num_entries: int = 0,
) -> Digest:
    """Helper to create a test digest with optional entries."""
    published_at = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    digest = Digest(
        date=target_date,
        status=status,
        published_at=published_at,
    )
    db_session.add(digest)
    db_session.commit()
    db_session.refresh(digest)

    # Create entries if requested
    for i in range(num_entries):
        cluster = Cluster(size=1, score=1.0)
        db_session.add(cluster)
        db_session.commit()
        db_session.refresh(cluster)

        entry = DigestEntry(
            digest_id=digest.id,
            cluster_id=cluster.id,
            rank=i + 1,
            category="test",
            headline=f"Test headline {i + 1}",
            summary=f"Test summary {i + 1}",
            source_count=1,
        )
        db_session.add(entry)
        db_session.commit()

    db_session.refresh(digest)
    return digest


class TestDigestQueryService:
    """Test suite for DigestQueryService."""

    def test_get_latest_with_published_digest(self, service, db_session):
        """Test get_latest returns published digest."""
        _create_test_digest(db_session, date(2026, 6, 20), status="published")
        _create_test_digest(db_session, date(2026, 6, 25), status="published")

        result = service.get_latest()

        assert result is not None
        assert result.date == "2026-06-25"

    def test_get_latest_falls_back_to_latest_date(self, service, db_session):
        """Test get_latest falls back to latest date if no published."""
        _create_test_digest(db_session, date(2026, 6, 20), status="draft")
        _create_test_digest(db_session, date(2026, 6, 25), status="draft")

        result = service.get_latest()

        assert result is not None
        assert result.date == "2026-06-25"

    def test_get_latest_returns_none_when_empty(self, service):
        """Test get_latest returns None when no digests exist."""
        result = service.get_latest()
        assert result is None

    def test_get_by_date_returns_digest(self, service, db_session):
        """Test get_by_date returns digest for specific date."""
        _create_test_digest(db_session, date(2026, 6, 20), num_entries=2)

        result = service.get_by_date(date(2026, 6, 20))

        assert result is not None
        assert result.date == "2026-06-20"
        assert len(result.entries) == 2
        assert result.entries[0].rank == 1
        assert result.entries[1].rank == 2

    def test_get_by_date_returns_none_when_not_found(self, service, db_session):
        """Test get_by_date returns None for non-existent date."""
        _create_test_digest(db_session, date(2026, 6, 20))

        result = service.get_by_date(date(2026, 6, 25))
        assert result is None

    def test_get_by_date_with_empty_entries(self, service, db_session):
        """Test get_by_date handles digest with no entries."""
        _create_test_digest(db_session, date(2026, 6, 20), num_entries=0)

        result = service.get_by_date(date(2026, 6, 20))

        assert result is not None
        assert result.date == "2026-06-20"
        assert len(result.entries) == 0

    def test_get_available_dates_returns_sorted_list(self, service, db_session):
        """Test get_available_dates returns dates in descending order."""
        _create_test_digest(db_session, date(2026, 6, 20))
        _create_test_digest(db_session, date(2026, 6, 25))
        _create_test_digest(db_session, date(2026, 6, 22))

        result = service.get_available_dates()

        assert result == [
            date(2026, 6, 25),
            date(2026, 6, 22),
            date(2026, 6, 20),
        ]

    def test_get_available_dates_respects_limit(self, service, db_session):
        """Test get_available_dates respects limit parameter."""
        _create_test_digest(db_session, date(2026, 6, 20))
        _create_test_digest(db_session, date(2026, 6, 25))
        _create_test_digest(db_session, date(2026, 6, 22))

        result = service.get_available_dates(limit=2)

        assert len(result) == 2
        assert result == [date(2026, 6, 25), date(2026, 6, 22)]

    def test_get_available_dates_empty(self, service):
        """Test get_available_dates returns empty list when no digests."""
        result = service.get_available_dates()
        assert result == []

    def test_digest_resource_structure_alignment(self, service, db_session):
        """Test that returned resource matches shared-types structure."""
        digest = _create_test_digest(db_session, date(2026, 6, 20), num_entries=1)

        result = service.get_by_date(date(2026, 6, 20))

        assert result is not None
        # Verify structure matches DigestResource
        assert hasattr(result, "date")
        assert hasattr(result, "published_at")
        assert hasattr(result, "entries")
        assert len(result.entries) == 1
        # Verify entry structure matches DigestEntryResource
        entry = result.entries[0]
        assert hasattr(entry, "cluster_id")
        assert hasattr(entry, "rank")
        assert hasattr(entry, "category")
        assert hasattr(entry, "headline")
        assert hasattr(entry, "summary")
        assert hasattr(entry, "source_count")
