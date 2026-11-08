#!/usr/bin/env sh
# Lint, type-check and test. Needs the dev extras: pip install -e '.[dev]'
set -eu
cd "$(dirname "$0")/.."

python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest -q
