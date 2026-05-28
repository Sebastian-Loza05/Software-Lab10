from poke_api.repositories import health_repository
from poke_api.schemas.health import HealthResponse


async def get_health() -> HealthResponse:
    db_ok = await health_repository.check_connection()
    return HealthResponse(
        status="ok",
        database="up" if db_ok else "down",
    )
