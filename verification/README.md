# Verification package: certified digits of the Golomb–Dickman constant

Author of the computation and of this package:
**Поздняков Константин Николаевич** / **Konstantin N. Pozdnyakov**
Surgut, Khanty-Mansi Autonomous Okrug — Yugra, Russia — fix@inbox.ru

    lambda = 0.6243299885435508709929363831008372441796426201805292869735519024...
             (OEIS A084945)

Certified results in this repository: **50,000 digits** (current, `50000/`)
and 40,000 digits (previous, `40000/`, the subject of the exported archive).

The point of this directory is to make verification cheap and honest. Three
levels answer three different questions, and none of them is allowed to
pretend to be a stronger one.

## Three commands

```sh
# 1. Certificate and digits: seconds, standard library only.
python verification/verify_certificate.py \
    --cert 50000/golomb_dickman_50000_certified.txt \
    --compare 40000/golomb_dickman_40000_digits.txt
python verification/verify_certificate.py --cert 40000/golomb_dickman_40000_certified.txt

# 2. Mathematics audit: parameters, bounds, and 12 chunks recomputed.
python verification/level_b.py

# 3. Independent recomputation with another algorithm (mpmath).
python verification/independent_quadrature.py --digits 1000
```

`python verification/run_all.py` runs levels A and B together, and
`--digits N` adds level C.

Level B needs the 1,209 checkpoint pickles (~70 MB) and is therefore run from
the full repository, not from this archive. The archive ships its report
(`reports/level_b.txt`) instead.

## MathWorld statement checks

