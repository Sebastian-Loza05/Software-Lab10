from fastapi import APIRouter, Query

from poke_api.schemas.pokemon import PokemonListResponse
from poke_api.services import pokemon_service

router = APIRouter()


@router.get("/pokemon", response_model=PokemonListResponse, tags=["pokemon"])
async def list_pokemon(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PokemonListResponse:
    return await pokemon_service.list_pokemon_names(limit=limit, offset=offset)
