import httpx

from poke_stats.core.config import settings


def _to_hrana(value: object) -> dict:
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "integer", "value": str(int(value))}
    if isinstance(value, int):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    return {"type": "text", "value": str(value)}


def _from_hrana(cell: dict) -> object:
    kind = cell.get("type")
    raw = cell.get("value")
    if kind == "null":
        return None
    if kind == "integer":
        return int(raw)
    if kind == "float":
        return float(raw)
    return raw


async def query(sql: str, params: list | None = None) -> list[dict]:
    body = {
        "requests": [
            {
                "type": "execute",
                "stmt": {
                    "sql": sql,
                    "args": [_to_hrana(p) for p in (params or [])],
                },
            },
            {"type": "close"},
        ]
    }
    headers = {"Authorization": f"Bearer {settings.turso_auth_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            settings.turso_pipeline_url, headers=headers, json=body
        )
    response.raise_for_status()
    payload = response.json()

    exec_result = payload["results"][0]
    if exec_result.get("type") == "error":
        raise RuntimeError(exec_result.get("error"))
    result = exec_result["response"]["result"]
    cols = [c["name"] for c in result["cols"]]
    return [
        {col: _from_hrana(cell) for col, cell in zip(cols, row)}
        for row in result["rows"]
    ]
