from datetime import date as date_type

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.digest import DigestResource
from app.schemas.error import ApiErrorEnvelope, ApiError
from app.services.digest_query_service import DigestQueryService


router = APIRouter(tags=["digests"])


def _error_response(status_code: int, code: str, message: str, request_id: str) -> JSONResponse:
    envelope = ApiErrorEnvelope(
        error=ApiError(code=code, message=message, request_id=request_id)
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


@router.get(
    "/digests/latest",
    response_model=DigestResource,
    responses={404: {"model": ApiErrorEnvelope}},
    summary="Get Latest Digest",
)
def get_latest_digest_route(db: Session = Depends(get_db)) -> DigestResource | JSONResponse:
    service = DigestQueryService(db)
    digest = service.get_latest()

    if digest is None:
        return _error_response(
            404,
            "digest_not_found",
            "未找到任何日报",
            "req_digest_latest",
        )

    return digest


@router.get(
    "/digests/{date}",
    response_model=DigestResource,
    responses={404: {"model": ApiErrorEnvelope}},
    summary="Get Digest By Date",
)
def get_digest_by_date_route(
    date: str,
    db: Session = Depends(get_db)
) -> DigestResource | JSONResponse:
    try:
        target_date = date_type.fromisoformat(date)
    except ValueError:
        return _error_response(
            400,
            "invalid_date_format",
            "日期格式无效，请使用 YYYY-MM-DD 格式",
            "req_digest_by_date",
        )

    service = DigestQueryService(db)
    digest = service.get_by_date(target_date)

    if digest is None:
        return _error_response(
            404,
            "digest_not_found",
            "未找到指定日期的日报",
            "req_digest_by_date",
        )

    return digest
