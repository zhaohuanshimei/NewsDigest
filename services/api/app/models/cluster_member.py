from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ClusterMember(Base):
    __tablename__ = "cluster_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cluster_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clusters.id"), nullable=False
    )
    article_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("articles.id"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    cluster = relationship("Cluster", back_populates="members")

    __table_args__ = (
        UniqueConstraint(
            "cluster_id", "article_id", name="uq_cluster_member_cluster_article"
        ),
    )

    def __repr__(self) -> str:
        return f"<ClusterMember cluster={self.cluster_id} article={self.article_id}>"
