from poke_api.schemas.health import HealthResponse


async def get_health() -> HealthResponse:
    return HealthResponse(status="ok")
