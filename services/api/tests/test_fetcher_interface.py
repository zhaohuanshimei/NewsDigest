from datetime import datetime

import pytest

from app.core.fetcher_interface import (
    BaseFetcher,
    ExtractedItem,
    FetchError,
    FetchRequest,
    FetchResult,
    NormalizedArticle,
    make_dedupe_key,
)


class TestFetchRequest:

    def test_required_fields(self) -> None:
        req = FetchRequest(url="https://example.com")
        assert req.url == "https://example.com"

    def test_default_timeout(self) -> None:
        req = FetchRequest(url="https://example.com")
        assert req.timeout_seconds == 30

    def test_optional_fields_default_to_none(self) -> None:
        req = FetchRequest(url="https://example.com")
        assert req.user_agent is None
        assert req.headers is None

    def test_set_optional_fields(self) -> None:
        req = FetchRequest(
            url="https://example.com",
            timeout_seconds=15,
            user_agent="test-agent",
            headers={"Accept": "text/html"},
        )
        assert req.timeout_seconds == 15
        assert req.user_agent == "test-agent"
        assert req.headers == {"Accept": "text/html"}


class TestFetchResult:

    def test_required_fields(self) -> None:
        result = FetchResult(
            raw_content="<html></html>",
            status_code=200,
            success=True,
        )
        assert result.raw_content == "<html></html>"
        assert result.status_code == 200
        assert result.success is True

    def test_fetched_at_defaults_to_now(self) -> None:
        before = datetime.now()
        result = FetchResult(raw_content="", status_code=200, success=True)
        after = datetime.now()
        assert before <= result.fetched_at <= after

    def test_optional_fields_default_to_none(self) -> None:
        result = FetchResult(raw_content="", status_code=200, success=True)
        assert result.content_type is None
        assert result.error_message is None

    def test_success_false_with_error_message(self) -> None:
        result = FetchResult(
            raw_content="",
            status_code=500,
            success=False,
            error_message="Internal server error",
        )
        assert result.success is False
        assert result.error_message == "Internal server error"

    def test_success_false_with_empty_error_message(self) -> None:
        result = FetchResult(
            raw_content="",
            status_code=500,
            success=False,
            error_message="",
        )
        assert result.success is False
        assert result.error_message == ""


class TestExtractedItem:

    def test_all_fields_default_to_none(self) -> None:
        item = ExtractedItem()
        assert item.title is None
        assert item.url is None
        assert item.summary is None
        assert item.body is None
        assert item.published_at is None
        assert item.language is None
        assert item.raw is None

    def test_set_all_fields(self) -> None:
        dt = datetime(2026, 1, 1)
        item = ExtractedItem(
            title="Test",
            url="https://example.com",
            summary="Summary",
            body="Body",
            published_at=dt,
            language="en",
            raw={"key": "val"},
        )
        assert item.title == "Test"
        assert item.url == "https://example.com"
        assert item.body == "Body"
        assert item.published_at == dt
        assert item.language == "en"
        assert item.raw == {"key": "val"}


class TestNormalizedArticle:

    def test_required_fields(self) -> None:
        article = NormalizedArticle(
            title="Test Title",
            url="https://example.com",
            language="en",
        )
        assert article.title == "Test Title"
        assert article.url == "https://example.com"
        assert article.language == "en"

    def test_optional_fields_default_to_none(self) -> None:
        article = NormalizedArticle(
            title="T", url="https://example.com", language="en"
        )
        assert article.summary is None
        assert article.body is None
        assert article.published_at is None
        assert article.source_id is None
        assert article.dedupe_key is None
        assert article.normalized_url is None

    def test_set_all_fields(self) -> None:
        dt = datetime(2026, 6, 24)
        article = NormalizedArticle(
            title="Title",
            url="https://example.com",
            language="zh",
            summary="Sum",
            body="Body text",
            published_at=dt,
            source_id=42,
            dedupe_key="abc123",
            normalized_url="https://example.com/normalized",
        )
        assert article.summary == "Sum"
        assert article.body == "Body text"
        assert article.published_at == dt
        assert article.source_id == 42
        assert article.dedupe_key == "abc123"
        assert article.normalized_url == "https://example.com/normalized"


class TestMakeDedupeKey:

    def test_returns_string(self) -> None:
        key = make_dedupe_key("Hello", "https://example.com")
        assert isinstance(key, str)
        assert len(key) == 64  # sha256 hexdigest

    def test_deterministic(self) -> None:
        key1 = make_dedupe_key("Hello", "https://example.com")
        key2 = make_dedupe_key("Hello", "https://example.com")
        assert key1 == key2

    def test_different_title_different_key(self) -> None:
        key1 = make_dedupe_key("Hello", "https://example.com")
        key2 = make_dedupe_key("World", "https://example.com")
        assert key1 != key2

    def test_different_url_different_key(self) -> None:
        key1 = make_dedupe_key("Hello", "https://example.com/a")
        key2 = make_dedupe_key("Hello", "https://example.com/b")
        assert key1 != key2


class TestFetchError:

    def test_members_are_unique(self) -> None:
        values = [e.value for e in FetchError]
        assert len(values) == len(set(values))

    def test_all_expected_members_exist(self) -> None:
        expected = {"timeout", "http_error", "parse_error", "network_error", "unknown"}
        actual = {e.value for e in FetchError}
        assert actual == expected

    def test_member_values_are_strings(self) -> None:
        for e in FetchError:
            assert isinstance(e.value, str)


class TestBaseFetcher:

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseFetcher()  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self) -> None:
        class ConcreteFetcher(BaseFetcher):
            def fetch(self, request: FetchRequest) -> FetchResult:
                return FetchResult(raw_content="", status_code=200, success=True)

            def extract(self, result: FetchResult) -> list[ExtractedItem]:
                return []

            def normalize(self, items: list[ExtractedItem]) -> list[NormalizedArticle]:
                return []

        fetcher = ConcreteFetcher()
        assert isinstance(fetcher, BaseFetcher)
