from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    pokemon_name: str = Field(..., min_length=1)


class StatItem(BaseModel):
    name: str
    value: int | None


class SearchResponse(BaseModel):
    name: str
    stats: list[StatItem]
    img: str | None
    # Per-service failure reasons, e.g. {"poke_stats": "404", "poke_api": "timeout"}.
    # Empty when every downstream succeeded.
    errors: dict[str, str] = {}
