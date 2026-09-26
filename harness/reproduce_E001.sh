#!/usr/bin/env bash
# Re-run E001 (flagship case + comparator controls) from scratch into evidence/E001-rerun.
# Needs: git, uv. Takes ~3 min on an M1 Max.
set -euo pipefail
cd "$(dirname "$0")/.."
TAG=v1.4.3
[ -d upstream-torax ] || git clone --quiet --branch "$TAG" --depth 1 \
  https://github.com/google-deepmind/torax.git upstream-torax
[ -d .venv ] || { uv venv --python 3.12 .venv -q; VIRTUAL_ENV=.venv uv pip install -q -e "./upstream-torax[dev]"; }

PY=.venv/bin/python
TD=upstream-torax/torax/tests/test_data
CFG=$TD/test_iterhybrid_rampup.py
REF=$TD/test_iterhybrid_rampup.nc
OUT=evidence/E001-rerun
mkdir -p "$OUT/runs" "$OUT/compare"

$PY harness/run_case.py --config $CFG --out $OUT/runs/P1.nc --label P1
$PY harness/run_case.py --config $CFG --out $OUT/runs/C1.nc --label C1
$PY harness/run_case.py --config $CFG --out $OUT/runs/C2.nc --label C2 \
  --override 'sources.generic_heat.P_total=20.2e6'
$PY harness/corrupt.py $REF $OUT/runs/C4a.nc --var /profiles/T_e --rel 1e-8
$PY harness/corrupt.py $REF $OUT/runs/C4b.nc --var /profiles/T_e --rel 1e-10

# Expected: P1 pass, C1 pass (bitwise), C2 fail, C3 fail, C4a fail, C4b pass.
check() {  # id expect(pass|fail) candidate reference
  if $PY harness/compare.py "$3" "$4" --out "$OUT/compare/$1.json" > /dev/null 2>&1; then got=pass; else got=fail; fi
  [ "$got" = "$2" ] && echo "$1 OK ($got)" || { echo "$1 UNEXPECTED: got $got, expected $2"; bad=1; }
}
bad=0
check P1 pass $OUT/runs/P1.nc $REF
check C1 pass $OUT/runs/C1.nc $OUT/runs/P1.nc
check C2 fail $OUT/runs/C2.nc $REF
check C3 fail $OUT/runs/P1.nc $TD/test_iterhybrid_predictor_corrector.nc
check C4a fail $OUT/runs/C4a.nc $REF
check C4b pass $OUT/runs/C4b.nc $REF
exit $bad
