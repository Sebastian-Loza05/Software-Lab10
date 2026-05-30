from fastapi import APIRouter, HTTPException, Query

from poke_api.schemas.pokemon import PokemonDetail, PokemonListResponse
from poke_api.services import pokemon_service

router = APIRouter()


@router.get("/pokemon", response_model=PokemonListResponse, tags=["pokemon"])
async def list_pokemon(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PokemonListResponse:
    return await pokemon_service.list_pokemon_names(limit=limit, offset=offset)


@router.get("/pokemon/{name}", response_model=PokemonDetail, tags=["pokemon"])
async def get_pokemon(name: str) -> PokemonDetail:
    result = await pokemon_service.get_pokemon_detail(name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Pokemon '{name}' not found")
    return result
