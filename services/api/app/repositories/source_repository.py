from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.source import Source


class SourceRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, source_id: int) -> Source | None:
        return self.db.get(Source, source_id)

    def get_by_name(self, name: str) -> Source | None:
        return self.db.query(Source).filter(Source.name == name).first()

    def get_enabled_sources(self) -> list[Source]:
        return (
            self.db.query(Source)
            .filter(Source.enabled.is_(True))
            .all()
        )

    def get_active_fetchable_sources(self) -> list[Source]:
        return (
            self.db.query(Source)
            .filter(Source.enabled.is_(True), Source.kind == "rss")
            .all()
        )

    def list_all(self) -> list[Source]:
        return self.db.query(Source).all()

    def create(self, **kwargs) -> Source:
        source = Source(**kwargs)
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def update(self, source_id: int, **kwargs) -> Source | None:
        source = self.get_by_id(source_id)
        if source is None:
            return None
        for key, value in kwargs.items():
            setattr(source, key, value)
        self.db.commit()
        self.db.refresh(source)
        return source

    def delete(self, source_id: int) -> bool:
        source = self.get_by_id(source_id)
        if source is None:
            return False
        self.db.delete(source)
        self.db.commit()
        return True
