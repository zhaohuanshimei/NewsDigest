"""Health check repository for database connectivity and digest status."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.digest import Digest


class HealthRepository:
    """Repository for health check operations."""

    def __init__(self, db: Session):
        self.db = db

    def check_database_connection(self) -> bool:
        """Check if database connection is healthy.

        Returns:
            True if connection is ok, False otherwise
        """
        try:
            self.db.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def get_latest_digest_info(self) -> dict[str, Any] | None:
        """Get information about the most recent digest.

        Returns:
            Dict with digest info (date, status, published_at) or None if no digest exists
        """
        latest_digest = (
            self.db.query(Digest)
            .order_by(Digest.date.desc())
            .first()
        )

        if latest_digest is None:
            return None

        return {
            "date": latest_digest.date.isoformat(),
            "status": latest_digest.status,
            "published_at": (
                latest_digest.published_at.isoformat()
                if latest_digest.published_at
                else None
            ),
        }
