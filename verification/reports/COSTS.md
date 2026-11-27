# Cost of the independent recomputation (Level C)

Measured on the machine that assembled this package: Windows 10/11, Python
3.12.10, mpmath 1.4.1, one core unless `--jobs` is given. `mpmath.quad` is
pure Python over its own arbitrary-precision floats, so the cost grows
roughly like the cube of the working precision.

| digits | working dps | rule | wall time |
|--------|-------------|------|-----------|
| 60 | 120 | tanh-sinh | 1.9 s |
| 60 | 120 | Gauss-Legendre | 2.1 s |
| 250 | 310 | tanh-sinh | 40 s |
| 300 | 360 | tanh-sinh | 61 s |
| 1000 | 1060 | tanh-sinh | 3817 s (63.6 min) |
| 1000 | 1060 | Gauss-Legendre | 3081 s (51.3 min) |
| 5000 | 5060 | tanh-sinh | hours (not run here) |
| 40000 | 40060 | tanh-sinh | days (not run here) |

The two rules are evaluated at the same truncation point

    U = (digits + 60) ln 10,

which makes the neglected tail smaller than `10^-(digits+60)`, because
`0 < exp(-u - E1(u)) <= exp(-u)` and `integral_U^inf exp(-u) du = exp(-U)`.

## Commands

```sh
# level C at 1,000 digits
python independent_quadrature.py --digits 1000 --json report.json

# level C at 5,000 digits, parallel over panels
python independent_quadrature.py --digits 5000 --jobs 12

# level C at full length
python independent_quadrature.py --digits 40000 --jobs 12
```

`--jobs N` parallelises the quadrature panels with `multiprocessing`; each
worker still integrates with the same rule, so the *algorithmic*
independence comes from the rule and the library, not from the number of
processes.

## What a match would and would not mean

At 1,000 digits the two rules agreed for 1,020 leading digits, and both
agreed with the certified file for the same 1,020 digits; see
`independent_1000.txt`.

The check was repeated on 2026-11-23 against the shipped
`50000/golomb_dickman_50000_digits.txt` (since removed from the repository;
this report is retained as a record). The earlier run compared with the
40,000-digit file. The two rules again agreed for 1,020 digits and matched
the 50,000-digit file for the same 1,020 digits, with no Arb and no
Python-flint in the loop:

| rule | working dps | wall time |
|------|-------------|-----------|
| tanh-sinh | 1060 | 912.64 s |
| Gauss-Legendre | 1060 | 1079.04 s |

Full output: `independent_1000_vs_50000.txt`; machine-readable:
`independent_1000_vs_50000.json`. The rerun was faster than the November 15
measurement in the table above (3,817 s and 3,081 s) on a different mpmath
build; both measurements are reported.


A match of the first N digits between the two rules and the certified file
is strong numerical evidence that the published digits are right. It is not
a proof: mpmath does not propagate rounding errors, so a systematic error
common to both rules would not be detected. Only the Arb certificate, and
its independent re-audit (`verify_checkpoints_arb.py`), give an enclosure.
