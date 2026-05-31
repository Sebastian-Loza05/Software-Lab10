"""ASCII line chart of availability or latency over time."""

from bot.chart import render_line
from bot.commands import check_availability, check_latency
from bot.modules import resolve
from bot.timeranges import from_cli


def run(args) -> int:
    module = resolve(args.module)
    days = from_cli(last=args.last, frm=args.frm, to=args.to)
    if args.metric == "latency":
        series = check_latency.compute(module, days)
        ylabel = f"{module} - latencia (ms)"
    else:
        series = check_availability.compute(module, days)
        ylabel = f"{module} - disponibilidad (%)"
    labels = [d.strftime("%d/%m") for d, _ in series]
    values = [v for _, v in series]
    print(render_line(labels, values, ylabel=ylabel))
    return 0
