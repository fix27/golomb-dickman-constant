# PLAN — four-sprint remediation of the 40,000-digit certificate

Scope: move the published 40,000-digit Golomb–Dickman certificate from
"one machine, one run, unverifiable by a third party" to "reproducible from
the source, LF-clean, with a resume policy that cannot contaminate a proof,
and with a measured performance path off the 12-hour single-machine run".

Nothing here changes the mathematics. The expected interval is unchanged:

```text
D = 40000, G = 30
nodes = 241688   K_L = 117064   K_R = 124623
h = 9.173124908556929e-05
Ebits = 133010   S = 133074
chunks = 1209 (chunk = 200)
width = 5.492e-40043   (42.26 decimal guard digits)
```

Every number below is either measured on this machine or explicitly marked
NOT RUN. Where a target is not met, the gap is written down instead of being
papered over.

---

## Sprint 1 — integrity of the artefact and of the proof boundary

### 1.1 Canonical line endings (LF)

**Problem.** The bundle pinned LF SHA-256 values in `SHA256SUMS.txt` and
`verify_40000.py`, but the files on disk were CRLF on Windows: the certificate
was 120,261 B instead of 120,257 B, the b-file 348,892 B instead of 308,891 B.
`sha256sum -c` failed on the very files it shipped. Any Windows checkout with
`core.autocrlf=true` reproduced the failure.

**Implementation.**

* `_open_text_lf(path, mode="w")` and `_write_text_lf(path, text)` in
  `golomb_dickman_27.py`; every text artefact (certificate, `meta_v13.json`,
  `MIGRATION.json`, JSON reports, profile text) is written through them, with
  `newline="\n"`.
* `verification/verify_40000.py`: `_normalise_lf()` before SHA-256, a
  `line_ending_report()` per file (`LF` / `CRLF x N` / bare CR), and
  `--strict-lf` to require LF bytes on disk. A mixed/bare CR file is still a
  hard failure.
* `.gitattributes` in this directory: `* text=auto eol=lf`, explicit `eol=lf`
  for `*.py`, `*.txt`, `*.md`, `*.json`, `*.toml`, `*.yml`, `*.tex`;
  `*.pkl binary`; `gd_rigorous_ckpt_*/** -text`.

**Acceptance.** `python verification/verify_40000.py` passes on a checkout with
CRLF working-tree files, and `--strict-lf` passes on the LF-normalised bundle.

**Result.** PASS. On the normalised bundle:

```text
OK: 40000 digits certified (Level A)
  width: 5.492 x 10^-40043  (< 10^-40042), 42 guard digits beyond the 40000th place
  b-file: 40000 terms, indices 0..39999
  first 102 digits match OEIS A084945
  SHA-256: MATCH (pinned in this script):
    8892c071...de9c  golomb_dickman_40000_certified.txt  [LF]
    fbae7579...5327  golomb_dickman_40000_digits.txt     [LF]
    c73af643...bed3  b084945.txt                         [LF]
```

### 1.2 A resume policy that cannot contaminate a proof

**Problem.** A single `--resume` flag let saved pickles be assembled into a run
that still printed `CERTIFICATE`. Pickles carry no proof; accepting them turns
the certificate into an assertion about a directory.

**Implementation.** Two orthogonal switches, and two commands:

| Surface | Behaviour |
|---|---|
| `certify` (default) | strict. Every chunk recomputed in Arb. `--resume` → `SystemExit(2)` before any chunk is computed, with the exact replacement command printed. |
| `certify --certify-mode audit` | accepts saved chunks; never writes a certificate; prints `CERTIFICATE: NONE (AUDIT ONLY)`. |
| `audit-resume` | separate subcommand for inspecting old directories; same terminal line; no `--out`. |
| `run_certificate(...)` | `certify_mode` is explicit; `audit` requires `trust_checkpoint=True`; the audit branch returns before any certificate write; `res["proven"] = False`, `res["audit_only"] = True`, `res["certificate"] = "NONE"`. |

**Acceptance.** `certify --resume` exits non-zero and writes nothing;
`audit-resume` completes and prints the audit banner; no code path can combine
`trust_checkpoint=True` with a written certificate.

**Result.** PASS.

