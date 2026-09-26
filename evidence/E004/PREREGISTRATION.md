# E004 pre-registration — E003 repeated on current main

Written before any E004 run. Hash in `E004/SHA256SUMS`.

## Object

- Code: google-deepmind/torax `main` @ `17cc32fb0dfc1d83a8f333a3fbb08d746ad5c1ae`
  (2026-09-24; equal to remote HEAD when checked on 2026-09-25). Unreleased.
- Env: `.venv-main` (Python 3.12.13, jax 0.11.2), macOS arm64, M1 Max. Same machine as E001-E003.
- Cases: the 55 test_data cases on main with `<case>.py` + `<case>.nc` (`evidence/E004_cases.txt`).
  Since v1.4.3: `..._lh_transition_adaptive_source` was renamed to
  `..._lh_transition_internal_boundary_condition`, `test_prescribed_transport` was removed,
  and 52 of 54 shared references were regenerated (`evidence/E004_refs_changed.txt`).
- Upstream runs 51 of them in `test_run_simulation` (`evidence/E004_upstream_map.json`).
  Not run: `lh_transition` (still `TODO(b/331171303)`), the 2 QuaLiKiz cases, and
  `radiation_collapse` (collapse check only).
- Instrument: `run_case.py` and `compare.py` unchanged since E001. `sweep.py` and `explain.py`
  gained a `--torax-root` / 2nd positional arg (defaults preserve E003 behaviour).

## Difference from E003

In E003 the scale-aware classifier was post hoc. **Here it is pre-registered**, unchanged
(`harness/explain.py`): NEAR_ZERO_ROUNDOFF means peak_rel < 1e-9; EXACT_ZERO_REF;
REAL_DEVIATION otherwise, split in the ledger into SMALL (1e-9 ≤ peak_rel < 1e-6) and
NOTABLE (≥ 1e-6).

## Expectations

1. Upstream suite `torax/tests/sim_test.py` on main: all tests pass, including
   restart1/2 (already seen on main in E002 follow-up). Any failure is a finding.
2. Sweep negative control (`CTRL_rampup_heat_plus1pct`) is DIFFERENT. Otherwise INVALID.
3. QuaLiKiz cases: RUN_ERROR (unregistered model), as in E003.
4. All 51 upstream-tested cases: 5 main profiles within rtol 1e-9.
5. Full output of upstream-tested cases: no NOTABLE deviation. Every miss is
   NEAR_ZERO_ROUNDOFF, EXACT_ZERO_REF (heat-disabled psichease dW/dt), a solver residual, or
   SMALL inside that case's upstream tolerance. Any NOTABLE deviation in an upstream-tested
   case is a finding and is examined before it is reported.
6. `lh_transition` (upstream-disabled): SMALL/NOTABLE deviations with differing solver
   iteration counts, as in E003. `radiation_collapse`: collapse reached with a similar end
   time; SHAPE mismatch acceptable.

## Claim boundary

- Supports: whether current (unreleased) main reproduces its own committed references on arm64,
  across full output, at the tiers found.
- Does not support: x86 behaviour, physics validity, or any comparison between v1.4.3 and main
  outputs (references changed by design; that is development, not reproduction).
