from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.models.cluster import Cluster
from app.models.cluster_member import ClusterMember
from app.models.article import Article
from app.models.digest import Digest
from app.models.digest_entry import DigestEntry


class ArchiveQueryRepository:
    """归档查询仓储。

    提供归档日期列表、cluster 详情、article 详情的数据查询。
    所有查询为只读操作，不涉及写操作。
    """

    def __init__(self, db: Session):
        self.db = db

    def get_archive_dates(self, limit: int = 30) -> list[date]:
        """获取有 digest 的日期列表（降序）。

        只返回 status="published" 的 digest 日期。
        """
        rows = (
            self.db.query(Digest.date)
            .filter(Digest.status == "published")
            .order_by(Digest.date.desc())
            .limit(limit)
            .all()
        )
        return [row[0] for row in rows]

    def get_cluster_with_details(self, cluster_id: int) -> Cluster | None:
        """获取 cluster 及其关联的 digest entries。

        返回 cluster 对象，包含：
        - digest_entries 关系（按 rank 排序）
        """
        cluster = (
            self.db.query(Cluster)
            .options(joinedload(Cluster.digest_entries))
            .filter(Cluster.id == cluster_id)
            .first()
        )
        return cluster

    def get_article_with_details(self, article_id: int) -> Article | None:
        """获取 article 及其关联的 source。

        返回 article 对象，包含：
        - source 关系
        """
        article = (
            self.db.query(Article)
            .options(joinedload(Article.source))
            .filter(Article.id == article_id)
            .first()
        )
        return article

    def get_cluster_id_for_article(self, article_id: int) -> int | None:
        """获取 article 所属的 cluster_id。"""
        member = (
            self.db.query(ClusterMember.cluster_id)
            .filter(ClusterMember.article_id == article_id)
            .first()
        )
        return member[0] if member else None

    def get_digest_dates_for_cluster(self, cluster_id: int) -> list[date]:
        """获取某个 cluster 出现过的所有 digest 日期（降序）。"""
        rows = (
            self.db.query(Digest.date)
            .join(DigestEntry, DigestEntry.digest_id == Digest.id)
            .filter(DigestEntry.cluster_id == cluster_id)
            .order_by(Digest.date.desc())
            .all()
        )
        return [row[0] for row in rows]
