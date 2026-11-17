# Papers: 50,000 and 40,000 certified digits

Author: **Konstantin N. Pozdnyakov** (Поздняков Константин Николаевич),
Surgut, Khanty-Mansi Autonomous Okrug — Yugra, Russia,
[fix@inbox.ru](mailto:fix@inbox.ru).

This directory contains two self-contained LaTeX articles about the
Golomb–Dickman constant

$$
\lambda=\int_0^\infty e^{-u-E_1(u)}\,du
=0.624329988543550870992936383100837244\ldots
$$

Both articles have the bibliography inline (no `.bib` file) and use no
figures.

| File | Result | Status |
|---|---|---|
| [`main-50000.tex`](main-50000.tex) | first **50,000** decimal digits | current result |
| [`main.tex`](main.tex) | first **40,000** decimal digits | previous result, kept as a control |

## Build

No PDF is checked in. Build either article with a standard TeX
distribution:

```bash
pdflatex main-50000.tex
pdflatex main-50000.tex      # second pass for the table of contents
```

or

```bash
tectonic main-50000.tex
```

For the 40,000-digit article, replace `main-50000.tex` by `main.tex`.

## Current result: 50,000 digits

`main-50000.tex` describes an integer interval certificate
$[\Lambda_-,\Lambda_+]$ with scale $S=166\,293$ such that

$$
\lambda\in[\Lambda_-/2^S,\Lambda_+/2^S],
\qquad
\left\lfloor 10^{50000}\Lambda_-/2^S\right\rfloor
=
\left\lfloor 10^{50000}\Lambda_+/2^S\right\rfloor .
$$

The interval width is $4.390\times10^{-50043}$, i.e.
$10^{-50042.3574387469}$; this leaves $42.36$ digits of margin beyond
the 50,000 certified digits. The digits are therefore proved by
truncation, not merely computed in floating point.

The paper gives:

- the error budget and all integer corrections
  $B=1$, $T_R=2\,400\,727\,111\,627\,803$,
  $T_L=26\,985\,556\,367\,958$,
  $C=T_R+T_L+B=2\,427\,712\,667\,995\,762$;
- the certificate format and a verifier that uses only exact integer
  arithmetic;
- a b-file for OEIS A084945 with $n=0,\ldots,49999$, extending the
  published 102 terms;
- measurements on the 50,000-digit string;
- the OEIS A225242 bounds $a(5),a(6)>50\,000$, strengthening both the
  published bound $a(5)>15\,000$ and the earlier 40,000-digit bounds
  $a(5),a(6)>40\,000$;
- an audit of the statements on the MathWorld page
  *Golomb–Dickman Constant Digits*.

### Parameters of the 50,000-digit run

| Quantity | Value |
|---|---|
| certified digits $D$ | 50,000 |
| guard digits $G$ | 30 |
| node radius exponent $E_{\mathrm{bits}}$ | 166,229 |
| certificate scale $S$ | 166,293 |
| step $h$ | $80\,846\,368/2^{40}$ |
| node counts $K_L,K_R$ | 149,075, 158,504 |
| chunks / nodes | 3,076 / 307,580 (chunk size 100) |
| $\log_{10}M$ | 360.3909 |
| $\log_{10}B_{\mathrm{disc}}$ | −51,594.8080 |
| $\log_{10}\tau_R$ | −50,043.8007 |
| $\log_{10}\tau_L$ | −50,045.7499 |
| interval width | $4.390\times10^{-50043}$ |
| margin beyond $10^{-D}$ | 42.36 digits |

## Previous result: 40,000 digits

`main.tex` is the earlier article and remains a correct description of
the 40,000-digit run. It is also the control for the 50,000-digit
result: the first 40,000 digits of the new certificate agree with the
older one.

Its certificate has $S=133\,074$, width
$5.492\times10^{-40043}$ ($10^{-40042.2602491239}$) and a margin of
$42.26$ digits. The b-file covers $n=0,\ldots,39999$, and the A225242
statement is $a(5),a(6)>40\,000$.

The 40,000-digit package is the only one that contains some
40,000-specific verification scripts
(`40000/checks/verify_nodes_decimal.py`,
`40000/checks/verify_checkpoints_arb.py`). They are described in that
paper and are not part of the 50,000-digit run.

## What neither paper claims

- **Not a formal proof.** The trust base is the correctness of Arb and
  the cited theorems; neither article is a formalisation in Coq or
  Lean.
- **No world-record claim.** The 50,000-digit result is an extension of
  the verified expansion, not a claim of a record.
