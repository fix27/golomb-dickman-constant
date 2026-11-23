# 40000-v2 — Golomb–Dickman certificate, production build (v27)

This directory is the second, audited build of the 40,000-digit certificate for
the Golomb–Dickman constant

$$\lambda \;=\; \int_0^1 e^{\operatorname{Ei}(x)}\,\frac{dx}{x}
\;=\; 0.6243299885\ldots$$

The mathematics, the plan and the certificate are unchanged from v26: for the
same `D`, `G` and `cf_min_u`, `make_plan()` produces the same grid and every
node ball is the same object. What changed is the infrastructure, and it
closes the four gaps found in the audit:

| # | Gap in the published bundle | Fix in v27 |
|---|---|---|
| 1 | `SHA256SUMS.txt` pins LF hashes, but the files on disk were CRLF, so the shipped bundle failed its own Level A check on Windows | every text write goes through `_open_text_lf()` (`newline="\n"`); `verification/verify_40000.py` hashes **LF-normalised** bytes and reports the on-disk line endings; `.gitattributes` forces `eol=lf` |
| 2 | `--resume` could feed saved pickles into a "certified" run | `certify --certify-mode {strict,audit}` (strict is the default); `certify --resume` is `SystemExit(2)` in strict mode; the audit path is a separate `audit-resume` command that prints `CERTIFICATE: NONE (AUDIT ONLY)` and never writes a certificate |
| 3 | checkpoint metadata was written by two different programs with no schema tag | `CHECKPOINT_SCHEMA_VERSION = 13`, `CHECKPOINT_FORMAT = "gd-checkpoint-v13"`, `CHECKPOINT_META_NAME = "meta_v13.json"`; legacy `meta.pkl` and `meta_v12.json` are detected, refused, and convertible only through `migrate-checkpoints`; mixed formats in one directory are always refused |
| 4 | nothing recomputed the 1209 chunks from scratch | `verification/full_arb_replay_40000.py` (and `golomb_dickman_27.py replay`) recompute every chunk from the plan alone, with no checkpoint input, and compare the assembled interval with the published certificate (Level B) |

Performance work is confined to the evaluator. `certify()` still re-checks the
assembled interval against the discretisation and tail bounds, so an
over-aggressive precision setting can only fail to prove digits; it can never
certify a wrong one.

## Files

| File | What it is |
|---|---|
| `golomb_dickman_27.py` | the whole pipeline: plan, Arb node balls, chunking, certificate, verification, CLI |
| `verification/verify_40000.py` | Level A: artefact check (digits, interval, b-file, LF-normalised SHA-256) |
| `verification/full_arb_replay_40000.py` | Level B: full Arb node replay of the 40,000-digit certificate |
| `verification/crosscheck_1000_mpmath.py` | Level C: two independent quadrature rules (tanh–sinh, Gauss–Legendre) in mpmath |
| `golomb_dickman_40000_certified.txt` | published certificate (`S=133074`, `[Λ₋, Λ₊]`, 40,000 digits), LF |
| `golomb_dickman_40000_digits.txt` | the 40,000 digits as a bare string, LF |
| `b084945.txt` | OEIS A084945 b-file, 40,000 terms `n=0..39999`, LF |
| `SHA256SUMS.txt` | checksums of this directory (regenerated for v2) |
| `PLAN.md` | the four-sprint remediation plan mapped to what is implemented |
| `VERIFICATION.md` | the verification protocol, the measured results, and what is *not* yet run |
| `pyproject.toml` | packaging for `golomb-dickman-core==0.1.0` |
| `ci/golomb_dickman_40000.yml` | Compute / Replay / Cross-check / Packaging CI template |

## Requirements

* Python ≥ 3.10 (tested on 3.15.2), `python-flint` ≥ 0.9 (tested on 0.9.0).
* `mpmath` ≥ 1.3 only for the Level C cross-check.

```bash
python -m pip install python-flint mpmath
python -c "import flint; print(flint.__version__)"
```

## Quick start

