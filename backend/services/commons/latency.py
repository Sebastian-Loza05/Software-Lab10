"""Block-level latency instrumentation (event_type=block).

Use the context manager around a hot internal block (an external HTTP call, a
DB query) to measure just that block, separate from the request total emitted
by the middleware. The difference between the two is what reveals bottlenecks
for part 2's analysis.

    with latency_block("pokeapi_external_call"):
        ...

The module and request_id are read from the request context, so the block log
correlates with its parent request automatically.
"""

import asyncio
import time
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Iterator

from commons.context import get_module, get_request_id
from commons.logger import get_logger


@contextmanager
def latency_block(name: str, function: str | None = None) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        module = get_module() or "unknown"
        get_logger(module).log(
            level="INFO",
            api=name,
            function=function or name,
            message="Block completed",
            event_type="block",
            request_id=get_request_id(),
            duration_ms=duration_ms,
        )


def measure(name: str | None = None) -> Callable:
    """Decorator form of latency_block. Works on sync and async functions."""

    def decorator(fn: Callable) -> Callable:
        block_name = name or fn.__name__

        if asyncio.iscoroutinefunction(fn):
            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                with latency_block(block_name, fn.__name__):
                    return await fn(*args, **kwargs)
            return async_wrapper

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            with latency_block(block_name, fn.__name__):
                return fn(*args, **kwargs)
        return sync_wrapper

    return decorator
