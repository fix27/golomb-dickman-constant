# Verification package: certified digits of the Golomb–Dickman constant

Author of the computation and of this package:
**Поздняков Константин Николаевич** / **Konstantin N. Pozdnyakov**
Surgut, Khanty-Mansi Autonomous Okrug — Yugra, Russia — fix@inbox.ru

    lambda = 0.6243299885435508709929363831008372441796426201805292869735519024...
             (OEIS A084945)

> **Current result:** 75,000 digits (`../75000/`, release `v75000`). The root
> [`../README.md`](../README.md) is the primary project description. Everything
> below describes the **historical 50,000/40,000-digit verification package**
> and is kept as provenance; use `../verification/verify_certificate.py` and
> `../verification/audit_chunks.py` for the current release.

Historical certified results in this repository: **50,000 digits** (`50000/`)
and 40,000 digits (`40000/`, the subject of the exported archive).

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
`--digits N` adds level C.  It also runs the independent Arb audit
(`verify_all_arb.py`), which is the only level that can turn the overall
verdict into `PASS`:

```sh
python verification/run_all.py                    # Arb level NOT_RUN -> INCOMPLETE
python verification/run_all.py --full-arb --arb-jobs 11   # hours
python verification/run_all.py --arb-report verification/reports/arb_50000.json
                                                  # re-check a finished audit
```

`--arb-report` does not trust the report: it re-reads every per-chunk
containment flag (and, in verbose reports, re-derives the intervals),
requires full node coverage, and demands that the recomputed total lies
inside the certificate.  Use it when the audit has already run, so that a
2-hour computation is not repeated merely to aggregate the verdict.

## Statuses are three-valued, and `NOT_RUN` is never `PASS`

Every check reports `PASS`, `FAIL` or `NOT_RUN`.  `run_all.py` aggregates
them as

| aggregate | meaning |
|---|---|
| `FAIL` | at least one required check ran and found a discrepancy |
| `INCOMPLETE` | nothing required failed, but something required did not run |
| `PASS` | every required check ran and passed |

Only `PASS` exits with code 0.  A skipped Arb audit therefore produces
`INCOMPLETE`, not a green release.  The same rule holds inside
`level_b.py`: without `--with-arb` its verdict is `INCOMPLETE`.

`verify_certificate.py` applies the rule to hashes as well.  It computes
SHA-256 for every input it reaches, but reports `MATCH (manifest)` /
`MATCH (--sha256)` only when a trusted reference is supplied via
`--sha256-manifest` or `--sha256 NAME=HEX`; otherwise it prints
`computed, UNVERIFIED (no trusted reference)`.  Checks fail fast, so an
input after an earlier failure is not hashed.

`audit_chunks.py` and `verify_all_arb.py` read checkpoints with
`safe_pickle.py`, which allows only plain-data opcodes and rejects
`GLOBAL`, `REDUCE`, `BUILD`, persistent IDs and extension codes.  The
producer's own `--resume` flag remains a documented audit-only shortcut.

Level B needs the 1,209 checkpoint pickles (~70 MB) and is therefore run from
the full repository, not from this archive. The archive ships its report
(`reports/level_b.txt`) instead.

## MathWorld statement checks

