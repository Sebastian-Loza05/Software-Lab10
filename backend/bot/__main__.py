"""Bot CLI entry point: python -m bot <Comando> <Modulo> [opciones]."""

import argparse
import re
import sys

from bot.commands import check_availability, check_latency, render_graph, stats

_LASTDAYS_RE = re.compile(r"^-?last(\d+)(days?|hours?|d|h)$", re.IGNORECASE)


def _preprocess(argv: list[str]) -> list[str]:
    """Translate the compact -Last5Days form into '--last 5d'."""
    out: list[str] = []
    for tok in argv:
        m = _LASTDAYS_RE.match(tok)
        if m:
            unit = "h" if m.group(2).lower().startswith("h") else "d"
            out.extend(["--last", f"{m.group(1)}{unit}"])
        else:
            out.append(tok)
    return out


def _add_time_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--last", help="Relative range: '5d', '24h', or 'Last5Days'.")
    p.add_argument("--from", dest="frm", help="Start date: DD/MM or YYYY-MM-DD.")
    p.add_argument("--to", help="End date: DD/MM or YYYY-MM-DD (default: today).")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bot")
    subs = parser.add_subparsers(dest="command", required=True)

    for name, mod in (
        ("CheckAvailability", check_availability),
        ("CheckLatency", check_latency),
        ("Stats", stats),
    ):
        sp = subs.add_parser(name, help=(mod.__doc__ or "").strip().splitlines()[0])
        sp.add_argument("module", help="Module name (e.g. PokeStats, poke-api).")
        _add_time_args(sp)
        sp.set_defaults(handler=mod.run)

    sp = subs.add_parser(
        "RenderGraph", help=(render_graph.__doc__ or "").strip().splitlines()[0]
    )
    sp.add_argument("module")
    sp.add_argument(
        "--metric", choices=("availability", "latency"), default="availability"
    )
    _add_time_args(sp)
    sp.set_defaults(handler=render_graph.run)

    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    argv = _preprocess(argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
