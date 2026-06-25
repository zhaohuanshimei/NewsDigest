from pydantic import BaseModel


class ClusterDetailResource(BaseModel):
    id: str
    category: str
    headline: str
    summary: str
    source_count: int
    digest_dates: list[str]
