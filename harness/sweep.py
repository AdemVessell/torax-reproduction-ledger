"""Run every test_data case that has a committed reference, and compare full output.

Usage:
  python harness/sweep.py --cases evidence/E003_cases.txt --out evidence/E003 [--workers 4]

Per case: harness/run_case.py (subprocess, own log), then harness/compare.py.
Writes <out>/sweep_results.json and <out>/sweep_table.md.
"""

import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TD = os.path.join(ROOT, 'upstream-torax', 'torax', 'tests', 'test_data')
PY = sys.executable
TIMEOUT_S = 1800


def run_one(case, out, overrides=(), label=None):
  label = label or case
  nc = os.path.join(out, 'runs', label + '.nc')
  log = os.path.join(out, 'logs', label + '.log')
  cmd = [PY, os.path.join(ROOT, 'harness', 'run_case.py'),
         '--config', os.path.join(TD, case + '.py'), '--out', nc, '--label', label]
  for o in overrides:
    cmd += ['--override', o]
  t0 = time.time()
  try:
    with open(log, 'w') as f:
      rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT,
                          timeout=TIMEOUT_S).returncode
  except subprocess.TimeoutExpired:
    rc = 'TIMEOUT'
  rec = {'case': case, 'label': label, 'overrides': list(overrides),
         'run_rc': rc, 'run_wall_s': round(time.time() - t0, 1), 'log': log}
  if rc != 0 or not os.path.exists(nc):
    rec['status'] = 'RUN_ERROR'
    with open(log) as f:
      tail = [l.rstrip() for l in f.readlines() if l.strip()][-3:]
    rec['error_tail'] = tail
    return rec
  with open(nc + '.json') as f:
    rec['sim_error'] = json.load(f)['sim_error']
  rep_path = os.path.join(out, 'compare', label + '.json')
  subprocess.run([PY, os.path.join(ROOT, 'harness', 'compare.py'), nc,
                  os.path.join(TD, case + '.nc'), '--out', rep_path],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=ROOT)
  with open(rep_path) as f:
    rep = json.load(f)
  worse = {k: v for k, v in rep['variables'].items()
           if v['tier'] not in ('BITWISE', 'RTOL_1e-9')}
  rec.update({
      'status': 'COMPARED',
      'worst_tier': rep['worst_tier'],
      'tier_counts': rep['tier_counts'],
      'n_common': rep['n_common'],
      'only_in_candidate': len(rep['only_in_candidate']),
      'only_in_reference': len(rep['only_in_reference']),
      'reference_torax_version': rep['reference_torax_version'],
      'upstream_five_profiles_worst': max(
          rep['upstream_five_profiles'].values(),
          key=['BITWISE', 'RTOL_1e-9', 'RTOL_1e-6', 'RTOL_1e-3', 'DIFFERENT',
               'SHAPE'].index, default=None),
      'vars_worse_than_1e-9': {
          k: {'tier': v['tier'], 'max_abs_diff': v.get('max_abs_diff'),
              'max_rel_diff': v.get('max_rel_diff')} for k, v in worse.items()},
  })
  return rec


def main():
  p = argparse.ArgumentParser()
  p.add_argument('--cases', required=True)
  p.add_argument('--out', required=True)
  p.add_argument('--workers', type=int, default=4)
  p.add_argument('--torax-root', default='upstream-torax',
                 help='TORAX clone whose test_data supplies configs and references')
  args = p.parse_args()
  global TD
  TD = os.path.join(ROOT, args.torax_root, 'torax', 'tests', 'test_data')
  for d in ('runs', 'logs', 'compare'):
    os.makedirs(os.path.join(args.out, d), exist_ok=True)

  jobs = [(c, ()) for c in open(args.cases).read().split()]
  # Sweep-level negative control: same runner path, +1 % heating. Must not pass.
  jobs.append(('test_iterhybrid_rampup', ('sources.generic_heat.P_total=20.2e6',),
               'CTRL_rampup_heat_plus1pct'))
  results = []
  with cf.ThreadPoolExecutor(args.workers) as ex:
    futs = {ex.submit(run_one, j[0], args.out, j[1], *(j[2:] or (None,))): j
            for j in jobs}
    for fut in cf.as_completed(futs):
      rec = fut.result()
      results.append(rec)
      print(f"{rec['label']}: {rec['status']} {rec.get('worst_tier', '')} "
            f"({rec['run_wall_s']}s)", flush=True)
  results.sort(key=lambda r: r['label'])
  with open(os.path.join(args.out, 'sweep_results.json'), 'w') as f:
    json.dump(results, f, indent=1)

  lines = ['| case | status | worst tier (all vars) | 5 upstream profiles | '
           'vars worse than 1e-9 | ref version | schema diff (cand/ref) |',
           '|---|---|---|---|---|---|---|']
  for r in results:
    if r['status'] != 'COMPARED':
      lines.append(f"| {r['label']} | {r['status']} | | | "
                   f"{' / '.join(r.get('error_tail', []))[:120]} | | |")
      continue
    worse = ', '.join(k.split('/')[-1] for k in r['vars_worse_than_1e-9'])
    lines.append(f"| {r['label']} | {r['status']} | {r['worst_tier']} | "
                 f"{r['upstream_five_profiles_worst']} | {worse or '-'} | "
                 f"{r['reference_torax_version']} | "
                 f"{r['only_in_candidate']}/{r['only_in_reference']} |")
  with open(os.path.join(args.out, 'sweep_table.md'), 'w') as f:
    f.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
  main()
