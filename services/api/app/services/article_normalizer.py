from __future__ import annotations

import re
from html import unescape
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.orm import Session

from app.core.fetcher_interface import NormalizedArticle, make_dedupe_key
from app.models.article import Article
from app.repositories.article_repository import ArticleRepository
from app.services.dedup_service import DedupService

TRACKING_PARAMS: frozenset[str] = frozenset({
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
})

TITLE_MAX_LENGTH = 500
SUMMARY_MAX_LENGTH = 2000


class ArticleNormalizer:
    """Normalizes articles: cleans URLs, sanitizes text, and prevents duplicates."""

    def __init__(self, db: Session, repository: ArticleRepository | None = None,
                 dedup_service: DedupService | None = None) -> None:
        self.db = db
        self.repository = repository or ArticleRepository(db)
        self.dedup_service = dedup_service or DedupService(repository=self.repository)

    def normalize_article(self, article: NormalizedArticle) -> Article | None:
        """Normalize and persist an article, or return None if it is a duplicate."""
        normalized_url = self._normalize_url(article.url)

        cleaned_title = self._clean_text(article.title, TITLE_MAX_LENGTH)
        cleaned_summary = (
            self._clean_text(article.summary, SUMMARY_MAX_LENGTH)
            if article.summary
            else None
        )
        cleaned_body = (
            self._clean_text(article.body, None) if article.body else None
        )

        # Dedup check 1 — normalized URL
        existing = self.repository.get_by_url(normalized_url)
        if existing is not None:
            return None

        # Dedup check 2 — dedupe_key
        dedupe_key = article.dedupe_key or make_dedupe_key(
            article.title, article.url
        )
        existing = self.repository.get_by_dedupe_key(dedupe_key)
        if existing is not None:
            return None

        return self.repository.create(
            source_id=article.source_id,
            url=normalized_url,
            title=cleaned_title,
            summary=cleaned_summary,
            body=cleaned_body,
            published_at=article.published_at,
            language=article.language,
            normalized_url=normalized_url,
            dedupe_key=dedupe_key,
        )

    def _normalize_url(self, url: str) -> str:
        if not url:
            return url

        if "://" not in url:
            url = f"https://{url}"

        parsed = urlparse(url)

        scheme = "https" if parsed.scheme in ("http", "https") else parsed.scheme

        path = parsed.path.rstrip("/") or "/"
        if path != "/" and not path.startswith("/"):
            path = f"/{path}"

        qs = parse_qs(parsed.query, keep_blank_values=True)
        filtered = {
            k: v
            for k, v in qs.items()
            if k.lower() not in TRACKING_PARAMS
        }
        query = urlencode(filtered, doseq=True) if filtered else ""

        return urlunparse((scheme, parsed.netloc, path, parsed.params, query, parsed.fragment))

    def _clean_text(self, text: str, max_length: int | None) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        text = unescape(text)
        if max_length is not None and len(text) > max_length:
            text = text[:max_length]
        return text
