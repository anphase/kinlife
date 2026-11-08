# Quality baseline

Recorded 2026-11-08 at 0.1.0 plus the rule variants (79 tests).

## Coverage

`pytest --cov=multicell`: 267 statements, 0 missed, **100%** on every module
(`cli`, `engine`, `render`, `slate`, `ui`, `__init__`, `__main__`).

Ratchet: `COV_MIN=100` in `scripts/ci-local.sh`.

## Cyclomatic complexity

Measured with ruff's C901 (McCabe), which is already a dev dependency; the
ratchet is `CC_MAX=13` in `scripts/ci-local.sh`. Highest scores, as ranked by
`radon cc -s` (31 blocks, average 4.3, grade A; radon counts one higher than
ruff on `cli.main`):

| Function | radon | ruff |
| --- | --- | --- |
| `ui._draw` | 13 | 13 |
| `cli.main` | 14 | 13 or less |
| `engine.step` | 12 | 12 or less |
| `ui.Session.handle` | 8 | |

Every other function scores 9 or under. No function exceeds the ratchet; a new
one over 13 fails `scripts/ci-local.sh`. Lower `CC_MAX` as these are split up.

## Run

`sh scripts/ci-local.sh`
