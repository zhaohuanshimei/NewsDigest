from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.cluster import ClusterDetailResource
from app.schemas.error import ApiErrorEnvelope, ApiError
from app.services.archive_query_service import ArchiveQueryService


router = APIRouter(tags=["clusters"])


def _error_response(status_code: int, code: str, message: str, request_id: str) -> JSONResponse:
    envelope = ApiErrorEnvelope(
        error=ApiError(code=code, message=message, request_id=request_id)
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


@router.get(
    "/clusters/{cluster_id}",
    response_model=ClusterDetailResource,
    responses={404: {"model": ApiErrorEnvelope}},
    summary="Get Cluster Detail",
)
def get_cluster_detail_route(
    cluster_id: int,
    db: Session = Depends(get_db)
) -> ClusterDetailResource | JSONResponse:
    service = ArchiveQueryService(db)
    cluster = service.get_cluster_detail(cluster_id)

    if cluster is None:
        return _error_response(
            404,
            "cluster_not_found",
            "未找到指定聚类",
            "req_cluster_detail",
        )

    return ClusterDetailResource(**cluster)
