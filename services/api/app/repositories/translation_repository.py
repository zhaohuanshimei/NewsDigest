"""Repository for Translation persistence and lookup."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.digest_entry import DigestEntry
from app.models.translation import Translation


class TranslationRepository:
    """Data-access layer for Translation records."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_entries_for_digest(self, digest_id: int) -> list[DigestEntry]:
        """Return all DigestEntry rows belonging to a digest, ordered by rank."""
        return (
            self.db.query(DigestEntry)
            .filter(DigestEntry.digest_id == digest_id)
            .order_by(DigestEntry.rank.asc())
            .all()
        )

    def get_completed_translation(
        self, digest_entry_id: int, target_language: str
    ) -> Translation | None:
        """Return the existing completed translation for an entry, if any."""
        return (
            self.db.query(Translation)
            .filter(
                Translation.digest_entry_id == digest_entry_id,
                Translation.target_language == target_language,
                Translation.status == "completed",
            )
            .first()
        )

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def save_translation(
        self,
        *,
        digest_entry_id: int,
        target_language: str,
        translated_title: str | None,
        translated_summary: str | None,
        provider: str,
    ) -> Translation:
        """Insert a new completed Translation row and return it."""
        translation = Translation(
            digest_entry_id=digest_entry_id,
            target_language=target_language,
            translated_title=translated_title,
            translated_summary=translated_summary,
            provider=provider,
            status="completed",
        )
        self.db.add(translation)
        self.db.commit()
        self.db.refresh(translation)
        return translation
