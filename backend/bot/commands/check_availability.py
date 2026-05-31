"""Daily availability: success_2xx / (success_2xx + error_5xx)."""

from datetime import date

from bot.logs_reader import iter_requests
from bot.modules import resolve
from bot.timeranges import from_cli


def compute(module: str, days: list[date]) -> list[tuple[date, float | None]]:
    counters: dict[date, dict[str, int]] = {d: {"ok": 0, "err": 0} for d in days}
    for entry in iter_requests(module, days):
        day = date.fromisoformat(entry["timestamp"][:10])
        if day not in counters:
            continue
        status = int(entry["http_status"])
        if 200 <= status < 300:
            counters[day]["ok"] += 1
        elif 500 <= status < 600:
            counters[day]["err"] += 1

    series: list[tuple[date, float | None]] = []
    for d in days:
        c = counters[d]
        total = c["ok"] + c["err"]
        series.append((d, (c["ok"] / total * 100) if total else None))
    return series


def run(args) -> int:
    module = resolve(args.module)
    days = from_cli(last=args.last, frm=args.frm, to=args.to)
    for day, pct in compute(module, days):
        label = day.strftime("%d/%m")
        print(f"{label} N/A" if pct is None else f"{label} {pct:.1f}%")
    return 0
