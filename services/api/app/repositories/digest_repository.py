from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.digest import Digest
from app.models.digest_entry import DigestEntry


class DigestRepository:
    """Repository for Digest and DigestEntry persistence."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_date(self, target_date: date) -> Digest | None:
        return (
            self.db.query(Digest)
            .filter(Digest.date == target_date)
            .first()
        )

    def delete_by_date(self, target_date: date) -> None:
        """Delete digest and its entries for the given date (idempotent)."""
        digest = self.get_by_date(target_date)
        if digest is not None:
            self.db.query(DigestEntry).filter(
                DigestEntry.digest_id == digest.id
            ).delete()
            self.db.delete(digest)
            self.db.commit()

    def create_digest(self, target_date: date, status: str = "draft") -> Digest:
        digest = Digest(date=target_date, status=status)
        self.db.add(digest)
        self.db.commit()
        self.db.refresh(digest)
        return digest

    def create_entry(
        self,
        digest_id: int,
        cluster_id: int,
        rank: int,
        category: str | None,
        headline: str,
        summary: str | None,
        source_count: int,
    ) -> DigestEntry:
        entry = DigestEntry(
            digest_id=digest_id,
            cluster_id=cluster_id,
            rank=rank,
            category=category,
            headline=headline,
            summary=summary,
            source_count=source_count,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
