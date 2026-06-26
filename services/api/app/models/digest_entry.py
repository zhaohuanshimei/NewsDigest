from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base import Base


class DigestEntry(Base):
    __tablename__ = "digest_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    digest_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("digests.id"), nullable=False
    )
    cluster_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clusters.id"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    digest = relationship("Digest", back_populates="entries")
    cluster = relationship("Cluster", back_populates="digest_entries")
    translations = relationship("Translation", back_populates="digest_entry")

    def __repr__(self) -> str:
        return f"<DigestEntry id={self.id} rank={self.rank}>"
