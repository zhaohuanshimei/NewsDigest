from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    message: str
    request_id: str
