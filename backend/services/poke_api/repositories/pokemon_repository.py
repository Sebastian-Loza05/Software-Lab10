import httpx

from poke_api.core.config import settings


async def list_pokemon(limit: int = 20, offset: int = 0) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.pokeapi_base_url}/pokemon",
            params={"limit": limit, "offset": offset},
        )
    response.raise_for_status()
    return response.json()
