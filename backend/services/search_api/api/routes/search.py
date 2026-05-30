from fastapi import APIRouter, HTTPException

from search_api.schemas.search import SearchRequest, SearchResponse
from search_api.services import search_service

router = APIRouter()


@router.post("/poke/search", response_model=SearchResponse, tags=["search"])
async def poke_search(payload: SearchRequest) -> SearchResponse:
    response, all_failed = await search_service.search(payload.pokemon_name)
    if all_failed:
        # Every downstream service was unreachable/errored — nothing to return.
        raise HTTPException(status_code=503, detail="All downstream services failed")
    return response
