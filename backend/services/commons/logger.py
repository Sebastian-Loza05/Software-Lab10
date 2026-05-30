"""Structured JSONL logger shared by all services.

Writes one JSON object per line to ``logs/{module}/{YYYY-MM-DD}.jsonl`` (the
source of truth for the part-2 bot) and mirrors a human-readable line to the
console in the literal format required by the assignment:

    [2026-05-27T14:23:11.482-05:00][poke-stats][/stats/{name}][get_stats] Request completed (200, 42.7ms)
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# services/commons/logger.py -> services -> backend (holds logs/ and data/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_ROOT = PROJECT_ROOT / "logs"
TZ = ZoneInfo("America/Lima")


class StructuredLogger:
    def __init__(self, module: str) -> None:
        self.module = module
        self._dir = LOG_ROOT / module
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _file_for(self, now: datetime) -> Path:
        return self._dir / f"{now:%Y-%m-%d}.jsonl"

    def log(
        self,
        *,
        level: str,
        api: str,
        function: str,
        message: str,
        event_type: str,
        request_id: str | None = None,
        http_status: int | None = None,
        duration_ms: float | None = None,
        **extra: object,
    ) -> None:
        now = datetime.now(TZ)
        entry: dict[str, object] = {
            "timestamp": now.isoformat(timespec="milliseconds"),
            "module": self.module,
            "api": api,
            "function": function,
            "level": level,
            "message": message,
            "request_id": request_id,
            "http_status": http_status,
            "duration_ms": duration_ms,
            "event_type": event_type,
        }
        if extra:
            entry.update(extra)

        line = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            with self._file_for(now).open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        self._to_console(entry)

    @staticmethod
    def _to_console(e: dict[str, object]) -> None:
        if e["event_type"] == "request" and e["http_status"] is not None:
            suffix = f" ({e['http_status']}, {e['duration_ms']}ms)"
        elif e["duration_ms"] is not None:
            suffix = f" ({e['duration_ms']}ms)"
        else:
            suffix = ""
        print(
            f"[{e['timestamp']}][{e['module']}][{e['api']}][{e['function']}] "
            f"{e['message']}{suffix}",
            flush=True,
        )


_loggers: dict[str, StructuredLogger] = {}
_loggers_lock = threading.Lock()


def get_logger(module: str) -> StructuredLogger:
    """Return a process-wide cached logger for ``module``."""
    with _loggers_lock:
        logger = _loggers.get(module)
        if logger is None:
            logger = StructuredLogger(module)
            _loggers[module] = logger
        return logger
