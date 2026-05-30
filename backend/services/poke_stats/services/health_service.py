from poke_stats.repositories import health_repository
from poke_stats.schemas.health import HealthResponse


async def get_health() -> HealthResponse:
    db_ok = await health_repository.check_connection()
    return HealthResponse(
        status="ok",
        database="up" if db_ok else "down",
    )