```text
$ python golomb_dickman_27.py certify --digits 120 --ckpt ckpt120 --resume
ERROR: --resume is disabled in strict certificate mode.
A strict run recomputes every chunk in Arb; accepting saved pickles cannot be proof-bearing.
...
exit code 2

$ python golomb_dickman_27.py audit-resume --digits 120 --ckpt ckpt120
WARNING: accepted 49/49 checkpoint chunks without recomputation; this is NOT a proof-bearing mode
CERTIFICATE: NONE (AUDIT ONLY)
```

### 1.3 Checkpoint schema, version, and migration

**Problem.** `40000/golomb_dickman.py` wrote `meta.pkl`, v26 wrote
`meta_v12.json`; both wrote `c_<lo>.pkl` into the same directory layout. A run
pointed at the wrong directory silently mixed formats. Nothing recorded the
schema, the chunk size, or the code that produced the chunks.

**Implementation.**

```python
CHECKPOINT_SCHEMA_VERSION = 13
CHECKPOINT_FORMAT         = "gd-checkpoint-v13"
CHECKPOINT_META_NAME      = "meta_v13.json"
LEGACY_META_NAMES         = ("meta.pkl", "meta_v12.json")
```

* `scan_checkpoint_schema()` classifies `empty` / `current` / `legacy` /
  `unknown` and **raises** `CheckpointSchemaError` when two formats coexist.
* `_checkpoint_identity()` records schema, format, program version, source
  SHA-256, Python/flint/platform, the plan parameters, the ladder settings and
  the chunk size.
* `_identity_key()` compares only fields that change the meaning of a pickle
  (`schema`, `format`, `parameters`, `precision_ladder`,
  `ladder_max_relax_bits`, `chunk`). `source_sha256` / `python` / `platform`
  are provenance: a code edit prints a NOTE, it does not forbid an audit.
* `migrate_checkpoints()` is the only way in: it validates the legacy
  parameters against the current plan, verifies that all 1209 `c_*.pkl` exist
  and are well formed, refuses a partial directory, writes `meta_v13.json` and
  `MIGRATION.json` with `"certificate": "NONE - AUDIT ONLY"`, and renames the
  old metadata to `*.migrated`.

**Acceptance.** A current directory refuses a legacy directory with a one-line
instruction; migration of a complete legacy directory succeeds and is marked
audit-only; a plan mismatch is refused.

**Result.** PASS on a real legacy directory
(`40000/gd_rigorous_ckpt_60` → 51 chunks):

```text
migrated meta.pkl -> meta_v13.json (51 chunks, AUDIT ONLY)
  NOTE: migrated legacy checkpoints; audit-only
WARNING: accepted 51/51 checkpoint chunks without recomputation; this is NOT a proof-bearing mode
CERTIFICATE: NONE (AUDIT ONLY)
```

A v27 directory pointed at a stale `gd_rigorous_ckpt_60` with another chunk
size is refused:

```text
CHECKPOINT ERROR: ...: checkpoint fingerprint mismatch.  This directory holds a
different plan or ladder setting.  Use a fresh --ckpt directory ...
```

### 1.4 Full Arb replay (Level B)

**Implementation.** `replay_certificate()` in the core and
`verification/full_arb_replay_40000.py` as the entry point. The replay

1. parses `S`, `lam_lo`, `lam_hi` and the digits from the certificate;
2. rebuilds the plan with `make_plan(D, G)` and **refuses** if `S` differs;
3. computes all `ceil(nodes / chunk)` chunks with `ckpt=None` (no checkpoint
   directory is opened, created or read);
4. assembles the interval with `certify()`;
5. checks: `digits_equal`, `lo_agrees_to_D`, `hi_agrees_to_D`,
   `intervals_overlap`, `replay_proves_digits`.

**Acceptance.** PASS/FAIL with a JSON report; exit 0/1/2.

**Result.** Harness validated end to end on a 120-digit certificate
(45 chunks at `chunk=32`), PASS. The 40,000-digit replay is **NOT RUN** — it is
the same multi-hour job as production (see Sprint 2 for the projection).

---

## Sprint 2 — performance

### 2.1 Profiling

`--profile FILE` wraps the run in `cProfile`, writes `FILE` and `FILE.txt`
(LF, top 40 by cumulative time). At `D=500` the hot path is entirely
`node_ball` → `series_S` → Arb multiplication; I/O is negligible once
checkpoints are asynchronous. Two concrete overheads were visible in v26's
source and are removed:

