from fastapi import FastAPI

from commons.middleware import LoggingMiddleware
from poke_stats.api.routes import health, stats

app = FastAPI(title="POKE_STATS")
app.add_middleware(LoggingMiddleware, module="poke-stats")

app.include_router(health.router)
app.include_router(stats.router)
