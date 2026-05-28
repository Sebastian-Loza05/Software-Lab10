from fastapi import FastAPI

from poke_api.api.routes import health, pokemon

app = FastAPI(title="POKE_API")

app.include_router(health.router)
app.include_router(pokemon.router)
