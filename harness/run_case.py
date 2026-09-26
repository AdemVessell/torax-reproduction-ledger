"""Run one TORAX config, optionally with dotted-path overrides, and save its output.

Usage:
  python harness/run_case.py --config <config.py> --out <out.nc> --label <name>
      [--override sources.generic_heat.P_total=20.2e6 ...]

Prints one JSON summary line to stdout and writes <out>.json beside the output.
"""

import argparse
import copy
import hashlib
import json
import platform
import runpy
import time

import jax
import torax
from torax._src.torax_pydantic import model_config


def sha256(path):
  h = hashlib.sha256()
  with open(path, 'rb') as f:
    for chunk in iter(lambda: f.read(1 << 20), b''):
      h.update(chunk)
  return h.hexdigest()


def set_dotted(cfg, dotted, value):
  keys = dotted.split('.')
  node = cfg
  for k in keys[:-1]:
    node = node[k]
  if keys[-1] not in node:
    raise KeyError(f'override target does not exist: {dotted}')
  node[keys[-1]] = value


def main():
  p = argparse.ArgumentParser()
  p.add_argument('--config', required=True)
  p.add_argument('--out', required=True)
  p.add_argument('--label', required=True)
  p.add_argument('--override', action='append', default=[])
  args = p.parse_args()

  cfg = copy.deepcopy(runpy.run_path(args.config)['CONFIG'])
  overrides = {}
  for item in args.override:
    key, raw = item.split('=', 1)
    value = json.loads(raw)
    set_dotted(cfg, key, value)
    overrides[key] = value

  torax_config = model_config.ToraxConfig.from_dict(cfg)
  t0 = time.perf_counter()
  data_tree, state_history = torax.run_simulation(
      torax_config, progress_bar=False
  )
  wall_s = time.perf_counter() - t0
  data_tree.to_netcdf(args.out)

  summary = {
      'label': args.label,
      'config': args.config,
      'config_sha256': sha256(args.config),
      'overrides': overrides,
      'sim_error': state_history.sim_error.name,
      'n_times': int(data_tree.time.shape[0]),
      't_final': float(data_tree.time.values[-1]),
      'wall_s_including_compile': round(wall_s, 3),
      'out': args.out,
      'out_sha256': sha256(args.out),
      'torax_version': torax.__version__,
      'jax_version': jax.__version__,
      'jax_x64': bool(jax.config.jax_enable_x64),
      'devices': [str(d) for d in jax.devices()],
      'machine': platform.machine(),
      'platform': platform.platform(),
  }
  with open(args.out + '.json', 'w') as f:
    json.dump(summary, f, indent=2)
  print(json.dumps(summary))


if __name__ == '__main__':
  main()
