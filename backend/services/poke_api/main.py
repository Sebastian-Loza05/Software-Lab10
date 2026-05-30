from fastapi import FastAPI

from commons.middleware import LoggingMiddleware
from poke_api.api.routes import health, pokemon

app = FastAPI(title="POKE_API")
app.add_middleware(LoggingMiddleware, module="poke-api")

app.include_router(health.router)
app.include_router(pokemon.router)
