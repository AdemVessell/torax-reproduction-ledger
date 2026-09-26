"""Compare every variable in two TORAX output files (candidate vs reference).

Independent of TORAX's own test harness: it walks the whole output DataTree
(profiles, scalars, numerics, ...) instead of the five profiles the upstream
sim tests check.

Per variable, the strictest tier that holds is recorded:
  BITWISE    arrays identical (NaNs in the same places)
  RTOL_1e-9  np.allclose(cand, ref, rtol=1e-9, atol=0)  (upstream default)
  RTOL_1e-6  same, rtol=1e-6
  RTOL_1e-3  same, rtol=1e-3
  DIFFERENT  none of the above
  SHAPE      shapes differ (not comparable)

Usage:
  python harness/compare.py <candidate.nc> <reference.nc> --out <report.json>
      [--require RTOL_1e-9]

Exit code 0 when every common variable meets --require and no variable is
missing on either side; 1 otherwise.
"""

import argparse
import json
import sys

import numpy as np
import xarray as xr

TIERS = ['BITWISE', 'RTOL_1e-9', 'RTOL_1e-6', 'RTOL_1e-3', 'DIFFERENT', 'SHAPE']
RTOLS = {'RTOL_1e-9': 1e-9, 'RTOL_1e-6': 1e-6, 'RTOL_1e-3': 1e-3}
UPSTREAM_PROFILES = ('T_i', 'T_e', 'psi', 'q', 'n_e')


def load(path):
  with open(path, 'rb') as f:
    return xr.open_datatree(f).compute()


def flatten(tree):
  out = {}
  for node in tree.subtree:
    ds = node.to_dataset(inherit=False)
    for name, var in list(ds.data_vars.items()) + list(ds.coords.items()):
      out[f'{node.path.rstrip("/")}/{name}'] = var.values
  return out


def tier_of(a, b):
  if a.shape != b.shape:
    return 'SHAPE'
  if not (np.issubdtype(a.dtype, np.number) and np.issubdtype(b.dtype, np.number)):
    return 'BITWISE' if np.array_equal(a, b) else 'DIFFERENT'
  if np.array_equal(a, b, equal_nan=True):
    return 'BITWISE'
  for name, rtol in RTOLS.items():
    if np.allclose(a, b, rtol=rtol, atol=0, equal_nan=True):
      return name
  return 'DIFFERENT'


def stats(a, b):
  if a.shape != b.shape or not np.issubdtype(a.dtype, np.number):
    return {}
  a = a.astype(np.float64)
  b = b.astype(np.float64)
  finite = np.isfinite(a) & np.isfinite(b)
  if not finite.any():
    return {'nan_pattern_equal': bool(np.array_equal(np.isnan(a), np.isnan(b)))}
  d = np.abs(a[finite] - b[finite])
  ref = np.abs(b[finite])
  nz = ref > 0
  rms_ref = float(np.sqrt(np.mean(b[finite] ** 2)))
  return {
      'max_abs_diff': float(d.max()),
      'max_rel_diff': float((d[nz] / ref[nz]).max()) if nz.any() else None,
      'nrmsd': float(np.sqrt(np.mean(d**2)) / rms_ref) if rms_ref > 0 else None,
      'nan_pattern_equal': bool(np.array_equal(np.isnan(a), np.isnan(b))),
  }


def embedded_config(tree):
  """The run config TORAX stores in the root attrs, minus the version stamp."""
  raw = tree.attrs.get('config')
  if raw is None:
    return None, None
  cfg = json.loads(raw)
  return cfg, cfg.pop('torax_version', None)


def compare(cand_path, ref_path):
  cand_tree, ref_tree = load(cand_path), load(ref_path)
  cand_cfg, cand_ver = embedded_config(cand_tree)
  ref_cfg, ref_ver = embedded_config(ref_tree)
  cand, ref = flatten(cand_tree), flatten(ref_tree)
  common = sorted(set(cand) & set(ref))
  records = {}
  for key in common:
    records[key] = {'tier': tier_of(cand[key], ref[key]), **stats(cand[key], ref[key])}
  counts = {t: sum(r['tier'] == t for r in records.values()) for t in TIERS}
  worst = max((r['tier'] for r in records.values()), key=TIERS.index, default='BITWISE')
  upstream = {
      k: records[k]['tier']
      for k in common
      if k.startswith('/profiles/') and k.split('/')[-1] in UPSTREAM_PROFILES
  }
  ranked = sorted(
      (k for k in common if records[k].get('nrmsd') is not None),
      key=lambda k: records[k]['nrmsd'],
      reverse=True,
  )
  return {
      'candidate': cand_path,
      'reference': ref_path,
      'candidate_torax_version': cand_ver,
      'reference_torax_version': ref_ver,
      'embedded_config_equal': (
          None if cand_cfg is None or ref_cfg is None else cand_cfg == ref_cfg
      ),
      'n_common': len(common),
      'only_in_candidate': sorted(set(cand) - set(ref)),
      'only_in_reference': sorted(set(ref) - set(cand)),
      'tier_counts': counts,
      'worst_tier': worst,
      'upstream_five_profiles': upstream,
      'top10_by_nrmsd': [{'var': k, **records[k]} for k in ranked[:10]],
      'variables': records,
  }


def main():
  p = argparse.ArgumentParser()
  p.add_argument('candidate')
  p.add_argument('reference')
  p.add_argument('--out', required=True)
  p.add_argument('--require', default='RTOL_1e-9', choices=TIERS[:5])
  args = p.parse_args()

  report = compare(args.candidate, args.reference)
  ok = (
      TIERS.index(report['worst_tier']) <= TIERS.index(args.require)
      and not report['only_in_candidate']
      and not report['only_in_reference']
  )
  report['require'] = args.require
  report['meets_require'] = ok
  with open(args.out, 'w') as f:
    json.dump(report, f, indent=2)
  print(json.dumps({k: report[k] for k in (
      'candidate', 'reference', 'candidate_torax_version',
      'reference_torax_version', 'embedded_config_equal', 'n_common',
      'tier_counts', 'worst_tier', 'require', 'meets_require')}))
  print('only_in_candidate:', len(report['only_in_candidate']),
        'only_in_reference:', len(report['only_in_reference']))
  for r in report['top10_by_nrmsd'][:5]:
    print(f"  {r['var']}: tier={r['tier']} nrmsd={r['nrmsd']:.3e} "
          f"max_rel={r['max_rel_diff']}")
  sys.exit(0 if ok else 1)


if __name__ == '__main__':
  main()
