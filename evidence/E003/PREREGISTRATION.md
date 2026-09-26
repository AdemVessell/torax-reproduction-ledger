# E003 pre-registration — full-output reproduction across all 56 referenced cases

Written before the sweep. Hash in `E003/SHA256SUMS`.

## Object

TORAX v1.4.3 @ 4aea237 (same pin as E001), macOS arm64, `.venv` (Py 3.12, jax 0.11.2).
The 56 cases in `torax/tests/test_data` that have both `<case>.py` and `<case>.nc`
(`evidence/E003_cases.txt`). Upstream `sim_test.py` runs 52 of them. It does not run
`test_iterhybrid_lh_transition`, `..._qualikiz`, `..._qualikiz_rotation`, or
`test_iterhybrid_radiation_collapse` (`evidence/E003_upstream_map.json`).

Instrument: `harness/run_case.py` + `harness/compare.py`, unchanged since E001 (hashes in
`evidence/MANIFEST.sha256`). New: `harness/sweep.py`, which only orchestrates.

## Expectations

1. Runner consistency: the sweep's `test_iterhybrid_rampup` output is BITWISE equal to E001 P1.
   If not, the sweep path differs from E001 and the sweep is INVALID.
2. Sweep negative control `CTRL_rampup_heat_plus1pct` reaches DIFFERENT. If it passes, INVALID.
3. QuaLiKiz cases: RUN_ERROR/BLOCKED (external QuaLiKiz binary not installed). Not a TORAX
   defect.
4. Upstream-tested cases, 5 upstream profiles: at the upstream tolerance for that case
   (default rtol 1e-9; loosened for eqdsk 1e-6, rotation 5e-6, tglfnn_rotation 2e-7,
   lengyel 1e-8), matching E001's 62/64 pass.
5. Full output (all variables), the new information: at least 80 % of compared cases reach
   RTOL_1e-9 or better on every common variable. Variables worse than 1e-9 are expected to
   cluster in quantities whose reference is exactly 0 or near a cancellation (like the
   E002 dW/dt scalars). Any variable at RTOL_1e-3 or DIFFERENT in an unperturbed case is a
   finding that must be explained before it is reported.
6. Schema diffs (variables only in candidate or only in reference) are expected for
   references written by older versions. They are reported, not scored.

## Claim boundary

- Supports: which cases and which output variables reproduce on arm64 at which tier, for
  v1.4.3.
- Does not support: physics validity, x86 behaviour, or behaviour on current main (which
  has moved since v1.4.3; see E002 follow-up).
