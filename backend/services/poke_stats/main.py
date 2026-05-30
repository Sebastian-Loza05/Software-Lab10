from fastapi import FastAPI

from poke_stats.api.routes import health, stats

app = FastAPI(title="POKE_STATS")

app.include_router(health.router)
app.include_router(stats.router)
