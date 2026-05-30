from poke_stats.repositories import stats_repository
from poke_stats.schemas.stats import PokemonStats


async def get_stats(name: str) -> PokemonStats | None:
    row = await stats_repository.get_by_name(name)
    if row is None:
        return None
    return PokemonStats(
        id=row["id"],
        name=row["name"],
        hp=row["hp"],
        attack=row["attack"],
        defense=row["defense"],
        sp_atk=row["sp_atk"],
        sp_def=row["sp_def"],
        speed=row["speed"],
        type_1=row["type_1"],
        type_2=row["type_2"],
        total=row["total"],
        generation=row["generation"],
        legendary=bool(row["legendary"]),
    )
