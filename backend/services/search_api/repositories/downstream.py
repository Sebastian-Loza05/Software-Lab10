"""HTTP clients for the three downstream services.

Each function performs one call and returns parsed data (or None for a clean
404). Transport/HTTP errors are left to propagate so the service layer can
classify them into the per-service ``errors`` map. The X-Request-ID header is
forwarded on every call so all four services can be correlated in logs.
"""

import httpx

from commons.latency import latency_block
from search_api.core.config import settings

REQUEST_ID_HEADER = "X-Request-ID"


def _headers(request_id: str) -> dict[str, str]:
    return {REQUEST_ID_HEADER: request_id}


async def fetch_pokemon(client: httpx.AsyncClient, name: str, request_id: str) -> dict | None:
    """POKE API wrapper -> canonical pokemon detail. None on 404."""
    with latency_block("poke_api_call"):
        response = await client.get(
            f"{settings.poke_api_url}/pokemon/{name}", headers=_headers(request_id)
        )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


async def fetch_stats(client: httpx.AsyncClient, name: str, request_id: str) -> dict | None:
    """POKE Stats -> stats object from Turso. None on 404."""
    with latency_block("poke_stats_call"):
        response = await client.get(
            f"{settings.poke_stats_url}/stats/{name}", headers=_headers(request_id)
        )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


async def image_exists(client: httpx.AsyncClient, name: str, request_id: str) -> bool:
    """POKE Images existence check. The Images route only serves GET (FastAPI
    does not auto-add HEAD), so we GET and inspect the status; the JPEG body is
    small and discarded."""
    with latency_block("poke_images_call"):
        response = await client.get(
            f"{settings.poke_images_url}/images/{name}", headers=_headers(request_id)
        )
    if response.status_code == 404:
        return False
    response.raise_for_status()
    return True
