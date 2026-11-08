"""Plain-text rendering, used when curses is unavailable or output is piped."""

from __future__ import annotations

import time
from collections import Counter
from typing import TextIO

from kinlife.engine import DEAD, Grid, Simulation

CLEAR = "\x1b[H\x1b[J"


def ordered_population(counts: Counter[str]) -> list[tuple[str, int]]:
    """``(species, count)`` pairs, largest population first."""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def population_text(counts: Counter[str]) -> str:
    """``A=12 B=30``, largest population first; ``extinct`` when empty."""
    if not counts:
        return "extinct"
    return " ".join(f"{species}={n}" for species, n in ordered_population(counts))


def frame(grid: Grid) -> str:
    """The grid in a box, with empty cells shown as spaces."""
    width = len(grid[0]) if grid else 0
    edge = "+" + "-" * width + "+"
    body = ["|" + row.replace(DEAD, " ") + "|" for row in grid]
    return "\n".join([edge, *body, edge])


def run_plain(
    sim: Simulation,
    generations: int,
    interval: float,
    out: TextIO,
    *,
    live: bool,
) -> None:
    """Print ``generations`` steps of ``sim``.

    With ``live`` (an interactive terminal) each frame replaces the last and
    frames are paced by ``interval``; otherwise frames are simply appended.
    """
    for number in range(generations + 1):
        if number:
            sim.step()
        header = f"Generation {sim.generation}  {population_text(sim.population)}"
        out.write((CLEAR if live else "") + header + "\n" + frame(sim.grid) + "\n")
        out.flush()
        if live and number < generations:
            time.sleep(interval)
