"""Fetcher adapter interface — abstract base class and data contracts.

Defines the three-stage pipeline contract (Fetch → Extract → Normalize)
that all content fetchers (RSS, web crawl, etc.) must implement.
"""

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FetchError(str, Enum):
    TIMEOUT = "timeout"
    HTTP_ERROR = "http_error"
    PARSE_ERROR = "parse_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class FetchRequest:
    url: str
    timeout_seconds: int = 30
    user_agent: str | None = None
    headers: dict[str, str] | None = None
    retry_count: int = 0
    retry_delay_seconds: float = 1.0


@dataclass
class FetchResult:
    raw_content: str
    status_code: int
    success: bool
    content_type: str | None = None
    fetched_at: datetime = field(default_factory=datetime.now)
    error_message: str | None = None
    error_code: FetchError | None = None


@dataclass
class ExtractedItem:
    title: str | None = None
    url: str | None = None
    summary: str | None = None
    body: str | None = None
    published_at: datetime | None = None
    language: str | None = None
    raw: dict | None = None


@dataclass
class NormalizedArticle:
    title: str
    url: str
    language: str
    summary: str | None = None
    body: str | None = None
    published_at: datetime | None = None
    source_id: int | None = None
    dedupe_key: str | None = None
    normalized_url: str | None = None


def make_dedupe_key(title: str, url: str) -> str:
    raw = f"{title}\0{url}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class BaseFetcher(ABC):

    @abstractmethod
    def fetch(self, request: FetchRequest) -> FetchResult:
        ...

    @abstractmethod
    def extract(self, result: FetchResult) -> list[ExtractedItem]:
        ...

    @abstractmethod
    def normalize(self, items: list[ExtractedItem]) -> list[NormalizedArticle]:
        ...
