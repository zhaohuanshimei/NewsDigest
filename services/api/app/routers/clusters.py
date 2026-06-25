from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.cluster import ClusterDetailResource
from app.schemas.error import ApiErrorEnvelope
from app.services.digests import get_cluster_detail


router = APIRouter(tags=["clusters"])


@router.get(
    "/clusters/{cluster_id}",
    response_model=ClusterDetailResource,
    responses={404: {"model": ApiErrorEnvelope}},
    summary="Get Cluster Detail",
)
def get_cluster_detail_route(cluster_id: str) -> ClusterDetailResource | JSONResponse:
    cluster = get_cluster_detail(cluster_id)
    if cluster is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "cluster_not_found",
                    "message": "未找到指定聚类",
                    "request_id": "req_static_cluster_lookup",
                }
            },
        )

    return cluster
