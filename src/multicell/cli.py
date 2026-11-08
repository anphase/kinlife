"""``multicell``: run a seed file."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

from multicell import __version__
from multicell.engine import SeedError, Simulation, pad, parse_seed
from multicell.render import run_plain
from multicell.ui import Session, run_curses

PADDING = 5
INTERVAL = 0.05
GENERATIONS = 50


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multicell",
        description="Run Conway's Game of Life with species from a seed file.",
    )
    parser.add_argument("seed_file", type=Path, help="seed file to run")
    parser.add_argument(
        "-p",
        "--padding",
        type=int,
        help=f"empty cells added around the seed (default {PADDING}, or 0 with --wrap)",
    )
    parser.add_argument(
        "-t",
        "--time-interval",
        type=float,
        default=INTERVAL,
        metavar="SECONDS",
        help=f"time between generations (default {INTERVAL})",
    )
    parser.add_argument(
        "--wrap",
        action="store_true",
        help="join opposite edges into a torus instead of treating them as walls",
    )
    parser.add_argument(
        "--rng-seed",
        type=int,
        metavar="N",
        help="seed the random tie-break so a run is reproducible",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="print frames instead of using the full-screen UI",
    )
    parser.add_argument(
        "-n",
        "--generations",
        type=int,
        default=GENERATIONS,
        help=f"generations to print in plain mode (default {GENERATIONS})",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def _error(message: str) -> int:
    print(f"multicell: {message}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    padding = (
        args.padding if args.padding is not None else (0 if args.wrap else PADDING)
    )
    if padding < 0:
        return _error("--padding must not be negative.")
    if args.time_interval < 0:
        return _error("--time-interval must not be negative.")
    if args.generations < 0:
        return _error("--generations must not be negative.")
    try:
        text = args.seed_file.read_text()
    except OSError as exc:
        return _error(f"cannot read {args.seed_file}: {exc.strerror}")
    try:
        start = pad(parse_seed(text), padding)
    except SeedError as exc:
        return _error(f"{args.seed_file}: {exc}")

    def make_sim() -> Simulation:
        return Simulation(start, wrap=args.wrap, seed=args.rng_seed)

    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    if not args.plain and interactive and importlib.util.find_spec("curses"):
        run_curses(Session(make_sim, args.time_interval))  # pragma: no cover
    else:
        run_plain(
            make_sim(),
            args.generations,
            args.time_interval,
            sys.stdout,
            live=interactive,
        )
    return 0
