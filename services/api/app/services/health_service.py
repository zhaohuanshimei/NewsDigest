"""Health check service for monitoring system status."""

from __future__ import annotations

from typing import Any, Literal

from sqlalchemy.orm import Session

from app.repositories.health_repository import HealthRepository


class HealthService:
    """Service for checking system health status."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = HealthRepository(db)

    def check_health(self) -> dict[str, Any]:
        """Check overall system health.

        Returns:
            Dict with status, database status, and last digest info
        """
        # Check database connectivity
        database_ok = self.repository.check_database_connection()
        database_status: Literal["ok", "error"] = "ok" if database_ok else "error"

        # Get latest digest info
        last_digest = self.repository.get_latest_digest_info()

        # Determine overall status
        if not database_ok:
            overall_status: Literal["ok", "degraded", "error"] = "error"
        else:
            overall_status = "ok"

        return {
            "status": overall_status,
            "database": database_status,
            "last_digest": last_digest,
        }
