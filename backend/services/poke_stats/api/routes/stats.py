from fastapi import APIRouter, HTTPException

from poke_stats.schemas.stats import PokemonStats
from poke_stats.services import stats_service

router = APIRouter()


@router.get("/stats/{name}", response_model=PokemonStats, tags=["stats"])
async def get_stats(name: str) -> PokemonStats:
    result = await stats_service.get_stats(name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Pokemon '{name}' not found")
    return result
