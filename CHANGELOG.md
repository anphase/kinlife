# Changelog

## [0.2.0] - 2026-11-08

### Changed

- Renamed to Kinlife: the package is `kinlife`, and the commands are `kinlife` and `kinlife-slate`. The idea and the original curses version are Adam Heins' Multicell (2015, MIT), credited in the README.

### Added

- 2026-11-08: quality baselines in `docs/quality/baseline.md` (100% coverage,
  complexity ranking) and `scripts/ci-local.sh`, which ratchets coverage at
  100% and function complexity at 13.
- 2026-11-08: `--rule` flag with HighLife (B36/S23), Day and Night
  (B3678/S34678) and Brian's Brain (three states, dying cells shown as `~`);
  species inheritance applies to births in each, with a random tie-break.

### Fixed

- 2026-11-08: restarting with `r` keeps the current wrap setting instead of
  resetting to the `--wrap` command-line value.

## 0.1.0

First release of the spin-off, based on Adam Heins' 2015 Multicell.

- Installable package with `multicell` and `multicell-slate` commands.
- UI-free simulation engine with a seeded random tie-break and an option for
  toroidal (wrap-around) edges.
- Test suite covering Conway's rules, species inheritance, reproducibility and
  seed parsing.
- Documented seed format; `seeds/` with a glider, a glider gun, an R-pentomino
  in two species and a competing-populations demo.
- Terminal UI with pause, step, speed, restart and wrap keys, species colours
  and a generation and per-species population counter; plain-text fallback
  where curses is unavailable.
- Fixed `multicell-slate` asking for confirmation with the Python 2 `raw_input`.
