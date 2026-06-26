from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Digest(Base):
    __tablename__ = "digests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    entries = relationship(
        "DigestEntry", back_populates="digest", order_by="DigestEntry.rank"
    )

    def __repr__(self) -> str:
        return f"<Digest id={self.id} date={self.date}>"
