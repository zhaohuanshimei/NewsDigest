from __future__ import annotations

import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from app.core.fetcher_interface import (
    ExtractedItem,
    FetchError as FetchErrorEnum,
    FetchRequest,
    FetchResult,
)
from app.services.fetchers.content_fetcher import ContentFetcher

SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head><title>Test Article</title></head>
<body>
<article>
<h1>Article Title</h1>
<p>This is a sample article with enough content for readability to extract it as the main body.
Readability works by scoring paragraphs and selecting the most content-rich section of the page.
This paragraph provides enough text for the algorithm to identify this as the main content.</p>
<p>Additional content that makes the article long enough for proper readability extraction.
The algorithm uses text density, comma counts, and other heuristics to find the main content
of a web page. This second paragraph helps ensure readability identifies the article area.</p>
<p>Third paragraph to further increase the text density in this section. Readability-lxml
is a Python port of Mozilla's Readability library which powers the reading mode in Firefox.
It strips navigation, sidebars, and other non-content elements from the page.</p>
</article>
</body>
</html>"""


def _make_urlopen_response(data: bytes, status: int = 200, content_type: str | None = "text/html") -> MagicMock:
    resp = MagicMock()
    resp.read.return_value = data
    resp.status = status
    resp.headers = {"Content-Type": content_type} if content_type else {}
    resp.__enter__.return_value = resp
    return resp


class TestContentFetcherKind:

    def test_kind_returns_content(self) -> None:
        fetcher = ContentFetcher()
        assert fetcher.kind == "content"


class TestContentFetcherFetch:

    def test_fetch_success(self) -> None:
        fetcher = ContentFetcher()
        mock_resp = _make_urlopen_response(SAMPLE_HTML.encode("utf-8"))
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = fetcher.fetch(FetchRequest(url="https://example.com/article"))
        assert result.success is True
        assert result.status_code == 200
        assert SAMPLE_HTML in result.raw_content
        assert result.error_message is None

    def test_fetch_http_404(self) -> None:
        fetcher = ContentFetcher()
        http_error = urllib.error.HTTPError(
            url="https://example.com/404",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        with patch("urllib.request.urlopen", side_effect=http_error):
            result = fetcher.fetch(FetchRequest(url="https://example.com/404"))
        assert result.success is False
        assert result.status_code == 404
        assert "HTTP 404" in (result.error_message or "")
        assert result.error_code == FetchErrorEnum.HTTP_ERROR

    def test_fetch_network_error(self) -> None:
        fetcher = ContentFetcher()
        url_error = urllib.error.URLError(reason="Connection refused")
        with patch("urllib.request.urlopen", side_effect=url_error):
            result = fetcher.fetch(FetchRequest(url="https://example.com/"))
        assert result.success is False
        assert result.status_code == 0
        assert "Connection refused" in (result.error_message or "")
        assert result.error_code == FetchErrorEnum.NETWORK_ERROR

    def test_fetch_timeout(self) -> None:
        fetcher = ContentFetcher()
        url_error = urllib.error.URLError(reason="timed out")
        with patch("urllib.request.urlopen", side_effect=url_error):
            result = fetcher.fetch(FetchRequest(url="https://example.com/"))
        assert result.success is False
        assert result.status_code == 0
        assert result.error_code == FetchErrorEnum.TIMEOUT

    def test_fetch_unknown_exception(self) -> None:
        fetcher = ContentFetcher()
        with patch("urllib.request.urlopen", side_effect=RuntimeError("unexpected")):
            result = fetcher.fetch(FetchRequest(url="https://example.com/"))
        assert result.success is False
        assert result.status_code == 0
        assert result.error_code == FetchErrorEnum.UNKNOWN

    def test_fetch_custom_user_agent(self) -> None:
        fetcher = ContentFetcher()
        mock_resp = _make_urlopen_response(b"content")
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            fetcher.fetch(FetchRequest(url="https://example.com/"))
        request_arg = mock_urlopen.call_args[0][0]
        assert request_arg.has_header("User-agent") is True
        assert request_arg.get_header("User-agent") == "NewsDigest/1.0 Content Fetcher"

    def test_fetch_request_user_agent_overrides_default(self) -> None:
        fetcher = ContentFetcher()
        mock_resp = _make_urlopen_response(b"content")
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            fetcher.fetch(FetchRequest(url="https://example.com/", user_agent="CustomAgent/1.0"))
        request_arg = mock_urlopen.call_args[0][0]
        assert request_arg.get_header("User-agent") == "CustomAgent/1.0"


class TestContentFetcherExtract:

    def test_extract_success(self) -> None:
        fetcher = ContentFetcher()
        result = FetchResult(
            raw_content=SAMPLE_HTML,
            status_code=200,
            success=True,
            content_type="text/html",
        )
        items = fetcher.extract(result)
        assert len(items) == 1
        item = items[0]
        assert item.title == "Test Article"
        assert item.body is not None
        assert "Article Title" in item.body
        assert item.url is None
        assert item.summary is None
        assert item.published_at is None
        assert item.language is None
        assert item.raw is None

    def test_extract_empty_title(self) -> None:
        """Readability may return None for a title-less document."""
        fetcher = ContentFetcher()
        html_no_title = "<html><body><p>No title here but lots of text for readability. " * 20 + "</p></body></html>"
        result = FetchResult(
            raw_content=html_no_title,
            status_code=200,
            success=True,
        )
        items = fetcher.extract(result)
        # Readability should still extract body content even without a title
        assert len(items) == 1
        item = items[0]
        assert item.title is not None  # readability returns '' or a fallback
        assert item.body is not None

    def test_extract_empty_html(self) -> None:
        fetcher = ContentFetcher()
        result = FetchResult(
            raw_content="",
            status_code=200,
            success=True,
        )
        items = fetcher.extract(result)
        assert items == []

    def test_extract_whitespace_only(self) -> None:
        fetcher = ContentFetcher()
        result = FetchResult(
            raw_content="   \n\n  ",
            status_code=200,
            success=True,
        )
        items = fetcher.extract(result)
        assert items == []

    def test_extract_from_failed_fetch(self) -> None:
        fetcher = ContentFetcher()
        result = FetchResult(
            raw_content="",
            status_code=500,
            success=False,
            error_message="Server error",
        )
        items = fetcher.extract(result)
        assert items == []

    def test_extract_from_none_content(self) -> None:
        fetcher = ContentFetcher()
        result = FetchResult(
            raw_content=None,  # type: ignore[arg-type]
            status_code=200,
            success=True,
        )
        items = fetcher.extract(result)
        assert items == []

    def test_extract_non_html_but_parseable(self) -> None:
        """Even without HTML structure, readability should handle gracefully."""
        fetcher = ContentFetcher()
        raw = "Just some plain text without HTML tags. " * 30
        result = FetchResult(
            raw_content=raw,
            status_code=200,
            success=True,
            content_type="text/plain",
        )
        items = fetcher.extract(result)
        # readability still processes this via lxml, may extract something or not
        # The important thing is it doesn't crash
        assert isinstance(items, list)
        assert len(items) <= 1

    def test_extract_readability_raises(self) -> None:
        fetcher = ContentFetcher()
        result = FetchResult(
            raw_content=SAMPLE_HTML,
            status_code=200,
            success=True,
        )
        with patch("app.services.fetchers.content_fetcher.Document", side_effect=ValueError("bad html")):
            items = fetcher.extract(result)
        assert items == []


class TestContentFetcherNormalize:

    def test_normalize_single_item(self) -> None:
        fetcher = ContentFetcher()
        items = [
            ExtractedItem(
                title="Test Title",
                url="https://example.com/article",
                summary="A summary",
                body="<p>Article body</p>",
                language="en",
                published_at=None,
                raw=None,
            )
        ]
        articles = fetcher.normalize(items)
        assert len(articles) == 1
        article = articles[0]
        assert article.title == "Test Title"
        assert article.url == "https://example.com/article"
        assert article.language == "en"
        assert article.summary == "A summary"
        assert article.body == "<p>Article body</p>"
        assert article.dedupe_key is not None
        assert isinstance(article.dedupe_key, str)
        assert len(article.dedupe_key) == 64

    def test_normalize_empty_list(self) -> None:
        fetcher = ContentFetcher()
        articles = fetcher.normalize([])
        assert articles == []

    def test_normalize_item_missing_title(self) -> None:
        fetcher = ContentFetcher()
        items = [
            ExtractedItem(
                title=None,
                url="https://example.com/article",
                body="<p>Body</p>",
            )
        ]
        articles = fetcher.normalize(items)
        assert articles == []

    def test_normalize_item_missing_body(self) -> None:
        fetcher = ContentFetcher()
        items = [
            ExtractedItem(
                title="Title Only",
                url="https://example.com/article",
                body=None,
            )
        ]
        articles = fetcher.normalize(items)
        assert articles == []

    def test_normalize_sets_default_language(self) -> None:
        fetcher = ContentFetcher()
        items = [
            ExtractedItem(
                title="Title",
                url="https://example.com/article",
                body="body",
            )
        ]
        articles = fetcher.normalize(items)
        assert articles[0].language == "en"

    def test_normalize_multiple_items(self) -> None:
        fetcher = ContentFetcher()
        items = [
            ExtractedItem(title="A", url="https://example.com/a", body="body a"),
            ExtractedItem(title="B", url="https://example.com/b", body="body b"),
        ]
        articles = fetcher.normalize(items)
        assert len(articles) == 2
        assert articles[0].title == "A"
        assert articles[1].title == "B"


class TestContentFetcherFullPipeline:

    def test_fetch_extract_normalize_integration(self) -> None:
        """Test the full pipeline with mocked HTTP and real readability."""
        fetcher = ContentFetcher()
        mock_resp = _make_urlopen_response(SAMPLE_HTML.encode("utf-8"))
        with patch("urllib.request.urlopen", return_value=mock_resp):
            fetch_result = fetcher.fetch(FetchRequest(url="https://example.com/article"))
        assert fetch_result.success is True

        items = fetcher.extract(fetch_result)
        assert len(items) == 1
        assert items[0].title == "Test Article"

        articles = fetcher.normalize(items)
        assert len(articles) == 1
        assert articles[0].title == "Test Article"
        assert articles[0].url == ""
        assert articles[0].language == "en"
        assert "Article Title" in (articles[0].body or "")

    def test_fetch_fails_pipeline_returns_empty(self) -> None:
        """When fetch fails, extract should return empty."""
        fetcher = ContentFetcher()
        http_error = urllib.error.HTTPError(
            url="https://example.com/404",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        with patch("urllib.request.urlopen", side_effect=http_error):
            fetch_result = fetcher.fetch(FetchRequest(url="https://example.com/404"))
        assert fetch_result.success is False

        items = fetcher.extract(fetch_result)
        assert items == []
