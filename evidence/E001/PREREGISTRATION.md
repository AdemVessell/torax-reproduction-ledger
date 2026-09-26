# E001 pre-registration — TORAX v1.4.3 flagship case, independent hardware

Written before the E001 flagship runs. Hash recorded in `E001/SHA256SUMS`.

## Object

- Code: google-deepmind/torax tag v1.4.3, commit 4aea2377385ba4dfe37b0ef4396374162af1314b
- Case: `torax/tests/test_data/test_iterhybrid_rampup.py` (ITER-hybrid-like rampup,
  QLKNN transport, Newton-Raphson + predictor-corrector, 0→80 s)
- Reference: `torax/tests/test_data/test_iterhybrid_rampup.nc` as committed at that tag
  (its embedded config says it was written by TORAX 1.4.0)
- Platform: Apple M1 Max, macOS arm64, JAX CPU backend (upstream CI reference is
  presumed Linux x86-64; not verified)

## Disclosure

A smoke run of the upstream pytest case `test_iterhybrid_rampup` (5 profiles, rtol 1e-9)
already PASSED before this file was written. So the upstream 5-profile result below is not
blind. The full-output comparison and every control are blind.

## Runs, expectations, interpretation

| ID | Run | Expected | If it fails |
|---|---|---|---|
| P1 | Unmodified config vs committed reference, all variables | Upstream 5 profiles meet rtol 1e-9. Full output: every common variable within rtol 1e-6. Not all BITWISE. Embedded config equal apart from version. | Worst tier and variable are the finding. Cross-platform agreement holds for the 5 tested profiles but not the full output. |
| C1 | Same config, second run, vs P1 | BITWISE on all variables | Nondeterminism on one machine. It would invalidate reading P1 as a cross-platform result. |
| C2 | `sources.generic_heat.P_total` 20e6→20.2e6 (+1 %) vs reference | Must NOT meet rtol 1e-9; T_e NRMSD order 1e-4..1e-2 | A +1 % physics change is invisible, so the comparator or run path is broken. E001 is INVALID. |
| C3 | P1 output vs a different case's reference (`test_iterhybrid_predictor_corrector.nc`) | Must fail (SHAPE or DIFFERENT, config unequal) | The comparator cannot tell cases apart. E001 is INVALID. |
| C4a | Reference vs reference with one `/profiles/T_e` value × (1+1e-8) | Exactly 1 variable leaves BITWISE. Its tier is RTOL_1e-6 (fails 1e-9). | Comparator misses a change above the upstream tolerance. INVALID. |
| C4b | Same, but × (1+1e-10) | Exactly 1 variable at RTOL_1e-9 (passes the upstream tolerance, not bitwise) | Comparator resolution is misreported. INVALID. |

A control that fails makes E001 INVALID, not a PASS. Any repair to the instrument is
recorded, the expectations are fixed again, and every run is repeated.

## Claim boundary (fixed in advance)

- Supports: TORAX v1.4.3 on this arm64 machine reproduces the maintainers' committed
  reference output for this case, to the measured tier.
- Does not support: physical validity, agreement with experiment, agreement with RAPTOR
  (the paper's benchmark; RAPTOR outputs are not in the repo), speed claims, or other cases.
