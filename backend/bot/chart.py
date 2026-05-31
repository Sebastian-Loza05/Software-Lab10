"""Tiny ASCII scatter chart (one dot per data point), no external deps."""

HEIGHT = 12
COL_WIDTH = 6  # chars per data-point column — leaves room for a horizontal DD/MM label
LABEL_WIDTH = 8


def render_line(
    labels: list[str],
    values: list[float | None],
    ylabel: str = "",
    value_labels: list[str] | None = None,
) -> str:
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

    n = len(values)
    chart_width = n * COL_WIDTH
    grid = [[" "] * chart_width for _ in range(HEIGHT)]
    for i, v in enumerate(values):
        r = row_for(v)
        if r < 0:
            continue
        col = i * COL_WIDTH + COL_WIDTH // 2
        grid[HEIGHT - 1 - r][col] = "•"

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
    out.append(" " * (LABEL_WIDTH - 1) + "└" + "─" * chart_width)

    if labels:
        out.append(_centered_row(labels, chart_width))
    if value_labels:
        out.append(_centered_row(value_labels, chart_width))
    return "\n".join(out)


def _centered_row(items: list[str], chart_width: int) -> str:
    """One label per data column, centered in its COL_WIDTH slot."""
    line = [" "] * (LABEL_WIDTH + chart_width)
    for i, txt in enumerate(items):
        col_center = LABEL_WIDTH + i * COL_WIDTH + COL_WIDTH // 2
        start = col_center - len(txt) // 2
        for j, ch in enumerate(txt):
            pos = start + j
            if 0 <= pos < len(line):
                line[pos] = ch
    return "".join(line).rstrip()
