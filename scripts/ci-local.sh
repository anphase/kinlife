#!/usr/bin/env sh
# Local gate: scripts/check.sh plus the quality ratchet in docs/quality/baseline.md.
# Coverage may not fall below COV_MIN; no function may exceed CC_MAX (McCabe,
# measured by ruff C901). Raise the floor / lower the ceiling when you improve
# the numbers, never the other way round.
set -eu
cd "$(dirname "$0")/.."

COV_MIN=100
CC_MAX=13

if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi

sh scripts/check.sh
"$PY" -m pytest -q --cov-fail-under="$COV_MIN"
"$PY" -m ruff check --select C901 --config "lint.mccabe.max-complexity=$CC_MAX" src tests
