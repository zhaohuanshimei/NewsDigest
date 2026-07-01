from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.cluster import Cluster
from app.models.cluster_member import ClusterMember


class ClusterRepository:
    """Cluster / ClusterMember 的持久化仓储。

    注意：写方法（create_cluster / add_member）只 add + flush，不 commit。
    事务边界由上层 service（ClusterService）统一控制，保证一次聚类操作原子提交。
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, cluster_id: int) -> Cluster | None:
        return self.db.get(Cluster, cluster_id)

    def get_clustered_article_ids(self) -> set[int]:
        """返回已经归属于任意 cluster 的 article_id 集合，用于跳过已聚类文章。"""
        rows = self.db.query(ClusterMember.article_id).distinct().all()
        return {row[0] for row in rows}

    def create_cluster(
        self,
        *,
        representative_article_id: int | None,
        size: int,
        score: float,
        topic: str | None = None,
    ) -> Cluster:
        cluster = Cluster(
            representative_article_id=representative_article_id,
            size=size,
            score=score,
            topic=topic,
        )
        self.db.add(cluster)
        self.db.flush()  # 让 cluster.id 可用，但不提交
        return cluster

    def add_member(self, cluster_id: int, article_id: int, rank: int) -> ClusterMember:
        member = ClusterMember(cluster_id=cluster_id, article_id=article_id, rank=rank)
        self.db.add(member)
        return member

    def list_recent(self, limit: int = 50) -> list[Cluster]:
        return (
            self.db.query(Cluster)
            .order_by(Cluster.last_updated_at.desc())
            .limit(limit)
            .all()
        )
