# TORAX Reproduction Ledger

An independent record of what reproduces, what doesn't, and why. Every entry has
pre-registered expectations, negative controls, raw evidence, and a fixed claim boundary.
A control that misbehaves makes an entry INVALID, not PASS.

Operator: Claude Code (Opus 5.5) agent, run for the author, Adem Vessell. Every number below comes from
files under `evidence/`.
Review: Codex reviewed the ledger and the maintainer note before publication, without rerunning
the experiments.

| Entry | Question | Verdict |
|---|---|---|
| E001 | Does TORAX v1.4.3 reproduce the maintainers' reference output on independent hardware? | **REPRODUCED** (flagship case, all 201 output variables within rtol 1e-9). Upstream suite: 62/64 pass. |
| E002 | Why do 2 upstream restart tests fail here? | **Test-tolerance sensitivity exposed by the arm64 run; addressed on main.** The failures come from 1–2 ulp round-off in dW/dt of heat-off cases, with the test atol (1e-8) below that round-off. They reproduce on arm64 (macOS and Linux, old and new deps) and **not** on x86_64 (E005: 64/64 on a GitHub AMD EPYC 7763 runner). **Not an arm64 defect:** E004 finds the same artifact on the reference platform in another case. Main raised atol to 1e-6 (`9274e5c2`, unreleased), so no issue was filed. |
| E003 | Does the full output of every referenced case reproduce? | **REPRODUCED, with one expectation miss.** All 52 upstream-tested cases: 5 main profiles within 1e-9. Full output: no deviation beyond round-off or upstream's own tolerance. 2 QuaLiKiz cases BLOCKED. 2 non-maintained references explained. |
| E004 | Same sweep on unreleased main (`17cc32fb`) | **REPRODUCED on shared variables, within upstream's own tolerances; 2 of 6 pre-registered expectations missed (3 cases), all explained.** Upstream suite 63/63. 49/51 cases have their 5 profiles within 1e-9; the 2 TGLF-NN cases are within upstream's 5e-6. **Not validated:** the new per-model transport outputs. 46/53 references predate that schema, so no reference exists for them. |
| E005 | Do the x86_64 legs match? (GitHub runner, AMD EPYC 7763) | **All 6 pre-registered expectations held** (after one runner termination, repaired and rerun). Flagship x86 vs reference and vs arm64 within 1e-9 (worst 2.5e-11 / 1.4e-11), not bitwise. Controls six OK. Heat-off dW/dt exactly 0 on x86. Upstream suite 64/64 on v1.4.3 with release-era deps. |
| P-RAPTOR | The paper's RAPTOR benchmark (NRMSD vs RAPTOR, ITER-like L-mode 11.5 MA / 50 MW / 10 s) | **NOT EVALUATED**: no RAPTOR reference output was available locally (none in the TORAX repo). RAPTOR's availability was not checked. |

---

## E001 — Flagship reproduction on independent hardware

**Object.** google-deepmind/torax tag `v1.4.3` @ `4aea2377385ba4dfe37b0ef4396374162af1314b`.
Case `test_iterhybrid_rampup` (ITER-hybrid-like rampup, QLKNN transport, Newton-Raphson
with predictor-corrector, 0→80 s). Compared against the committed reference
`test_iterhybrid_rampup.nc`, whose embedded stamp says TORAX 1.4.0.

**Platform.** Apple M1 Max, macOS 27.0 arm64, Python 3.12.13, jax/jaxlib 0.11.2, numpy
2.5.3, CPU backend, x64 on (`evidence/E001/raw/freeze_py312.txt`, `host.txt`). Upstream CI
runs only ubuntu-latest (x86_64) with Python 3.11.

**Pre-registration.** `evidence/E001/PREREGISTRATION.md`, sha256 in `evidence/E001/SHA256SUMS`.
Disclosed: one upstream 5-profile smoke test had already passed before it was written.

### Results

