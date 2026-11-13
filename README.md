# Kinlife

Conway's Game of Life where cells belong to species. A newborn cell takes the
majority species of its three parents, so populations compete for territory.

## Install and run

Requires Python 3.11 or newer and nothing else. On Linux and macOS the full-screen
UI uses the standard library's `curses`; where that is missing, or when output is
not a terminal, a plain-text renderer is used.

```
git clone https://github.com/anphase/kinlife
cd kinlife
pip install .
kinlife seeds/gosper-gun.txt
```

Keys: `space` or `p` pause, `s` step, `+` / `-` speed, `r` restart, `w` toggle
wrap-around edges, `q` quit. The header shows the generation and the live count of
each species, each in its own colour.

Options: `-p N` padding (empty cells added around the seed, default 5), `-t SECONDS`
time between generations, `--wrap` for toroidal edges, `--rng-seed N` for a
reproducible run, `--plain -n N` to print N generations as text. Run `kinlife -h`
for all of them. `python -m kinlife` works too.

## The rules

Each cell has eight neighbours (the surrounding cells, diagonals included). All
cells update at once.

1. **Survival.** A live cell with 2 or 3 live neighbours survives, keeping its
   species. Otherwise it dies.
2. **Birth.** An empty cell with exactly 3 live neighbours becomes live.
3. **Inheritance.** The newborn's species is the species shared by at least two of
   its three parents. If all three parents are different species, one of the three
   is chosen uniformly at random.
4. **Edges.** By default cells beyond the edge are permanently empty. With
   `--wrap` opposite edges are joined (a torus).

With a single species this is exactly Conway's Game of Life. The random choice
in rule 3 is the only randomness; `--rng-seed` makes it reproducible.

### Rule variants

`--rule NAME` swaps the survival and birth counts (the default is `life`). In
every variant a newborn takes the species with the most parents, and a tie
(for example three A and three B parents) is broken at random.

| `--rule`   | Rule                  | Born with N neighbours | Survives with N neighbours |
| ---------- | --------------------- | ---------------------- | -------------------------- |
| `life`     | B3/S23                | 3                      | 2, 3                       |
| `highlife` | B36/S23               | 3, 6                   | 2, 3                       |
| `daynight` | B3678/S34678          | 3, 6, 7, 8             | 3, 4, 6, 7, 8              |
| `brain`    | Brian's Brain         | exactly 2              | never                      |

Brian's Brain has three states. A live cell always becomes *dying* (shown as
`~`) for one generation and then empty, and a dying cell neither counts as a
neighbour nor has a species. `~` is therefore reserved; it is not counted in the
population.

## Seed format

A seed is a plain text file holding a rectangle of characters, one row per line.

- `.` is an empty cell, and so is any whitespace, tabs included.
- Any other printable character except the reserved `~` is a live cell whose
  species is that character. `A`/`B`, `X`/`O` and `1`/`2` all work; use as many
  species as you like.
- Non-printable characters, such as escape characters and bidi overrides, are
  rejected with the line and column they are on.
- Every row must be the same width, otherwise Kinlife reports which line is wrong.
- Trailing blank lines are ignored.

```
.A.
..A
BBB
```

`kinlife-slate -r 30 -c 80 -o mine.txt` writes a blank rectangle to edit. The
`seeds/` folder has examples: `glider.txt`, `gosper-gun.txt` (a glider gun and a
blinker in two species), `r-pentomino.txt` (an R-pentomino whose cells are two
species) and `competing-populations.txt` (two random soups meeting in the middle).

## What this remix adds

- An installable package (`kinlife`, `kinlife-slate`) with no dependencies.
- A simulation engine separate from the display, with a seedable tie-break and
  toroidal edges.
- Tests that pin down the rules above.
- A documented seed format and a folder of seeds.
- A terminal UI with speed control, species colours and population counts, and a
  plain-text fallback.

## Development

```
pip install -e '.[dev]'
scripts/check.sh   # ruff, mypy (strict) and pytest
```

## Roadmap

A browser version (no server) with painting, species colours and population graphs,
plus rule variants.

## Related

Mathomaly has interactive explorations of other cellular automata:
[Rule 30](https://mathomaly.com/explore/rule-30/),
[Langton's ant](https://mathomaly.com/explore/langton/) and
[the sandpile](https://mathomaly.com/explore/sandpile/).

## Credits

Kinlife started from [Adam Heins' Multicell](https://github.com/adamheins/multicell) (2015, MIT),
which first combined Life with species inheritance.

## License

MIT. Copyright (c) 2015 Adam Heins, (c) 2026 anphase. See [LICENSE](LICENSE).
