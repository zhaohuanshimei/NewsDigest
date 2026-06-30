from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    representative_article_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("articles.id"), nullable=True
    )
    size: Mapped[int] = mapped_column(Integer, default=1)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    importance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    members = relationship("ClusterMember", back_populates="cluster")
    digest_entries = relationship("DigestEntry", back_populates="cluster")

    def __repr__(self) -> str:
        return f"<Cluster id={self.id} size={self.size}>"
