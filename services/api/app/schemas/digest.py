from pydantic import BaseModel


class DigestEntryResource(BaseModel):
    cluster_id: str
    rank: int
    category: str
    headline: str
    summary: str
    source_count: int
    sources: list[str] = []
    image_url: str = ""
    video_url: str = ""
    headline_translated: str = ""
    summary_translated: str = ""


class DigestResource(BaseModel):
    date: str
    published_at: str
    entries: list[DigestEntryResource]
