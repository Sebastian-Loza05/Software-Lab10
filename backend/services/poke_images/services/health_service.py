from poke_images.repositories import health_repository
from poke_images.schemas.health import HealthResponse


async def get_health() -> HealthResponse:
    storage_ok = health_repository.check_storage()
    return HealthResponse(
        status="ok",
        storage="up" if storage_ok else "down",
    )
