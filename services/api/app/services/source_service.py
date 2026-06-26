from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.source import Source
from app.repositories.source_repository import SourceRepository

DEFAULT_SOURCES: list[dict] = [
    {
        "name": "BBC News",
        "kind": "rss",
        "url": "http://feeds.bbci.co.uk/news/rss.xml",
        "language": "en",
        "enabled": True,
        "fetch_interval_minutes": 30,
    },
    {
        "name": "Reuters World News",
        "kind": "rss",
        "url": "https://www.reutersagency.com/feed/",
        "language": "en",
        "enabled": True,
        "fetch_interval_minutes": 30,
    },
    {
        "name": "The Guardian International",
        "kind": "rss",
        "url": "https://www.theguardian.com/international/rss",
        "language": "en",
        "enabled": True,
        "fetch_interval_minutes": 30,
    },
    {
        "name": "NYT Home Page",
        "kind": "rss",
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "language": "en",
        "enabled": True,
        "fetch_interval_minutes": 30,
    },
    {
        "name": "AP News",
        "kind": "rss",
        "url": "https://apnews.com/rss",
        "language": "en",
        "enabled": True,
        "fetch_interval_minutes": 30,
    },
    {
        "name": "CNN Edition",
        "kind": "rss",
        "url": "http://rss.cnn.com/rss/edition.rss",
        "language": "en",
        "enabled": True,
        "fetch_interval_minutes": 30,
    },
    {
        "name": "NPR News",
        "kind": "rss",
        "url": "https://feeds.npr.org/1001/rss.xml",
        "language": "en",
        "enabled": True,
        "fetch_interval_minutes": 30,
    },
]


class SourceService:

    def __init__(self, repository: SourceRepository):
        self.repository = repository

    def get_default_sources(self) -> list[dict]:
        return list(DEFAULT_SOURCES)

    def seed_default_sources(self, db: Session) -> list[Source]:
        existing = self.repository.list_all()
        if existing:
            return existing
        created = []
        for data in DEFAULT_SOURCES:
            source = self.repository.create(**data)
            created.append(source)
        return created

    def get_active_fetchable_sources(self) -> list[Source]:
        return self.repository.get_active_fetchable_sources()