* `eps = arb(1) / arb(1 << Eb)` and `thr = arb(1) / arb(1 << thr_bits)` were
  rebuilt at every node, allocating a 133,010-bit integer each time;
* `arb(pl["h"])` was rebuilt at every node.

### 2.2 Caches and initializer

* `pow2_ball(bits)` — exact ball for `2^bits` (either sign), cached per
  process in `_POW2_CACHE`. Used for `eps`, `thr` and `to_fixed`'s scale.
* `pl["_hA"]` — the exact `arb(h)` ball cached on the plan copy in the worker.
* `_worker_init(pw)` — `ProcessPoolExecutor(initializer=..., initargs=(pw,))`
  sets `ctx.prec` and `get_EG()` once per worker instead of once per task.
* `RS_M = 32` (was 8) — rectangular-splitting block size in `series_S`.
  Measured at `D=4000`, `u ∈ {300, 1000, 3000, 8000}`:
  `m=8 → 0.263 s`, `m=16 → 0.201 s`, `m=32 → 0.191 s`, `m=64 → 0.222 s`.
  `m` stays even.

### 2.3 Asynchronous checkpoints

`_AsyncCheckpointWriter`: a daemon thread consumes a `queue.Queue`, writes
`c_<lo>.pkl.tmp`, `flush` + `fsync`, `os.replace`, and propagates the first
exception to the caller on the next `submit()` or at `close()`. Compute workers
never block on disk. Bounded in-flight tasks (`2·jobs`) keep memory flat.

### 2.4 Precision ladder (opt-in, and fail-safe by construction)

A far-tail chunk may declare a relaxed per-node radius ``Ebits - r`` where

```
(hi - lo) · 2^-(Ebits-r) ≤ 10^-D · 10^-4 · nchunks
r ≤ LADDER_MAX_RELAX_BITS (= 48)
Ebits - r ≥ ceil(D·log2 10) + LADDER_MIN_GUARD_BITS (= 64 bits)
```

The relaxation is recorded in `meta_v13.json` (the pickle stays a 4-tuple, so
the chunk format is unchanged), and `certify()` still checks the assembled
interval against the discretisation and tail bounds. A ladder that is too
aggressive can only fail to prove digits. It is **off by default** because it
widens the certificate interval; `--ladder` / `--precision-ladder` enables it.

### 2.5 Measurements

Single core, `jobs=1`, `chunk=100`, this machine (Windows 11, Python 3.15.2,
python-flint 0.9.0, 8 logical CPUs). Both builds produce `proven = True` and
the same interval width, so this is a like-for-like comparison.

| D | nodes | Ebits | v26 wall | v27 wall | speed-up |
|---:|---:|---:|---:|---:|---:|
| 2,000 | 10,490 | 6,777 | 36.1 s | 33.3 s | 1.08× |
| 3,000 | 15,599 | 10,099 | 104.2 s | 91.3 s | 1.14× |
| 6,000 | 31,742 | 20,064 | — | 616.4 s | — |

Fitting `time ∝ nodes · Ebits^p` on 3,000 → 6,000 gives `p ≈ 1.75`; the fit
reproduces the 2,000 → 3,000 ratio to 8%. Extrapolating to `D = 40000`
(nodes ×7.61, Ebits ×6.63) gives

```
single core : 616 s × 207 ≈ 35 h
16 cores    : 35 h / (16 · 0.85) ≈ 2.6 h
```

**Status of the "< 8 h on 16 cores" target: projected, not measured.** The
extrapolation is a power law through three measured points, not a run. Two
known risks: Arb multiplication is not a pure power law over five extra
decimal orders of magnitude, and the far-tail `cf_min_u` threshold is fixed at
a heuristic for `D < 500000`, so the true cost could be higher. A full 40,000-
digit run is required before the target can be called met.

---

## Sprint 3 — packaging, CI, verification levels

### 3.1 Core package

`pyproject.toml` packages the single module as `golomb-dickman-core==0.1.0`
(`py-modules = ["golomb_dickman_27"]`, console script
`golomb-dickman = "golomb_dickman_27:main"`, dependency
`python-flint>=0.9,<1`, optional extra `crosscheck = ["mpmath>=1.3"]`).

The verification scripts import only the core, and locate it by walking up
from themselves, so `python verification/*.py` works both in-tree and from an
installed wheel.

