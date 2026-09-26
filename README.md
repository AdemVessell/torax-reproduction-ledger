# TORAX Reproduction Ledger

An independent check of whether [TORAX](https://github.com/google-deepmind/torax), Google
DeepMind's open-source tokamak transport simulator, reproduces its own committed reference
outputs on Apple silicon, a platform its CI does not run on.

Each entry's expectations were written and SHA-256 sealed before its graded runs. Every
comparison has negative controls, and the misses are reported next to the passes.

Summary page: [arkhē.org/torax](https://www.xn--arkh-eva.org/torax/)
Full record: [`LEDGER.md`](LEDGER.md)

## Results

| Entry | Question | Result | Pre-registered expectations |
|---|---|---|---|
| E001 | Does the flagship ITER-hybrid rampup case reproduce on independent hardware? (v1.4.3) | All 201 output variables within relative 1e-9 (worst 1.25e-11). Repeat runs are bit-for-bit equal. | 6 of 7 held |
| E002 | Why do 2 upstream restart tests fail on arm64? | Their absolute tolerance (1e-8) is below ulp-level round-off in dW/dt for heating-off cases. Current main raised it to 1e-6 and they pass. | Reproduced on arm64 (macOS, Linux); does not occur on x86 (E005) |
| E003 | Does the full output of every referenced case reproduce? (v1.4.3) | 52/52 maintainer-tested cases within 1e-9 on the 5 main profiles | 5 of 6 held; all-variable target missed (20/52) |
| E004 | Does unreleased main reproduce its references? (`17cc32fb`) | Upstream suite 63/63. 49/51 within 1e-9, 2 TGLF-NN cases within the maintainers' 5e-6. New per-model outputs not validated. | 4 of 6 held |
| E005 | Do the x86_64 legs match? (GitHub runner, AMD EPYC 7763) | Flagship within 1e-9 of the reference and of arm64 (worst 1.4e-11 cross-architecture). Heat-off dW/dt exactly 0. Upstream suite 64/64 on v1.4.3. | 6 of 6 held (after one runner termination, repaired and rerun) |
| RAPTOR | The paper's RAPTOR benchmark | Not evaluated: no reference output available | — |

## Rerun E001

Needs `git` and [`uv`](https://docs.astral.sh/uv/). It takes about a minute on an M1 Max.

```bash
bash harness/reproduce_E001.sh
```

The script clones TORAX v1.4.3, installs it into `.venv` (Python 3.12), runs the flagship
case plus the controls, and prints six `OK` lines. Dependencies resolve at install time. The
versions used here are in `evidence/E001/raw/freeze_py312.txt`, and newer ones can move results
slightly (E004 shows one example).

The sweeps (E003, E004) use `harness/sweep.py` and `harness/explain.py`. Their commands are
in `LEDGER.md`.

The x86 legs (E005) run in GitHub Actions: open **Actions → x86 reproduction (E005) → Run
workflow**, or push a change under `harness/`. Each job uploads its evidence as an artifact.

## Check the hashes

```bash
shasum -a 256 -c evidence/E001/SHA256SUMS evidence/E002/SHA256SUMS evidence/E003/SHA256SUMS evidence/E004/SHA256SUMS evidence/E005/SHA256SUMS
shasum -a 256 -c MANIFEST.sha256
```

The pre-registration files are byte-identical to what was sealed. The E004 seal also covers
`harness/sweep.py` and `harness/explain.py`.

## What is here and what is not

- `harness/`: the runner, the all-variable comparator, the comparator controls, the sweep and
  the miss classifier.
- `evidence/E00N/`: sealed pre-registrations, comparison reports, run metadata, test logs and
  pinned dependency lists. E001's NetCDF outputs are included.
- Not included: the E003/E004 NetCDF outputs (~130 MB; rerunning the sweeps regenerates them)
  and private working notes.
- Local paths and machine names were stripped from logs and JSON files for publication. Sealed
  files were not modified.

## Limits

- Software reproducibility on one arm64 machine and one x86 CPU model. No claim about physical
  validity or agreement with experiment.
- x86 was checked on one CPU model (AMD EPYC 7763, no AVX-512). JAX compiles for the host CPU, so
  other x86 CPUs may differ in the last bits.
- No RAPTOR comparison and no speed claim.
- Main's new per-model transport outputs have no reference yet, so they are not validated.
- E003's miss classifier was written after seeing early results; E004 repeated it pre-registered.

## Provenance

Author: Adem Vessell. The runs were executed by Claude Code, an AI coding agent, under the
author's direction. Codex reviewed the ledger and the maintainer note before publication,
without rerunning the experiments. Every number in the ledger comes from files in `evidence/`.

This is an independent check, not affiliated with or reviewed by Google DeepMind or the TORAX
maintainers. TORAX is Apache-2.0 and is not included here. This repository's own scripts and
text are MIT licensed.
