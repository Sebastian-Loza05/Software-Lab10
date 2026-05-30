from fastapi import FastAPI

from poke_images.api.routes import health, images

app = FastAPI(title="POKE_IMAGES")

app.include_router(health.router)
app.include_router(images.router)
