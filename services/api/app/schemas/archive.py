from pydantic import BaseModel


class ArchiveDateListResource(BaseModel):
    dates: list[str]
