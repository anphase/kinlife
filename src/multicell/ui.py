"""Interactive terminal UI: a curses front end over a UI-free ``Session``."""

from __future__ import annotations

import contextlib
import time
from collections.abc import Callable
from typing import Any

from multicell.engine import DEAD, Simulation
from multicell.render import ordered_population

MIN_INTERVAL = 0.005
MAX_INTERVAL = 2.0
SPEED_FACTOR = 1.5

HELP = "space/p pause  s step  +/- speed  r restart  w wrap on/off  q quit"


class Session:
    """Playback state and key handling, independent of any terminal."""

    def __init__(self, make_sim: Callable[[], Simulation], interval: float) -> None:
        self._make_sim = make_sim
        self.sim = make_sim()
        self.interval = min(max(interval, MIN_INTERVAL), MAX_INTERVAL)
        self.paused = False
        self.quit = False

    def tick(self) -> None:
        """Advance one generation if running."""
        if not self.paused:
            self.sim.step()

    def handle(self, key: str) -> None:
        if key in ("q", "Q"):
            self.quit = True
        elif key in (" ", "p", "P"):
            self.paused = not self.paused
        elif key in ("s", "S"):
            self.paused = True
            self.sim.step()
        elif key in ("+", "="):
            self.interval = max(MIN_INTERVAL, self.interval / SPEED_FACTOR)
        elif key in ("-", "_"):
            self.interval = min(MAX_INTERVAL, self.interval * SPEED_FACTOR)
        elif key in ("r", "R"):
            self.sim = self._make_sim()
        elif key in ("w", "W"):
            self.sim.wrap = not self.sim.wrap

    def status(self) -> str:
        state = "paused" if self.paused else "running"
        edges = "wrap" if self.sim.wrap else "bounded"
        return (
            f"Generation {self.sim.generation}  {state}  "
            f"{self.interval:.3f}s/gen  edges: {edges}"
        )


def run_curses(session: Session) -> bool:  # pragma: no cover - needs a terminal
    """Run ``session`` full screen; False if curses cannot run here.

    curses.wrapper restores the terminal on exit.
    """
    try:
        import curses
    except ImportError:  # Python built without the _curses extension
        return False

    def loop(screen: Any) -> None:
        # Not every terminal can hide the cursor.
        with contextlib.suppress(curses.error):
            curses.curs_set(0)
        palette = _init_colours()
        styles: dict[str, int] = {}
        next_step = time.monotonic()
        while not session.quit:
            _draw(screen, session, palette, styles)
            if session.paused:
                screen.timeout(-1)
            else:
                wait = max(0.0, next_step - time.monotonic())
                screen.timeout(int(wait * 1000))
            key = screen.getch()
            if 0 <= key < 256:
                was_paused = session.paused
                session.handle(chr(key))
                if was_paused and not session.paused:
                    next_step = time.monotonic()
            if not session.paused and time.monotonic() >= next_step:
                session.tick()
                next_step = time.monotonic() + session.interval

    try:
        with contextlib.suppress(KeyboardInterrupt):
            curses.wrapper(loop)
    except curses.error:  # unknown or too-limited TERM
        return False
    return True


def _init_colours() -> list[int]:  # pragma: no cover - needs a terminal
    import curses

    if not curses.has_colors():
        return [0]
    curses.start_color()
    curses.use_default_colors()
    colours = [
        curses.COLOR_RED,
        curses.COLOR_GREEN,
        curses.COLOR_YELLOW,
        curses.COLOR_BLUE,
        curses.COLOR_MAGENTA,
        curses.COLOR_CYAN,
    ]
    attrs = []
    for number, colour in enumerate(colours, start=1):
        curses.init_pair(number, colour, -1)
        attrs.append(curses.color_pair(number))
    return attrs + [a | curses.A_BOLD for a in attrs]


def _wrap_words(words: list[str], width: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in words:
        if line and len(line) + 2 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line}  {word}" if line else word
    return [*lines, line]


def _draw(
    win: Any, session: Session, palette: list[int], styles: dict[str, int]
) -> None:  # pragma: no cover - needs a terminal
    import curses

    win.erase()
    height, width = win.getmaxyx()

    def put(y: int, x: int, text: str, attr: int = 0) -> None:
        # Clip to the line instead of letting curses wrap into the next row;
        # writing the bottom-right cell raises, which is harmless.
        room = width - x
        if y >= height or room <= 0:
            return
        with contextlib.suppress(curses.error):
            win.addnstr(y, x, text, room, attr)

    grid = session.sim.grid
    counts = session.sim.population
    for species in sorted(counts):
        styles.setdefault(species, len(styles))

    def attr_for(species: str) -> int:
        return palette[styles[species] % len(palette)]

    # Header: status, then the population legend wrapped to the window width.
    put(0, 0, session.status())
    x, y = 0, 1
    ordered = ordered_population(counts)
    if not ordered:
        put(y, 0, "extinct")
    for species, n in ordered:
        token = f"{species}={n}"
        if x and x + len(token) > width:
            x, y = 0, y + 1
        put(y, x, token, attr_for(species))
        x += len(token) + 2
    top = y + 2

    help_lines = _wrap_words(HELP.split("  "), width)
    for offset, text in enumerate(reversed(help_lines)):
        put(height - 1 - offset, 0, text)

    # Grid, cropped to the room available (and say so when it is).
    room_rows = max(0, height - top - len(help_lines) - 1)
    room_cols = max(0, width - 2)
    rows, cols = len(grid), len(grid[0]) if grid else 0
    if rows > room_rows or cols > room_cols:
        put(
            top - 1,
            0,
            f"Showing {min(rows, room_rows)}x{min(cols, room_cols)} of "
            f"{rows}x{cols}; enlarge the window to see more.",
        )
    for r, row in enumerate(grid[:room_rows]):
        put(top + r, 0, "|")
        for c, ch in enumerate(row[:room_cols]):
            if ch != DEAD:
                put(top + r, 1 + c, ch, attr_for(ch) | curses.A_BOLD)
    win.refresh()
