# Changelog

## Unreleased

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
