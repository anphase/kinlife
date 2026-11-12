"""Pure Kinlife simulation: no I/O, no terminal, no global state.

A grid is a tuple of equal-length strings. ``DEAD`` ('.') is an empty cell and
every other character is a live cell whose character is its species.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass

DEAD = "."
# A dying cell in Brian's Brain. It has no species and counts as no neighbour.
DYING = "~"

Grid = tuple[str, ...]


@dataclass(frozen=True)
class Rule:
    """A birth/survival rule over the eight neighbours, or Brian's Brain.

    ``birth`` and ``survive`` are the live-neighbour counts at which an empty
    cell is born and a live cell survives. A ``brain`` rule has three states
    (empty, live, dying): a live cell always becomes dying, a dying cell
    becomes empty, and an empty cell is born by ``birth``; ``survive`` is unused.
    """

    name: str
    birth: frozenset[int]
    survive: frozenset[int]
    brain: bool = False


RULES: dict[str, Rule] = {
    rule.name: rule
    for rule in (
        Rule("life", frozenset({3}), frozenset({2, 3})),
        Rule("highlife", frozenset({3, 6}), frozenset({2, 3})),
        Rule(
            "daynight",
            frozenset({3, 6, 7, 8}),
            frozenset({3, 4, 6, 7, 8}),
        ),
        Rule("brain", frozenset({2}), frozenset(), brain=True),
    )
}
LIFE = RULES["life"]


class SeedError(ValueError):
    """Raised when seed text is not a valid Kinlife grid."""


def parse_seed(text: str) -> Grid:
    """Parse seed text into a grid.

    '.' and any whitespace are empty cells; any other printable character is a
    species. Control and invisible characters (escape, bell, bidi overrides)
    are rejected so a seed file cannot drive the terminal it is shown on.
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
        for column, ch in enumerate(line, start=1):
            if not ch.isprintable():
                raise SeedError(
                    f"Seed has an unprintable character at line {number}, "
                    f"column {column}: U+{ord(ch):04X}."
                )
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
    del counts[DYING]
    return counts


def _live_neighbours(grid: Grid, row: int, col: int, wrap: bool) -> list[str]:
    rows, cols = len(grid), len(grid[0])
    # Keyed by coordinate, so that on a torus only one or two cells wide a
    # neighbour reached by wrapping in two directions is counted once, and a cell
    # is never its own neighbour.
    seen: dict[tuple[int, int], None] = {}
    for d_row in (-1, 0, 1):
        for d_col in (-1, 0, 1):
            r, c = row + d_row, col + d_col
            if wrap:
                r, c = r % rows, c % cols
            elif not (0 <= r < rows and 0 <= c < cols):
                continue
            seen[r, c] = None
    seen.pop((row, col), None)
    return [grid[r][c] for r, c in seen if grid[r][c] not in (DEAD, DYING)]


def _inherit(parents: list[str], rng: random.Random) -> str:
    """Species of a newborn: the species with most parents, a tie broken at random."""
    counts = Counter(parents)
    top = max(counts.values())
    leaders = [species for species, n in counts.items() if n == top]
    return leaders[0] if len(leaders) == 1 else rng.choice(leaders)


def step(
    grid: Grid,
    *,
    wrap: bool = False,
    rng: random.Random | None = None,
    rule: Rule = LIFE,
) -> Grid:
    """Return the next generation under ``rule`` (Conway's Life by default).

    A live cell survives when its live-neighbour count is in ``rule.survive``
    and dies otherwise. An empty cell whose count is in ``rule.birth`` is born
    with the species most common among its parents, or one of the tied species
    chosen with ``rng``. With ``wrap`` the edges join up (a torus); otherwise
    cells beyond the edge are empty. Brian's Brain: see ``Rule``.
    """
    if not grid or not grid[0]:
        return grid
    rng = rng or random.Random()
    new_rows: list[str] = []
    for row, line in enumerate(grid):
        cells: list[str] = []
        for col, cell in enumerate(line):
            neighbours = _live_neighbours(grid, row, col, wrap)
            if cell == DYING:
                cells.append(DEAD)
            elif cell != DEAD and rule.brain:
                cells.append(DYING)
            elif cell != DEAD:
                cells.append(cell if len(neighbours) in rule.survive else DEAD)
            elif len(neighbours) in rule.birth:
                cells.append(_inherit(neighbours, rng))
            else:
                cells.append(DEAD)
        new_rows.append("".join(cells))
    return tuple(new_rows)


class Simulation:
    """A grid plus the settings and random state needed to advance it."""

    def __init__(
        self,
        grid: Grid,
        *,
        wrap: bool = False,
        seed: int | None = None,
        rule: Rule = LIFE,
    ) -> None:
        self.grid = grid
        self.rule = rule
        self.wrap = wrap
        self.generation = 0
        self._rng = random.Random(seed)

    @property
    def population(self) -> Counter[str]:
        return population(self.grid)

    def step(self) -> None:
        self.grid = step(self.grid, wrap=self.wrap, rng=self._rng, rule=self.rule)
        self.generation += 1
