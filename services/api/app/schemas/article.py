from pydantic import BaseModel


class ArticleDetailResource(BaseModel):
    id: str
    cluster_id: str
    title: str
    summary: str
    body: str
    source: str
    url: str
    published_at: str
    language: str
