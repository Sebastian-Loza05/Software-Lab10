from poke_api.repositories import pokemon_repository
from poke_api.schemas.pokemon import PokemonListResponse


async def list_pokemon_names(limit: int = 20, offset: int = 0) -> PokemonListResponse:
    data = await pokemon_repository.list_pokemon(limit=limit, offset=offset)
    names = [item["name"] for item in data["results"]]
    return PokemonListResponse(count=data["count"], names=names)
