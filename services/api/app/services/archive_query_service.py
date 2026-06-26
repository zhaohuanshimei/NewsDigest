from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.repositories.archive_query_repository import ArchiveQueryRepository


class ArchiveQueryService:
    """归档与详情查询服务。

    提供：
    - 归档日期列表（ArchiveDateListResource）
    - cluster 详情（ClusterDetailResource）
    - article 详情（ArticleDetailResource）

    所有返回结构严格对齐 shared-types 契约。
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = ArchiveQueryRepository(db)

    def get_archive_dates(self, limit: int = 30) -> list[str]:
        """获取归档日期列表。

        返回 ISO 格式的日期字符串列表，按时间倒序排列。
        """
        dates = self.repo.get_archive_dates(limit=limit)
        return [d.isoformat() for d in dates]

    def get_cluster_detail(self, cluster_id: int) -> dict[str, Any] | None:
        """获取 cluster 详情。

        返回符合 shared-types ClusterDetailResource 的结构：
        {
            "id": "1",
            "category": "tech",
            "headline": "AI breakthrough",
            "summary": "Summary text",
            "source_count": 3,
            "digest_dates": ["2026-06-26", "2026-06-25"]
        }

        若 cluster 不存在，返回 None。
        """
        cluster = self.repo.get_cluster_with_details(cluster_id)
        if cluster is None:
            return None

        # 从 digest_entries 提取信息（取 rank 最高的 entry 作为代表）
        if not cluster.digest_entries:
            # 没有 digest entry，返回基础信息
            return {
                "id": str(cluster.id),
                "category": "",
                "headline": "",
                "summary": "",
                "source_count": 0,
                "digest_dates": []
            }

        # 取 rank 最高的 entry 作为代表
        primary_entry = min(cluster.digest_entries, key=lambda e: e.rank)

        # 获取该 cluster 出现过的所有 digest 日期
        digest_dates = self.repo.get_digest_dates_for_cluster(cluster_id)

        return {
            "id": str(cluster.id),
            "category": primary_entry.category or "",
            "headline": primary_entry.headline or "",
            "summary": primary_entry.summary or "",
            "source_count": primary_entry.source_count,
            "digest_dates": [d.isoformat() for d in digest_dates]
        }

    def get_article_detail(self, article_id: int) -> dict[str, Any] | None:
        """获取 article 详情。

        返回符合 shared-types ArticleDetailResource 的结构：
        {
            "id": "1",
            "cluster_id": "5",
            "title": "Article title",
            "summary": "Article summary",
            "body": "Full article body",
            "source": "Source name",
            "url": "https://example.com/article",
            "published_at": "2026-06-26T10:00:00Z",
            "language": "en"
        }

        若 article 不存在，返回 None。
        """
        article = self.repo.get_article_with_details(article_id)
        if article is None:
            return None

        # 获取 cluster_id
        cluster_id = self.repo.get_cluster_id_for_article(article_id)

        # 获取 source 名称
        source_name = article.source.name if article.source else ""

        # 格式化 published_at
        published_at_str = ""
        if article.published_at:
            # 确保包含时区信息
            if article.published_at.tzinfo is None:
                from datetime import timezone
                article.published_at = article.published_at.replace(tzinfo=timezone.utc)
            published_at_str = article.published_at.isoformat()

        return {
            "id": str(article.id),
            "cluster_id": str(cluster_id) if cluster_id is not None else "",
            "title": article.title or "",
            "summary": article.summary or "",
            "body": article.body or "",
            "source": source_name,
            "url": article.url or "",
            "published_at": published_at_str,
            "language": article.language or ""
        }
