from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.article import ArticleDetailResource
from app.schemas.error import ApiErrorEnvelope, ApiError
from app.services.archive_query_service import ArchiveQueryService


router = APIRouter(tags=["articles"])


def _error_response(status_code: int, code: str, message: str, request_id: str) -> JSONResponse:
    envelope = ApiErrorEnvelope(
        error=ApiError(code=code, message=message, request_id=request_id)
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


@router.get(
    "/articles/{article_id}",
    response_model=ArticleDetailResource,
    responses={404: {"model": ApiErrorEnvelope}},
    summary="Get Article Detail",
)
def get_article_detail_route(
    article_id: int,
    db: Session = Depends(get_db)
) -> ArticleDetailResource | JSONResponse:
    service = ArchiveQueryService(db)
    article = service.get_article_detail(article_id)

    if article is None:
        return _error_response(
            404,
            "article_not_found",
            "未找到指定文章",
            "req_article_detail",
        )

    return ArticleDetailResource(**article)
