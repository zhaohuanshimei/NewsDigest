from __future__ import annotations

from unittest.mock import MagicMock, create_autospec

import pytest

from app.core.fetcher_interface import NormalizedArticle, make_dedupe_key
from app.models.article import Article
from app.repositories.article_repository import ArticleRepository
from app.services.article_normalizer import ArticleNormalizer


def _make_article(
    title: str = "Test Title",
    url: str = "https://example.com/article",
    summary: str | None = "A short summary",
    body: str | None = "Article body",
    language: str = "en",
    source_id: int = 1,
    **kwargs,
) -> Article:
    a = Article(
        source_id=source_id,
        url=url,
        title=title,
        summary=summary,
        body=body,
        language=language,
        **kwargs,
    )
    a.id = 42
    return a


@pytest.fixture
def mock_repo() -> MagicMock:
    return create_autospec(ArticleRepository, instance=True)


@pytest.fixture
def normalizer(mock_repo: MagicMock) -> ArticleNormalizer:
    db = MagicMock()
    return ArticleNormalizer(db=db, repository=mock_repo)


class TestUrlNormalization:
    def test_strip_trailing_slash(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._normalize_url("https://example.com/article/")
        assert result == "https://example.com/article"

    def test_strip_trailing_slash_root(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._normalize_url("https://example.com/")
        assert result == "https://example.com/"

    def test_nop_without_trailing_slash(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._normalize_url("https://example.com/article")
        assert result == "https://example.com/article"

    def test_remove_utm_params(self, normalizer: ArticleNormalizer) -> None:
        url = "https://example.com/page?utm_source=twitter&utm_medium=social&a=1"
        result = normalizer._normalize_url(url)
        assert "utm_source" not in result
        assert "utm_medium" not in result
        assert "a=1" in result

    def test_remove_fbclid(self, normalizer: ArticleNormalizer) -> None:
        url = "https://example.com/page?fbclid=abc123&keep=me"
        result = normalizer._normalize_url(url)
        assert "fbclid" not in result
        assert "keep=me" in result

    def test_remove_gclid(self, normalizer: ArticleNormalizer) -> None:
        url = "https://example.com/page?gclid=xyz789"
        result = normalizer._normalize_url(url)
        assert "gclid" not in result

    def test_normalize_http_to_https(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._normalize_url("http://example.com/page")
        assert result.startswith("https://")

    def test_preserve_non_http_scheme(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._normalize_url("ftp://example.com/file")
        assert result.startswith("ftp://")

    def test_all_tracking_params_removed(self, normalizer: ArticleNormalizer) -> None:
        url = (
            "https://example.com/page"
            "?utm_source=s"
            "&utm_medium=m"
            "&utm_campaign=c"
            "&utm_term=t"
            "&utm_content=ct"
            "&fbclid=f"
            "&gclid=g"
            "&real=param"
        )
        result = normalizer._normalize_url(url)
        assert "real=param" in result
        assert "utm_" not in result
        assert "fbclid" not in result
        assert "gclid" not in result

    def test_empty_url(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._normalize_url("")
        assert result == ""

    def test_url_without_scheme(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._normalize_url("example.com/page")
        assert result == "https://example.com/page"


class TestTextCleaning:
    def test_strip_whitespace(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._clean_text("  Hello World  ", None)
        assert result == "Hello World"

    def test_collapse_multi_spaces(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._clean_text("Hello   World    Test", None)
        assert result == "Hello World Test"

    def test_collapse_newlines(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._clean_text("Hello\nWorld\n\rTest", None)
        assert result == "Hello World Test"

    def test_html_entities_amp(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._clean_text("Hello &amp; World", None)
        assert result == "Hello & World"

    def test_html_entities_lt_gt(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._clean_text("A &lt; B &gt; C", None)
        assert result == "A < B > C"

    def test_html_entities_quot(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._clean_text('He said &quot;hello&quot;', None)
        assert result == 'He said "hello"'

    def test_html_entities_apos(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._clean_text("It&apos;s a test", None)
        assert result == "It's a test"

    def test_html_entities_nbsp(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._clean_text("Hello&nbsp;World", None)
        assert result == "Hello World"

    def test_truncate_title(self, normalizer: ArticleNormalizer) -> None:
        long_title = "A" * 600
        result = normalizer._clean_text(long_title, 500)
        assert len(result) == 500

    def test_truncate_summary(self, normalizer: ArticleNormalizer) -> None:
        long_summary = "B" * 2500
        result = normalizer._clean_text(long_summary, 2000)
        assert len(result) == 2000

    def test_no_truncate_within_limit(self, normalizer: ArticleNormalizer) -> None:
        text = "A" * 100
        result = normalizer._clean_text(text, 500)
        assert len(result) == 100

    def test_body_not_truncated(self, normalizer: ArticleNormalizer) -> None:
        long_body = "C" * 5000
        result = normalizer._clean_text(long_body, None)
        assert len(result) == 5000

    def test_whitespace_then_html_entities(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._clean_text("  Hello &amp; goodbye  ", None)
        assert result == "Hello & goodbye"

    def test_only_spaces(self, normalizer: ArticleNormalizer) -> None:
        result = normalizer._clean_text("   ", None)
        assert result == ""


class TestDedupByUrl:
    def test_returns_none_when_url_exists(
        self, normalizer: ArticleNormalizer, mock_repo: MagicMock
    ) -> None:
        existing = _make_article(url="https://example.com/article")
        mock_repo.get_by_url.return_value = existing

        article = NormalizedArticle(
            title="New Title",
            url="https://example.com/article",
            language="en",
            source_id=1,
        )
        result = normalizer.normalize_article(article)
        assert result is None
        mock_repo.get_by_url.assert_called_once_with(
            "https://example.com/article"
        )
        mock_repo.create.assert_not_called()

    def test_checks_normalized_url(
        self, normalizer: ArticleNormalizer, mock_repo: MagicMock
    ) -> None:
        existing = _make_article(url="https://example.com/article")
        mock_repo.get_by_url.return_value = existing

        article = NormalizedArticle(
            title="New Title",
            url="http://example.com/article/",
            language="en",
            source_id=1,
        )
        result = normalizer.normalize_article(article)
        assert result is None
        # Both http->https and trailing-slash strip were applied
        mock_repo.get_by_url.assert_called_once_with(
            "https://example.com/article"
        )


class TestDedupByDedupeKey:
    def test_returns_none_when_dedupe_key_exists(
        self, normalizer: ArticleNormalizer, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_by_url.return_value = None
        existing = _make_article()
        mock_repo.get_by_dedupe_key.return_value = existing

        article = NormalizedArticle(
            title="Existing Title",
            url="https://example.com/article",
            language="en",
            source_id=1,
        )
        result = normalizer.normalize_article(article)
        assert result is None
        mock_repo.get_by_url.assert_called_once()
        mock_repo.get_by_dedupe_key.assert_called_once()
        mock_repo.create.assert_not_called()

    def test_uses_provided_dedupe_key(
        self, normalizer: ArticleNormalizer, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_by_url.return_value = None
        existing = _make_article()
        mock_repo.get_by_dedupe_key.return_value = existing

        article = NormalizedArticle(
            title="Title",
            url="https://example.com/article",
            language="en",
            source_id=1,
            dedupe_key="custom-key",
        )
        result = normalizer.normalize_article(article)
        assert result is None
        mock_repo.get_by_dedupe_key.assert_called_once_with("custom-key")


class TestSuccessfulCreation:
    def test_creates_article_when_not_duplicate(
        self, normalizer: ArticleNormalizer, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_by_url.return_value = None
        mock_repo.get_by_dedupe_key.return_value = None
        new_article = _make_article()
        mock_repo.create.return_value = new_article

        article = NormalizedArticle(
            title="Test Title",
            url="https://example.com/article",
            summary="Summary text",
            body="Body text",
            language="en",
            source_id=1,
        )
        result = normalizer.normalize_article(article)
        assert result is not None
        assert result.id == 42
        mock_repo.create.assert_called_once()

    def test_sets_normalized_url_and_dedupe_key(
        self, normalizer: ArticleNormalizer, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_by_url.return_value = None
        mock_repo.get_by_dedupe_key.return_value = None
        new_article = _make_article()
        mock_repo.create.return_value = new_article

        article = NormalizedArticle(
            title="Test Title",
            url="http://Example.com/Article/",
            language="en",
            source_id=1,
        )
        normalizer.normalize_article(article)
        _, kwargs = mock_repo.create.call_args
        assert kwargs["url"] == "https://Example.com/Article"
        assert kwargs["normalized_url"] == "https://Example.com/Article"
        assert kwargs["dedupe_key"] == make_dedupe_key("Test Title", "http://Example.com/Article/")

    def test_creates_with_all_fields(
        self, normalizer: ArticleNormalizer, mock_repo: MagicMock
    ) -> None:
        from datetime import datetime, timezone

        mock_repo.get_by_url.return_value = None
        mock_repo.get_by_dedupe_key.return_value = None
        new_article = _make_article()
        mock_repo.create.return_value = new_article

        pub_at = datetime(2026, 6, 24, 12, 0, 0, tzinfo=timezone.utc)
        article = NormalizedArticle(
            title="Full Article",
            url="https://example.com/full",
            summary="A summary",
            body="Body content",
            language="fr",
            source_id=5,
            published_at=pub_at,
        )
        normalizer.normalize_article(article)
        _, kwargs = mock_repo.create.call_args
        assert kwargs["source_id"] == 5
        assert kwargs["url"] == "https://example.com/full"
        assert kwargs["title"] == "Full Article"
        assert kwargs["summary"] == "A summary"
        assert kwargs["body"] == "Body content"
        assert kwargs["language"] == "fr"
        assert kwargs["published_at"] == pub_at

    def test_url_dedup_takes_priority(
        self, normalizer: ArticleNormalizer, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_by_url.return_value = _make_article()

        article = NormalizedArticle(
            title="Should Be Dup",
            url="https://example.com/article",
            language="en",
            source_id=1,
        )
        result = normalizer.normalize_article(article)
        assert result is None
        # get_by_dedupe_key should never be called since URL dup wins
        mock_repo.get_by_dedupe_key.assert_not_called()


class TestEdgeCases:
    def test_normalize_article_without_summary(
        self, normalizer: ArticleNormalizer, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_by_url.return_value = None
        mock_repo.get_by_dedupe_key.return_value = None
        article = _make_article(summary=None)
        mock_repo.create.return_value = article

        na = NormalizedArticle(
            title="No Summary",
            url="https://example.com/no-summary",
            language="en",
            source_id=1,
        )
        result = normalizer.normalize_article(na)
        assert result is not None
        _, kwargs = mock_repo.create.call_args
        assert kwargs["summary"] is None

    def test_normalize_article_without_body(
        self, normalizer: ArticleNormalizer, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_by_url.return_value = None
        mock_repo.get_by_dedupe_key.return_value = None
        article = _make_article(body=None)
        mock_repo.create.return_value = article

        na = NormalizedArticle(
            title="No Body",
            url="https://example.com/no-body",
            summary="Only summary",
            language="en",
            source_id=1,
        )
        result = normalizer.normalize_article(na)
        assert result is not None
        _, kwargs = mock_repo.create.call_args
        assert kwargs["body"] is None

    def test_mixed_whitespace_and_entities_in_text(
        self, normalizer: ArticleNormalizer, mock_repo: MagicMock
    ) -> None:
        mock_repo.get_by_url.return_value = None
        mock_repo.get_by_dedupe_key.return_value = None
        article = _make_article()
        mock_repo.create.return_value = article

        na = NormalizedArticle(
            title="  Hello &amp; goodbye  ",
            url="https://example.com/mixed",
            summary="  This   has &lt;extra&gt; spaces  ",
            language="en",
            source_id=1,
        )
        result = normalizer.normalize_article(na)
        assert result is not None
        _, kwargs = mock_repo.create.call_args
        assert kwargs["title"] == "Hello & goodbye"
        assert kwargs["summary"] == "This has <extra> spaces"
