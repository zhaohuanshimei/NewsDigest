"""Core configuration and metadata for the API service."""

from app.core.fetcher_interface import (
    BaseFetcher,
    ExtractedItem,
    FetchError,
    FetchRequest,
    FetchResult,
    NormalizedArticle,
    make_dedupe_key,
)

__all__ = [
    "BaseFetcher",
    "ExtractedItem",
    "FetchError",
    "FetchRequest",
    "FetchResult",
    "NormalizedArticle",
    "make_dedupe_key",
]
