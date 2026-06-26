"""Batch translation service for digest entries.

Translates the headline and summary of each DigestEntry in a digest using an
abstracted TranslationProvider. Translations are persisted in the Translation
table. Empty results are not stored, already-completed translations are
skipped, and provider failures are isolated per entry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import structlog
from sqlalchemy.orm import Session

from app.repositories.translation_repository import TranslationRepository

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Provider abstraction
# ---------------------------------------------------------------------------


class TranslationProvider(ABC):
    """Abstract translation provider.

    ``translate`` returns the translated string on success and ``None`` on
    failure. Implementations MUST NOT raise exceptions for expected failure
    modes — return ``None`` instead so the caller can apply fallback logic.
    """

    name: str = "abstract"

    @abstractmethod
    def translate(self, text: str, target_lang: str) -> str | None:
        """Translate *text* into *target_lang*, or return ``None`` on failure."""


class MockTranslationProvider(TranslationProvider):
    """Deterministic provider useful in tests and demos.

    By default it returns ``"[<target_lang>] <text>"`` for any input.  A
    pre-defined mapping can be supplied to override specific translations.
    """

    name = "mock"

    def __init__(self, overrides: dict[str, str] | None = None) -> None:
        self.overrides = overrides or {}

    def translate(self, text: str, target_lang: str) -> str | None:
        if text in self.overrides:
            return self.overrides[text]
        return f"[{target_lang}] {text}"


class NullTranslationProvider(TranslationProvider):
    """Fallback provider that never fails.

    It delegates to an underlying provider and returns the original text
    whenever the delegate returns ``None`` (or would raise).  This guarantees
    a non-``None`` result so that downstream code can always fall back to the
    original source text rather than losing content.
    """

    name = "null"

    def __init__(self, delegate: TranslationProvider | None = None) -> None:
        self.delegate = delegate

    def translate(self, text: str, target_lang: str) -> str | None:
        if not text:
            return None
        if self.delegate is not None:
            try:
                result = self.delegate.translate(text, target_lang)
                if result:
                    return result
            except Exception as exc:  # noqa: BLE001 - intentional safety net
                logger.warning(
                    "null_provider_delegate_failed",
                    error=str(exc),
                    text_len=len(text),
                )
        # Ultimate fallback: keep the original text.
        return text


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TranslationService:
    """Orchestrates batch translation of digest entries."""

    def __init__(
        self,
        db: Session,
        provider: TranslationProvider | None = None,
    ) -> None:
        self.db = db
        self.provider: TranslationProvider = provider or NullTranslationProvider()
        self.repo = TranslationRepository(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def translate_digest_entries(
        self, digest_id: int, target_language: str = "zh"
    ) -> int:
        """Translate every entry in a digest.

        Returns the number of newly-created translations.  Entries with a
        ``completed`` translation are skipped.  Empty summaries are not
        translated.  Provider failures do not abort the batch.
        """

        entries = self.repo.get_entries_for_digest(digest_id)
        if not entries:
            return 0

        translated = 0
        for entry in entries:
            try:
                if self._translate_entry(entry, target_language):
                    translated += 1
            except Exception as exc:  # noqa: BLE001 - keep batch alive
                logger.error(
                    "translation_entry_failed",
                    digest_id=digest_id,
                    entry_id=entry.id,
                    error=str(exc),
                )
        return translated

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _translate_entry(self, entry: DigestEntry, target_language: str) -> bool:
        """Translate a single entry.  Returns ``True`` if a row was stored."""

        # Skip if we already have a completed translation.
        existing = self.repo.get_completed_translation(entry.id, target_language)
        if existing is not None:
            return False

        headline = (entry.headline or "").strip()
        summary = (entry.summary or "").strip()

        # Headline is mandatory — if empty there's nothing useful to do.
        if not headline:
            return False

        translated_headline = self.provider.translate(headline, target_language)
        # Empty translated headline → do NOT persist (would clobber the original).
        if not translated_headline:
            return False

        translated_summary: str | None = None
        if summary:
            translated_summary = self.provider.translate(summary, target_language)
            # Empty summary translation is silently dropped; headline is kept.

        # Determine provider name for the stored record.
        provider_name = getattr(self.provider, "name", "unknown")

        self.repo.save_translation(
            digest_entry_id=entry.id,
            target_language=target_language,
            translated_title=translated_headline,
            translated_summary=translated_summary,
            provider=provider_name,
        )
        return True
