"""Service for digest query operations."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.repositories.digest_query_repository import DigestQueryRepository
from app.schemas.digest import DigestResource, DigestEntryResource


class DigestQueryService:
    """Service for querying digests, aligned with shared-types DigestResource."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = DigestQueryRepository(db)

    def get_latest(self) -> DigestResource | None:
        """Get the latest digest as DigestResource."""
        digest = self.repo.get_latest_digest()
        if digest is None:
            return None

        return self._to_resource(digest)

    def get_by_date(self, target_date: date) -> DigestResource | None:
        """Get digest for a specific date as DigestResource."""
        digest = self.repo.get_digest_by_date(target_date)
        if digest is None:
            return None

        return self._to_resource(digest)

    def get_available_dates(self, limit: int = 30) -> list[date]:
        """Get list of dates with digests, in descending order."""
        return self.repo.get_available_dates(limit)

    def _to_resource(self, digest) -> DigestResource:
        """Convert Digest model to DigestResource schema."""
        entries = []
        if digest.entries:
            for entry in digest.entries:
                entries.append(
                    DigestEntryResource(
                        cluster_id=str(entry.cluster_id),
                        rank=entry.rank,
                        category=entry.category or "",
                        headline=entry.headline,
                        summary=entry.summary or "",
                        source_count=entry.source_count,
                    )
                )

        # Format published_at as ISO string
        published_at = ""
        if digest.published_at:
            published_at = digest.published_at.isoformat()
        elif digest.created_at:
            published_at = digest.created_at.isoformat()

        return DigestResource(
            date=digest.date.isoformat(),
            published_at=published_at,
            entries=entries,
        )
