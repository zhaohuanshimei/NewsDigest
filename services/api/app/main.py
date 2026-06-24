from fastapi import FastAPI

from app.core.config import API_PREFIX
from app.core.metadata import APP_NAME, APP_VERSION
from app.routers.health import router as health_router


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)

app.include_router(health_router, prefix=API_PREFIX)
