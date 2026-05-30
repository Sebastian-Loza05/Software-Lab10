from fastapi import FastAPI

from commons.middleware import LoggingMiddleware
from poke_images.api.routes import health, images

app = FastAPI(title="POKE_IMAGES")
app.add_middleware(LoggingMiddleware, module="poke-images")

app.include_router(health.router)
app.include_router(images.router)
