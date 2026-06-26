from __future__ import annotations

from datetime import date, datetime, timezone
import pytest

from app.models.article import Article
from app.models.cluster import Cluster
from app.models.cluster_member import ClusterMember
from app.models.digest import Digest
from app.models.digest_entry import DigestEntry
from app.models.source import Source
from app.services.archive_query_service import ArchiveQueryService


@pytest.fixture
def archive_service(db_session):
    """创建 ArchiveQueryService 实例。"""
    return ArchiveQueryService(db_session)


def _create_source(db_session, name="Test Source", kind="rss") -> Source:
    """创建测试用 source。"""
    source = Source(
        name=name,
        kind=kind,
        url=f"https://example.com/{name.lower().replace(' ', '-')}",
        language="en",
        enabled=True,
    )
    db_session.add(source)
    db_session.commit()
    return source


def _create_article(
    db_session,
    source_id: int,
    title="Test Article",
    summary="Test summary",
    body="Test body content",
    published_at=None,
    use_default_published_at=True,
) -> Article:
    """创建测试用 article。"""
    if use_default_published_at and published_at is None:
        published_at = datetime.now(timezone.utc)
    article = Article(
        source_id=source_id,
        url=f"https://example.com/article/{title.lower().replace(' ', '-')}",
        title=title,
        summary=summary,
        body=body,
        published_at=published_at,
        language="en",
    )
    db_session.add(article)
    db_session.commit()
    return article


def _create_cluster_with_members(
    db_session,
    articles: list[Article],
    representative_article_id: int | None = None,
) -> Cluster:
    """创建 cluster 并添加成员。"""
    rep_id = representative_article_id or (articles[0].id if articles else None)
    cluster = Cluster(
        representative_article_id=rep_id,
        size=len(articles),
        score=1.0,
    )
    db_session.add(cluster)
    db_session.commit()

    for rank, article in enumerate(articles):
        member = ClusterMember(
            cluster_id=cluster.id,
            article_id=article.id,
            rank=rank,
        )
        db_session.add(member)

    db_session.commit()
    return cluster


def _create_digest_with_entries(
    db_session,
    digest_date: date,
    cluster_ids: list[int],
    status="published",
) -> Digest:
    """创建 digest 并关联 clusters。"""
    digest = Digest(
        date=digest_date,
        status=status,
        published_at=datetime.now(timezone.utc) if status == "published" else None,
    )
    db_session.add(digest)
    db_session.commit()

    for rank, cluster_id in enumerate(cluster_ids):
        entry = DigestEntry(
            digest_id=digest.id,
            cluster_id=cluster_id,
            rank=rank,
            category="tech",
            headline=f"Headline for cluster {cluster_id}",
            summary=f"Summary for cluster {cluster_id}",
            source_count=2,
        )
        db_session.add(entry)

    db_session.commit()
    return digest


class TestArchiveDates:
    """测试归档日期列表查询。"""

    def test_get_archive_dates_empty(self, archive_service):
        """空数据库返回空列表。"""
        result = archive_service.get_archive_dates()
        assert result == []

    def test_get_archive_dates_with_published_digests(self, archive_service, db_session):
        """返回有 published digest 的日期（降序）。"""
        # 创建多个 digest
        _create_digest_with_entries(db_session, date(2026, 6, 26), [1])
        _create_digest_with_entries(db_session, date(2026, 6, 25), [1])
        _create_digest_with_entries(db_session, date(2026, 6, 20), [1])

        result = archive_service.get_archive_dates()
        assert result == ["2026-06-26", "2026-06-25", "2026-06-20"]

    def test_get_archive_dates_excludes_drafts(self, archive_service, db_session):
        """只返回 published 状态的 digest。"""
        _create_digest_with_entries(db_session, date(2026, 6, 26), [1], status="published")
        _create_digest_with_entries(db_session, date(2026, 6, 25), [1], status="draft")

        result = archive_service.get_archive_dates()
        assert result == ["2026-06-26"]

    def test_get_archive_dates_with_limit(self, archive_service, db_session):
        """限制返回数量。"""
        for i in range(10):
            _create_digest_with_entries(db_session, date(2026, 6, 26 - i), [1])

        result = archive_service.get_archive_dates(limit=5)
        assert len(result) == 5


