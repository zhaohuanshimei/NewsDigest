from __future__ import annotations

from time import sleep

from sqlalchemy.orm import Session

from app.core.fetcher_interface import BaseFetcher, FetchRequest, FetchResult
from app.models.source import Source
from app.repositories.article_repository import ArticleRepository
from app.repositories.source_repository import SourceRepository
from app.services.topic_classifier import classify_by_text


class ArticleService:

    def __init__(
        self,
        article_repo: ArticleRepository,
        source_repo: SourceRepository,
        fetcher: BaseFetcher,
    ):
        self.article_repo = article_repo
        self.source_repo = source_repo
        self.fetcher = fetcher

    def fetch_and_persist(self, source: Source) -> tuple[int, int]:
        request = FetchRequest(url=source.url, retry_count=2, retry_delay_seconds=1.0)
        result = self._fetch_with_retry(request)
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
            topic = classify_by_text(article.title, article.summary)
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
                topic=topic,
                image_url=article.image_url,
                video_url=article.video_url,
            )
            new_count += 1

        self.source_repo.update_last_fetched_at(source.id)
        return (new_count, dup_count)

    def _fetch_with_retry(self, request: FetchRequest) -> FetchResult:
        for attempt in range(request.retry_count + 1):
            result = self.fetcher.fetch(request)
            if result.success:
                return result
            if attempt < request.retry_count:
                sleep(request.retry_delay_seconds)
        return result

    def fetch_all_active_sources(
        self, db: Session
    ) -> dict[str, tuple[int, int]]:
        sources = self.source_repo.get_active_fetchable_sources()
        results: dict[str, tuple[int, int]] = {}
        for source in sources:
            results[source.name] = self.fetch_and_persist(source)
        return results
