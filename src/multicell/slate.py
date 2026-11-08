"""``multicell-slate``: write a blank seed file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from multicell.engine import blank

OUT_FILE = "seed.txt"
ROWS = 35
COLS = 100


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multicell-slate", description="Write a blank Multicell seed file."
    )
    parser.add_argument("-o", "--out", default=OUT_FILE, metavar="FILE")
    parser.add_argument("-r", "--rows", type=int, default=ROWS)
    parser.add_argument("-c", "--cols", type=int, default=COLS)
    parser.add_argument(
        "-f", "--force", action="store_true", help="overwrite without asking"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.rows < 0 or args.cols < 0:
        print(
            "multicell-slate: --rows and --cols must not be negative.", file=sys.stderr
        )
        return 2
    out = Path(args.out)
    if out.exists() and not args.force:
        try:
            answer = input(f"The file {out} already exists. Overwrite it? [Y/n] ")
        except EOFError:
            print(f"multicell-slate: {out} exists; use --force.", file=sys.stderr)
            return 1
        if answer.strip().lower() not in ("", "y", "yes"):
            return 1
    try:
        out.write_text("".join(row + "\n" for row in blank(args.rows, args.cols)))
    except OSError as exc:
        print(f"multicell-slate: cannot write {out}: {exc.strerror}", file=sys.stderr)
        return 1
    return 0
