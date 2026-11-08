from pathlib import Path

import pytest

from kinlife.engine import Simulation, pad, parse_seed

SEEDS = sorted((Path(__file__).parent.parent / "seeds").glob("*.txt"))


def test_seeds_folder_is_populated() -> None:
    assert {p.stem for p in SEEDS} >= {
        "glider",
        "gosper-gun",
        "r-pentomino",
        "competing-populations",
    }


@pytest.mark.parametrize("path", SEEDS, ids=lambda p: p.stem)
def test_seed_parses_and_runs(path: Path) -> None:
    sim = Simulation(pad(parse_seed(path.read_text()), 5), seed=1)
    assert sim.population
    for _ in range(20):
        sim.step()


def test_competing_populations_has_two_species() -> None:
    text = (SEEDS[0].parent / "competing-populations.txt").read_text()
    assert set(Simulation(parse_seed(text)).population) == {"A", "B"}