| ID | Run | Expected | Observed | Verdict |
|---|---|---|---|---|
| P1 | Unmodified config vs reference, all 201 variables | 5 profiles ≤1e-9; all vars ≤1e-6; not all bitwise | 82 BITWISE, 119 within rtol 1e-9, 0 worse. Worst: `/profiles/ei_exchange` max rel 1.25e-11. Solver iteration counts bitwise equal. | PASS, stronger than expected |
| P1-cfg | Embedded config equal apart from version | equal | **Not equal.** v1.4.3 adds 3 keys absent in the 1.4.0 reference, all at defaults: `pedestal.pedestal_profile_form`, `solver.fixed_point_sufficient_decrease`, `solver.fixed_point_use_backtracking`. Every shared key is equal. | EXPECTATION MISS: schema drift, not input drift |
| C1 | Second identical run vs P1 | bitwise | 201/201 BITWISE. A later full rerun (`evidence/E001-rerun/compare/P1_rerun_vs_P1.json`) is also 201/201 bitwise vs P1. | PASS (deterministic) |
| C2 | Heating +1 % (`P_total` 20→20.2 MW) vs reference | fails 1e-9; T_e NRMSD 1e-4..1e-2 | 105 variables DIFFERENT. T_e NRMSD 6.9e-3, T_i 7.9e-4, n_e 2.2e-3, q 3.8e-3. | PASS (control detected) |
| C3 | P1 vs a different case's reference | fail | 192 SHAPE mismatches, config unequal | PASS (control detected) |
| C4a | Reference with one T_e value × (1+1e-8) | exactly 1 var at RTOL_1e-6 | exactly 1 var (`/profiles/T_e`) at RTOL_1e-6 | PASS (resolution confirmed) |
| C4b | Same × (1+1e-10) | exactly 1 var at RTOL_1e-9 | exactly 1 var at RTOL_1e-9 | PASS (no overstatement) |

**Upstream suite on the same platform** (`torax/tests/sim_test.py`, 64 cases, `-n 6`):
62 passed, 2 failed: `test_simulation_with_restart1` and `...restart2`. The same 2 fail
serially too, so it is not a parallel-run race. See E002.
Evidence: `evidence/E001/raw/sim_test_full.log`, `sim_test_junit.xml`, `restart_serial.log`.

**Scale for context.** The largest cross-platform difference (1.25e-11 relative) is about
9 orders of magnitude smaller than a 1 % change in heating power (T_e NRMSD 6.9e-3).

**Claim boundary.** Supported: TORAX v1.4.3 on macOS arm64 reproduces the maintainers'
reference for this case across its whole output, to within 1.3e-11 relative, and is
deterministic run to run. Not supported: physical validity, agreement with experiment or
RAPTOR, speed, or any case other than this one (see the upstream suite line above for the
other 63).

**Rerun.** `bash harness/reproduce_E001.sh` → six `OK` lines expected (verified 2026-09-25).

---

## E002 — Attribution of the two restart-test failures

**Mechanism observed.** Both failing cases (`test_psichease_prescribed_jtot`, `..._johm`)
switch the heat equations off (`evolve_ion_heat=False`, `evolve_electron_heat=False`), so
thermal energy should stay constant. The reference stores `W_thermal_e/i` as exactly
constant and `dW_thermal_*_dt` as exactly 0.0. On arm64, `W_thermal_e` and `W_thermal_i`
change by 1 and 2 ulp respectively (1.49e-8 J and 2.98e-8 J on ≈1.2e8 J, where 1 ulp = 1.49e-8 J; ~1e-16 to 2.5e-16 relative) at one step. (Earlier text said "1 ulp" for both; corrected 2026-09-26.)
Divided by dt ≈ 0.178 s, that gives `dW_thermal_dt` = 2.514e-7 W. The restart test compares
every output variable with `xr.testing.assert_allclose` defaults (rtol 1e-5, **atol 1e-8**),
and rtol cannot help when the reference is exactly 0. So atol 1e-8 W sits below the
round-off floor of a finite-differenced ~1e8 J quantity. The non-restart sim tests for these
cases pass, because they check only 5 profiles.
The same 4 variables (and nothing else) fail in the non-restart full-output comparison too
(`evidence/E001/compare/N_*.json`). The deviation exists in every run on this platform; only
the restart test looks at it.

**Pre-registration.** `evidence/E002/PREREGISTRATION.md` + `PREREG_ADDENDUM_M3b.md`
(hashes in `evidence/E002/SHA256SUMS`). Hypothesis H: platform floating point, not
dependency drift. Dependencies were pinned to the CI date with
`uv --exclude-newer 2026-07-03T17:00Z` (jax 0.10.2, numpy 2.4.6, xarray 2026.4.0), Python 3.11.

