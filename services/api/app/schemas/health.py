from typing import Any, Literal

from pydantic import BaseModel


class HealthResource(BaseModel):
    status: Literal["ok", "degraded", "error"]
    service: str
    version: str
    database: Literal["ok", "error"]
    last_digest: dict[str, Any] | None = None
