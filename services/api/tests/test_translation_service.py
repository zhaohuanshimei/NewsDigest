"""Tests for TranslationService (L1-C09)."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.base import Base
from app.models.digest import Digest
from app.models.digest_entry import DigestEntry
from app.models.translation import Translation
from app.services.translation_service import (
    MockTranslationProvider,
    NullTranslationProvider,
    TranslationProvider,
    TranslationService,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc)


def _make_digest(db, target_date: date = date(2026, 6, 26)) -> Digest:
    digest = Digest(date=target_date, status="draft")
    db.add(digest)
    db.commit()
    db.refresh(digest)
    return digest


def _make_entry(
    db,
    digest: Digest,
    rank: int,
    headline: str,
    summary: str | None = "Summary text.",
    cluster_id: int = 1,
) -> DigestEntry:
    entry = DigestEntry(
        digest_id=digest.id,
        cluster_id=cluster_id,
        rank=rank,
        category=None,
        headline=headline,
        summary=summary,
        source_count=1,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


class _FailingProvider(TranslationProvider):
    """Provider that always fails by returning ``None``."""

    name = "failing"

    def translate(self, text: str, target_lang: str) -> str | None:
        return None


class _RaisingProvider(TranslationProvider):
    """Provider that raises on every call — NullTranslationProvider should
    catch this and fall back to the original text."""

    name = "raising"

    def translate(self, text: str, target_lang: str) -> str | None:
        raise RuntimeError("provider boom")


# ---------------------------------------------------------------------------
# Tests — normal translation
# ---------------------------------------------------------------------------


def test_normal_translation_creates_rows(db_session):
    digest = _make_digest(db_session)
    _make_entry(db_session, digest, rank=1, headline="Hello world")
    _make_entry(db_session, digest, rank=2, headline="Second story")

    provider = MockTranslationProvider()
    service = TranslationService(db_session, provider=provider)

    count = service.translate_digest_entries(digest.id, target_language="zh")

    assert count == 2

    rows = (
        db_session.query(Translation)
        .filter(Translation.digest_entry_id.isnot(None))
        .all()
    )
    assert len(rows) == 2
    for row in rows:
        assert row.target_language == "zh"
        assert row.status == "completed"
        assert row.provider == "mock"
        assert row.translated_title.startswith("[zh]")
        assert row.translated_summary.startswith("[zh]")


def test_returns_count_of_newly_translated_entries(db_session):
    digest = _make_digest(db_session)
    for i in range(5):
        _make_entry(db_session, digest, rank=i + 1, headline=f"Headline {i}")

    service = TranslationService(db_session, provider=MockTranslationProvider())
    assert service.translate_digest_entries(digest.id) == 5


# ---------------------------------------------------------------------------
# Tests — empty summary is skipped but headline still translated
# ---------------------------------------------------------------------------


def test_empty_summary_not_translated(db_session):
    digest = _make_digest(db_session)
    entry = _make_entry(
        db_session, digest, rank=1, headline="Only headline", summary=None
    )

    service = TranslationService(db_session, provider=MockTranslationProvider())
    count = service.translate_digest_entries(digest.id)

    assert count == 1
    row = (
        db_session.query(Translation)
        .filter(Translation.digest_entry_id == entry.id)
        .one()
    )
    assert row.translated_title == "[zh] Only headline"
    assert row.translated_summary is None


def test_empty_headline_skipped(db_session):
    digest = _make_digest(db_session)
    _make_entry(db_session, digest, rank=1, headline="   ", summary="ignored")

    service = TranslationService(db_session, provider=MockTranslationProvider())
    assert service.translate_digest_entries(digest.id) == 0
    assert db_session.query(Translation).count() == 0


# ---------------------------------------------------------------------------
# Tests — provider failure
# ---------------------------------------------------------------------------


def test_provider_returns_none_does_not_store_translation(db_session):
    digest = _make_digest(db_session)
    _make_entry(db_session, digest, rank=1, headline="News")

    service = TranslationService(db_session, provider=_FailingProvider())
    assert service.translate_digest_entries(digest.id) == 0
    assert db_session.query(Translation).count() == 0


def test_null_provider_falls_back_to_original_text(db_session):
    digest = _make_digest(db_session)
    entry = _make_entry(
        db_session, digest, rank=1, headline="Breaking news", summary="Some details"
    )

    service = TranslationService(
        db_session, provider=NullTranslationProvider(delegate=_RaisingProvider())
    )
    count = service.translate_digest_entries(digest.id)

    assert count == 1
    row = (
        db_session.query(Translation)
        .filter(Translation.digest_entry_id == entry.id)
        .one()
    )
    # Original text is preserved as the "translation".
    assert row.translated_title == "Breaking news"
    assert row.translated_summary == "Some details"
    assert row.provider == "null"


# ---------------------------------------------------------------------------
# Tests — already-translated skip
# ---------------------------------------------------------------------------


def test_already_translated_entries_are_skipped(db_session):
    digest = _make_digest(db_session)
    _make_entry(db_session, digest, rank=1, headline="Old news")

    service = TranslationService(db_session, provider=MockTranslationProvider())
    assert service.translate_digest_entries(digest.id) == 1

    # Second run should skip the existing translation.
    assert service.translate_digest_entries(digest.id) == 0
    assert db_session.query(Translation).count() == 1


def test_pending_translation_does_not_block_new_attempt(db_session):
    """Only ``status=completed`` translations prevent re-translation."""
    digest = _make_digest(db_session)
    entry = _make_entry(db_session, digest, rank=1, headline="Fresh story")

    # Seed a pending (non-completed) translation row.
    pending = Translation(
        digest_entry_id=entry.id,
        target_language="zh",
        translated_title=None,
        translated_summary=None,
        provider="mock",
        status="pending",
    )
    db_session.add(pending)
    db_session.commit()

    service = TranslationService(db_session, provider=MockTranslationProvider())
    # The pending row is NOT "completed" → service should still translate.
    assert service.translate_digest_entries(digest.id) == 1
    assert db_session.query(Translation).count() == 2


# ---------------------------------------------------------------------------
# Tests — batch / mixed behaviour
# ---------------------------------------------------------------------------


def test_batch_mixed_entries(db_session):
    """Combine: empty summary, empty headline, already-translated, normal."""
    digest = _make_digest(db_session)

    normal = _make_entry(db_session, digest, rank=1, headline="Normal", summary="s1")
    no_summary = _make_entry(
        db_session, digest, rank=2, headline="No summary", summary=None, cluster_id=2
    )
    _make_entry(
        db_session, digest, rank=3, headline="   ", summary="ignored", cluster_id=3
    )
    already = _make_entry(
        db_session, digest, rank=4, headline="Already done", summary="done", cluster_id=4
    )
    # Pre-seed a completed translation for entry 4.
    db_session.add(
        Translation(
            digest_entry_id=already.id,
            target_language="zh",
            translated_title="Already done ZH",
            translated_summary="done ZH",
            provider="mock",
            status="completed",
        )
    )
    db_session.commit()

    service = TranslationService(db_session, provider=MockTranslationProvider())
    translated = service.translate_digest_entries(digest.id)

    # normal + no_summary → 2 new; empty-headline skipped; already completed skipped.
    assert translated == 2
    assert db_session.query(Translation).count() == 3  # 2 new + 1 pre-seeded

    # Spot-check the no-summary row.
    no_summary_row = (
        db_session.query(Translation)
        .filter(Translation.digest_entry_id == no_summary.id)
        .one()
    )
    assert no_summary_row.translated_title == "[zh] No summary"
    assert no_summary_row.translated_summary is None

    # Normal row has both.
    normal_row = (
        db_session.query(Translation)
        .filter(Translation.digest_entry_id == normal.id)
        .one()
    )
    assert normal_row.translated_title == "[zh] Normal"
    assert normal_row.translated_summary == "[zh] s1"


def test_provider_failure_does_not_abort_batch(db_session):
    """A per-entry exception must not prevent other entries from translating."""
    digest = _make_digest(db_session)
    _make_entry(db_session, digest, rank=1, headline="Good headline")
    _make_entry(
        db_session, digest, rank=2, headline="Another one", cluster_id=2
    )

    class _FlakyProvider(TranslationProvider):
        name = "flaky"
        _calls = 0

        def translate(self, text: str, target_lang: str) -> str | None:
            _FlakyProvider._calls += 1
            if _FlakyProvider._calls == 1:
                raise RuntimeError("transient error")
            return f"[{target_lang}] {text}"

    service = TranslationService(db_session, provider=_FlakyProvider())
    # First entry raises → caught and logged; second entry succeeds.
    translated = service.translate_digest_entries(digest.id)
    assert translated == 1


def test_empty_digest_returns_zero(db_session):
    digest = _make_digest(db_session)
    service = TranslationService(db_session, provider=MockTranslationProvider())
    assert service.translate_digest_entries(digest.id) == 0


def test_default_target_language_is_zh(db_session):
    digest = _make_digest(db_session)
    _make_entry(db_session, digest, rank=1, headline="Test")

    service = TranslationService(db_session, provider=MockTranslationProvider())
    service.translate_digest_entries(digest.id)  # default target_language

    row = db_session.query(Translation).one()
    assert row.target_language == "zh"
