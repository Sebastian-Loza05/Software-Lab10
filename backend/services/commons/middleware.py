"""ASGI middleware emitting one event_type=request log per HTTP request.

Captures the total response time and the final HTTP status — including 500 when
the handler raises an unhandled exception (the status is logged before the
exception propagates and FastAPI turns it into a 500 response). This is what
the bot's CheckLatency / CheckAvailability / Stats commands consume.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware

from commons.context import (
    REQUEST_ID_HEADER,
    new_request_id,
    set_module,
    set_request_id,
)
from commons.logger import get_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, module: str) -> None:
        super().__init__(app)
        self.module = module
        self.logger = get_logger(module)

    async def dispatch(self, request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or new_request_id()
        set_request_id(request_id)
        set_module(self.module)

        start = time.perf_counter()
        status = 500  # assume failure until the handler returns a response
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            route = request.scope.get("route")
            api = getattr(route, "path", None) or request.url.path
            function = getattr(getattr(route, "endpoint", None), "__name__", request.method)
            self.logger.log(
                level="INFO" if status < 500 else "ERROR",
                api=api,
                function=function,
                message="Request completed",
                event_type="request",
                request_id=request_id,
                http_status=status,
                duration_ms=duration_ms,
            )