- **No claim about normality.** The digit statistics are consistent
  with uniformity but say nothing about the normality of $\lambda$,
  which remains open.
- **No full Arb re-audit.** The Arb re-audit of the 40,000-digit nodes
  was not executed on the packaging machine; the corresponding script is
  included for an unrestricted host. No analogous full Arb re-audit was
  run for the 50,000-digit certificate.
- **Level C is numerical evidence only.** The independent recomputation
  covers 1,000 digits (the two methods and the certificate agree for
  1,020 leading digits). It does not cover 50,000 digits and is not a
  proof.
- **Probable primes are marked as such.** The 1,659- and 2,508-digit
  truncations are probable primes, not proved primes; prime substrings
  beyond the deterministic Miller–Rabin range are also only probable
  primes. The 40,000-digit article states the deterministic range
  explicitly.
- **Historical MathWorld attributions are not verified.** The claims
  attributed to Mitchell (1968) and Weisstein (2013) are marked
  historical / `NOT_VERIFIABLE` in the 50,000-digit audit.

## Verification

The repository's verification package is in
[`../verification/`](../verification/); the canonical data bundles are
[`../50000/`](../50000/) and [`../40000/`](../40000/).

```bash
# Level A: exact integer certificate check for 50,000 digits,
# also comparing the first 40,000 digits with the older certificate.
python verification/verify_certificate.py \
    --cert 50000/golomb_dickman_50000_certified.txt \
    --compare 40000/golomb_dickman_40000_digits.txt

# Level A: 40,000 digits.
python verification/verify_certificate.py \
    --cert 40000/golomb_dickman_40000_certified.txt

# Level B: audit the 3,076 chunks of the 50,000-digit run.
python verification/audit_chunks.py \
    --ckpt 50000/gd_rigorous_ckpt_50000 \
    --cert 50000/golomb_dickman_50000_certified.txt

# Level B: audit the 1,209 chunks of the 40,000-digit run (stdlib only).
python 40000/checks/verify_checkpoints.py
```

Level A runs in well under a second. Level B for 50,000 digits checks
contiguous coverage of 307,580 nodes, reproduces both endpoints with
$B=1$ and $C=2\,427\,712\,667\,995\,762$, and obtains a chunk-sum width
of $4.230\times10^{-50043}$ (the certificate width is
$4.390\times10^{-50043}$). Level B for 40,000 digits recovers
$m=100\,859\,575$ and $C=65\,673\,984\,721\,697$. Level C is

```bash
python verification/independent_quadrature.py --digits 1000
```

and is numerical evidence, not part of the proof.

## Checksums

Canonical files, ASCII/UTF-8 without BOM and with LF line endings:

```text
76f4155981049003351409769505c3cec39e26dfc30624c46bd199e70ed6477a  golomb_dickman_50000_certified.txt
8f017d45ee5108bb6b976882b079279f44f8a767ce62b44bd7c54e9167ad09a0  golomb_dickman_50000_digits.txt
1e3d23e9ac3ce51990d83decd395d6bde96027f43811b94cebd5a6a4b7c19c43  b084945.txt
8892c0715f1afbb271c9f07cc9658cea0f3ca83c2dda3ec7d23b447dc908de9c  golomb_dickman_40000_certified.txt
fbae757900983bd4fb6421c5f27bf9602af1a1bfc013e4c501bb9da2b5a65327  golomb_dickman_40000_digits.txt
c73af643198da299d2e624e3c2f69d05439efcddbbefa7cec176ac63f993bed3  b084945.txt
```

The first three entries are checked by
[`../50000/SHA256SUMS.txt`](../50000/SHA256SUMS.txt); the last three
appear in the appendix of `main.tex`. The two `b084945.txt` files are
different: the first has $n=0,\ldots,49999$, the second
$n=0,\ldots,39999$.

## Suggested arXiv metadata

For the 50,000-digit paper:

- **Title:** Fifty thousand certified decimal digits of the
  Golomb–Dickman constant
- **Primary category:** math.NA
- **Cross-list:** cs.MS (optionally math.NT)
- **License:** CC BY 4.0
- **Comments:** code, certificates and OEIS b-files at
  <https://github.com/fix27/golomb-dickman-constant>

[`ARXIV_SUBMISSION.md`](ARXIV_SUBMISSION.md) currently contains the
metadata and abstract for the **40,000-digit** article. Update its
title, abstract and digit count before submitting
`main-50000.tex`.
