"""Daily average request latency (ms)."""

from datetime import date

from bot.logs_reader import iter_requests
from bot.modules import resolve
from bot.timeranges import from_cli


def compute(module: str, days: list[date]) -> list[tuple[date, float | None]]:
    bucket: dict[date, list[float]] = {d: [] for d in days}
    for entry in iter_requests(module, days):
        day = date.fromisoformat(entry["timestamp"][:10])
        if day not in bucket:
            continue
        ms = entry.get("duration_ms")
        if ms is not None:
            bucket[day].append(float(ms))
    return [(d, (sum(v) / len(v)) if v else None) for d, v in bucket.items()]


def run(args) -> int:
    module = resolve(args.module)
    days = from_cli(last=args.last, frm=args.frm, to=args.to)
    for day, avg in compute(module, days):
        label = day.strftime("%d/%m")
        print(f"{label} N/A" if avg is None else f"{label} {int(round(avg))}ms")
    return 0
