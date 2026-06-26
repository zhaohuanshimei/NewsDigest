from __future__ import annotations

import urllib.error
import urllib.request

from readability import Document

from app.core.fetcher_interface import (
    BaseFetcher,
    ExtractedItem,
    FetchError,
    FetchRequest,
    FetchResult,
    NormalizedArticle,
    make_dedupe_key,
)

DEFAULT_USER_AGENT = "NewsDigest/1.0 Content Fetcher"


class ContentFetcher(BaseFetcher):
    """Fetcher that retrieves article HTML from URLs and extracts
    readable content using readability-lxml."""

    def __init__(self, user_agent: str | None = None):
        self.user_agent = user_agent or DEFAULT_USER_AGENT

    @property
    def kind(self) -> str:
        return "content"

    def fetch(self, request: FetchRequest) -> FetchResult:
        try:
            headers = {"User-Agent": request.user_agent or self.user_agent}
            if request.headers:
                headers.update(request.headers)
            req = urllib.request.Request(request.url, headers=headers)
            with urllib.request.urlopen(
                req, timeout=request.timeout_seconds
            ) as response:
                raw = response.read().decode("utf-8", errors="replace")
                return FetchResult(
                    raw_content=raw,
                    status_code=response.status,
                    success=True,
                    content_type=response.headers.get("Content-Type"),
                )
        except urllib.error.HTTPError as e:
            return FetchResult(
                raw_content="",
                status_code=e.code,
                success=False,
                error_message=f"HTTP {e.code}: {e.reason}",
                error_code=FetchError.HTTP_ERROR,
            )
        except urllib.error.URLError as e:
            code = (
                FetchError.TIMEOUT
                if isinstance(e.reason, str) and "timed out" in e.reason
                else FetchError.NETWORK_ERROR
            )
            return FetchResult(
                raw_content="",
                status_code=0,
                success=False,
                error_message=f"URL error: {e.reason}",
                error_code=code,
            )
        except Exception as e:
            return FetchResult(
                raw_content="",
                status_code=0,
                success=False,
                error_message=str(e),
                error_code=FetchError.UNKNOWN,
            )

    def extract(self, result: FetchResult) -> list[ExtractedItem]:
        if not result.success or not result.raw_content:
            return []
        try:
            doc = Document(result.raw_content)
            title = doc.title()
            body = doc.summary()
            if not body:
                return []
            return [
                ExtractedItem(
                    title=title,
                    url=None,
                    body=body,
                )
            ]
        except Exception:
            return []

    def normalize(self, items: list[ExtractedItem]) -> list[NormalizedArticle]:
        result: list[NormalizedArticle] = []
        for item in items:
            if not item.title or not item.body:
                continue
            dedupe_key = make_dedupe_key(item.title, item.body)
            result.append(NormalizedArticle(
                title=item.title,
                url=item.url or "",
                language="en",
                summary=item.summary,
                body=item.body,
                published_at=item.published_at,
                dedupe_key=dedupe_key,
            ))
        return result