class TestClusterDetail:
    """测试 cluster 详情查询。"""

    def test_get_cluster_detail_not_found(self, archive_service):
        """不存在的 cluster 返回 None。"""
        result = archive_service.get_cluster_detail(99999)
        assert result is None

    def test_get_cluster_detail_without_digest_entries(self, archive_service, db_session):
        """没有 digest entries 的 cluster 返回基础信息。"""
        source = _create_source(db_session)
        article = _create_article(db_session, source.id)
        cluster = _create_cluster_with_members(db_session, [article])

        result = archive_service.get_cluster_detail(cluster.id)
        assert result is not None
        assert result["id"] == str(cluster.id)
        assert result["category"] == ""
        assert result["headline"] == ""
        assert result["summary"] == ""
        assert result["source_count"] == 0
        assert result["digest_dates"] == []

    def test_get_cluster_detail_with_digest_entries(self, archive_service, db_session):
        """有 digest entries 的 cluster 返回完整信息。"""
        source = _create_source(db_session)
        article = _create_article(db_session, source.id)
        cluster = _create_cluster_with_members(db_session, [article])
        _create_digest_with_entries(
            db_session,
            date(2026, 6, 26),
            [cluster.id],
        )

        result = archive_service.get_cluster_detail(cluster.id)
        assert result is not None
        assert result["id"] == str(cluster.id)
        assert result["category"] == "tech"
        assert result["headline"] == f"Headline for cluster {cluster.id}"
        assert result["summary"] == f"Summary for cluster {cluster.id}"
        assert result["source_count"] == 2
        assert result["digest_dates"] == ["2026-06-26"]

    def test_get_cluster_detail_multiple_digest_dates(self, archive_service, db_session):
        """cluster 出现在多个 digest 中，返回所有日期。"""
        source = _create_source(db_session)
        article = _create_article(db_session, source.id)
        cluster = _create_cluster_with_members(db_session, [article])

        _create_digest_with_entries(db_session, date(2026, 6, 26), [cluster.id])
        _create_digest_with_entries(db_session, date(2026, 6, 25), [cluster.id])

        result = archive_service.get_cluster_detail(cluster.id)
        assert result is not None
        assert len(result["digest_dates"]) == 2
        assert result["digest_dates"] == ["2026-06-26", "2026-06-25"]


class TestArticleDetail:
    """测试 article 详情查询。"""

    def test_get_article_detail_not_found(self, archive_service):
        """不存在的 article 返回 None。"""
        result = archive_service.get_article_detail(99999)
        assert result is None

    def test_get_article_detail_without_cluster(self, archive_service, db_session):
        """未聚类的 article 返回空 cluster_id。"""
        source = _create_source(db_session, name="CNN")
        article = _create_article(
            db_session,
            source.id,
            title="Test Article",
            summary="Test summary",
            body="Full body text",
            published_at=datetime(2026, 6, 26, 10, 0, 0, tzinfo=timezone.utc),
        )

        result = archive_service.get_article_detail(article.id)
        assert result is not None
        assert result["id"] == str(article.id)
        assert result["cluster_id"] == ""
        assert result["title"] == "Test Article"
        assert result["summary"] == "Test summary"
        assert result["body"] == "Full body text"
        assert result["source"] == "CNN"
        assert result["url"] == article.url
        assert result["published_at"] == "2026-06-26T10:00:00+00:00"
        assert result["language"] == "en"

    def test_get_article_detail_with_cluster(self, archive_service, db_session):
        """已聚类的 article 返回 cluster_id。"""
        source = _create_source(db_session)
        article = _create_article(db_session, source.id)
        cluster = _create_cluster_with_members(db_session, [article])

        result = archive_service.get_article_detail(article.id)
        assert result is not None
        assert result["cluster_id"] == str(cluster.id)

    def test_get_article_detail_without_published_at(self, archive_service, db_session):
        """published_at 为空时返回空字符串。"""
        source = _create_source(db_session)
        article = _create_article(db_session, source.id, published_at=None, use_default_published_at=False)

        result = archive_service.get_article_detail(article.id)
        assert result is not None
        assert result["published_at"] == ""
