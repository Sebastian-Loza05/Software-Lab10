"""Per-request context shared across the logging helpers.

The LoggingMiddleware binds ``request_id`` and ``module`` at the start of each
request; the logger and latency_block read them automatically so call sites
never have to thread them through. asyncio.gather child tasks copy the current
context at creation, so blocks spawned by gather (e.g. the gateway's parallel
downstream calls) still see these values.
"""

import uuid
from contextvars import ContextVar

REQUEST_ID_HEADER = "X-Request-ID"

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_module: ContextVar[str | None] = ContextVar("module", default=None)


def new_request_id() -> str:
    return str(uuid.uuid4())


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(value: str) -> None:
    _request_id.set(value)


def get_module() -> str | None:
    return _module.get()


def set_module(value: str) -> None:
    _module.set(value)
