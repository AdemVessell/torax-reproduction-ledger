#!/usr/bin/env bash
# E005: x86_64 legs of the ledger, run by .github/workflows/x86-reproduction.yml
# on a GitHub-hosted ubuntu runner. Everything lands in evidence/E005/ci/.
# Measurement only: outcomes are graded against evidence/E005/PREREGISTRATION.md,
# so the script does not stop on a failing comparison.
set -uo pipefail
cd "$(dirname "$0")/.."
OUT=evidence/E005/ci
TD=upstream-torax/torax/tests/test_data
mkdir -p "$OUT"

{ uname -a; echo; lscpu; } > "$OUT/host_cpu.txt" 2>&1
grep -o -w -E 'avx|avx2|fma|avx512f' /proc/cpuinfo | sort | uniq -c > "$OUT/cpu_flags.txt"

git clone --quiet --branch v1.4.3 --depth 1 https://github.com/google-deepmind/torax.git upstream-torax
git -C upstream-torax rev-parse HEAD > "$OUT/torax_commit.txt"

# X1 / X3: the dependency versions E001 used on arm64 (Python 3.12).
grep -v '^-e ' evidence/E001/raw/freeze_py312.txt > "$OUT/constraints_e001.txt"
uv venv --python 3.12 .venv -q
VIRTUAL_ENV=.venv uv pip install -q -c "$OUT/constraints_e001.txt" -e "./upstream-torax[dev]"
VIRTUAL_ENV=.venv uv pip freeze > "$OUT/freeze_x1.txt"
PY=.venv/bin/python

run() { $PY harness/run_case.py --config "$TD/$1.py" --out "$OUT/$2.nc" --label "$2" > "$OUT/$2.log" 2>&1; }
cmp_() { $PY harness/compare.py "$2" "$3" --out "$OUT/$1.json" > "$OUT/$1.txt" 2>&1; }

run test_iterhybrid_rampup X1_P1
run test_iterhybrid_rampup X1_C1
cmp_ X1a "$OUT/X1_P1.nc" "$TD/test_iterhybrid_rampup.nc"   # x86 vs maintainer reference
cmp_ X1b "$OUT/X1_P1.nc" evidence/E001/runs/P1.nc          # x86 vs arm64 (E001)
cmp_ X1c "$OUT/X1_C1.nc" "$OUT/X1_P1.nc"                   # x86 repeat

run test_psichease_prescribed_jtot X3_jtot
cmp_ X3a "$OUT/X3_jtot.nc" "$TD/test_psichease_prescribed_jtot.nc"          # vs reference
cmp_ X3b "$OUT/X3_jtot.nc" evidence/E001/runs/N_test_psichease_prescribed_jtot.nc  # vs arm64

# E001's controls on x86, through the same rerun script readers use.
bash harness/reproduce_E001.sh > "$OUT/X1_controls.log" 2>&1
echo "exit=$?" >> "$OUT/X1_controls.log"

# X2: dependencies as of the v1.4.3 release date (Python 3.11), full upstream sim suite.
uv venv --python 3.11 .venv-ci311 -q
VIRTUAL_ENV=.venv-ci311 uv pip install -q --exclude-newer 2026-07-03T17:00:00Z -e "./upstream-torax[dev]"
VIRTUAL_ENV=.venv-ci311 uv pip freeze > "$OUT/freeze_x2.txt"
(cd upstream-torax && ../.venv-ci311/bin/python -m pytest torax/tests/sim_test.py -n 4 \
  -p no:cacheprovider -rA --junitxml="../$OUT/X2_sim_test_junit.xml" > "../$OUT/X2_sim_test.log" 2>&1
 echo "exit=$?" >> "../$OUT/X2_sim_test.log")

$PY - "$OUT" > "$OUT/SUMMARY.md" <<'EOF'
import json, os, re, sys
out = sys.argv[1]
def rep(i):
  p = os.path.join(out, i + '.json')
  return json.load(open(p)) if os.path.exists(p) else None
print('# E005 x86 summary\n')
print('CPU flags:', open(os.path.join(out, 'cpu_flags.txt')).read().split())
for i, what in [('X1a', 'x86 vs maintainer reference'), ('X1b', 'x86 vs arm64 E001 P1'),
                ('X1c', 'x86 repeat run'), ('X3a', 'heat-off jtot vs reference'),
                ('X3b', 'heat-off jtot vs arm64')]:
  r = rep(i)
  if r is None:
    print(f'- {i} ({what}): MISSING'); continue
  top = r['top10_by_nrmsd'][0] if r['top10_by_nrmsd'] else {}
  print(f"- {i} ({what}): worst={r['worst_tier']} counts={r['tier_counts']} "
        f"top={top.get('var')} max_rel={top.get('max_rel_diff')}")
  if i.startswith('X3'):
    dw = r['variables'].get('/scalars/dW_thermal_dt', {})
    print(f"  dW_thermal_dt: tier={dw.get('tier')} max_abs={dw.get('max_abs_diff')}")
ctrl = open(os.path.join(out, 'X1_controls.log')).read()
print('- controls:', re.findall(r'^(\S+ (?:OK|UNEXPECTED).*)$', ctrl, re.M), ctrl.strip().splitlines()[-1])
suite = open(os.path.join(out, 'X2_sim_test.log')).read()
print('- X2 upstream suite:', (re.findall(r'=+ (.*(?:passed|failed).*) =+', suite) or ['?'])[-1])
print('  failed:', re.findall(r'^FAILED (\S+)', suite, re.M))
EOF
cat "$OUT/SUMMARY.md"
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && cat "$OUT/SUMMARY.md" >> "$GITHUB_STEP_SUMMARY"
exit 0