| ID | Platform | Expected under H | Observed | Verdict |
|---|---|---|---|---|
| M1 | macOS arm64, Py 3.11.13, CI-era deps, full suite | restart1/2 fail, rest pass | 62 pass, restart1/2 fail on the same 4 dW/dt variables | consistent with H. Rules out jax 0.11 / numpy 2.5 drift. |
| M2 | Linux arm64 (Docker), Py 3.11.15, CI-era deps | restart1/2 fail if architecture drives it | restart0/3 pass, restart1/2 fail on the same 4 variables | consistent with H. Rules out macOS-specific libm. |
| M3 | Linux x86_64 via qemu | all pass | jaxlib refuses to load (needs AVX, qemu lacks it) | **BLOCKED** |
| M3b | Linux x86_64 via colima vz + Rosetta | all pass | same AVX refusal | **BLOCKED** |

**Conclusion (narrow).** The two failures follow arm64 on both macOS and Linux, with both
CI-era and current dependencies. Only the upstream CI's green checks (ubuntu x86_64) support
x86_64 passing; this ledger has not reproduced that. It is a test-tolerance fragility on a
platform CI does not cover, not a physics defect: the deviation is ~1e-16 relative on W.
A likely but **untested** mechanism is FMA contraction or instruction-order differences in
XLA's arm64 CPU codegen.

**Updated by E004 (2026-09-25).** On main, the reference platform's own file for
`test_psichease_ip_chease_vloop` holds the same 2.514e-7 W dW/dt artifact, and arm64 gives
exactly 0. So the ulp-level artifact appears on both platforms. What E002 establishes is a
restart-test tolerance sensitivity that this arm64 run exposed and current main addresses.
It does **not** establish an arm64 defect. "Follows arm64" above holds only for these two
cases in these environments.

**M3 closed by E005 (2026-09-26).** On a GitHub-hosted x86_64 runner (AMD EPYC 7763), restart0-3
all pass with release-era deps, and the heat-off dW/dt is exactly 0. See E005.

### E002 follow-up (2026-09-25): duplicate gate before filing — killed the filing

The author approved filing the draft. The pre-filing check then looked at commits and PRs,
not just issues (the first gate searched issues only, which was incomplete), and found:

