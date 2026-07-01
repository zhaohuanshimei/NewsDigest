from __future__ import annotations

import urllib.error
import urllib.request
from datetime import datetime
from time import mktime

import feedparser

from app.core.fetcher_interface import (
    BaseFetcher,
    ExtractedItem,
    FetchError,
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
                error_code=FetchError.HTTP_ERROR,
            )
        except urllib.error.URLError as e:
            code = FetchError.TIMEOUT if isinstance(e.reason, str) and "timed out" in e.reason else FetchError.NETWORK_ERROR
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

            image_url = _extract_image_url(entry)
            video_url = _extract_video_url(entry)

            items.append(ExtractedItem(
                title=entry.get("title"),
                url=entry.get("link"),
                summary=entry.get("summary") or entry.get("description"),
                body=body,
                published_at=published,
                language=feed.feed.get("language") if hasattr(feed, "feed") else None,
                image_url=image_url,
                video_url=video_url,
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
                image_url=item.image_url,
                video_url=item.video_url,
            ))
        return result


def _extract_image_url(entry) -> str | None:
    """Extract the best available image URL from an RSS entry.

    Priority: media_thumbnail > media_content (medium=image) > enclosure (image/*)
    """
    # media_thumbnail (BBC style)
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        for thumb in entry.media_thumbnail:
            url = thumb.get("url") if isinstance(thumb, dict) else getattr(thumb, "url", None)
            if url:
                return url

    # media_content with medium=image (Guardian/CNN style)
    if hasattr(entry, "media_content") and entry.media_content:
        for media in entry.media_content:
            if isinstance(media, dict):
                medium = media.get("medium", "")
                url = media.get("url", "")
                if url and (medium == "image" or not medium):
                    return url

    # enclosure with image type
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            enc_type = getattr(enc, "type", "") or (enc.get("type", "") if isinstance(enc, dict) else "")
            enc_url = getattr(enc, "href", "") or (enc.get("href", "") if isinstance(enc, dict) else "")
            if enc_url and ("image" in enc_type):
                return enc_url

    return None


def _extract_video_url(entry) -> str | None:
    """Detect video content from an RSS entry.

    Checks: media_content with medium=video > enclosure with video type > URL pattern.
    """
    # media_content with medium=video
    if hasattr(entry, "media_content") and entry.media_content:
        for media in entry.media_content:
            if isinstance(media, dict):
                if media.get("medium") == "video" and media.get("url"):
                    return media["url"]

    # enclosure with video type
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            enc_type = getattr(enc, "type", "") or (enc.get("type", "") if isinstance(enc, dict) else "")
            enc_url = getattr(enc, "href", "") or (enc.get("href", "") if isinstance(enc, dict) else "")
            if enc_url and ("video" in enc_type):
                return enc_url

    # URL pattern detection (e.g. CNN /videos/ paths)
    link = entry.get("link", "") or ""
    if "/video" in link.lower() or "/watch/" in link.lower():
        return link

    return None
