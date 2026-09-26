#!/usr/bin/env bash
# Runs inside python:3.11-slim. /src = TORAX clone (read-only), /out = evidence dir.
# Usage (host): docker run --rm --platform linux/<arch> -v <clone>:/src:ro \
#   -v <evidence>:/out python:3.11-slim bash /out/../../harness/container_restart.sh <label>
set -u
LABEL="$1"
LOG="/out/${LABEL}.log"
{
  uname -m; python --version
  pip install -q uv
  cp -r /src /work && cd /work
  uv pip install --system -q --exclude-newer 2026-07-03T17:00:00Z -e '.[dev]'
  uv pip freeze --system > "/out/${LABEL}_freeze.txt"
  python -c "import jax,numpy;print('jax',jax.__version__,'numpy',numpy.__version__,jax.devices())"
  python -m pytest torax/tests/sim_test.py -k test_simulation_with_restart \
    -p no:cacheprovider -rA --junitxml="/out/${LABEL}_junit.xml"
  echo "pytest_exit=$?"
} > "$LOG" 2>&1
