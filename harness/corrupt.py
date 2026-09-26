"""Write a copy of a TORAX output with one value nudged by a relative amount.

Used as a comparator control: compare.py must see the nudge when it exceeds
the tier tolerance, and must not overstate it when it does not.

Usage:
  python harness/corrupt.py <in.nc> <out.nc> --var /profiles/T_e
      --rel 1e-8 [--index 20,13]
"""

import argparse
import json

import numpy as np
import xarray as xr


def main():
  p = argparse.ArgumentParser()
  p.add_argument('src')
  p.add_argument('dst')
  p.add_argument('--var', required=True)
  p.add_argument('--rel', type=float, required=True)
  p.add_argument('--index', default=None, help='comma-separated, default=middle')
  args = p.parse_args()

  with open(args.src, 'rb') as f:
    tree = xr.open_datatree(f).compute()
  group, name = args.var.rsplit('/', 1)
  ds = tree[group].to_dataset(inherit=False)
  values = ds[name].values.copy()
  idx = (tuple(int(i) for i in args.index.split(','))
         if args.index else tuple(s // 2 for s in values.shape))
  before = float(values[idx])
  values[idx] = before * (1.0 + args.rel)
  ds[name] = (ds[name].dims, values, ds[name].attrs)
  tree[group] = xr.DataTree(ds)
  tree.to_netcdf(args.dst)
  print(json.dumps({'var': args.var, 'index': idx, 'rel': args.rel,
                    'before': before, 'after': float(values[idx])}))


if __name__ == '__main__':
  main()
