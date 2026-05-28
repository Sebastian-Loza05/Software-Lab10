from pydantic import BaseModel


class PokemonListResponse(BaseModel):
    count: int
    names: list[str]
