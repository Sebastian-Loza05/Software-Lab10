from fastapi import FastAPI

from commons.middleware import LoggingMiddleware
from search_api.api.routes import health, search

app = FastAPI(title="SEARCH_API")
app.add_middleware(LoggingMiddleware, module="search-api")

app.include_router(health.router)
app.include_router(search.router)
