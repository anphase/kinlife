import random

import pytest

from multicell.engine import (
    DEAD,
    Grid,
    SeedError,
    Simulation,
    blank,
    pad,
    parse_seed,
    population,
    step,
)


def grid(*rows: str) -> Grid:
    return parse_seed("\n".join(rows))


def run(g: Grid, n: int, *, wrap: bool = False) -> Grid:
    for _ in range(n):
        g = step(g, wrap=wrap)
    return g


def trim(g: Grid) -> list[tuple[int, int]]:
    return sorted(
        (r, c) for r, row in enumerate(g) for c, ch in enumerate(row) if ch != DEAD
    )


# --- Conway's Life with a single species ---------------------------------


def test_block_is_still() -> None:
    g = pad(grid("XX", "XX"), 2)
    assert step(g) == g


def test_beehive_is_still() -> None:
    g = pad(grid(".XX.", "X..X", ".XX."), 2)
    assert step(g) == g


def test_blinker_period_two() -> None:
    g = pad(grid("XXX"), 2)
    one = step(g)
    assert one != g
    assert trim(one) == [(1, 3), (2, 3), (3, 3)]
    assert step(one) == g


def test_toad_period_two() -> None:
    g = pad(grid(".XXX", "XXX."), 2)
    assert step(g) != g
    assert run(g, 2) == g


def test_glider_translates_diagonally() -> None:
    g = pad(grid(".X.", "..X", "XXX"), 6)
    after = run(g, 4)
    assert after != g
    assert trim(after) == [(r + 1, c + 1) for r, c in trim(g)]


def test_lonely_cell_dies_and_crowded_cell_dies() -> None:
    assert trim(step(pad(grid("X"), 1))) == []
    plus = pad(grid(".X.", "XXX", ".X."), 1)
    # centre has four neighbours and dies
    assert step(plus)[2][2] == DEAD


def test_survival_with_two_or_three() -> None:
    assert step(grid("XXX"))[0][1] == "X"
    assert step(grid("XX", "X."))[0][0] == "X"


def test_no_birth_without_exactly_three() -> None:
    assert trim(step(pad(grid("XX"), 1))) == []


# --- inheritance -----------------------------------------------------------


def corner(a: str, b: str, c: str) -> Grid:
    """Three parents around the empty centre cell of a 3x3 grid."""
    return grid(f"{a}{b}.", f"{c}..", "...")


@pytest.mark.parametrize(
    ("parents", "expected"),
    [("AAA", "A"), ("AAB", "A"), ("ABA", "A"), ("BAA", "A"), ("BBA", "B")],
)
def test_majority_species_inherited(parents: str, expected: str) -> None:
    born = step(corner(*parents))[1][1]
    assert born == expected


def test_all_different_picks_one_of_the_parents() -> None:
    seen = {step(corner("A", "B", "C"), rng=random.Random(s))[1][1] for s in range(60)}
    assert seen == {"A", "B", "C"}


def test_tie_break_reproducible_with_seed() -> None:
    g = corner("A", "B", "C")
    first = [step(g, rng=random.Random(7))[1][1] for _ in range(5)]
    assert len(set(first)) == 1


def test_simulation_seed_reproduces_whole_run() -> None:
    seed = "\n".join(["ABC..DEF", ".G.H.I..", "..J..K..", "L..M.N.O", ".P.Q.R.."])
    runs = []
    for _ in range(2):
        sim = Simulation(pad(parse_seed(seed), 3), seed=42)
        for _ in range(10):
            sim.step()
        runs.append(sim.grid)
    assert runs[0] == runs[1]


def test_survivors_keep_their_species() -> None:
    assert step(grid("ABA"))[0][1] == "B"


# --- edges -----------------------------------------------------------------


def test_bounded_glider_ends_as_block_in_corner() -> None:
    g = grid(".X....", "..X...", "XXX...", "......", "......", "......")
    assert trim(run(g, 20)) == [(4, 4), (4, 5), (5, 4), (5, 5)]


def test_toroidal_glider_returns() -> None:
    g = grid(".X...", "..X..", "XXX..", ".....", ".....")
    assert run(g, 20, wrap=True) == g


def test_wrap_births_across_edge() -> None:
    g = grid("...X", "....", "....", "X..X")  # parents of corner (0, 0) on a torus
    assert step(g, wrap=True)[0][0] == "X"
    assert step(g)[0][0] == DEAD


# --- helpers ---------------------------------------------------------------


def test_population_counts() -> None:
    assert population(grid("AAB", "..B")) == {"A": 2, "B": 2}
    assert population(grid("...")) == {}


def test_blank_and_pad() -> None:
    assert blank(2, 3) == ("...", "...")
    assert pad(grid("X"), 1) == ("...", ".X.", "...")
    assert pad(grid("X"), 0) == ("X",)
    assert pad((), 3) == ()
    with pytest.raises(ValueError, match="negative"):
        blank(-1, 2)
    with pytest.raises(ValueError, match="negative"):
        pad(grid("X"), -1)


def test_step_of_empty_grid_is_noop() -> None:
    assert step(()) == ()
    assert step(("",)) == ("",)


def test_simulation_counts_generations_and_population() -> None:
    sim = Simulation(pad(grid("AAA"), 2))
    assert sim.generation == 0
    assert sim.population == {"A": 3}
    sim.step()
    assert sim.generation == 1
    assert sim.population == {"A": 3}


def test_simulation_wrap_option() -> None:
    sim = Simulation(grid("X..X", "....", "....", "X..."), wrap=True)
    sim.step()
    assert sim.grid[0][0] == "X"


# --- parsing ---------------------------------------------------------------


def test_parse_basic_and_spaces_are_empty() -> None:
    assert parse_seed("A. \n.B.\n") == ("A..", ".B.")


def test_parse_keeps_dead_margin_rows() -> None:
    assert parse_seed("...\n.X.\n...\n") == ("...", ".X.", "...")


def test_parse_ignores_trailing_blank_lines_and_crlf() -> None:
    assert parse_seed("A.\r\n.B\r\n\r\n   \n") == ("A.", ".B")


def test_parse_non_rectangular() -> None:
    with pytest.raises(SeedError, match=r"line 2 has 3 columns, expected 2"):
        parse_seed("A.\nB..\n")


def test_parse_empty() -> None:
    for text in ("", "\n\n", "  \n"):
        with pytest.raises(SeedError, match="empty"):
            parse_seed(text)


def test_wrap_counts_each_neighbour_once_on_a_thin_torus() -> None:
    # On a one-row torus the cell above, below and itself all wrap to the same
    # row; only the two real neighbours may count.
    assert step((".A.",), wrap=True) == ("...",)
    assert step(("AAA",), wrap=True) == ("AAA",)
