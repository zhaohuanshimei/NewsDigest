from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.article import ArticleDetailResource
from app.schemas.error import ApiErrorEnvelope
from app.services.digests import get_article_detail


router = APIRouter(tags=["articles"])


@router.get(
    "/articles/{article_id}",
    response_model=ArticleDetailResource,
    responses={404: {"model": ApiErrorEnvelope}},
    summary="Get Article Detail",
)
def get_article_detail_route(article_id: str) -> ArticleDetailResource | JSONResponse:
    article = get_article_detail(article_id)
    if article is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "article_not_found",
                    "message": "未找到指定文章",
                    "request_id": "req_static_article_lookup",
                }
            },
        )

    return article
