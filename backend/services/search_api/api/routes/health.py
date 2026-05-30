from fastapi import APIRouter

from search_api.schemas.health import HealthResponse
from search_api.services import health_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return await health_service.get_health()
