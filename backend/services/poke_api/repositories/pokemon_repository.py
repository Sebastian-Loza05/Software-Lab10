import httpx

from commons.latency import latency_block
from poke_api.core.config import settings


async def list_pokemon(limit: int = 20, offset: int = 0) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.pokeapi_base_url}/pokemon",
            params={"limit": limit, "offset": offset},
        )
    response.raise_for_status()
    return response.json()


async def get_pokemon(name: str) -> dict | None:
    """Fetch a single pokemon from PokeAPI. Returns None on 404, raises on other
    HTTP/network errors so the caller can surface them."""
    async with httpx.AsyncClient() as client:
        with latency_block("pokeapi_external_call"):
            response = await client.get(f"{settings.pokeapi_base_url}/pokemon/{name}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()
