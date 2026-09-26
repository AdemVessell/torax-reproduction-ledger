# E005 addendum 1 — instrument repair after run 36212744690 (written before the rerun)

## What happened

Run 36212744690 (commit 8ebd7fa, 2026-09-26 02:46-03:09 UTC) ended with exit code 143
(SIGTERM) in the step running `harness/ci_x86.sh`. It happened about 19 minutes into X2 (the
full upstream sim suite with `-n 4`). The following `if: always()` upload step was skipped,
which fits the runner itself being terminated. No artifact exists. **No E005 result was seen:**
the X1/X3/control outputs died with the runner, and the job log does not print them. The
likely cause is memory pressure from 4 parallel JAX-compiling workers on a 16 GB runner. It was
not confirmed.

## Repair (instrument only; expectations unchanged)

- Two independent jobs, each uploading its own evidence:
  - `x1x3`: X1a/X1b/X1c, X1-ctrl, X3 → artifact `e005-x1x3`
  - `x2`: full upstream sim suite, now `-n 2`, with a 30 s memory log → artifact `e005-x2`
- Each job records its own host CPU (the two jobs may land on different CPU models).
- `runs-on: ubuntu-24.04` (pinned) instead of `ubuntu-latest`, which GitHub moves to Ubuntu 26
  from 2026-10-19. Run 36212744690 was on the Ubuntu 24.04 image `20260920.314`, so this keeps
  the same OS.
- setup-uv cache disabled (clean installs every run).

Every expectation in `PREREGISTRATION.md` stands unchanged. All legs rerun in full. If a job is
terminated again, its legs are BLOCKED, not PASS.
