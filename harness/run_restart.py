"""Replay upstream sim_test.test_simulation_with_restart for one case, saving output.

Mirrors the upstream test: restart from the reference file at its midpoint time,
stitch, and run to t_final. Saves the stitched output so compare.py can report
every variable instead of stopping at xarray's first assert_allclose failure.

Usage:
  python harness/run_restart.py --case test_psichease_prescribed_jtot --out <out.nc>
"""

import argparse
import json
import os

import torax
from torax._src.config import config_loader
from torax._src.orchestration import run_simulation
from torax._src.output_tools import output
from torax._src.torax_pydantic import file_restart as file_restart_pydantic

TEST_DATA = os.path.join(os.path.dirname(__file__), '..', 'upstream-torax',
                         'torax', 'tests', 'test_data')


def main():
  p = argparse.ArgumentParser()
  p.add_argument('--case', required=True)
  p.add_argument('--out', required=True)
  args = p.parse_args()

  ref_path = os.path.abspath(os.path.join(TEST_DATA, args.case + '.nc'))
  ref = output.load_state_file(ref_path)
  ref_time = ref.children[output.PROFILES].dataset[output.TIME].to_numpy()
  loading_time = ref_time[len(ref_time) // 2]

  cfg = config_loader.build_torax_config_from_file(
      os.path.join(TEST_DATA, args.case + '.py'))
  cfg.update_fields({'numerics.t_initial': loading_time})
  cfg.update_fields({'restart': file_restart_pydantic.FileRestart.from_dict(
      dict(filename=ref_path, time=loading_time, do_restart=True, stitch=True))})
  out, history = run_simulation.run_simulation(cfg, progress_bar=False)
  out.to_netcdf(args.out)
  print(json.dumps({'case': args.case, 'restart_time': float(loading_time),
                    'sim_error': history.sim_error.name, 'out': args.out,
                    'torax_version': torax.__version__}))


if __name__ == '__main__':
  main()
