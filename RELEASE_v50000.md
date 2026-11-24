# Release v50000 — 50,000 certified decimal digits of the Golomb–Dickman constant

Status: **release candidate**. The numerical certificate passes every check that
can run on this machine; the full independent Arb re-audit has **not** run here
(see *Verification status*). Overall status is therefore `INCOMPLETE`, not
`PASS`.

- Repository: <https://github.com/fix27/golomb-dickman-constant>
- Version / tag: `50000` / `v50000`
- DOI: **pending** — minted by Zenodo when the tag is archived. Do not cite a
  DOI for this release until it appears here and in `CITATION.cff`.
- License: MIT (code and data), see `LICENSE`
- Canonical article: `paper/main.tex` (the 50,000-digit manuscript)
- Superseded draft: `paper/main-50000.tex` (kept for provenance, marked
  superseded in the document itself)

## What is certified

$$\lambda=\int_0^\infty e^{-u-E_1(u)}\,du
=0.624329988543550870992936383100837244\ldots$$

The certificate `50000/golomb_dickman_50000_certified.txt` contains integers
$\Lambda_-<\Lambda_+$ and a scale $S=166293$ such that

$$\lambda\in\left[\frac{\Lambda_-}{2^S},\frac{\Lambda_+}{2^S}\right],
\qquad
\left\lfloor\frac{10^{50000}\Lambda_-}{2^S}\right\rfloor
=\left\lfloor\frac{10^{50000}\Lambda_+}{2^S}\right\rfloor .$$

The two floors are equal, so the first 50,000 decimal places are **proved by
truncation**, not merely computed in floating point. The interval width is
$4.390\times10^{-50043}$, i.e. 42.36 guard digits beyond the 50,000th place.

## Method

- Split $\lambda=\int_{\mathbb R}G(t)\,dt$ at $t=0$ and $t=2$;
- trapezoidal rule after the Takahashi–Mori substitution, which turns both
  ends into double-exponential decay;
- $E_1$ evaluated by a power series, a Stieltjes continued fraction, or an
  asymptotic expansion, whichever is cheapest at the node;
- every node value enclosed in an Arb ball (midpoint–radius interval
  arithmetic with directed rounding); the ball radius is checked against
  $2^{-E_{\text{bits}}}$ inside the node routine, not assumed;
- explicit discretisation and tail bounds (Trefethen–Weideman style), giving
  the integer corrections stored in the certificate.

The trust base is Arb plus the cited theorems and the elementary lemmas in the
source. This is not a formalisation in a proof assistant.

## Parameters (from `50000/gd_rigorous_ckpt_50000/meta_v12.json`)

| Parameter | Value |
|---|---|
| certified decimal digits $D$ | 50,000 |
| guard digits $G$ | 30 |
| certificate scale $S$ | 166293 |
| node radius exponent $E_{\text{bits}}$ | 166229 |
| global radius exponent $EG_{\text{bits}}$ | 241732 |
| left / right node counts $K_L,K_R$ | 149075 / 158504 |
| nodes / chunks / chunk size | 307580 / 3076 / 100 |
| step numerator $m$ | 80846368 |
| step $h=m/2^{40}$ | 7.352934335358441e-05 |
| continued-fraction cut-off $u$ | 13000.0 |
| interval width | 4.390e-50043 |
| checkpoint format | `gd-checkpoint-v12` |

## Hardware and runtime

Production run (recorded in `meta_v12.json`):

- AMD Ryzen 5 7430U, 6 cores / 12 threads, 11.9 GB RAM;
- Windows 11 (build 10.0.26300), Python 3.14.6, python-flint 0.9.0.

The production run took hours of CPU and is checkpointed, so it can be
interrupted and resumed; no wall-clock log of the original run was preserved,
and none is claimed. Only the verification timings below are measured.

Verification on the packaging machine (Python 3.12.10, no python-flint
needed except for the Arb audit):

| Step | Command | Time | Result |
|---|---|---:|---|
| certificate + digits + b-file + OEIS prefix + 40k agreement | `verify_certificate.py` | 0.2 s | PASS |
| 40,000-digit certificate | `verify_40000.py` | 0.2 s | PASS |
| 3,076 checkpoint chunks, 307,580 nodes | `audit_chunks.py` | 2.0 s | PASS |
| structural Arb plan audit | `verify_all_arb.py --structural-only` | 1.4 s | NOT_RUN (by design) |
| independent 1,000-digit recomputation, two rules | `independent_quadrature.py` | 912.6 s + 1079.0 s | PASS (1,020 digits) |
| release checks | `test_release_checks.py` | seconds | INCOMPLETE |
| all levels | `run_all.py` | ~20 s | INCOMPLETE |

## Files and SHA-256 (canonical LF, no BOM)

