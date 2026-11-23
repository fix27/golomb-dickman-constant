# VERIFICATION — 40000-v2 (v27)

What was checked, with what, on what, and what was **not** checked. Nothing in
this file is inferred from an intention to run something.

## Environment

```text
platform      Windows-11-10.0.26300-SP0
python        3.15.2
python-flint  0.9.0
mpmath        1.4.1
CPUs          8 logical (all timings below are single-core unless stated)
```

`python golomb_dickman_27.py test` prints the environment and an API self-test,
then runs the exact rational tests. All pass:

```text
API-selftest: OK
lemma7_exact_recurrence_test():
  OK: 3 rational z values × 16 levels; exact identities hold
contraction_identity_test():
  OK: S→J contraction verified for x ∈ {1/7, 1/3, 2, 17/5}, n=0..3
contraction_symbolic_test():
  OK: P_{2m+1} = R_m and Q_{2m+1} = S_m as polynomial identities for m = 0..6
```

## Published plan (unchanged from v26)

```text
D = 40000, G = 30
nodes   = 241688     K_L = 117064     K_R = 124623
h       = 9.173124908556929e-05
Ebits   = 133010     S   = 133074
chunk   = 200  →  1209 chunks
```

`make_plan(40000, 30)` reproduces these values in this build, which is the
first check every level depends on.

## Level A — artefact consistency  → **PASS**

```bash
python verification/verify_40000.py
```

```text
OK: 40000 digits certified (Level A)
  certificate: 40000-v2/golomb_dickman_40000_certified.txt
  scale: lam_lo/2^133074 .. lam_hi/2^133074
  width: 5.492 x 10^-40043  (< 10^-40042), 42 guard digits beyond the 40000th place
  b-file: 40000 terms, indices 0..39999
  first 102 digits match OEIS A084945
  SHA-256: MATCH (pinned in this script):
    8892c0715f1afbb271c9f07cc9658cea0f3ca83c2dda3ec7d23b447dc908de9c  golomb_dickman_40000_certified.txt  [LF]
    fbae757900983bd4fb6421c5f27bf9602af1a1bfc013e4c501bb9da2b5a65327  golomb_dickman_40000_digits.txt     [LF]
    c73af643198da299d2e624e3c2f69d05439efcddbbefa7cec176ac63f993bed3  b084945.txt                         [LF]
```

`--strict-lf` also passes on this tree. The same script now reports
`CRLF x N (normalised to LF for hashing)` instead of failing when a file has
CRLF, which is the behaviour change that closes the original defect: the
published hashes are LF hashes, and the v2 tree stores LF bytes.

**Interval width and guard digits.** The requirement for this sprint was a
width near `10^-40043` with at least 64 guard bits in the *ladder floor*. The
published artefact was produced with `G = 30` and has width `5.492e-40043`,
i.e. **42.26 decimal guard digits**, not 64. Those are two different
quantities and the file states both rather than rounding one into the other:

* ladder floor: `ceil(D·log2 10) + 64` bits ≈ 19.3 decimal digits — a hard
  lower bound for the optional ladder, never a claim about the default run;
* published artefact: 42.26 decimal guard digits at `G = 30`.

Producing ≥ 64 decimal guard digits would need a larger `--guard` (a different
`S`, therefore a different certificate). It is supported but was not run here.

## Level B — full Arb replay  → **NOT RUN at 40,000 digits**

```bash
python verification/full_arb_replay_40000.py --jobs 16 --chunk 200 --json level_b.json
```

This recomputes all 1209 chunks from `make_plan(40000, 30)`, with `ckpt=None`
(no checkpoint directory is created or read), assembles the interval with
`certify()`, and compares it with the published certificate. It is the same
order of work as the production run; on this 8-CPU machine that is a
multi-hour job that was not executed.

What *was* executed is the same code path on a certificate small enough to
finish, to prove the harness works and that the comparison is not vacuous:

```bash
python golomb_dickman_27.py certify --digits 120 --jobs 2 --ckpt %TEMP%/gd_v27_120 --out %TEMP%/gd_v27_120.txt
python verification/full_arb_replay_40000.py --cert %TEMP%/gd_v27_120.txt --jobs 2 --chunk 32
```

