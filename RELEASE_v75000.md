# Release v75000 — 75,000 certified decimal digits of the Golomb–Dickman constant

Status: **release candidate**. The numerical certificate passes every
dependency-free check available here; the full independent Arb re-audit of all
476,648 nodes has **not** run (see *Verification status*). Overall verdict:
`INCOMPLETE`, not `PASS`. This is an extension of a published computation,
**not a world-record claim**.

- Repository: <https://github.com/fix27/golomb-dickman-constant>
- Version / tag: `75000` / `v75000`
- DOI: [10.5281/zenodo.24567561](https://doi.org/10.5281/zenodo.24567561)
  (version DOI; concept DOI `10.5281/zenodo.24567560`)
- License: MIT (code and data), see `LICENSE`
- Canonical manuscript: `paper/main-75000.tex`
- MathWorld mention archived in `submission/MATHWORLD_MENTION.md`

## What is certified

$$\lambda=\int_0^\infty e^{-u-E_1(u)}\,du
 =0.624329988543550870992936383100837244\ldots$$

The certificate `75000/golomb_dickman_75000_certified.txt` contains integers
$\Lambda_-<\Lambda_+$ and scale $S=249341$ such that

$$\lambda\in\left[\frac{\Lambda_-}{2^S},\frac{\Lambda_+}{2^S}\right],
\qquad
\left\lfloor\frac{10^{75000}\Lambda_-}{2^S}\right\rfloor
=\left\lfloor\frac{10^{75000}\Lambda_+}{2^S}\right\rfloor .$$

The equal floors prove the first 75,000 decimal places **by truncation**, not
by floating-point rounding. Interval width:
$5.8205594787\times10^{-75043}$ — about 42.235 guard digits beyond the
75,000th place.

## Method

- split $\lambda=\int_{\mathbb R}G(t)\,dt$ at $t=0$ and $t=2$;
- trapezoidal rule after the Takahashi–Mori substitution (double-exponential
  decay at both ends);
- $E_1$ by power series / Stieltjes continued fraction / asymptotic expansion,
  selected per node;
- each node enclosed in an Arb ball with directed rounding; the radius is
  checked inside the node routine, not assumed;
- explicit discretisation and tail bounds (Trefethen–Weideman style) produce
  the integer corrections $B$ and $C$ stored with the certificate.

Trust base: Arb correctness, the cited theorems, the elementary lemmas in the
source, and exact Python integer arithmetic. This is **not** a formalisation
in a proof assistant.

## Parameters (`75000/gd_rigorous_ckpt_75000/meta_v13.json`)

| Parameter | Value |
|---|---|
| certified digits $D$ | 75,000 |
| guard digits $G$ | 30 |
| scale $S$ | 249341 |
| node radius exponent $E_{\text{bits}}$ | 249277 |
| global radius exponent $EG_{\text{bits}}$ | 362151 |
| $K_L,K_R$ | 231270 / 245377 |
| nodes (full range) | 476,648 (`-231270 … 245377`) |
| step $h$ | $54039302/2^{40}=4.9148458856507204\times10^{-5}$ |
| chunks / chunk size | 4,767 / 100 |
| $B$ | 1 |
| $C$ | 34133488394318882 |
| checkpoint format | `gd-checkpoint-v13` |

## Platform and runtime

Recorded in `meta_v13.json`: Linux `7.3.0-9-generic` x86_64, glibc 2.44,
Python 3.14.8, `python-flint` 0.9.0, producer v27. The CPU model and a
wall-clock log of the production run were **not** preserved; no runtime is
claimed for it. Measured during auditing: 2,000 nodes in 141 s on 4 threads,
which extrapolates to roughly 9 h on 4 threads (about 3 h on 11) for a full
Arb re-audit. That extrapolation is an audit estimate, not a production
benchmark.

## Files and SHA-256 (canonical LF, no BOM)

```text
b177fc551c8a9f950e037fdc92ed72fb9219eb11d81999410967f8013e6df534  golomb_dickman_75000_certified.txt
0c5f2b212eb5fd25b1def672226f65f46b97d44c5e371c5db10ab1cef9b468aa  golomb_dickman_75000_digits.txt
f5a02374d79b4ca6af889a9c4a63b53fe265bc3c861a1c20dc2683c696e781ea  golomb_dickman_27.py
ee9dfe75ea130c15c8a3ade41d6994bcb734d413c1c49e2cd58b39ab31bbf8f9  gd_rigorous_ckpt_75000/meta_v13.json
```

Full manifest: `75000/SHA256SUMS.txt`. A hash binds a name to bytes only;
`verify_certificate.py --sha256-manifest` prints `MATCH (manifest)` rather than
an unconditional `OK`.

## Verification status

| Check | Status |
|---|---|
| exact integer check of all 75,000 digits | PASS |
| digit file equals certificate; OEIS A084945 prefix (102 digits) | PASS |
| first 50,000 / 40,000 digits agree with earlier certificates | PASS |
| `make_plan(75000)` vs `meta_v13.json` (8 parameters) | PASS |
| 4,767 chunks, 476,648 nodes, no gaps or duplicates; $B$, $C$ | PASS |
| independent mpmath quadrature (tanh–sinh + Gauss–Legendre), 320 digits | PASS |
| applicable MathWorld digit-page statements on 75,000 digits | PASS / NOT_VERIFIABLE / OPEN |
| full Arb re-audit of all 476,648 nodes | **NOT_RUN** (2,000 of 476,648 checked, 20/20 contained) |
| exhaustive prime-truncation search beyond 2,508 digits | NOT_RUN (sampled only) |
| PDF compilation of the manuscript | NOT_RUN (no TeX engine on packaging machine) |

Normality of $\lambda$ remains open; digit statistics are sanity checks only.
Details: `audit/06-75000.md` and `75000/README.md`.

## Reproduce

```bash
python verification/verify_certificate.py \
    --cert 75000/golomb_dickman_75000_certified.txt \
    --digits-file golomb_dickman_75000_digits.txt \
    --sha256-manifest 75000/SHA256SUMS.txt \
    --compare 50000/golomb_dickman_50000_digits.txt

python verification/audit_chunks.py \
    --ckpt 75000/gd_rigorous_ckpt_75000 \
    --cert 75000/golomb_dickman_75000_certified.txt

python verification/independent_quadrature.py --digits 300 --jobs 2 \
    --certified golomb_dickman_75000_digits.txt
```

The first two use only the Python standard library and exact integer
arithmetic. Full production: `python golomb_dickman_27.py certify --digits
75000` (hours, checkpointed; use an empty checkpoint directory).

## MathWorld fixation

MathWorld listed both *Golomb-Dickman Constant* and *Golomb-Dickman Constant
Digits* under 2026-11-14 in its whatsnew log (the cited commit is dated
2026-11-15 +04:00); the latter page says "Pozdnyakov (2026) provides digit data
and computation code" and links to a commit-specific GitHub URL. Exact URLs,
wording, date, HTTP headers, HTML, screenshots and PDF are archived in
`submission/MATHWORLD_MENTION.md` and `submission/mathworld-evidence/`,
including a direct live-page PDF printed from the main page through Edge.
A Wayback snapshot of the digits page was also requested on 2026-11-26:
<https://web.archive.org/web/20261126160603/https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html>.
No new submission to MathWorld was made or is required.

## Zenodo

Published through the Zenodo GitHub integration on 2026-11-26 at 17:47 UTC as
record [24567561](https://zenodo.org/records/24567561). Version DOI:
<https://doi.org/10.5281/zenodo.24567561>; all-versions concept DOI:
`10.5281/zenodo.24567560`. The archived source bundle is
`fix27/golomb-dickman-constant-v75000.zip` (532,212,203 bytes). This is now the
canonical citation for `v75000`; the same DOI is in `CITATION.cff` and in the
(draft, unsent) `submission/mathworld-thanks.eml`.
