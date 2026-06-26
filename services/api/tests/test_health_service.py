"""Unit tests for HealthService."""

import pytest
from datetime import date, datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.base import Base
from app.models.digest import Digest
from app.services.health_service import HealthService


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_health_check_database_ok_no_digest(db_session):
    """Test health check when database is ok and no digest exists."""
    service = HealthService(db_session)
    result = service.check_health()

    assert result["status"] == "ok"
    assert result["database"] == "ok"
    assert result["last_digest"] is None


def test_health_check_database_ok_with_digest(db_session):
    """Test health check when database is ok and digest exists."""
    # Create a test digest
    test_digest = Digest(
        date=date(2026, 6, 25),
        status="published",
        published_at=datetime(2026, 6, 25, 10, 0, 0, tzinfo=timezone.utc),
    )
    db_session.add(test_digest)
    db_session.commit()

    service = HealthService(db_session)
    result = service.check_health()

    assert result["status"] == "ok"
    assert result["database"] == "ok"
    assert result["last_digest"] is not None
    assert result["last_digest"]["date"] == "2026-06-25"
    assert result["last_digest"]["status"] == "published"
    assert result["last_digest"]["published_at"] is not None


def test_health_check_database_ok_with_draft_digest(db_session):
    """Test health check with draft digest (not published yet)."""
    test_digest = Digest(
        date=date(2026, 6, 26),
        status="draft",
        published_at=None,
    )
    db_session.add(test_digest)
    db_session.commit()

    service = HealthService(db_session)
    result = service.check_health()

    assert result["status"] == "ok"
    assert result["database"] == "ok"
    assert result["last_digest"] is not None
    assert result["last_digest"]["date"] == "2026-06-26"
    assert result["last_digest"]["status"] == "draft"
    assert result["last_digest"]["published_at"] is None


def test_health_check_database_error(db_session, monkeypatch):
    """Test health check when database connection fails."""
    # Mock the repository method to simulate database error
    from app.repositories.health_repository import HealthRepository

    original_check = HealthRepository.check_database_connection

    def mock_check_connection(self):
        return False

    monkeypatch.setattr(
        HealthRepository,
        "check_database_connection",
        mock_check_connection,
    )

    service = HealthService(db_session)
    result = service.check_health()

    assert result["status"] == "error"
    assert result["database"] == "error"

    # Restore original method
    monkeypatch.setattr(
        HealthRepository,
        "check_database_connection",
        original_check,
    )


def test_health_check_multiple_digests_returns_latest(db_session):
    """Test health check returns most recent digest when multiple exist."""
    # Create multiple digests
    digest1 = Digest(
        date=date(2026, 6, 20),
        status="published",
        published_at=datetime(2026, 6, 20, 10, 0, 0, tzinfo=timezone.utc),
    )
    digest2 = Digest(
        date=date(2026, 6, 25),
        status="published",
        published_at=datetime(2026, 6, 25, 10, 0, 0, tzinfo=timezone.utc),
    )
    digest3 = Digest(
        date=date(2026, 6, 22),
        status="published",
        published_at=datetime(2026, 6, 22, 10, 0, 0, tzinfo=timezone.utc),
    )

    db_session.add_all([digest1, digest2, digest3])
    db_session.commit()

    service = HealthService(db_session)
    result = service.check_health()

    assert result["status"] == "ok"
    assert result["database"] == "ok"
    assert result["last_digest"] is not None
    # Should return the most recent one (2026-06-25)
    assert result["last_digest"]["date"] == "2026-06-25"
