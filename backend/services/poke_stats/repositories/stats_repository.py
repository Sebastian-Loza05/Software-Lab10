from poke_stats.db.client import query

_COLUMNS = (
    "id, name, hp, attack, defense, sp_atk, sp_def, speed, "
    "type_1, type_2, total, generation, legendary"
)


async def get_by_name(name: str) -> dict | None:
    rows = await query(
        f"SELECT {_COLUMNS} FROM pokemon_stats WHERE name = ?",
        [name.lower()],
    )
    return rows[0] if rows else None
