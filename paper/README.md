# arXiv preprint

Two self-contained LaTeX articles are provided:

- `main.tex` describes the earlier 50,000-digit certificate;
- `main-75000.tex` describes the new 75,000-digit certificate, its
  error budget and its audit status. Its exact-integer checks pass, while
  the full independent Arb re-audit of all 476,648 nodes is reported as
  `NOT_RUN` (a 20-chunk sample was contained).

Both compile with any standard TeX distribution:

```bash
pdflatex main.tex
pdflatex main.tex        # second pass for the table of contents
```

or, with Tectonic:

```bash
tectonic main.tex
```

## What the paper claims

- the interval $[\Lambda_-,\Lambda_+]$ is a certificate for the first
  50,000 decimal digits, with width $10^{-50042.3574}$;
- every number in the error budget is either an exact integer or an
  outward-rounded bound;
- the verifier needs only exact integer arithmetic;
- the digit measurements and the A225242 extension are consequences of
  the certified string, not of a floating-point computation.

## What it does not claim

- it is not a formal proof in Coq/Lean; the trust base is Arb plus the
  cited theorems;
- the independent Arb re-audit of all nodes
  (`checks/verify_checkpoints_arb.py`) was not executed on the packaging
  machine; see Section 6;
- no claim about the normality of $\lambda$.

## Files

| File | Purpose |
|---|---|
| `main.tex` | the article for the 50,000-digit result (bibliography inline) |
| `main-75000.tex` | the article for the 75,000-digit result (bibliography inline) |
| `ARXIV_SUBMISSION.md` | title, abstract, categories and metadata for arXiv |
| `README.md` | this file |

A PDF is not checked into the repository; build it from `main.tex`.

## Suggested arXiv metadata

- **Primary category:** math.NA
- **Cross-list:** cs.MS (and optionally math.NT)
- **License:** CC BY 4.0
- **Comments:** 8 pages, 2 tables. Code, certificate and OEIS b-file:
  https://github.com/fix27/golomb-dickman-constant

The abstract for the submission form is in `ARXIV_SUBMISSION.md`.
