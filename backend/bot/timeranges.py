"""Parse the CLI's time-range arguments into a list of dates."""

import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Lima")

_LAST_RE = re.compile(r"^-?last[-_]?(\d+)(d|h|days?|hours?)$", re.IGNORECASE)
_SHORT_RE = re.compile(r"^(\d+)(d|h)$", re.IGNORECASE)


def today() -> date:
    return datetime.now(TZ).date()


def parse_last(token: str) -> int:
    """Number of days covered by a relative token like '5d', '24h', 'Last5Days'."""
    m = _LAST_RE.match(token) or _SHORT_RE.match(token)
    if not m:
        raise ValueError(f"Cannot parse relative range '{token}'")
    n = int(m.group(1))
    unit = m.group(2).lower()
    if unit.startswith("h"):
        return max(1, (n + 23) // 24)
    return n


def parse_date(token: str) -> date:
    """Accept 'YYYY-MM-DD', 'DD/MM' or 'DD/MM/YYYY'."""
    token = token.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", token):
        return date.fromisoformat(token)
    parts = token.split("/")
    if len(parts) == 2:
        d, m = int(parts[0]), int(parts[1])
        return date(today().year, m, d)
    if len(parts) == 3:
        d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
        if y < 100:
            y += 2000
        return date(y, m, d)
    raise ValueError(f"Cannot parse date '{token}' (use DD/MM or YYYY-MM-DD)")


def daterange(start: date, end: date) -> list[date]:
    if end < start:
        raise ValueError("--from must be on or before --to")
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def from_cli(*, last: str | None, frm: str | None, to: str | None) -> list[date]:
    if last:
        n_days = parse_last(last)
        end = today()
        start = end - timedelta(days=n_days - 1)
        return daterange(start, end)
    if frm:
        start = parse_date(frm)
        end = parse_date(to) if to else today()
        return daterange(start, end)
    if to and not frm:
        raise ValueError("--to needs --from (or use --last)")
    return [today()]
