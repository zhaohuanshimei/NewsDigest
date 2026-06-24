from fastapi import APIRouter

from app.core.metadata import APP_VERSION, SERVICE_NAME
from app.schemas.health import HealthResource


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResource)
def get_health() -> HealthResource:
    return HealthResource(
        status="ok",
        service=SERVICE_NAME,
        version=APP_VERSION,
    )