`mathworld_checks.py` checks every statement on
[MathWorld's "Golomb-Dickman Constant Digits" page](https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html)
against the digits file (at the time: 50,000 digits; default now 75,000): the opening digits, the Earls sequence
(A225242), A229195, digit scanning, absence of `0123456789` and
`9876543210`, the digit-count table, A174975/A174974, and the reported prime
search through 15,000 digits.

```sh
python verification/mathworld_checks.py            # ~30 s with Monte Carlo run tests
python verification/mathworld_checks.py --primes   # + exhaustive 1..2508
python verification/mathworld_checks.py --primes --deep-primes  # ~12 min (698 s)
```

Result: 8 PASS, two historical attributions NOT_VERIFIABLE (Mitchell 1968 and
Weisstein's 2013 computation depth), normality OPEN, and the 15,000-digit
prime search PARTIAL (140 sampled lengths). Extra checks cover runs and
their Monte Carlo p-values, palindromes, repeated and tandem substrings,
periodic runs, k-gram coverage, chi-square tests including triples, and
random prime substrings. The citation and edit date are fixed in
`../submission/MATHWORLD_MENTION.md`; the detailed report and JSON were removed
from the repository. Reference b-files are in `reports/oeis/`. These are checks
of the digit string and of the page's statements, not a proof of normality and
not a world-record claim.

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
| Arb | tens of minutes–hours | every node of the 50,000-digit run is recomputed in Arb from `G(t)=exp(-u-E1(u))u(1+e^{-t})` with Arb's own `E1`; every recomputed chunk interval is contained in the saved one; the recomputed total is contained in the certificate; `B`, `C` cover the recomputed discretisation and tail bounds | that the digits are right if Arb itself is wrong |
| C | minutes–days | the leading digits reproduce from a different formula arrangement, a different quadrature rule, and a different library | rigour: mpmath is floating point, so this is numerical evidence |

Level A contains no checkpoint access, no import of the producing program and
no floating point.  Level B and the Arb audit do read checkpoints, but only
through the restricted reader in `safe_pickle.py`, and only as a cache: every
compared value is recomputed from the formula, and the comparison is a
containment test of two enclosures, not a tolerance.  There is no
`trust_checkpoint=True` path in the verification code.

## Certificate shape

| quantity | 50,000 (historical) | 40,000 (historical) |
|----------|------------------|-------------------|
| decimal digits `D` | 50,000 | 40,000 |
| working guard digits `G` in the plan | 30 | 30 |
| scale `S` | 166,293 bits | 133,074 bits |
| nodes | 307,580 in 3,076 chunks of 100 | 241,688 in 1,209 chunks of 200 |
| interval | `[lam_lo, lam_hi] / 2^166293` | `[lam_lo, lam_hi] / 2^133074` |
| width | `4.390 × 10^-50043` (below `10^-50042`) | `5.492 × 10^-40043` (below `10^-40042`) |
| guard digits beyond the `D`-th place | 42 | 42 |

## Honest status at the historical 50,000-digit checkout

The bullets below record the state at the time of the archived 50,000-digit
reports. The CRLF issue mentioned there was later fixed; current status is in
the root [`../README.md`](../README.md). The reports in `reports/` are historical artefacts from an LF-normalised
packaging run; they are not the live status of this checkout.

* The canonical artefacts in `50000/`, their root copies and `40000/` are
  currently CRLF on disk. Strict LF checks therefore give **FAIL** today:
  `verify_certificate.py`, `level_b.py`, `test_release_checks.py` and
  `run_all.py` stop on `contains CR`. After LF normalisation the decimal
  arithmetic, the digits, the b-files, the first 102 OEIS digits and the
  SHA-256 values in `50000/SHA256SUMS.txt` all reproduce. Normalise LF and
  rebuild the affected manifests before treating saved `PASS` reports as
  current; nothing in the arithmetic needs changing.
* Level B mathematics needs no fix: `M`, `B_disc`, both tails, `B`, `C`, the
  Λ± reconstruction and the exact `Fraction` identities for Lemma 7 were
  reproduced independently. The 50,000-digit checkpoint-sum audit
  (`audit_chunks.py`) passes: 3,076 chunks / 307,580 nodes, `B = 1`,
  `C = 2427712667995762`.
* Arb: `reports/arb_50000.json` is `NOT_RUN` and contains no per-chunk
  blocks. Current `python-flint` provides `arb.expint`, so the old
  “DLL blocked by Application Control” explanation is obsolete; a 5-chunk
  smoke run gave containment 5/5, but the full 3,076-chunk audit has not
  been rerun here. The Arb level stays `NOT_RUN` until it is.
* Level C: the saved prose/log reports say 1,020 leading digits by both
  quadrature rules and against the certificate. The saved JSON stored only
  the requested 1,000 digits, so that claim was not reproducible from the
  machine-readable report. `independent_quadrature.py` now stores the full
  probe strings; existing JSON reports need regeneration to benefit.
* Level D: χ² for digits/positions/pairs/triples and the fixed-seed Monte
  Carlo runs tests now live in `mathworld_checks.py`; all p-values are above
  0.01. Prime prefixes are supported by Miller–Rabin/BPSW as **probable
  primes**; no APRCL/ECPP certificate is produced or claimed.

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

## Tests for the verifiers themselves

```sh
python verification/test_release_checks.py    # paper formula, LF canon, SHA, statuses, pickle
python verification/test_verify_all_arb.py    # 27 tests of the Arb audit's structure and containment logic
```

`test_release_checks.py` also checks that `verify_certificate.py` never
prints an unqualified `OK` for a hash, that `run_all.aggregate` maps
`NOT_RUN` to `INCOMPLETE`, and that the certificate, digits, b-file, plan,
producer and README all match `50000/SHA256SUMS.txt` byte-for-byte.

`check_report_containment.py` re-reads the Arb report and decides whether
containment (not merely intersection) holds:

```sh
python verification/check_report_containment.py --report verification/reports/arb_50000.json
```

It exits 0 only when every recomputed chunk interval is inside the saved one
and the recomputed total is inside the certificate; exit 2 means `WEAK`, i.e.
the intersections hold but only the weaker claim is supported.

## Requirements

* Levels A and B: Python 3.10+, standard library only.
* Level C: `mpmath` (tested with 1.4.1), see `independent_check/requirements.txt`.
* The deep Arb audit: `python-flint` with a working Arb.

## Contact

Konstantin N. Pozdnyakov, Surgut, KhMAO — Yugra, Russia, fix@inbox.ru.
