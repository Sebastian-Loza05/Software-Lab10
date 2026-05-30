from poke_api.repositories import pokemon_repository
from poke_api.schemas.pokemon import PokemonDetail, PokemonListResponse


async def list_pokemon_names(limit: int = 20, offset: int = 0) -> PokemonListResponse:
    data = await pokemon_repository.list_pokemon(limit=limit, offset=offset)
    names = [item["name"] for item in data["results"]]
    return PokemonListResponse(count=data["count"], names=names)


def _extract_sprite(sprites: dict) -> str | None:
    # Prefer the official artwork; fall back to the default front sprite.
    official = (sprites.get("other") or {}).get("official-artwork") or {}
    return official.get("front_default") or sprites.get("front_default")


async def get_pokemon_detail(name: str) -> PokemonDetail | None:
    data = await pokemon_repository.get_pokemon(name.strip().lower())
    if data is None:
        return None
    return PokemonDetail(
        id=data["id"],
        name=data["name"],
        types=[t["type"]["name"] for t in data.get("types", [])],
        sprite=_extract_sprite(data.get("sprites") or {}),
    )
