from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.article import Article


class ArticleRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, article_id: int) -> Article | None:
        return self.db.get(Article, article_id)

    def get_by_url(self, url: str) -> Article | None:
        return self.db.query(Article).filter(Article.url == url).first()

    def get_by_dedupe_key(self, dedupe_key: str) -> Article | None:
        return (
            self.db.query(Article)
            .filter(Article.dedupe_key == dedupe_key)
            .first()
        )

    def create(self, **kwargs) -> Article:
        article = Article(**kwargs)
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return article

    def list_recent(self, limit: int = 50) -> list[Article]:
        return (
            self.db.query(Article)
            .order_by(Article.created_at.desc())
            .limit(limit)
            .all()
        )
