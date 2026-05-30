from pydantic import BaseModel


class PokemonStats(BaseModel):
    id: int | None
    name: str
    hp: int | None
    attack: int | None
    defense: int | None
    sp_atk: int | None
    sp_def: int | None
    speed: int | None
    type_1: str | None
    type_2: str | None
    total: int | None
    generation: int | None
    legendary: bool
