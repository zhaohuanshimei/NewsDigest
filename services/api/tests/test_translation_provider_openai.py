"""Tests for the OpenAI-compatible translation provider and pipeline adapter."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import httpx
import pytest

from app.models.digest import Digest
from app.models.digest_entry import DigestEntry
from app.services.translation_provider_factory import build_translation_provider
from app.services.translation_provider_openai import OpenAICompatibleTranslationProvider
from app.services.translation_service import (
    NullTranslationProvider,
    PipelineTranslatorAdapter,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_digest(db_session) -> Digest:
    """A published digest with one entry ready for translation."""
    digest = Digest(date=date(2026, 6, 29), status="published")
    db_session.add(digest)
    db_session.commit()
    db_session.refresh(digest)

    entry = DigestEntry(
        digest_id=digest.id,
        cluster_id=1,
        rank=1,
        category="tech",
        headline="AI chips and model infrastructure continue to heat up",
        summary="Multiple chip makers released new progress around training infrastructure.",
        source_count=2,
    )
    db_session.add(entry)
    db_session.commit()
    return digest


# ---------------------------------------------------------------------------
# OpenAICompatibleTranslationProvider
# ---------------------------------------------------------------------------


class _MockResponse:
    """Minimal mock for httpx.Response."""

    def __init__(self, json_data: dict, status_code: int = 200) -> None:
        self._json = json_data
        self.status_code = status_code

    def json(self) -> dict:
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def _make_completion_response(content: str) -> dict:
    return {
        "choices": [
            {"message": {"role": "assistant", "content": content}, "finish_reason": "stop"},
        ]
    }


class TestOpenAICompatibleProvider:
    def test_translate_success(self) -> None:
        provider = OpenAICompatibleTranslationProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
            model="test-model",
        )
        mock = _MockResponse(_make_completion_response("翻译结果"))
        with patch("app.services.translation_provider_openai.httpx.post", return_value=mock):
            result = provider.translate("hello", "zh")
        assert result == "翻译结果"

    def test_translate_empty_text_returns_none(self) -> None:
        provider = OpenAICompatibleTranslationProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
        )
        assert provider.translate("", "zh") is None
        assert provider.translate("   ", "zh") is None

    def test_translate_http_error_returns_none(self) -> None:
        provider = OpenAICompatibleTranslationProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
        )
        with patch(
            "app.services.translation_provider_openai.httpx.post",
            side_effect=httpx.ConnectError("network error"),
        ):
            result = provider.translate("hello", "zh")
        assert result is None

    def test_translate_empty_content_returns_none(self) -> None:
        provider = OpenAICompatibleTranslationProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
        )
        mock = _MockResponse(_make_completion_response(""))
        with patch("app.services.translation_provider_openai.httpx.post", return_value=mock):
            result = provider.translate("hello", "zh")
        assert result is None

    def test_translate_malformed_response_returns_none(self) -> None:
        provider = OpenAICompatibleTranslationProvider(
            base_url="https://api.example.com/v1",
            api_key="sk-test",
        )
        mock = _MockResponse({"unexpected": "shape"})
        with patch("app.services.translation_provider_openai.httpx.post", return_value=mock):
            result = provider.translate("hello", "zh")
        assert result is None

    def test_base_url_trailing_slash_stripped(self) -> None:
        provider = OpenAICompatibleTranslationProvider(
            base_url="https://api.example.com/v1/",
            api_key="sk-test",
        )
        assert provider.base_url == "https://api.example.com/v1"

    def test_from_env_missing_vars_returns_none(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            assert OpenAICompatibleTranslationProvider.from_env() is None

    def test_from_env_with_vars_returns_provider(self) -> None:
        env = {
            "TRANSLATION_API_BASE_URL": "https://api.example.com/v1",
            "TRANSLATION_API_KEY": "sk-test",
            "TRANSLATION_MODEL": "my-model",
        }
        with patch.dict("os.environ", env, clear=True):
            provider = OpenAICompatibleTranslationProvider.from_env()
        assert provider is not None
        assert provider.model == "my-model"
        assert provider.api_key == "sk-test"

    def test_from_env_empty_key_returns_none(self) -> None:
        env = {
            "TRANSLATION_API_BASE_URL": "https://api.example.com/v1",
            "TRANSLATION_API_KEY": "",
        }
        with patch.dict("os.environ", env, clear=True):
            assert OpenAICompatibleTranslationProvider.from_env() is None


# ---------------------------------------------------------------------------
# build_translation_provider factory
# ---------------------------------------------------------------------------


class TestBuildTranslationProvider:
    def test_returns_openai_provider_when_configured(self) -> None:
        env = {
            "TRANSLATION_API_BASE_URL": "https://api.example.com/v1",
            "TRANSLATION_API_KEY": "sk-test",
            "TRANSLATION_MODEL": "test-model",
        }
        with patch.dict("os.environ", env, clear=True):
            provider = build_translation_provider()
        assert isinstance(provider, OpenAICompatibleTranslationProvider)
        assert provider.model == "test-model"

    def test_returns_null_when_no_config(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            provider = build_translation_provider()
        assert isinstance(provider, NullTranslationProvider)


# ---------------------------------------------------------------------------
# PipelineTranslatorAdapter
# ---------------------------------------------------------------------------


class TestPipelineTranslatorAdapter:
    def test_no_digest_for_date_returns_zero(self, db_session) -> None:
        adapter = PipelineTranslatorAdapter(db_session, provider=NullTranslationProvider())
        from datetime import date

        count = adapter.translate_digest_entries(target_date=date(2020, 1, 1))
        assert count == 0

    def test_translates_existing_digest(self, db_session, sample_digest) -> None:
        adapter = PipelineTranslatorAdapter(
            db_session,
            provider=None,  # NullTranslationProvider keeps original text
        )
        count = adapter.translate_digest_entries(target_date=sample_digest.date)
        assert count >= 1
