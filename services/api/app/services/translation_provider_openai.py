"""OpenAI-compatible translation provider.

Works with any API that implements the OpenAI chat completions format:
OpenAI official, NewAPI gateway channels, DeepSeek, Qwen, GLM, etc.

Configure via environment variables:
    TRANSLATION_API_BASE_URL  e.g. https://api.openai.com/v1 or NewAPI URL
    TRANSLATION_API_KEY       sk-... key
    TRANSLATION_MODEL         model name (default: gpt-4o-mini)
"""

from __future__ import annotations

import os

import httpx
import structlog

logger = structlog.get_logger()

_DEFAULT_SYSTEM_PROMPT = (
    "You are a professional news translator. "
    "Translate the user message into the target language. "
    "Return ONLY the translation — no explanations, no quotes, no preamble."
)

# Map our internal lang codes to readable names for the prompt.
_LANG_NAMES = {
    "zh": "Simplified Chinese",
    "zh-CN": "Simplified Chinese",
    "zh-TW": "Traditional Chinese",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
}


class OpenAICompatibleTranslationProvider:
    """Translation provider that calls an OpenAI-compatible chat completions endpoint.

    Duck-types :class:`TranslationProvider` — implements ``translate`` and
    sets ``name``. Avoids importing the ABC to prevent a circular import
    (translation_service imports this module for the factory).

    Returns the translated string on success, or ``None`` on any failure
    (network error, non-2xx response, empty content, malformed JSON).
    Never raises — failures are logged and returned as ``None`` so the
    caller's batch logic can apply fallbacks.
    """

    name = "openai-compatible"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: float = 30.0,
        system_prompt: str = _DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.system_prompt = system_prompt

    def translate(self, text: str, target_lang: str) -> str | None:
        if not text or not text.strip():
            return None

        lang_name = _LANG_NAMES.get(target_lang, target_lang)
        user_prompt = f"Translate the following text into {lang_name}:\n\n{text}"

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": min(2048, max(256, len(text) * 4)),
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning(
                "translation_http_failed",
                model=self.model,
                error=str(exc),
                text_len=len(text),
            )
            return None

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            logger.warning(
                "translation_parse_failed",
                model=self.model,
                error=str(exc),
            )
            return None

        if not content or not content.strip():
            return None

        return content.strip()

    @classmethod
    def from_env(cls) -> "OpenAICompatibleTranslationProvider | None":
        """Build a provider from environment variables.

        Returns ``None`` if required env vars are missing, so callers can
        fall back to the null provider gracefully.
        """
        base_url = os.getenv("TRANSLATION_API_BASE_URL", "").strip()
        api_key = os.getenv("TRANSLATION_API_KEY", "").strip()
        if not base_url or not api_key:
            return None
        model = os.getenv("TRANSLATION_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        return cls(base_url=base_url, api_key=api_key, model=model)
