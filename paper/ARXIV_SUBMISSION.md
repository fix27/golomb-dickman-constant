# arXiv submission metadata

Copy the fields below into the arXiv submission form. arXiv accepts a
single `main.tex` for this paper.

## Title

```text
Fifty thousand certified decimal digits of the Golomb-Dickman constant
```

## Authors

```text
Konstantin N. Pozdnyakov
```

Affiliation (if the form asks for one):

```text
Surgut, Khanty-Mansi Autonomous Okrug - Yugra, Russia
```

Contact e-mail:

```text
fix@inbox.ru
```

## Abstract (plain text, for the form)

```text
We describe a rigorous interval-arithmetic certificate for the first
50,000 decimal digits of the Golomb-Dickman constant
lambda = integral_0^infinity exp(-u - E_1(u)) du
       = 0.624329988543550870992936383100837244...,
where E_1 is the exponential integral. The certificate consists of
integers Lambda_- < Lambda_+ and a scale S = 166293 such that lambda lies
in [Lambda_-/2^S, Lambda_+/2^S] and

  floor(10^50000 Lambda_-/2^S) = floor(10^50000 Lambda_+/2^S).

Consequently the digits are proved by truncation, not merely computed in
floating point. The interval width is 10^-50042.3574, which leaves more
than 42 guard digits. The computation evaluates
lambda = integral_R G(t) dt by the trapezoidal rule after the
Takahashi-Mori substitution, with explicit tail and discretisation
bounds in the spirit of Trefethen-Weideman and with every node enclosed
in an Arb ball. We give the error budget, the certificate format, a
checker that uses only exact integer arithmetic, and a b-file for OEIS
A084945 with terms n = 0..49999. The 40,000-digit certificate of the
earlier run is kept unchanged as the previous result. We also report
measurements on the resulting digit string and two extensions of OEIS
A225242. The trust base is the correctness of Arb together with the
cited theorems; this is not a formalisation in a proof assistant.
```

## Categories

- Primary: **math.NA** (Numerical Analysis)
- Cross-list: **cs.MS** (Mathematical Software)
- Optional second cross-list: **math.NT** (Number Theory)

## Comments field

```text
8 pages, 2 tables. Certificate, code, checkpoints and OEIS b-file:
https://github.com/fix27/golomb-dickman-constant/tree/main/50000
```

## MSC codes

```text
65G40 (primary), 65D30, 11Y60, 33B20
```

## License

CC BY 4.0 is the usual choice for a data-and-software paper. arXiv also
offers the non-exclusive licence; either is acceptable here.

## Endorsement

A first submission to math.NA normally needs an endorsement from an
established author in that category. If arXiv asks for one, send the
request together with the abstract above; the SeqFan announcement
(`../submission/EMAILS.md`) is a reasonable place to ask for a
colleague who can endorse.

## Checklist

1. Compile `main.tex` locally and read the PDF once.
2. Submit `main.tex` (arXiv compiles it; no external files needed).
3. Check the generated PDF: table of contents, two tables, references.
4. Add the arXiv identifier to `40000/README.md` and the root `README.md`
   after the announcement appears.
