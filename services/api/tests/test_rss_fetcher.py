from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.core.fetcher_interface import (
    BaseFetcher,
    ExtractedItem,
    FetchRequest,
    FetchResult,
    NormalizedArticle,
    make_dedupe_key,
)
from app.models.source import Source
from app.repositories.article_repository import ArticleRepository
from app.repositories.source_repository import SourceRepository
from app.services.article_service import ArticleService
from app.services.fetchers.rss_fetcher import RssFetcher

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test News</title>
    <language>en</language>
    <item>
      <title>First Article</title>
      <link>https://example.com/1</link>
      <description>First article summary</description>
      <pubDate>Mon, 24 Jun 2026 08:30:00 GMT</pubDate>
    </item>
    <item>
      <title>Second Article</title>
      <link>https://example.com/2</link>
      <description>Second article summary</description>
      <pubDate>Tue, 25 Jun 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Third Article</title>
      <link>https://example.com/3</link>
      <description>Third article summary</description>
    </item>
  </channel>
</rss>"""


class TestRssFetcherIsSubclass:

    def test_implements_base_fetcher(self):
        assert issubclass(RssFetcher, BaseFetcher)

    def test_can_instantiate(self):
        fetcher = RssFetcher()
        assert isinstance(fetcher, RssFetcher)

    def test_default_user_agent(self):
        fetcher = RssFetcher()
        assert "NewsDigest" in fetcher.user_agent


class TestRssFetcherFetch:

    def test_success(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"<rss><channel><item><title>A</title></item></channel></rss>"
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/rss+xml"}
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response):
            fetcher = RssFetcher()
            result = fetcher.fetch(FetchRequest(url="https://example.com/feed"))

        assert result.success is True
        assert result.status_code == 200
        assert "<title>A</title>" in result.raw_content

    def test_http_error(self):
        from urllib.error import HTTPError

        mock_error = HTTPError(
            "https://example.com/feed", 404, "Not Found", {}, None
        )
        with patch("urllib.request.urlopen", side_effect=mock_error):
            fetcher = RssFetcher()
            result = fetcher.fetch(FetchRequest(url="https://example.com/feed"))

        assert result.success is False
        assert "404" in (result.error_message or "")

    def test_url_error(self):
        from urllib.error import URLError

        with patch("urllib.request.urlopen", side_effect=URLError("Connection refused")):
            fetcher = RssFetcher()
            result = fetcher.fetch(FetchRequest(url="https://example.com/feed"))

        assert result.success is False
        assert "Connection refused" in (result.error_message or "")

    def test_timeout_error(self):
        from urllib.error import URLError

        with patch("urllib.request.urlopen", side_effect=URLError("timed out")):
            fetcher = RssFetcher()
            result = fetcher.fetch(FetchRequest(url="https://example.com/feed"))

        assert result.success is False

    def test_generic_exception(self):
        with patch("urllib.request.urlopen", side_effect=RuntimeError("boom")):
            fetcher = RssFetcher()
            result = fetcher.fetch(FetchRequest(url="https://example.com/feed"))

        assert result.success is False
        assert "boom" in (result.error_message or "")


class TestRssFetcherExtract:

    def test_extract_returns_entries(self):
        result = FetchResult(
            raw_content=SAMPLE_RSS, status_code=200, success=True
        )
        fetcher = RssFetcher()
        items = fetcher.extract(result)
        assert len(items) == 3

    def test_extract_item_fields(self):
        result = FetchResult(
            raw_content=SAMPLE_RSS, status_code=200, success=True
        )
        fetcher = RssFetcher()
        items = fetcher.extract(result)
        first = items[0]
        assert first.title == "First Article"
        assert first.url == "https://example.com/1"
        assert first.summary == "First article summary"
        assert first.language == "en"

    def test_extract_parses_pub_date(self):
        result = FetchResult(
            raw_content=SAMPLE_RSS, status_code=200, success=True
        )
        fetcher = RssFetcher()
        items = fetcher.extract(result)
        assert items[0].published_at is not None
        assert items[1].published_at is not None
        assert items[0].published_at.year == 2026

    def test_extract_handles_missing_pub_date(self):
        result = FetchResult(
            raw_content=SAMPLE_RSS, status_code=200, success=True
        )
        fetcher = RssFetcher()
        items = fetcher.extract(result)
        assert items[2].published_at is None

    def test_extract_returns_empty_on_failed_result(self):
        result = FetchResult(
            raw_content="", status_code=500, success=False
        )
        fetcher = RssFetcher()
        items = fetcher.extract(result)
        assert items == []

    def test_extract_returns_empty_on_empty_content(self):
        result = FetchResult(
            raw_content="", status_code=200, success=True
        )
        fetcher = RssFetcher()
        items = fetcher.extract(result)
        assert items == []

    def test_extract_handles_malformed_xml(self):
        result = FetchResult(
            raw_content="<<<not-xml>>>", status_code=200, success=True
        )
        fetcher = RssFetcher()
        items = fetcher.extract(result)
        assert items == []


class TestRssFetcherNormalize:

    def test_normalize_returns_articles(self):
        fetcher = RssFetcher()
        items = [
            ExtractedItem(title="A", url="https://example.com/a", summary="Sum"),
            ExtractedItem(title="B", url="https://example.com/b"),
        ]
        articles = fetcher.normalize(items)
        assert len(articles) == 2

    def test_normalize_sets_dedupe_key(self):
        fetcher = RssFetcher()
        items = [
            ExtractedItem(title="Test", url="https://example.com/test"),
        ]
        articles = fetcher.normalize(items)
        expected_key = make_dedupe_key("Test", "https://example.com/test")
        assert articles[0].dedupe_key == expected_key

    def test_normalize_skips_item_without_title(self):
        fetcher = RssFetcher()
        items = [
            ExtractedItem(title=None, url="https://example.com/a"),
            ExtractedItem(title="B", url="https://example.com/b"),
        ]
        articles = fetcher.normalize(items)
        assert len(articles) == 1
        assert articles[0].title == "B"

    def test_normalize_skips_item_without_url(self):
        fetcher = RssFetcher()
        items = [
            ExtractedItem(title="A", url=None),
            ExtractedItem(title="B", url="https://example.com/b"),
        ]
        articles = fetcher.normalize(items)
        assert len(articles) == 1
        assert articles[0].url == "https://example.com/b"

    def test_normalize_defaults_language(self):
        fetcher = RssFetcher()
        items = [
            ExtractedItem(title="A", url="https://example.com/a", language=None),
        ]
        articles = fetcher.normalize(items)
        assert articles[0].language == "en"

    def test_full_pipeline(self):
        result = FetchResult(
            raw_content=SAMPLE_RSS, status_code=200, success=True
        )
        fetcher = RssFetcher()
        extracted = fetcher.extract(result)
        articles = fetcher.normalize(extracted)
        assert len(articles) == 3
        assert all(isinstance(a, NormalizedArticle) for a in articles)
        assert all(a.dedupe_key for a in articles)


class TestArticleRepository:

    def test_create_and_get_by_id(self, db_session):
        repo = ArticleRepository(db_session)
        article = repo.create(
            source_id=0,
            url="https://example.com/a1",
            title="Test Article",
            language="en",
        )
        assert article.id is not None
        assert article.title == "Test Article"
        found = repo.get_by_id(article.id)
        assert found is not None
        assert found.url == "https://example.com/a1"

    def test_get_by_url(self, db_session):
        repo = ArticleRepository(db_session)
        repo.create(
            source_id=0, url="https://example.com/unique", title="Unique", language="en"
        )
        found = repo.get_by_url("https://example.com/unique")
        assert found is not None
        assert found.title == "Unique"

    def test_get_by_url_not_found(self, db_session):
        repo = ArticleRepository(db_session)
        assert repo.get_by_url("https://example.com/nope") is None

    def test_get_by_dedupe_key(self, db_session):
        repo = ArticleRepository(db_session)
        key = make_dedupe_key("Deduped", "https://example.com/deduped")
        repo.create(
            source_id=0,
            url="https://example.com/deduped",
            title="Deduped",
            language="en",
            dedupe_key=key,
        )
        found = repo.get_by_dedupe_key(key)
        assert found is not None
        assert found.title == "Deduped"

    def test_get_by_dedupe_key_not_found(self, db_session):
        repo = ArticleRepository(db_session)
        assert repo.get_by_dedupe_key("nonexistent") is None

    def test_list_recent(self, db_session):
        repo = ArticleRepository(db_session)
        for i in range(5):
            repo.create(
                source_id=0,
                url=f"https://example.com/a{i}",
                title=f"Article {i}",
                language="en",
            )
        recent = repo.list_recent(limit=3)
        assert len(recent) == 3


class TestArticleService:

    def test_fetch_and_persist_returns_counts(self, db_session):
        src_repo = SourceRepository(db_session)
        art_repo = ArticleRepository(db_session)
        source = src_repo.create(
            name="Test RSS",
            kind="rss",
            url="https://example.com/feed",
            enabled=True,
        )

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = FetchResult(
            raw_content=SAMPLE_RSS, status_code=200, success=True
        )
        mock_fetcher.extract.return_value = [
            ExtractedItem(title="A", url="https://example.com/a"),
            ExtractedItem(title="B", url="https://example.com/b"),
        ]
        mock_fetcher.normalize.return_value = [
            NormalizedArticle(
                title="A",
                url="https://example.com/a",
                language="en",
                dedupe_key=make_dedupe_key("A", "https://example.com/a"),
            ),
            NormalizedArticle(
                title="B",
                url="https://example.com/b",
                language="en",
                dedupe_key=make_dedupe_key("B", "https://example.com/b"),
            ),
        ]

        svc = ArticleService(art_repo, src_repo, fetcher=mock_fetcher)
        new_count, dup_count = svc.fetch_and_persist(source)

        assert new_count == 2
        assert dup_count == 0
        assert art_repo.list_recent(10) is not None

    def test_fetch_and_persist_skips_duplicates_by_url(self, db_session):
        src_repo = SourceRepository(db_session)
        art_repo = ArticleRepository(db_session)
        source = src_repo.create(
            name="Dup Test",
            kind="rss",
            url="https://example.com/feed",
            enabled=True,
        )
        art_repo.create(
            source_id=source.id,
            url="https://example.com/a",
            title="A",
            language="en",
        )

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = FetchResult(
            raw_content=SAMPLE_RSS, status_code=200, success=True
        )
        mock_fetcher.extract.return_value = [
            ExtractedItem(title="A", url="https://example.com/a"),
        ]
        mock_fetcher.normalize.return_value = [
            NormalizedArticle(
                title="A",
                url="https://example.com/a",
                language="en",
                dedupe_key=make_dedupe_key("A", "https://example.com/a"),
            ),
        ]

        svc = ArticleService(art_repo, src_repo, fetcher=mock_fetcher)
        new_count, dup_count = svc.fetch_and_persist(source)

        assert new_count == 0
        assert dup_count == 1

    def test_fetch_and_persist_handles_fetch_failure(self, db_session):
        src_repo = SourceRepository(db_session)
        art_repo = ArticleRepository(db_session)
        source = src_repo.create(
            name="Fail Test",
            kind="rss",
            url="https://example.com/feed",
            enabled=True,
        )

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = FetchResult(
            raw_content="",
            status_code=500,
            success=False,
            error_message="Server error",
        )

        svc = ArticleService(art_repo, src_repo, fetcher=mock_fetcher)
        new_count, dup_count = svc.fetch_and_persist(source)

        assert new_count == 0
        assert dup_count == 0

    def test_fetch_and_persist_updates_last_fetched_at(self, db_session):
        src_repo = SourceRepository(db_session)
        art_repo = ArticleRepository(db_session)
        source = src_repo.create(
            name="Timestamp Test",
            kind="rss",
            url="https://example.com/feed",
            enabled=True,
        )
        assert source.last_fetched_at is None

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = FetchResult(
            raw_content=SAMPLE_RSS, status_code=200, success=True
        )
        mock_fetcher.extract.return_value = []
        mock_fetcher.normalize.return_value = []

        svc = ArticleService(art_repo, src_repo, fetcher=mock_fetcher)
        svc.fetch_and_persist(source)

        assert source.last_fetched_at is not None

    def test_fetch_all_active_sources(self, db_session):
        src_repo = SourceRepository(db_session)
        art_repo = ArticleRepository(db_session)
        src_repo.create(
            name="Active1", kind="rss", url="https://example.com/feed1", enabled=True
        )
        src_repo.create(
            name="Active2", kind="rss", url="https://example.com/feed2", enabled=True
        )

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = FetchResult(
            raw_content=SAMPLE_RSS, status_code=200, success=True
        )
        mock_fetcher.extract.return_value = []
        mock_fetcher.normalize.return_value = []

        svc = ArticleService(art_repo, src_repo, fetcher=mock_fetcher)
        results = svc.fetch_all_active_sources(db_session)

        assert isinstance(results, dict)
        assert "Active1" in results
        assert "Active2" in results