### 3.2 CI jobs

`ci/golomb_dickman_40000.yml` (a template: copy to
`.github/workflows/` to activate):

| Job | What it runs | Runner | Status |
|---|---|---|---|
| `compute` | `test`, `smoke`, strict `certify --digits 40000 --jobs 16 --chunk 200`, uploads certificate + checkpoints | self-hosted 16 vCPU, 600 min | NOT RUN (no such runner here) |
| `replay` | `full_arb_replay_40000.py --jobs 16 --chunk 200`, uploads `level_b_report.json` | self-hosted 16 vCPU, 600 min | NOT RUN |
| `crosscheck` | `crosscheck_1000_mpmath.py --digits 1000` | ubuntu-latest | NOT RUN in CI (run locally, see VERIFICATION.md) |
| `packaging` | LF-only zip of cert/digits/b-file, then `verify_40000.py --no-hash --strict-lf` on the fresh bundle | ubuntu-latest | NOT RUN |

No CI PASS is claimed. GitHub-hosted 4-vCPU runners cannot fit the 40,000-digit
compute or replay job in a 6-hour limit at the measured throughput.

### 3.3 Verification levels

| Level | Meaning | Tool |
|---|---|---|
| A | the artefact is well formed: tiling, `floor(10^D·Λ₋) = floor(10^D·Λ₊)`, b-file coverage, OEIS prefix, LF-normalised hashes | `verification/verify_40000.py` |
| B | the interval is reproducible from the plan alone, without any saved chunk | `verification/full_arb_replay_40000.py` |
| B′ | a checkpoint directory (including a migrated legacy one) assembles to a consistent interval — informational, never proof-bearing | `audit-resume` |
| C | an independent numerical method agrees to the claimed digits | `verification/crosscheck_1000_mpmath.py` |

### 3.4 Deliberate non-goals

* **Adaptive `h`.** Node count is driven by `N = D + G`, not by `M`; reducing
  the grid would change the plan and therefore the certificate. Not safe to
  bolt on to a published artefact, so it is not attempted.
* **Formal proof assistant.** Out of scope; the trust boundary is Arb plus the
  explicitly written discretisation/tail bounds, as in v26.

---

## Sprint 4 — documentation and publication

| Document | Change | Status |
|---|---|---|
| `40000-v2/README.md` | new: build description, modes, files, status table | DONE |
| `40000-v2/PLAN.md` | this file | DONE |
| `40000-v2/VERIFICATION.md` | protocol, measured results, NOT RUN list | DONE |
| `40000-v2/SHA256SUMS.txt` | regenerated over the v2 tree (LF) | DONE |
| `40000/VERIFICATION.md` | status section: points at 40000-v2, records the CRLF root cause as fixed in v2, keeps the old results as history | DONE |
| `40000/OEIS_SUBMISSION.md` | status section: b-file unchanged and still valid (same LF SHA-256); reproducibility statement now points at 40000-v2; Level B not yet run | DONE |
| `submission/oeis-bfile.eml` | reproducibility paragraph updated; no claim of a completed replay | DONE |
| `paper/main.tex` | status footnote for the v2 build; numbers unchanged | DONE |

Publication claims are limited to what is measured: Level A passes, the
published digits are unchanged, and the 40,000-digit replay is not yet run.
The OEIS b-file itself is not re-uploaded by this work.

---

## Residual risk register

| Risk | Mitigation | Status |
|---|---|---|
| CRLF reintroduced on a Windows checkout | `.gitattributes`, `newline="\n"`, LF-normalised hashing, `--strict-lf`, CI `packaging` job | closed for v2 tree |
| A saved pickle silently promoted to a proof | strict default, `SystemExit` on `--resume`, separate `audit-resume`, no certificate write in audit | closed |
| Two checkpoint formats in one directory | schema constants, `scan_checkpoint_schema()` refusal, explicit migration with `MIGRATION.json` | closed |
| Certificate never independently recomputed | Level B replay tool + CI job | tool done, run NOT DONE |
| 8-hour target on 16 cores | measured 1.08–1.14× over v26; projection 2.6 h | projected, NOT measured |
| Ladder too aggressive | ladder floor of 64 bits above `D·log2 10`, cap 48 bits, `certify()` as final arbiter, off by default | by construction |
