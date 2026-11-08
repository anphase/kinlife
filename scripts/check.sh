#!/usr/bin/env sh
# Lint, type-check and test. Needs the dev extras: pip install -e '.[dev]'
set -eu
cd "$(dirname "$0")/.."

# Prefer the repo's own virtual environment when there is one.
if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi

"$PY" -m ruff check .
"$PY" -m ruff format --check .
"$PY" -m mypy
"$PY" -m pytest -q
