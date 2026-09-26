# E005 pre-registration — the x86_64 legs, on a GitHub-hosted runner

Written before any x86 run. Hash in `E005/SHA256SUMS`. It is also committed to the public repo
before the workflow's first run, so the commit timestamp is an independent seal.

## Object

- TORAX tag v1.4.3 @ 4aea2377, as in E001-E003.
- Runner: GitHub-hosted `ubuntu-latest`, x86_64. CPU model and AVX/AVX2/FMA/AVX-512 flags are
  recorded (`ci/host_cpu.txt`, `ci/cpu_flags.txt`). XLA compiles for the host CPU, so the runner's
  CPU is part of the object.
- Workflow `.github/workflows/x86-reproduction.yml` runs `harness/ci_x86.sh`. Evidence is
  uploaded as the `e005-x86-evidence` artifact and copied to `evidence/E005/ci/`.
- `harness/run_case.py` and `harness/compare.py` are unchanged since E001.

## Legs and expectations

| ID | What | Expected | Reading if not |
|---|---|---|---|
| X1a | Flagship `test_iterhybrid_rampup`, E001's exact dependency versions (Py 3.12), vs maintainer reference | All 201 variables within rtol 1e-9. Not all BITWISE. | Worse than 1e-9 on x86 would mean arm64 matched the reference better than x86 does. |
| X1b | Same x86 output vs E001's arm64 output (`evidence/E001/runs/P1.nc`) | All within rtol 1e-9. **Not** bitwise: architecture changes last bits. | BITWISE means architecture has no effect on this case, which weakens the E002 mechanism story. |
| X1c | x86 repeat run vs X1_P1 | BITWISE (deterministic) | Nondeterminism on x86. X1a/X1b become INVALID. |
| X1-ctrl | `harness/reproduce_E001.sh` on x86 (E001's controls) | Six `OK` lines | Any UNEXPECTED makes X1 INVALID. |
| X3 | Heat-off `test_psichease_prescribed_jtot`, E001 deps: `dW_thermal_dt` | **Exactly 0 everywhere**, matching the reference (arm64 gave 2.514e-7 W at one step) | Nonzero on x86 means the ulp flip is not arm64-specific for this case. The E002 attribution weakens further. |
| X2 | Full upstream `sim_test.py` on v1.4.3, deps pinned to 2026-07-03 (Py 3.11), the release-era setup | **64/64 pass**, including restart1/2 (reproduces maintainers' CI) | restart1/2 failing on x86 **falsifies** E002's "follows arm64". Other failures are findings to explain. |

A leg whose install or run fails is BLOCKED, not PASS. Any instrument repair is recorded, and
the affected legs are rerun in full.

## Claim boundary

- Supports: on this runner's CPU, how x86 compares with the maintainer reference and with
  arm64, and whether E002's two restart failures reproduce on x86.
- Does not support: all x86 CPUs (a runner with other SIMD features may differ in last bits),
  physics validity, or current main.