```text
  replay width ~2^-532, published width ~2^-532
  comparisons: digits_equal=OK, lo_agrees_to_D=OK, hi_agrees_to_D=OK,
               intervals_overlap=OK, replay_proves_digits=OK
Level B verdict: PASS
LEVEL B: PASS (49 chunks, 120 digits)
```

The comparison is not satisfied by construction: it requires the replayed
interval to prove all `D` digits on its own, to agree with the published
endpoints to better than one unit in the `D`-th place, and to overlap the
published interval. A change of `G` makes the replay refuse before computing
anything (`S` mismatch).

A cheap preflight (no node is evaluated) confirms that the replay would
compare the right objects:

```text
plan S 133074   cert S 133074   D 40000
nodes 241688    tiling 241688   chunks 1209 (chunk = 200)
Level B preflight: OK
```

**Projected cost of the 40,000-digit replay.** Measured single-core wall
times with this build: `D=2000` 33.3 s (10,490 nodes, `Ebits=6777`), `D=3000`
91.3 s (15,599 nodes, `Ebits=10099`), `D=6000` 616.4 s (31,742 nodes,
`Ebits=20064`). A power-law fit `time ∝ nodes·Ebits^1.75` puts `D=40000` at
≈ 35 core-hours, ≈ 2.6 h on 16 cores at 85% efficiency. This is an estimate
from three points, not a measurement, and it is labelled as such everywhere it
appears.

## Level B′ — checkpoint audit  → **PASS at 60 digits, NOT RUN at 40,000**

A real legacy directory from `40000/golomb_dickman.py` (51 chunks, 60 digits)
was copied, migrated and audited:

```bash
python golomb_dickman_27.py migrate-checkpoints --ckpt %TEMP%/gd_legacy_60 --digits 60
python golomb_dickman_27.py audit-resume --digits 60 --jobs 1 --ckpt %TEMP%/gd_legacy_60
```

```text
migrated meta.pkl -> meta_v13.json (51 chunks, AUDIT ONLY)
  NOTE: checkpoint source hash differs from this build; the plan matches, provenance is recorded but not trusted.
  NOTE: migrated legacy checkpoints; audit-only
WARNING: accepted 51/51 checkpoint chunks without recomputation; this is NOT a proof-bearing mode
strict interval width ~ 2^-331 ≈ 10^-99.6
discretisation bound B ≈ 10^-111, tails ≈ 10^-100 / 10^-101
ALL 60 DIGITS PROVEN (floor(lo·10^D) == floor(hi·10^D))
OEIS A084945 cross-check (first 60 digits, informational only - input NOT verified): OK
CERTIFICATE: NONE (AUDIT ONLY)
```

`MIGRATION.json` records `"certificate": "NONE - AUDIT ONLY"` and the note
that the chunks were not recomputed. The 40,000-digit legacy directory was not
migrated or audited here.

## Level C — independent quadrature  → **PASS at 60 digits**

```bash
python verification/crosscheck_1000_mpmath.py --digits 60 --jobs 2
```

```text
tanh-sinh: 1.1s at 120 working digits, tail < 1e-120
gauss-legendre: 1.9s at 120 working digits, tail < 1e-120
agreement between tanh-sinh and gauss-legendre: 80 leading digits
agreement with golomb_dickman_40000_digits.txt: 80 leading digits
OK: 60 digits reproduced independently (Level C, numerical)
```

The two rules share only the integrand, not the node placement or the
extrapolation, so agreement is evidence that the Arb pipeline is not
reproducing a shared bug in a single quadrature scheme.

A 1,000-digit run (`--digits 1000 --jobs 4`) is a separate, longer job. It was
started locally and had not finished at the time of writing; no result is
claimed for it. At these precisions mpmath's Gauss–Legendre node generation
dominates, so the run is measured in hours, not minutes.

## Strict/audit policy — behavioural tests

| Test | Command | Expected | Observed |
|---|---|---|---|
| strict `--resume` refused | `certify --digits 120 --ckpt ckpt120 --resume` | exit 2, message names `audit-resume` | PASS (exit 2, nothing written) |
| audit does not certify | `audit-resume --digits 120 --ckpt ckpt120` | `CERTIFICATE: NONE (AUDIT ONLY)`, no file written | PASS |
| strict ignores saved chunks | copy ckpt120, delete 24 of 49 `c_*.pkl`, run `certify` | recompute all 49, succeed | PASS (see below) |
| mixed schemas refused | `meta.pkl` + `meta_v13.json` in one directory | `CheckpointSchemaError` naming both | PASS (see below) |
| plan mismatch refused | `meta_v13.json` for `D=60, chunk=25`, run with `chunk=50` | `CheckpointSchemaError` | PASS |
| `D=500` profile run (Sprint 2 setup) | `certify --digits 500 --chunk 100 --profile FILE` | certificate + `.prof` + `.prof.txt` | PASS |