```bash
# environment self-test + exact rational Lemma-7 tests
python golomb_dickman_27.py test

# 60-digit end-to-end run (seconds); writes no checkpoint directory
python golomb_dickman_27.py smoke

# a real certificate, 120 digits, 2 workers
python golomb_dickman_27.py certify --digits 120 --jobs 2 \
    --ckpt ckpt120 --out cert120.txt

# Level A on the published bundle
python verification/verify_40000.py

# Level B on the published bundle (expensive: same work as production)
python verification/full_arb_replay_40000.py --jobs 16 --chunk 200
```

## Modes, and what they mean

### `certify` (strict, the default)

Every chunk is computed in Arb in this run. Saved chunks are never read, even
if the directory is full. `--resume` is refused:

```text
$ python golomb_dickman_27.py certify --digits 40000 --ckpt ckpt40000 --resume
ERROR: --resume is disabled in strict certificate mode.
...
exit code 2
```

`--certify-mode audit` exists so that an interrupted run can be inspected
without pretending it is a proof. It implies `--resume`, and reports

```text
CERTIFICATE: NONE (AUDIT ONLY)
```

and writes no certificate file.

### `audit-resume`

A separate command, with its own help text, for looking at a checkpoint
directory that was produced earlier (including a directory migrated from an
older schema). It always ends with `CERTIFICATE: NONE (AUDIT ONLY)`.

```bash
python golomb_dickman_27.py audit-resume --digits 40000 --ckpt ckpt40000
```

### `migrate-checkpoints`

`meta.pkl` (from `40000/golomb_dickman.py`) and `meta_v12.json` (from v26) are
not readable by a v27 run. Migration is explicit:

```bash
python golomb_dickman_27.py migrate-checkpoints --ckpt old_ckpt --digits 40000
```

It validates the legacy parameters against the current plan, checks that every
expected `c_*.pkl` exists and is well formed, refuses a partial directory, and
then writes `meta_v13.json` plus `MIGRATION.json`. The migrated directory is
**audit-only**: the chunks were produced by an older program and were not
recomputed.

### `replay`

```bash
python golomb_dickman_27.py replay \
    --cert golomb_dickman_40000_certified.txt --jobs 16 --chunk 200 \
    --json level_b.json
```

Recomputes every chunk from `make_plan(D, G)` and compares with the published
interval. `--ladder` enables the (opt-in) precision ladder; it is off by
default so that a replay reproduces the published width.

## Line endings

Canonical form is UTF-8/ASCII with LF and no BOM. `SHA256SUMS.txt` is defined
over the LF bytes.

* `golomb_dickman_27.py` writes every text artefact with `newline="\n"`.
* `verification/verify_40000.py` normalises CRLF → LF before hashing and prints
  the detected line endings, so a Windows checkout with `core.autocrlf=true`
  still verifies. `--strict-lf` additionally requires LF bytes on disk.
* `.gitattributes` sets `* text=auto eol=lf`, marks `*.pkl` binary, and leaves
  `gd_rigorous_ckpt_*/**` untouched.

## Status

Honest status of this build, with the evidence in [`VERIFICATION.md`](VERIFICATION.md):

| Level | What it establishes | Status |
|---|---|---|
| A — artefacts | the published bundle is internally consistent, LF-clean, and matches OEIS A084945 in its first 102 digits | **PASS** |
| B — full Arb replay | the 40,000-digit interval is reproducible from the plan with no checkpoint input | **NOT RUN** (harness PASS at 120 digits; the 40,000-digit run is a multi-hour job) |
| B′ — checkpoint audit | migrated legacy chunks assemble to the same interval (informational) | **PASS** on a 60-digit legacy directory; **NOT RUN** at 40,000 digits |
| C — independent quadrature | mpmath tanh–sinh and Gauss–Legendre agree with the certificate | **PASS** at 60 digits; the 1,000-digit run is a separate job |

No 40,000-digit production run has been performed in this build. The
certificate shipped here is the published one; what is new is that it is now
reproducible, that its line endings are canonical, and that resume can no
longer contaminate a proof.
