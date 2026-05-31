"""Tiny ASCII line chart, no external deps."""

HEIGHT = 12
LABEL_WIDTH = 8


def render_line(labels: list[str], values: list[float | None], ylabel: str = "") -> str:
    clean = [v for v in values if v is not None]
    if not clean:
        return "(no data)"

    vmin, vmax = min(clean), max(clean)
    if vmin == vmax:
        delta = max(abs(vmin) * 0.05, 1.0)
        vmin, vmax = vmin - delta, vmax + delta
    span = vmax - vmin

    def row_for(v: float | None) -> int:
        if v is None:
            return -1
        return round((v - vmin) / span * (HEIGHT - 1))

    rows = [row_for(v) for v in values]
    width = len(values)
    grid = [[" "] * width for _ in range(HEIGHT)]
    for i, r in enumerate(rows):
        if r < 0:
            continue
        if i > 0 and rows[i - 1] >= 0:
            lo, hi = sorted((rows[i - 1], r))
            for rr in range(lo + 1, hi):
                if grid[HEIGHT - 1 - rr][i] == " ":
                    grid[HEIGHT - 1 - rr][i] = "·"
        grid[HEIGHT - 1 - r][i] = "•"

    out: list[str] = []
    if ylabel:
        out.append(ylabel)
    for r, row in enumerate(grid):
        if r == 0:
            prefix = f"{vmax:>{LABEL_WIDTH-1}.1f}┤"
        elif r == HEIGHT - 1:
            prefix = f"{vmin:>{LABEL_WIDTH-1}.1f}┤"
        elif r == HEIGHT // 2:
            prefix = f"{(vmax+vmin)/2:>{LABEL_WIDTH-1}.1f}┤"
        else:
            prefix = " " * (LABEL_WIDTH - 1) + "│"
        out.append(prefix + "".join(row))
    out.append(" " * (LABEL_WIDTH - 1) + "└" + "─" * width)

    if labels:
        out.append(_x_axis_labels(labels, width))
    return "\n".join(out)


def _x_axis_labels(labels: list[str], width: int) -> str:
    """One char per row per column, read top-down. Avoids overlap on narrow charts."""
    max_len = max(len(l) for l in labels)
    rows: list[str] = []
    for k in range(max_len):
        row = " " * LABEL_WIDTH
        for lbl in labels:
            row += lbl[k] if k < len(lbl) else " "
        rows.append(row)
    return "\n".join(rows)
