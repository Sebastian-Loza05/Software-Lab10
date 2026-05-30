from fastapi import APIRouter

from poke_images.schemas.health import HealthResponse
from poke_images.services import health_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return await health_service.get_health()
