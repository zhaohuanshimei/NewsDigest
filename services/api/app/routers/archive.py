from fastapi import APIRouter

from app.schemas.archive import ArchiveDateListResource
from app.services.digests import list_archive_dates


router = APIRouter(tags=["archive"])


@router.get(
    "/archive/dates",
    response_model=ArchiveDateListResource,
    summary="Get Archive Dates",
)
def get_archive_dates_route() -> ArchiveDateListResource:
    return list_archive_dates()
