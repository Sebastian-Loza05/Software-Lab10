from poke_api.db.client import query


async def check_connection() -> bool:
    try:
        await query("SELECT 1")
        return True
    except Exception:
        return False
