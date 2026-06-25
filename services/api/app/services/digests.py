from app.schemas.archive import ArchiveDateListResource
from app.schemas.article import ArticleDetailResource
from app.schemas.cluster import ClusterDetailResource
from app.schemas.digest import DigestResource


_DIGESTS_BY_DATE = {
    "2026-06-24": {
        "date": "2026-06-24",
        "published_at": "2026-06-24T09:00:00Z",
        "entries": [
            {
                "cluster_id": "cluster-ai-chip-001",
                "rank": 1,
                "category": "technology",
                "headline": "AI 芯片与模型基础设施继续升温",
                "summary": "多家厂商围绕训练基础设施与推理部署发布新进展。",
                "source_count": 3,
            }
        ],
    },
    "2026-06-23": {
        "date": "2026-06-23",
        "published_at": "2026-06-23T09:00:00Z",
        "entries": [
            {
                "cluster_id": "cluster-energy-002",
                "rank": 1,
                "category": "business",
                "headline": "能源与算力基础设施投资继续扩大",
                "summary": "多地基础设施投资项目推进，带动上游设备与电力话题升温。",
                "source_count": 4,
            }
        ],
    },
}

_ARTICLES_BY_ID = {
    "article-nvidia-001": {
        "id": "article-nvidia-001",
        "cluster_id": "cluster-ai-chip-001",
        "title": "Nvidia partners outline new AI infrastructure roadmap",
        "summary": "厂商围绕 AI 训练与推理基础设施披露新的产品与合作计划。",
        "body": "This is a static article body used to validate the V2 article detail contract.",
        "source": "Example Tech Daily",
        "url": "https://example.com/articles/nvidia-ai-infrastructure-roadmap",
        "published_at": "2026-06-24T08:30:00Z",
        "language": "en",
    }
}


def get_digest_by_date(date: str) -> DigestResource | None:
    payload = _DIGESTS_BY_DATE.get(date)
    if payload is None:
        return None

    return DigestResource(**payload)


def list_archive_dates() -> ArchiveDateListResource:
    return ArchiveDateListResource(dates=sorted(_DIGESTS_BY_DATE, reverse=True))


def get_cluster_detail(cluster_id: str) -> ClusterDetailResource | None:
    matched_entry = None
    digest_dates: list[str] = []

    for digest_date in sorted(_DIGESTS_BY_DATE, reverse=True):
        payload = _DIGESTS_BY_DATE[digest_date]
        for entry in payload["entries"]:
            if entry["cluster_id"] != cluster_id:
                continue

            digest_dates.append(digest_date)
            if matched_entry is None:
                matched_entry = entry

    if matched_entry is None:
        return None

    return ClusterDetailResource(
        id=matched_entry["cluster_id"],
        category=matched_entry["category"],
        headline=matched_entry["headline"],
        summary=matched_entry["summary"],
        source_count=matched_entry["source_count"],
        digest_dates=digest_dates,
    )


def get_article_detail(article_id: str) -> ArticleDetailResource | None:
    payload = _ARTICLES_BY_ID.get(article_id)
    if payload is None:
        return None

    return ArticleDetailResource(**payload)


def get_latest_digest() -> DigestResource:
    latest_date = max(_DIGESTS_BY_DATE)
    return DigestResource(**_DIGESTS_BY_DATE[latest_date])
