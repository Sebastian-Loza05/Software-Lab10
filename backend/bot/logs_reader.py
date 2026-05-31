"""Read JSONL logs produced by commons/logger.py."""

import json
from datetime import date
from pathlib import Path
from typing import Iterator

LOG_ROOT = Path(__file__).resolve().parent.parent / "logs"


def _file_for(module: str, day: date) -> Path:
    return LOG_ROOT / module / f"{day.isoformat()}.jsonl"


def iter_lines(module: str, days: list[date]) -> Iterator[dict]:
    for day in days:
        path = _file_for(module, day)
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def iter_requests(module: str, days: list[date]) -> Iterator[dict]:
    for entry in iter_lines(module, days):
        if entry.get("event_type") == "request" and entry.get("http_status") is not None:
            yield entry
