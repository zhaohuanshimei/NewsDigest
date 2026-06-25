from fastapi import FastAPI

from app.core.config import API_PREFIX
from app.core.metadata import APP_NAME, APP_VERSION
from app.routers.archive import router as archive_router
from app.routers.articles import router as articles_router
from app.routers.clusters import router as clusters_router
from app.routers.digests import router as digests_router
from app.routers.health import router as health_router


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)

app.include_router(archive_router, prefix=API_PREFIX)
app.include_router(articles_router, prefix=API_PREFIX)
app.include_router(clusters_router, prefix=API_PREFIX)
app.include_router(digests_router, prefix=API_PREFIX)
app.include_router(health_router, prefix=API_PREFIX)