`mathworld_checks.py` checks every statement on
[MathWorld's "Golomb-Dickman Constant Digits" page](https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html)
against the 50,000-digit file: the opening digits, the Earls sequence
(A225242), A229195, digit scanning, absence of `0123456789` and
`9876543210`, the digit-count table, A174975/A174974, and the reported prime
search through 15,000 digits.

```sh
python verification/mathworld_checks.py            # ~7 s
python verification/mathworld_checks.py --primes   # + exhaustive 1..2508
python verification/mathworld_checks.py --primes --deep-primes  # ~12 min (698 s)
```

Result: 8 PASS, two historical attributions NOT_VERIFIABLE (Mitchell 1968 and
Weisstein's 2013 computation depth), normality OPEN, and the 15,000-digit
prime search PARTIAL (140 sampled lengths). Extra checks cover runs,
palindromes, repeated and tandem substrings, periodic runs, k-gram coverage,
chi-square tests, and random prime substrings. See
`reports/mathworld_50000.md` (Russian) and `reports/mathworld_50000.json`;
reference b-files are in `reports/oeis/`. These are checks of the digit string
and of the page's statements, not a proof of normality and not a world-record
claim.

In the exported bundle the layout is

```
verification/
├── README.md
├── SHA256SUMS
├── fast_verifier/verify_40000.py
├── independent_check/independent_quadrature.py
├── independent_check/requirements.txt
├── math_audit/level_b.py, verify_checkpoints.py, verify_nodes_decimal.py, verify_checkpoints_arb.py
├── certificate/golomb_dickman_40000_certified.txt
├── digits/golomb_dickman_40000_digits.txt, b084945.txt
└── reports/
```

and the scripts find the artefacts in either layout without arguments.
`reports/level_b.txt` documents the mathematical audit performed in the full
repository, whose checkpoints are too large to ship here.

## What each level establishes

| Level | Cost | Establishes | Does **not** establish |
|-------|------|-------------|------------------------|
| A | seconds | SHA-256 of all inputs; `0 < lam_lo < lam_hi`; `floor(10^D*lam_lo/2^S) = floor(10^D*lam_hi/2^S)`; the digits file equals that integer; the interval is narrower than one unit in the D-th place; the b-file matches digit by digit; the first 102 digits match OEIS A084945 | that the constant really lies in the published interval |
| B | seconds | meta-parameters reproduce from the formulas; chunk coverage 1..1,209 of the 40,000-digit run is contiguous; the integer certificate arithmetic reproduces `lam_lo`, `lam_hi`; the discretisation bound and both tails reproduce the corrections `B`, `TR`, `TL`; nodes recomputed from scratch in `Decimal` agree with the saved balls | the Arb enclosure itself (that needs `verify_checkpoints_arb.py` and python-flint) |
| C | minutes–days | the leading digits reproduce from a different formula arrangement, a different quadrature rule, and a different library | rigour: mpmath is floating point, so this is numerical evidence |

Levels A and B deliberately contain **no pickle loading, no import of the
producing program, and no floating point** in the decision path. Level B's
node check treats checkpoints as a cache: every compared value is recomputed
from the formula, and the comparison tolerance is printed. There is no
`trust_checkpoint=True` path.

## Certificate shape

| quantity | 50,000 (current) | 40,000 (previous) |
|----------|------------------|-------------------|
| decimal digits `D` | 50,000 | 40,000 |
| working guard digits `G` in the plan | 30 | 30 |
| scale `S` | 166,293 bits | 133,074 bits |
| nodes | 307,580 in 3,076 chunks of 100 | 241,688 in 1,209 chunks of 200 |
| interval | `[lam_lo, lam_hi] / 2^166293` | `[lam_lo, lam_hi] / 2^133074` |
| width | `4.390 × 10^-50043` (below `10^-50042`) | `5.492 × 10^-40043` (below `10^-40042`) |
| guard digits beyond the `D`-th place | 42 | 42 |

## Honest status on the packaging machine

* Level A: **PASS**.
* Level B: **PASS** for the checklist, the plan and 12 recomputed chunks.
  The rigorous Arb re-audit of all 1,209 chunks was **not run here**:
  `python-flint` installs but its DLL cannot be loaded on this machine
  (`ImportError: DLL load failed while importing flint_base`, Windows
  Application Control). Consequently the enclosure of the constant by the
  published interval still rests on the original production run, and this
  package says so instead of implying otherwise.
* The 50,000-digit certificate added on 2026-11-16 passes level A and the
  checkpoint-sum audit (`reports/50000_verification.txt`): its first 40,000
  digits agree with the older certificate, and its 3,076 checkpoint chunks
  are contiguous and reproduce both endpoints with corrections `B = 1`,
  `C = 2427712667995762`. Its plan is `meta_v12.json` (not `meta.pkl`):
  the recorded step `h = 7.352934335358441e-05` gives exactly
  `m = 80846368`, and `K_L = 149075`, `K_R = 158504` match the covered
  node range, so the audit uses the planned step and `B = 1` is a genuine
  consistency check. The 40,000-digit control, whose plan is `meta.pkl`,
  recovers exactly the documented values, which validates the old format
  as well.
* Level C: 1,000 digits reproduced independently (see
  `reports/independent_1000.txt`): the two quadrature rules agree for 1,020
  leading digits and both agree with the certified file for the same 1,020.
  The run took 64 min (tanh-sinh) and 51 min (Gauss-Legendre) at 1,060
  working digits. 5,000 / 10,000 / 40,000 digits are supported by the same
  script; the full run needs hours to days of CPU.

## Deliberate non-claims

* This is not claimed to be a world record, and the package makes no
  statement about the normality of `lambda`.
* `lambda` is not known to be normal; 50,000 digits are far too few to say
  anything statistical about it.
* Matching prefixes from level C are evidence about the digits, not about the
  enclosure.

## Checksums

`SHA256SUMS` lists every file in this archive, relative to the archive root:

```sh
sha256sum -c SHA256SUMS            # GNU coreutils
```

```powershell
Get-Content SHA256SUMS | ForEach-Object {
    $hash, $path = $_ -split '  ', 2
    if ((Get-FileHash $path -Algorithm SHA256).Hash -ne $hash.ToUpper()) { "FAIL $path" }
}
```

## Requirements

* Levels A and B: Python 3.10+, standard library only.
* Level C: `mpmath` (tested with 1.4.1), see `independent_check/requirements.txt`.
* The deep Arb audit: `python-flint` with a working Arb.

## Contact

Konstantin N. Pozdnyakov, Surgut, KhMAO — Yugra, Russia, fix@inbox.ru.