- PR google-deepmind/torax#2351 "Fix flaky sim restart test" (`2720fdfb`, 2026-08-10) set
  `atol=1e-8`. That equals xarray's default (checked: `assert_allclose(..., rtol=1e-05,
  atol=1e-08)` in xarray 2026.4.0 and 2026.7.0), so on its own it changes nothing.
- Commit `9274e5c2` (2026-08-18, "Convert transport models from sequence to mapping...")
  raised that same line to `atol=1e-6`, above the 2.5e-7 W round-off seen here.
- Current main `17cc32fb` (2026-09-24) on this Mac (Py 3.12, jax 0.11.2): restart0-3 all
  **PASS** (`evidence/E002/raw/MAIN_17cc32f_macos_arm64_restart.log`).

Verdict: the upstream issue would duplicate a fix that is already made (only unreleased;
v1.4.3 is still the latest release). **Not filed.** The draft is kept privately. O2 below is still structurally present on main (`output.py` L431/L438), but it was
not part of the approved issue and would need its own OK.

### Secondary observation O2 — stitched restart outputs keep the old run's metadata

With `restart.stitch=True`, `output.py:475` writes the new run's config into the output
attrs. Then `output.py:480-482` stitches through `concat_datatrees`, which keeps the
*previous* file's attrs. The stitched file produced by v1.4.3 therefore reports
`torax_version: "1.3.0"`, `t_initial: 0.0` and `restart: null`
(`evidence/E001/runs/R_test_psichease_prescribed_jtot.nc`). This may be intended (it
presents one continuous history), but the file no longer records which version produced
its second half, or that a restart happened. Low severity, provenance only.

---

## E003 — Full-output sweep across all 56 referenced cases

**Object.** v1.4.3, same platform and venv as E001. The 56 cases with both `<case>.py` and
`<case>.nc`, plus one sweep-level negative control. Pre-registration
`evidence/E003/PREREGISTRATION.md` (sealed; hash in `evidence/E003/SHA256SUMS`). Instrument
hashes matched the E001 manifest before the run. The first automated check printed a false
diff because of line order; a per-file recheck confirmed both files unchanged.
Outputs: `evidence/E003/sweep_results.json`, `sweep_table.md`, `explained.json`,
`compare/`, `logs/`.

**Controls.**
- Runner consistency: the sweep's `test_iterhybrid_rampup` is 201/201 BITWISE vs E001 P1. PASS.
- `CTRL_rampup_heat_plus1pct` (+1 % heating) is DIFFERENT on all 5 main profiles
  (T_e max rel 9.7e-3). PASS: the control was caught.

**Results by pre-registered expectation.**

| # | Expectation | Observed | Verdict |
|---|---|---|---|
| 1 | Sweep rampup bitwise = E001 P1 | 201/201 BITWISE | held |
| 2 | Negative control DIFFERENT | DIFFERENT | held |
| 3 | QuaLiKiz cases BLOCKED | both RUN_ERROR: `model_name 'qualikiz'` is not a registered transport model in this install (optional QuaLiKiz support absent) | held (the mechanism is an unregistered model, not a missing binary) |
| 4 | Upstream-tested cases: 5 profiles at upstream tolerance | **52/52 within rtol 1e-9**, including the 4 cases where upstream loosens tolerance to 1e-8..5e-6 | held, stronger than required |
| 5 | ≥80 % of cases within rtol 1e-9 on *every* variable; misses clustered at exact-zero/near-zero values | **20/52 (38 %)** clean on every variable. Every miss in an upstream-tested case is explained below; none is a physics-scale deviation. | **frequency MISSED, mechanism HELD** |
| 6 | Schema diffs reported, not scored | 0 variables only-in-candidate / only-in-reference in any compared case | held |

**Explaining the 32 upstream-tested cases that miss rtol 1e-9 somewhere.**
`harness/explain.py` measures each miss against the variable's own scale
(peak_rel = max|Δ| / max|ref|). *Disclosure:* this classifier was written after early sweep
output showed the pattern, so it is post hoc. Its 1e-9 cut-off is the same number as the
pre-registered tier.

| Class | Cases | What it is |
|---|---|---|
| Near-zero round-off only (peak_rel < 1e-9) | 26 | rtol with atol=0 fails on near-zero entries. Example: `j_external` in `test_iterhybrid_predictor_corrector`: rel 0.25 on a tail value ~4e-9 A/m², absolute 9.9e-10, NRMSD 8.3e-16. |
| Exact-zero reference (dW/dt, heat equations off) | 4 | `test_psichease_prescribed_jtot`, `_johm`, `_jtot_vloop`, `_ip_parameters_vloop_varying`: same mechanism as E002. Two of these are not in the restart test, so upstream never sees them. |
| Small, within upstream's own tolerance | 1 | `..._rotation`: turbulent-transport coefficients peak_rel ≤ 2.4e-8; upstream sets rtol 5e-6 for this case. |
| Solver residual | 1 | `..._mavrin_n_e_ratios_lengyel`: `edge/solver_residual` values of ~3e-6..3e-5 differ at peak_rel ≤ 2.7e-7. It is the residual of an iterative root solve, not a physical output. |

**The two cases upstream does not compare against their reference.**
- `test_iterhybrid_lh_transition` is **disabled upstream** (`sim_test.py` ~L296:
  `TODO(b/331171303): Reinstate when fixed`). Here Newton inner-iteration counts differ by up
  to 4 at some steps, and outputs then differ at solver-tolerance scale. The largest are
  `ei_exchange` peak_rel 2.0e-5, `P_ei_exchange` 9.9e-6 and `P_SOL_i` 2.2e-6; T_e/T_i are
  ≤ 6.6e-8. Reading: round-off changes a convergence decision, and the trajectory then
  diverges at the solver's tolerance (residual_tol 1e-5). Consistent with why upstream parked it.
- `test_iterhybrid_radiation_collapse`: upstream's `test_low_temperature_error` says it does
  "not compare the results to a reference solution". Both runs end in
  LOW_TEMPERATURE_COLLAPSE at t = 1.2066 s here vs 1.2063 s in the reference, with 38 vs 31
  adaptive steps, so full-output SHAPE mismatch is expected. The physical outcome (collapse,
  time to within 3e-4 s) matches.

**Claim boundary.** Supported: for TORAX v1.4.3 on macOS arm64, every upstream-tested case
reproduces its committed reference across the whole output. The only deviations are
near-zero round-off, exact-zero derivative scalars, one solver residual, and one case already
within upstream's loosened tolerance. Not supported: x86 behaviour (E002 blocked leg),
current main, QuaLiKiz-coupled runs, physical validity.

**Resulting upstream-useful observation (not filed, needs the author's OK).** Four
heat-disabled psichease cases store round-off-level dW/dt on arm64 where references hold
exact zeros. Main's restart-test atol now covers two of them. The other two are never
compared on full output upstream, so nothing is failing and there is nothing to report.
Kept as a note only.

---

## E004 — Full-output sweep on current main (unreleased)

**Object.** `main` @ `17cc32fb` (2026-09-24, still remote HEAD on 2026-09-25), `.venv-main`
(Py 3.12.13, jax 0.11.2, fusion-surrogates **0.4.7**, where v1.4.3 has 0.4.6). 55 cases on main
with `.py` + `.nc`; 51 are upstream-tested. Since v1.4.3, 52 of 54 shared references were
regenerated. Pre-registration `evidence/E004/PREREGISTRATION.md` was sealed together with the
hashes of `sweep.py` and `explain.py`. **The scale-aware classifier was pre-registered this
time**, unlike E003. `run_case.py` and `compare.py` are unchanged since E001 (per-file hash check).

| # | Expectation | Observed | Verdict |
|---|---|---|---|
| 1 | Upstream `sim_test.py` all pass | **63 passed, 0 failed** (`evidence/E004/raw/sim_test_full.log`). Includes restart1/2. | held |
| 2 | Negative control DIFFERENT | SHAPE on all compared variables: +1 % heating changes main's step count | held (stronger rejection than predicted) |
| 3 | QuaLiKiz RUN_ERROR | both RUN_ERROR, `'qualikiz'` not a registered transport model | held |
| 4 | 51/51 upstream-tested: 5 profiles within 1e-9 | **49/51.** The two TGLF-NN cases: max rel psi 1.8e-6, q 1.5e-6, T_e 8.2e-7. Upstream's own tolerance for both is **5e-6**, so it passes upstream too. | **MISSED for 2 cases**, explained below |
| 5 | No NOTABLE (peak_rel ≥ 1e-6) deviation in upstream-tested cases | 3 cases NOTABLE: the 2 TGLF-NN cases and `test_psichease_ip_chease_vloop` | **MISSED for 3 cases**, explained below |
| 6 | `lh_transition` SMALL/NOTABLE; `radiation_collapse` SHAPE | lh_transition only SMALL (peak_rel ≤ 6.3e-9, better than v1.4.3); radiation_collapse SHAPE | held |

**Full output, 51 upstream-tested cases.** 36 clean on every common variable. 11 miss only on
near-zero round-off. 1 solver residual (lengyel, SMALL). 2 TGLF-NN. 1 vloop dW/dt.

**Explaining the misses.**
- **TGLF-NN cases** (`..._tglfnn_ukaea`, `..._tglfnn_ukaea_rotation`): five profiles within
  ≤1.8e-6, and transport coefficients up to peak_rel 2.5e-5 (`chi_turb_e`), which upstream does
  not check. On v1.4.3 (fusion-surrogates 0.4.6) the same cases matched at 1e-9 (E003). Main's
  commit `dd68448b` loosened these tests to 5e-6 "due to f32 inference and sensitivity between
  environments". So the maintainers already know this sensitivity exists; the ledger only
  measures its size on arm64. Not new.
- **`test_psichease_ip_chease_vloop`: E002's mechanism, mirrored.** Main's regenerated
  reference holds `dW_thermal_dt` = **2.514e-7 W** at one step, while arm64 gives exactly 0.
  That is the same 2.514e-7 W value E002 saw, in the opposite direction. W_thermal (~9.4e7 J) is
  identical to all printed digits. The pre-registered classifier calls it NOTABLE because the
  variable's "peak" is itself round-off. Physically it is ~1e-16 of W. This **updates E002**:
  the heat-off dW/dt artifact appears on the reference platform too, so it is platform
  round-off in both directions, not an arm64 defect. (On main, `_prescribed_jtot`/`_johm` now
  match at ≤1e-9.)

**Unexpected: reference schema drift (not pre-registered, descriptive only).** 46 of 53
compared references lack main's new `/auxiliary/turbulent_transport/<model>/...` per-model
outputs (docstring: "turbulent transport per-model outputs"). 21 of them still carry old
`/profiles/chi_itg_e`, `chi_tem_e`, `D_itg_e`… per-mode fields that main no longer writes
there. It is **not a pure move**: matching leaf names differ in value (e.g. `chi_tem_e` peak_rel
7.5, `D_itg_e` 5.5), so the new fields are different quantities, most likely raw per-model
outputs before the patching and clipping that `/profiles` totals include. This was not
verified in code. The shared totals (`/profiles/chi_turb_e` etc.) still reproduce. Only
`test_iterhybrid_rampup` has a regenerated full schema, and it is the only reference upstream
compares on full output. Impact: none on upstream's tests; it only affects full-output users
like this ledger.

**Claim boundary.** Supported: on arm64, unreleased main reproduces its committed references
for every upstream-tested case within upstream's own per-case tolerances, and the upstream
suite passes 63/63. Not supported: x86, physics validity, per-model transport output
correctness (no valid reference exists for it), and anything about v1.4.3 vs main outputs.

---

## E005 — x86_64 legs on a GitHub-hosted runner

**Object.** v1.4.3 @ 4aea237 on GitHub Actions `ubuntu-24.04`, x86_64, **AMD EPYC 7763**
(AVX, AVX2, FMA; no AVX-512), 4 vCPU, 16 GB. Workflow `.github/workflows/x86-reproduction.yml`
runs `harness/ci_x86.sh` in the public repo. Pre-registration `evidence/E005/PREREGISTRATION.md`
was sealed 02:46:02 UTC and committed in `8ebd7fa`, the commit that triggered the first run.

**Instrument repair.** The first run (36212744690) was terminated (exit 143) about 19 minutes
into X2 and uploaded nothing. No result was seen. `PREREG_ADDENDUM_1.md` was sealed before the
rerun and changed only the instrument: two jobs with separate uploads, `-n 2`, a memory log,
and `ubuntu-24.04` pinned. The rerun (36214030775, commit `bf64cb1`) completed. Its X2 memory log
peaks at 15.6 of 16 GB with 2 workers, which fits memory exhaustion at `-n 4` (not proven).

| ID | Expected | Observed (`evidence/E005/ci/`) | Verdict |
|---|---|---|---|
| X1a x86 vs maintainer reference (E001 deps) | all 201 within 1e-9, not all bitwise | 99 BITWISE, 102 within 1e-9; worst `ei_exchange` 2.5e-11; solver iteration counts bitwise | held |
| X1b x86 vs arm64 E001 P1 | within 1e-9, **not** bitwise | 82 BITWISE, 119 within 1e-9; worst `FFprime` 1.4e-11 | held |
| X1c x86 repeat | bitwise | 201/201 BITWISE | held |
| X1-ctrl E001 controls via `reproduce_E001.sh` | six OK | six OK | held |
| X3 heat-off `dW_thermal_dt` | exactly 0, matching reference | all 0; the 4 dW/dt scalars BITWISE vs reference; vs arm64 they differ by exactly E002's 2.514e-7 W | held |
| X2 upstream `sim_test.py`, release-era deps (jax 0.10.2, Py 3.11) | 64/64 incl. restart1/2 | **64 passed**, 0 failed | held |

**What this settles.** For v1.4.3, the E002 restart failures and the heat-off dW/dt flip appear
on arm64 and not on this x86 CPU. Together with E004 (the reverse artifact in a reference file
written on the maintainers' platform), the picture is platform-dependent last-bit round-off in
a quantity that should be exactly zero. The tests' old atol could not absorb it; main's can.
Cross-architecture, the flagship case differs by at most 1.4e-11 relative.

**Claim boundary.** One x86 CPU model (AMD EPYC 7763, no AVX-512). XLA compiles for the host
CPU, so other x86 CPUs may differ in the last bits. No physics claim.

---

## Parked: paper benchmark P-RAPTOR

```text
Status: BLOCKED
Why parked: the paper's headline verification compares TORAX to RAPTOR (NRMSD). RAPTOR
  outputs are not in the TORAX repo, so none was available locally. (An earlier version of this
  line also said RAPTOR "is not openly distributed". That was never verified and was removed
  on 2026-09-26.)
Gate to reopen: RAPTOR reference profiles for the paper's ITER-like L-mode case (from the
  authors or a data supplement).
Current fact (2026-09-26): in google-deepmind/torax discussion #2141 a maintainer states that
  "there are currently no other publicly available configs and output files" besides the
  sim_test suite in tests/test_data. So the E003/E004 sweeps cover every public TORAX reference
  output, and no public RAPTOR output exists. The same thread gives a config that reproduces the
  paper's Figure 6 more closely (TORAX side only).
Exact next action: check the arXiv 2406.06718 ancillary files and the TORAX docs for
  published benchmark data; if none, the authors could be asked (external contact,
  needs the author's OK).
Evidence path: LEDGER.md (this section); paper https://arxiv.org/abs/2406.06718
```
