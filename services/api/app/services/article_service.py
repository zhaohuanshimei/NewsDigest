from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.fetcher_interface import BaseFetcher, FetchRequest
from app.models.source import Source
from app.repositories.article_repository import ArticleRepository
from app.repositories.source_repository import SourceRepository
from app.services.fetchers.rss_fetcher import RssFetcher


class ArticleService:

    def __init__(
        self,
        article_repo: ArticleRepository,
        source_repo: SourceRepository,
        fetcher: BaseFetcher | None = None,
    ):
        self.article_repo = article_repo
        self.source_repo = source_repo
        self.fetcher = fetcher or RssFetcher()

    def fetch_and_persist(self, source: Source) -> tuple[int, int]:
        request = FetchRequest(url=source.url)
        result = self.fetcher.fetch(request)
        if not result.success:
            return (0, 0)

        extracted = self.fetcher.extract(result)
        normalized = self.fetcher.normalize(extracted)

        new_count = 0
        dup_count = 0
        for article in normalized:
            existing = self.article_repo.get_by_url(article.url)
            if existing is not None:
                dup_count += 1
                continue
            if article.dedupe_key:
                existing = self.article_repo.get_by_dedupe_key(article.dedupe_key)
                if existing is not None:
                    dup_count += 1
                    continue
            self.article_repo.create(
                source_id=source.id,
                url=article.url,
                title=article.title,
                summary=article.summary,
                body=article.body,
                published_at=article.published_at,
                language=article.language,
                normalized_url=article.normalized_url,
                dedupe_key=article.dedupe_key,
            )
            new_count += 1

        source.last_fetched_at = datetime.utcnow()
        self.source_repo.db.commit()
        return (new_count, dup_count)

    def fetch_all_active_sources(
        self, db: Session
    ) -> dict[str, tuple[int, int]]:
        sources = self.source_repo.get_active_fetchable_sources()
        results: dict[str, tuple[int, int]] = {}
        for source in sources:
            results[source.name] = self.fetch_and_persist(source)
        return results
