"""Gateway orchestration: fan out to the 3 downstream services in parallel and
compose a partial response.

Design (decided up front):
- All three calls run concurrently with a per-call timeout.
- If a service errors or returns 404, its field is left empty/null and the
  reason is recorded in ``errors`` — the gateway still answers 200 as long as
  at least one service actually responded.
- The X-Request-ID generated here is propagated to every downstream call so the
  whole request can be correlated across services.
"""

import asyncio

import httpx

from commons.context import get_request_id, new_request_id
from search_api.core.config import settings
from search_api.repositories import downstream
from search_api.schemas.search import SearchResponse, StatItem

# Battle stats exposed as the ordered ``stats`` array, mapping our response
# label to the column returned by POKE Stats.
_STAT_FIELDS = [
    ("hp", "hp"),
    ("attack", "attack"),
    ("defense", "defense"),
    ("special-attack", "sp_atk"),
    ("special-defense", "sp_def"),
    ("speed", "speed"),
]


def _classify(exc: BaseException) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, httpx.HTTPStatusError):
        return str(exc.response.status_code)
    if isinstance(exc, httpx.RequestError):
        return "unreachable"
    return "error"


def _stats_to_array(stats: dict) -> list[StatItem]:
    return [StatItem(name=label, value=stats.get(col)) for label, col in _STAT_FIELDS]


async def search(pokemon_name: str) -> tuple[SearchResponse, bool]:
    """Return (response, all_failed). ``all_failed`` is True only when every
    downstream call raised — the route turns that into a 503."""
    name = pokemon_name.strip().lower()
    # Reuse the id the middleware bound for this request so the same request_id
    # is forwarded downstream and correlates all four services in the logs.
    request_id = get_request_id() or new_request_id()
    errors: dict[str, str] = {}

    timeout = httpx.Timeout(settings.downstream_timeout)
    async with httpx.AsyncClient(timeout=timeout) as client:
        pokemon_res, stats_res, image_res = await asyncio.gather(
            downstream.fetch_pokemon(client, name, request_id),
            downstream.fetch_stats(client, name, request_id),
            downstream.image_exists(client, name, request_id),
            return_exceptions=True,
        )

    hard_failures = 0

    # --- name (from POKE API canonical detail, falling back to the input) ---
    resolved_name = name
    if isinstance(pokemon_res, BaseException):
        errors["poke_api"] = _classify(pokemon_res)
        hard_failures += 1
    elif pokemon_res is None:
        errors["poke_api"] = "404"
    else:
        resolved_name = pokemon_res.get("name", name)

    # --- stats (from POKE Stats, transformed to an array) ---
    stats: list[StatItem] = []
    if isinstance(stats_res, BaseException):
        errors["poke_stats"] = _classify(stats_res)
        hard_failures += 1
    elif stats_res is None:
        errors["poke_stats"] = "404"
    else:
        stats = _stats_to_array(stats_res)

    # --- img (URL into POKE Images, only when the artwork exists) ---
    img: str | None = None
    if isinstance(image_res, BaseException):
        errors["poke_images"] = _classify(image_res)
        hard_failures += 1
    elif image_res is False:
        errors["poke_images"] = "404"
    else:
        img = f"{settings.poke_images_url}/images/{name}"

    response = SearchResponse(name=resolved_name, stats=stats, img=img, errors=errors)
    return response, hard_failures == 3
