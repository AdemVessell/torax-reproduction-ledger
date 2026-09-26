"""Explain every variable that compare.py put below RTOL_1e-9 in a sweep.

For each such variable, reload candidate and reference and report:
  peak_rel   max|cand - ref| / max|ref|   (error against the variable's own scale)
  at_ref     the reference value where the largest relative difference sits
  class      NEAR_ZERO_ROUNDOFF  peak_rel < 1e-9 (the rtol miss is at near-zero entries)
             EXACT_ZERO_REF      reference is all zeros (rtol meaningless; see E002)
             REAL_DEVIATION      anything else; must be explained by hand

Usage: python harness/explain.py <sweep_dir> [torax_root]   -> <sweep_dir>/explained.json
"""

import json
import os
import sys

import numpy as np
import xarray as xr

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def load(path):
  with open(path, 'rb') as f:
    return xr.open_datatree(f).compute()


def main():
  sweep = sys.argv[1]
  torax_root = sys.argv[2] if len(sys.argv) > 2 else 'upstream-torax'
  results = json.load(open(os.path.join(sweep, 'sweep_results.json')))
  out = []
  for r in results:
    if r['status'] != 'COMPARED' or not r['vars_worse_than_1e-9']:
      continue
    cand = load(os.path.join(sweep, 'runs', r['label'] + '.nc'))
    ref = load(os.path.join(ROOT, torax_root, 'torax', 'tests', 'test_data',
                            r['case'] + '.nc'))
    for var, info in r['vars_worse_than_1e-9'].items():
      group, name = var.rsplit('/', 1)
      a = cand[group or '/'].to_dataset(inherit=False)[name].values.astype(float)
      b = ref[group or '/'].to_dataset(inherit=False)[name].values.astype(float)
      if a.shape != b.shape:
        out.append({'case': r['label'], 'var': var, 'tier': info['tier'],
                    'class': 'SHAPE_MISMATCH', 'shapes': [a.shape, b.shape]})
        continue
      d = np.abs(a - b)
      peak = np.nanmax(np.abs(b))
      if peak == 0:
        cls, peak_rel, at_ref = 'EXACT_ZERO_REF', None, 0.0
      else:
        peak_rel = float(np.nanmax(d) / peak)
        with np.errstate(divide='ignore', invalid='ignore'):
          rel = np.where(b != 0, d / np.abs(b), np.inf * (d > 0))
        at_ref = float(b.flat[int(np.nanargmax(rel))])
        cls = 'NEAR_ZERO_ROUNDOFF' if peak_rel < 1e-9 else 'REAL_DEVIATION'
      out.append({'case': r['label'], 'var': var, 'tier': info['tier'],
                  'max_rel_diff': info['max_rel_diff'], 'peak_rel': peak_rel,
                  'ref_peak': float(peak), 'ref_value_at_worst_rel': at_ref,
                  'class': cls})
  with open(os.path.join(sweep, 'explained.json'), 'w') as f:
    json.dump(out, f, indent=1)
  counts = {}
  for o in out:
    counts[o['class']] = counts.get(o['class'], 0) + 1
  print('classes:', counts)
  for o in out:
    if o['class'] == 'REAL_DEVIATION':
      print('  REAL_DEVIATION', o['case'], o['var'], o['tier'],
            f"peak_rel={o['peak_rel']:.3e}")


if __name__ == '__main__':
  main()
