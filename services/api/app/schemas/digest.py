from pydantic import BaseModel


class DigestEntryResource(BaseModel):
    cluster_id: str
    rank: int
    category: str
    headline: str
    summary: str
    source_count: int


class DigestResource(BaseModel):
    date: str
    published_at: str
    entries: list[DigestEntryResource]
