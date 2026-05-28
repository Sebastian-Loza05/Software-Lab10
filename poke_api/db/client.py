import httpx

from poke_api.core.config import settings


async def query(sql: str, params: list | None = None) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            settings.turso_url,
            headers={"Authorization": f"Bearer {settings.turso_token}"},
            json={
                "requests": [
                    {"type": "execute", "stmt": {"sql": sql, "args": params or []}},
                    {"type": "close"},
                ]
            },
        )
    response.raise_for_status()
    return response.json()
