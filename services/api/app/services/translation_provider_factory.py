"""Translation provider factory.

Builds the appropriate :class:`TranslationProvider` based on environment
variables. Kept in a separate module from ``translation_service`` to avoid
circular imports (the OpenAI provider module does not import the service).
"""

from __future__ import annotations

from app.services.translation_provider_openai import OpenAICompatibleTranslationProvider
from app.services.translation_service import NullTranslationProvider, TranslationProvider


def build_translation_provider() -> TranslationProvider:
    """Build the translation provider from environment variables.

    Priority:
      1. If ``TRANSLATION_API_BASE_URL`` + ``TRANSLATION_API_KEY`` are set,
         use :class:`OpenAICompatibleTranslationProvider`
         (supports OpenAI / NewAPI / DeepSeek / GLM / Qwen / etc.).
      2. Otherwise, return :class:`NullTranslationProvider`
         (no-op, keeps original text — pipeline still runs, just no translation).

    Add new provider branches here as new integrations are needed.
    """
    provider = OpenAICompatibleTranslationProvider.from_env()
    if provider is not None:
        return provider
    return NullTranslationProvider()
