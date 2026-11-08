"""Pure Multicell simulation: no I/O, no terminal, no global state.

A grid is a tuple of equal-length strings. ``DEAD`` ('.') is an empty cell and
every other character is a live cell whose character is its species.
"""

from __future__ import annotations

import random
from collections import Counter

DEAD = "."

Grid = tuple[str, ...]


class SeedError(ValueError):
    """Raised when seed text is not a valid Multicell grid."""


def parse_seed(text: str) -> Grid:
    """Parse seed text into a grid.

    '.' and any whitespace are empty cells; any other character is a species.
    Trailing blank lines (empty or only spaces) are ignored. Every row must
    have the same width.
    """
    raw = text.splitlines()
    while raw and not raw[-1].strip():
        raw.pop()
    lines = ["".join(DEAD if ch.isspace() else ch for ch in line) for line in raw]
    if not lines:
        raise SeedError("Seed is empty: it has no rows.")
    width = len(lines[0])
    for number, line in enumerate(lines, start=1):
        if len(line) != width:
            raise SeedError(
                f"Seed is not rectangular: line {number} has {len(line)} "
                f"columns, expected {width}."
            )
    return tuple(lines)


def blank(rows: int, cols: int) -> Grid:
    """A grid of ``rows`` x ``cols`` empty cells."""
    if rows < 0 or cols < 0:
        raise ValueError("rows and cols must not be negative.")
    return (DEAD * cols,) * rows


def pad(grid: Grid, margin: int) -> Grid:
    """Surround ``grid`` with ``margin`` empty cells on every side."""
    if margin < 0:
        raise ValueError("margin must not be negative.")
    if margin == 0 or not grid:
        return grid
    side = DEAD * margin
    edge = DEAD * (len(grid[0]) + 2 * margin)
    return (
        (edge,) * margin + tuple(side + row + side for row in grid) + (edge,) * margin
    )


def population(grid: Grid) -> Counter[str]:
    """Number of live cells of each species."""
    counts: Counter[str] = Counter()
    for row in grid:
        counts.update(row)
    del counts[DEAD]
    return counts


def _live_neighbours(grid: Grid, row: int, col: int, wrap: bool) -> list[str]:
    rows, cols = len(grid), len(grid[0])
    # A set, so that on a torus only one or two cells wide a neighbour reached
    # by wrapping in two directions is counted once, and a cell is never its
    # own neighbour.
    seen: set[tuple[int, int]] = set()
    for d_row in (-1, 0, 1):
        for d_col in (-1, 0, 1):
            r, c = row + d_row, col + d_col
            if wrap:
                r, c = r % rows, c % cols
            elif not (0 <= r < rows and 0 <= c < cols):
                continue
            seen.add((r, c))
    seen.discard((row, col))
    return [grid[r][c] for r, c in sorted(seen) if grid[r][c] != DEAD]


def _inherit(parents: list[str], rng: random.Random) -> str:
    """Species of a newborn: the majority of its three parents, else random."""
    species, count = Counter(parents).most_common(1)[0]
    return species if count >= 2 else rng.choice(parents)


def step(grid: Grid, *, wrap: bool = False, rng: random.Random | None = None) -> Grid:
    """Return the next generation.

    A live cell survives with 2 or 3 live neighbours and dies otherwise. An
    empty cell with exactly 3 live neighbours is born with the majority species
    of those three, or a species chosen with ``rng`` when all three differ. With
    ``wrap`` the edges join up (a torus); otherwise cells beyond the edge are
    empty.
    """
    if not grid or not grid[0]:
        return grid
    rng = rng or random.Random()
    new_rows: list[str] = []
    for row, line in enumerate(grid):
        cells: list[str] = []
        for col, cell in enumerate(line):
            neighbours = _live_neighbours(grid, row, col, wrap)
            if cell != DEAD:
                cells.append(cell if len(neighbours) in (2, 3) else DEAD)
            elif len(neighbours) == 3:
                cells.append(_inherit(neighbours, rng))
            else:
                cells.append(DEAD)
        new_rows.append("".join(cells))
    return tuple(new_rows)


class Simulation:
    """A grid plus the settings and random state needed to advance it."""

    def __init__(
        self, grid: Grid, *, wrap: bool = False, seed: int | None = None
    ) -> None:
        self.grid = grid
        self.wrap = wrap
        self.generation = 0
        self._rng = random.Random(seed)

    @property
    def population(self) -> Counter[str]:
        return population(self.grid)

    def step(self) -> None:
        self.grid = step(self.grid, wrap=self.wrap, rng=self._rng)
        self.generation += 1
