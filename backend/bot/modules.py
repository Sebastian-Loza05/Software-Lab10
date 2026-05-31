"""User-facing module names mapped to the canonical names emitted by the services."""

KNOWN_MODULES = ("poke-api", "poke-stats", "poke-images", "search-api")

_ALIASES: dict[str, str] = {
    "pokeapi": "poke-api",
    "poke-api": "poke-api",
    "poke_api": "poke-api",
    "pokestats": "poke-stats",
    "poke-stats": "poke-stats",
    "poke_stats": "poke-stats",
    "pokeimage": "poke-images",
    "pokeimages": "poke-images",
    "poke-images": "poke-images",
    "poke_images": "poke-images",
    "searchapi": "search-api",
    "search-api": "search-api",
    "search_api": "search-api",
}


def resolve(name: str) -> str:
    key = name.strip().lower()
    if key in _ALIASES:
        return _ALIASES[key]
    raise ValueError(
        f"Unknown module '{name}'. Valid modules: {', '.join(KNOWN_MODULES)}"
    )
