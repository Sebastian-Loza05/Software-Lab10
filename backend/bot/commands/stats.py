"""General stats over a window."""

import statistics
from collections import Counter

from bot.logs_reader import iter_requests
from bot.modules import resolve
from bot.timeranges import from_cli


def run(args) -> int:
    module = resolve(args.module)
    days = from_cli(last=args.last, frm=args.frm, to=args.to)

    durations: list[float] = []
    status_counts: Counter[int] = Counter()
    failing_by_api: Counter[str] = Counter()

    for entry in iter_requests(module, days):
        durations.append(float(entry["duration_ms"]))
        status = int(entry["http_status"])
        status_counts[status] += 1
        if status >= 500:
            failing_by_api[entry.get("api") or "<unknown>"] += 1

    total = sum(status_counts.values())
    if total == 0:
        print(f"No requests for {module} in the selected range.")
        return 0

    if len(durations) >= 20:
        p95 = statistics.quantiles(durations, n=20)[18]
    else:
        s = sorted(durations)
        p95 = s[max(0, int(round(0.95 * (len(s) - 1))))]

    minutes = len(days) * 24 * 60
    rpm = total / minutes
    errors = sum(c for s, c in status_counts.items() if 500 <= s < 600)
    error_ratio = errors / total

    if failing_by_api:
        top_api, top_count = failing_by_api.most_common(1)[0]
    else:
        top_api, top_count = "-", 0

    print(f"P95 latency:        {p95:.0f}ms")
    print(f"Requests/min:       {rpm:.2f}")
    print(f"Error ratio:        {error_ratio * 100:.2f}%")
    print(f"Throughput:         {total:,}")
    print(f"Top failing API:    {top_api} ({top_count} 5xx)")
    return 0
