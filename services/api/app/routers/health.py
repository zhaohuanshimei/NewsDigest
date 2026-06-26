from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.metadata import APP_VERSION, SERVICE_NAME
from app.database import get_db
from app.schemas.health import HealthResource
from app.services.health_service import HealthService


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResource)
def get_health(db: Session = Depends(get_db)) -> HealthResource:
    health_service = HealthService(db)
    health_status = health_service.check_health()

    return HealthResource(
        status=health_status["status"],
        service=SERVICE_NAME,
        version=APP_VERSION,
        database=health_status["database"],
        last_digest=health_status["last_digest"],
    )
