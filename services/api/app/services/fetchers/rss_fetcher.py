from __future__ import annotations

import urllib.error
import urllib.request
from datetime import datetime
from time import mktime

import feedparser

from app.core.fetcher_interface import (
    BaseFetcher,
    ExtractedItem,
    FetchRequest,
    FetchResult,
    NormalizedArticle,
    make_dedupe_key,
)

DEFAULT_USER_AGENT = "NewsDigest/1.0 RSS Fetcher"


class RssFetcher(BaseFetcher):

    def __init__(self, user_agent: str | None = None):
        self.user_agent = user_agent or DEFAULT_USER_AGENT

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
            )
        except urllib.error.URLError as e:
            return FetchResult(
                raw_content="",
                status_code=0,
                success=False,
                error_message=f"URL error: {e.reason}",
            )
        except Exception as e:
            return FetchResult(
                raw_content="",
                status_code=0,
                success=False,
                error_message=str(e),
            )

    def extract(self, result: FetchResult) -> list[ExtractedItem]:
        if not result.success or not result.raw_content:
            return []
        try:
            feed = feedparser.parse(result.raw_content)
        except Exception:
            return []
        items: list[ExtractedItem] = []
        for entry in feed.entries:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime.fromtimestamp(mktime(entry.published_parsed))
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime.fromtimestamp(mktime(entry.updated_parsed))

            body = None
            if hasattr(entry, "content") and entry.content:
                body = entry.content[0].get("value", "")

            items.append(ExtractedItem(
                title=entry.get("title"),
                url=entry.get("link"),
                summary=entry.get("summary") or entry.get("description"),
                body=body,
                published_at=published,
                language=feed.feed.get("language") if hasattr(feed, "feed") else None,
                raw=entry,
            ))
        return items

    def normalize(self, items: list[ExtractedItem]) -> list[NormalizedArticle]:
        result: list[NormalizedArticle] = []
        for item in items:
            if not item.title or not item.url:
                continue
            dedupe_key = make_dedupe_key(item.title, item.url)
            result.append(NormalizedArticle(
                title=item.title,
                url=item.url,
                language=item.language or "en",
                summary=item.summary,
                body=item.body,
                published_at=item.published_at,
                dedupe_key=dedupe_key,
            ))
        return result