```text
76f4155981049003351409769505c3cec39e26dfc30624c46bd199e70ed6477a  golomb_dickman_50000_certified.txt
8f017d45ee5108bb6b976882b079279f44f8a767ce62b44bd7c54e9167ad09a0  golomb_dickman_50000_digits.txt
1e3d23e9ac3ce51990d83decd395d6bde96027f43811b94cebd5a6a4b7c19c43  b084945.txt
78783a09bae599298a07415056b0ca521717c9f7ecaa1fd15cb19b4d5ab6b0e0  gd_rigorous_ckpt_50000/meta_v12.json
e2eb7d4ccca761c5c5e1f2b37075f9baea245dac86cbe962fd9dc92aa574ef71  golomb_dickman_26.py
9260265b15b7ef13b7b5fa5fcc1e4cdbda0c7a26b79a84c16ac62e45b52ae0d1  README.md
```

The manifest is `50000/SHA256SUMS.txt`; run
`python verification/verify_certificate.py --cert 50000/golomb_dickman_50000_certified.txt --sha256-manifest 50000/SHA256SUMS.txt`
to check it. A hash matches a *reference*; the script prints `MATCH (manifest)`
or `computed, UNVERIFIED (no trusted reference)` and never an unconditional
`OK`.

## Verification status

| Check | Status |
|---|---|
| integer certificate, decimal cell, interval width | PASS |
| digit file equals the certificate | PASS |
| b-file: 50,000 terms, `n = 0..49999`, every digit | PASS |
| first 102 digits = OEIS A084945 | PASS |
| first 40,000 digits = 40,000-digit certificate | PASS |
| 3,076 chunks: continuity, no gaps or duplicates | PASS |
| chunk sums reproduce the certificate corrections | PASS |
| independent 1,000-digit recomputation (mpmath, two rules) | PASS, 1,020 digits |
| all statements of the MathWorld page | 8 PASS, 2 historical attributions NOT_VERIFIABLE, prime scan PARTIAL |
| full Arb re-audit of all 307,580 nodes | **NOT_RUN** |
| PDF compilation of `paper/main.tex` | **NOT_RUN** (no TeX engine here) |

Why the Arb re-audit did not run: `python-flint` cannot be imported on the
packaging machine (Windows Application Control blocks a DLL). The certificate
is still established by the original production run, but it has not been
independently re-derived node by node, and this release says so. The overall
verdict of `verification/test_release_checks.py` and `verification/run_all.py`
is `INCOMPLETE` with exit code 1, never `PASS`.

## Reproduce

```bash
python verification/verify_certificate.py \
    --cert 50000/golomb_dickman_50000_certified.txt \
    --sha256-manifest 50000/SHA256SUMS.txt \
    --compare 40000/golomb_dickman_40000_digits.txt

python verification/audit_chunks.py \
    --ckpt 50000/gd_rigorous_ckpt_50000 \
    --cert 50000/golomb_dickman_50000_certified.txt

# independent numerical check, ~33 minutes on the machine above
python verification/independent_quadrature.py --digits 1000 \
    --methods tanh-sinh,gauss-legendre \
    --certified 50000/golomb_dickman_50000_digits.txt

# full Arb re-audit: hours, needs python-flint
python verification/verify_all_arb.py \
    --ckpt 50000/gd_rigorous_ckpt_50000 \
    --cert 50000/golomb_dickman_50000_certified.txt --jobs 11
```

The first two scripts use only the Python standard library and exact integer
arithmetic. `verify_all_arb.py` exits 2 (`NOT_RUN`) when Arb is unavailable and
0 only after every node has been recomputed and every interval contained.

## What this release does not claim

- no world record and no priority claim;
- no statement about the normality of $\lambda$;
- no formal proof in Coq/Lean/Isabelle;
- no independent 50,000-digit recomputation beyond the 1,000-digit Level C run;
- no claim that MathWorld verifies these digits. The MathWorld page
  *Golomb–Dickman Constant Digits* (snapshot 2026-11-23) cites the **40,000**
  digit result and commit `87bdfe3`; see
  `verification/evidence/mathworld_mention_2026-11-23/`.

## Changes since v40000

- new 50,000-digit certificate, digit file and b-file (`n = 0..49999`);
- corrected $M_3$ term in the manuscript
  ($e^{\,e^{e^{-2}-2}}$, not $e^{\,e^{e^{-2}}-2}$);
- `50000/` text artefacts normalized to canonical LF; manifest rebuilt and
  checked; superseded draft flagged instead of silently disagreeing;
- independent 1,000-digit recomputation repeated against the 50,000-digit
  file and archived under `verification/reports/`;
- MathWorld citation captured verbatim with page HTML, text and screenshot.