The strict "delete half the chunk files" test is the important one: it shows
that the strict path recomputes rather than quietly reusing whatever happens
to be on disk. With 25 of 49 chunk files missing, the run still recomputed
every chunk and produced the same interval:

```text
kept 25/49 chunks
strict interval width ~ 2^-532 ≈ 10^-160.1
ALL 120 DIGITS PROVEN (floor(lo·10^D) == floor(hi·10^D))
wrote ...gd_half.txt | wall 1 s
```

Mixed schemas are refused before any file is read as a chunk:

```text
CHECKPOINT ERROR: ...gd_mixed: mixed checkpoint formats (meta_v13.json and meta.pkl).
Keep one schema per directory: move the old files out, or run migrate-checkpoints.
exit code 1
```

## Performance measurements

| D | nodes | Ebits | v26 (1 core) | v27 (1 core) | proven | width (bits) |
|---:|---:|---:|---:|---:|---|---:|
| 2,000 | 10,490 | 6,777 | 36.1 s | 33.3 s | yes | 59 |
| 3,000 | 15,599 | 10,099 | 104.2 s | 91.3 s | yes | 58 |
| 6,000 | 31,742 | 20,064 | — | 616.4 s | yes | 58 |

Both builds produce the same interval width at the same `D`, so the comparison
is like for like. The gains come from the per-process caches (`eps`, `thr`,
`arb(h)`), the initializer, asynchronous checkpoints and `RS_M = 32`; they are
larger at higher precision, which is where the 40,000-digit run lives.

## Packaging  → **PASS**

```bash
python -m pip wheel --no-deps . -w %TEMP%/gdwheel
python -m pip install --no-deps --target %TEMP%/gdinstall %TEMP%/gdwheel/golomb_dickman_core-0.1.0-py3-none-any.whl
PYTHONPATH=%TEMP%/gdinstall python -m golomb_dickman_27 test
```

```text
golomb_dickman_core-0.1.0-py3-none-any.whl   47,419 bytes
module version 27 schema 13
All tests passed.
golomb-dickman.exe
```

The wheel contains only `golomb_dickman_27.py`, declares
`python-flint>=0.9,<1`, and exposes the `golomb-dickman` console script. This
is a packaging check, not a CI run: the workflow in `ci/` was never executed.

## NOT RUN — explicit inventory

| Item | Why | What would close it |
|---|---|---|
| `certify --digits 40000 --jobs 16 --chunk 200` (production) | ~35 core-hours (projected); not available here | the `compute` CI job on a 16-vCPU runner, or a machine with ~16 cores for a day |
| `full_arb_replay_40000.py --jobs 16` (Level B at 40k) | same order of work | the `replay` CI job |
| Level B′ at 40,000 digits | needs the production checkpoint directory | migrate/audit after the compute job |
| CI pipeline execution | no self-hosted 16-vCPU runner; GitHub-hosted runners are too small for the timeout | provision the runner and run the workflow |
| ≥ 64 decimal guard digits | different `G`, different certificate | decide whether to publish a wider certificate |
| Level C at 1,000 digits | long mpmath job (Gauss–Legendre node generation dominates) | let the local `--digits 1000 --jobs 4` run finish, then record its prefix agreement |

No claim of a completed 40,000-digit run, of Level B PASS, of CI PASS, or of
meeting the 8-hour target is made in this document or anywhere in the tree.

## How to finish Level B

On a 16-core Linux machine with `python-flint` installed:

```bash
cd 40000-v2
python -m pip install python-flint mpmath
python golomb_dickman_27.py test
python verification/full_arb_replay_40000.py \
    --cert golomb_dickman_40000_certified.txt \
    --jobs 16 --chunk 200 --json level_b.json
python verification/verify_40000.py --strict-lf
```

`level_b.json` contains both intervals, both widths, the five boolean checks
and the verdict. Only then may `README.md`, `PLAN.md`, this file, the OEIS
note and the paper status be changed to say Level B PASS.
