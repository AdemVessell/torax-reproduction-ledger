#!/usr/bin/env bash
# E005: x86_64 legs of the ledger, run by .github/workflows/x86-reproduction.yml
# on a GitHub-hosted ubuntu runner.
#   bash harness/ci_x86.sh x1x3   # X1a/X1b/X1c, E001 controls, X3  -> evidence/E005/ci/x1x3/
#   bash harness/ci_x86.sh x2     # full upstream sim suite, release-era deps -> evidence/E005/ci/x2/
# Measurement only: outcomes are graded against evidence/E005/PREREGISTRATION.md
# (and PREREG_ADDENDUM_1.md), so the script does not stop on a failing comparison.
set -uo pipefail
cd "$(dirname "$0")/.."
LEG="${1:?usage: ci_x86.sh x1x3|x2}"
OUT="evidence/E005/ci/$LEG"
TD=upstream-torax/torax/tests/test_data
mkdir -p "$OUT"

{ uname -a; echo; lscpu; echo; free -m; } > "$OUT/host_cpu.txt" 2>&1
grep -o -w -E 'avx|avx2|fma|avx512f' /proc/cpuinfo | sort | uniq -c > "$OUT/cpu_flags.txt"
( while true; do echo "$(date -u +%T) $(free -m | awk '/^Mem:/{print "used_mb="$3" avail_mb="$7}')"; sleep 30; done ) > "$OUT/mem.log" 2>&1 &
MEMLOG=$!
trap 'kill $MEMLOG 2>/dev/null' EXIT

git clone --quiet --branch v1.4.3 --depth 1 https://github.com/google-deepmind/torax.git upstream-torax
git -C upstream-torax rev-parse HEAD > "$OUT/torax_commit.txt"

if [ "$LEG" = x1x3 ]; then
  # The dependency versions E001 used on arm64 (Python 3.12).
  grep -v '^-e ' evidence/E001/raw/freeze_py312.txt > "$OUT/constraints_e001.txt"
  uv venv --python 3.12 .venv -q
  VIRTUAL_ENV=.venv uv pip install -q -c "$OUT/constraints_e001.txt" -e "./upstream-torax[dev]"
  VIRTUAL_ENV=.venv uv pip freeze > "$OUT/freeze.txt"
  PY=.venv/bin/python
  run() { $PY harness/run_case.py --config "$TD/$1.py" --out "$OUT/$2.nc" --label "$2" > "$OUT/$2.log" 2>&1; }
  cmp_() { $PY harness/compare.py "$2" "$3" --out "$OUT/$1.json" > "$OUT/$1.txt" 2>&1; }

  run test_iterhybrid_rampup X1_P1
  run test_iterhybrid_rampup X1_C1
  cmp_ X1a "$OUT/X1_P1.nc" "$TD/test_iterhybrid_rampup.nc"   # x86 vs maintainer reference
  cmp_ X1b "$OUT/X1_P1.nc" evidence/E001/runs/P1.nc          # x86 vs arm64 (E001)
  cmp_ X1c "$OUT/X1_C1.nc" "$OUT/X1_P1.nc"                   # x86 repeat

  run test_psichease_prescribed_jtot X3_jtot
  cmp_ X3a "$OUT/X3_jtot.nc" "$TD/test_psichease_prescribed_jtot.nc"                 # vs reference
  cmp_ X3b "$OUT/X3_jtot.nc" evidence/E001/runs/N_test_psichease_prescribed_jtot.nc  # vs arm64

  # E001's controls on x86, through the same rerun script readers use.
  bash harness/reproduce_E001.sh > "$OUT/X1_controls.log" 2>&1
  echo "exit=$?" >> "$OUT/X1_controls.log"
  cat "$OUT"/X1a.txt "$OUT"/X1b.txt "$OUT"/X1c.txt "$OUT"/X3a.txt "$OUT"/X3b.txt "$OUT/X1_controls.log" | grep -v libtpu

elif [ "$LEG" = x2 ]; then
  # Dependencies as of the v1.4.3 release date (Python 3.11), full upstream sim suite.
  uv venv --python 3.11 .venv-ci311 -q
  VIRTUAL_ENV=.venv-ci311 uv pip install -q --exclude-newer 2026-07-03T17:00:00Z -e "./upstream-torax[dev]"
  VIRTUAL_ENV=.venv-ci311 uv pip freeze > "$OUT/freeze.txt"
  (cd upstream-torax && ../.venv-ci311/bin/python -m pytest torax/tests/sim_test.py -n 2 \
    -p no:cacheprovider -rA --junitxml="../$OUT/X2_sim_test_junit.xml" > "../$OUT/X2_sim_test.log" 2>&1
   echo "exit=$?" >> "../$OUT/X2_sim_test.log")
  grep -E "^(FAILED|ERROR)|passed|failed|exit=" "$OUT/X2_sim_test.log" | tail -8
fi
exit 0
