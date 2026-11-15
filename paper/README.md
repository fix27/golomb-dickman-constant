# arXiv preprint

`main.tex` is a self-contained LaTeX article (no `.bib` file, no figures)
describing the 40,000-digit certificate. It compiles with any standard
TeX distribution:

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
  40,000 decimal digits, with width $10^{-40042.2602491239}$;
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
| `main.tex` | the article (single file, bibliography inline) |
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
