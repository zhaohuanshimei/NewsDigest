from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.digest import DigestResource
from app.schemas.error import ApiErrorEnvelope
from app.services.digests import get_digest_by_date, get_latest_digest


router = APIRouter(tags=["digests"])


@router.get(
    "/digests/latest",
    response_model=DigestResource,
    summary="Get Latest Digest",
)
def get_latest_digest_route() -> DigestResource:
    return get_latest_digest()


@router.get(
    "/digests/{date}",
    response_model=DigestResource,
    responses={404: {"model": ApiErrorEnvelope}},
    summary="Get Digest By Date",
)
def get_digest_by_date_route(date: str) -> DigestResource | JSONResponse:
    digest = get_digest_by_date(date)
    if digest is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "digest_not_found",
                    "message": "未找到指定日期的日报",
                    "request_id": "req_static_digest_lookup",
                }
            },
        )

    return digest
