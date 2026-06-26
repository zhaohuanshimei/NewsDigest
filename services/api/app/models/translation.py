from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base import Base


class Translation(Base):
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("articles.id"), nullable=True
    )
    digest_entry_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("digest_entries.id"), nullable=True
    )
    target_language: Mapped[str] = mapped_column(String(8), nullable=False)
    translated_title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    translated_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    review_state: Mapped[str] = mapped_column(String(16), default="unreviewed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    article = relationship("Article", back_populates="translations")
    digest_entry = relationship("DigestEntry", back_populates="translations")

    def __repr__(self) -> str:
        return f"<Translation id={self.id} lang={self.target_language}>"
