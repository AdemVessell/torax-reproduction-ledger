# E002 pre-registration — why do 2 upstream restart tests fail on this machine?

Written before any E002 run. Hash in `E002/SHA256SUMS`.

## Observation carried from E001

With TORAX v1.4.3 on macOS arm64 (Python 3.12.13, jax 0.11.2, numpy 2.5.3), upstream
`sim_test.py` gives 62 passed and 2 failed. The failures are
`test_simulation_with_restart1` (test_psichease_prescribed_jtot) and `...restart2`
(test_psichease_prescribed_johm). They fail the same way when run serially, so it is not
an xdist race. Mechanism seen: heat equations are off, so the reference stores
W_thermal_e/i as exactly constant and dW/dt as exactly 0. Here W_thermal_e/i flip by
1 ulp (1.49e-8 J / 2.98e-8 J on ~1.2e8 J) at one step. That gives dW_thermal_dt up to
2.51e-7 W, and xarray's default `assert_allclose` atol is 1e-8.

Upstream CI for the tag commit: ubuntu-latest, Python 3.11 only, all shards green.
Dependency confound: CI on 2026-07-03 would have resolved jax 0.10.2 (0.11.x came later).

## Hypothesis

H: the failure comes from platform floating-point behaviour (architecture or OS), not from
the newer dependencies.

## Runs (all TORAX v1.4.3 @ 4aea237; deps resolved with uv --exclude-newer 2026-07-03T17:00Z)

| ID | Platform | Expected under H | Reading if not |
|---|---|---|---|
| M1 | macOS arm64 native, Py 3.11, CI-era deps, full sim_test.py | restart1/2 FAIL, all others PASS | If they pass, dependency drift (jax 0.11 / numpy 2.5) causes it. H is falsified. |
| M2 | Linux arm64 (Docker via colima), Py 3.11, CI-era deps, restart tests | restart1/2 FAIL if architecture drives it | If they pass, it is macOS-specific (libm/Accelerate/compiler). |
| M3 | Linux x86_64 (Docker, emulated), Py 3.11, CI-era deps, restart tests | ALL PASS (reproduces CI) | If restart1/2 fail, this environment does not reproduce CI. Attribution from M1/M2 is INVALID. If jaxlib cannot run under emulation, M3 is BLOCKED, not PASS. |

Controls inside every run: restart0 (test_psi_heat_dens) and restart3
(test_iterhybrid_rampup) must PASS. Otherwise the restart path itself is broken in that
environment and the run is INVALID.

## Claim boundary

- Supports: which platform factor the 2 failures follow, within these environments.
- Does not support: that TORAX physics is wrong. The observed deviation is ~1e-16 relative
  on W and ~1e-14 of heating power on dW/dt. Nor that CI's exact environment is matched
  (the image patch version and emulation layer differ).
