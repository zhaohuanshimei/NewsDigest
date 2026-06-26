from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.archive import ArchiveDateListResource
from app.schemas.error import ApiErrorEnvelope, ApiError
from app.services.archive_query_service import ArchiveQueryService


router = APIRouter(tags=["archive"])


def _error_response(status_code: int, code: str, message: str, request_id: str) -> JSONResponse:
    envelope = ApiErrorEnvelope(
        error=ApiError(code=code, message=message, request_id=request_id)
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


@router.get(
    "/archive/dates",
    response_model=ArchiveDateListResource,
    responses={400: {"model": ApiErrorEnvelope}},
    summary="Get Archive Dates",
)
def get_archive_date_route(
    limit: int = 30,
    db: Session = Depends(get_db)
) -> ArchiveDateListResource | JSONResponse:
    if limit <= 0 or limit > 365:
        return _error_response(
            400,
            "invalid_limit",
            "limit 参数必须在 1-365 之间",
            "req_archive_dates",
        )

    service = ArchiveQueryService(db)
    dates = service.get_archive_dates(limit=limit)

    return ArchiveDateListResource(dates=dates)
