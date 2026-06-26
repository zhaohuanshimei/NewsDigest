"""Repository for digest query operations."""
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.digest import Digest


class DigestQueryRepository:
    """Repository for reading digest data from the database."""

    def __init__(self, db: Session):
        self.db = db

    def get_latest_digest(self) -> Optional[Digest]:
        """
        Get the latest digest.
        Prefers published status, falls back to latest by date.
        """
        # Try to find the latest published digest
        published = self.db.query(Digest).filter(
            Digest.status == "published"
        ).order_by(Digest.date.desc()).first()

        if published:
            return published

        # Fall back to latest by date regardless of status
        return self.db.query(Digest).order_by(Digest.date.desc()).first()

    def get_digest_by_date(self, target_date: date) -> Optional[Digest]:
        """Get digest for a specific date."""
        return self.db.query(Digest).filter(
            Digest.date == target_date
        ).first()

    def get_available_dates(self, limit: int = 30) -> list[date]:
        """Get list of dates with digests, in descending order."""
        results = self.db.query(Digest.date).order_by(
            Digest.date.desc()
        ).limit(limit).all()

        return [row[0] for row in results]
