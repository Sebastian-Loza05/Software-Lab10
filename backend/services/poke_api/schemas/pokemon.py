from pydantic import BaseModel


class PokemonListResponse(BaseModel):
    count: int
    names: list[str]


class PokemonDetail(BaseModel):
    id: int
    name: str
    types: list[str]
    sprite: str | None
