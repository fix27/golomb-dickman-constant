# Golomb–Dickman v28: formal bridges (Lean 4 / Mathlib)

This package adds a bridge module to the previous `GolombDickman27.lean` formalization. Its Python file is based on the v28 source attached in this chat, with bounded checkpoint reads and certificate-parser hardening. It has not been rebased against the newer repository-root revision identified in the review by SHA-256 prefix `c7d58993`; that exact source was not attached here.

## Build

The package targets Lean `v4.36.0` and Mathlib `v4.36.0`:

```bash
lake update
lake build
```

To check the new module directly:

```bash
lake env lean GolombDickman28_Bridge.lean
```

## What the new module adds

1. **`cfRun -> sContinuant` algebraic bridge.** The theorem `cfRun_to_sContinuant` proves, for every finite index, that the numerator and denominator columns of the production recurrence are scaled evaluations of the existing S-continuants. `cfRun_odd_to_J` then connects odd convergents to the existing S-to-J contraction. This closes the recurrence-identification gap; it does not by itself prove that the continued fraction converges to `exp(u) * E1(u)`.
2. **Lemma 3 discrete-sum layer.** The module defines the exact `u(t)`, right/left majorants, grid samples, adjacent cells, and tail expressions from v28. The finite and infinite sum-comparison theorems are proved. The monotone sample-to-cell inequalities, summability of the cell integrals, and the cell-integral tail evaluations are deliberately exposed as fields of `Lemma3DiscreteTailProof`; the package does not claim those analytic fields have been instantiated.
3. **Lemma 4 strip layer.** The exact constants `d,c,thetaMax,kappa,kappaPrime,M1,M2,M3` and the three regional envelopes are encoded. Positivity consequences and the composition from a strip witness to the trapezoidal hypotheses are proved. The witness still requires proof of entire-ness, uniform decay, horizontal integrability, and the three regional integral bounds for the actual complex integrand `G`.
4. **Decimal-cell isolation.** `nat_division_decimal_cell` and `dyadic_certificate_decimal_isolation` formalize the Python integer quotient/floor test (the latter returns the Nat-indexed predicate `InNatDecimalCell`). The theorem proves that if both dyadic endpoints have the same quotient after multiplication by `10^D`, then every enclosed value lies in the same half-open decimal cell. `nat_decimal_cell_unique` proves uniqueness for Python's nonnegative quotient; `decimal_cell_unique` is the signed-integer version.
5. **Conditional global assembly.** `explicit_analytic_assembly` wires these outputs into the pre-existing rational interval assembly theorem.

## Important verification status

The Lean/Lake executables were not available in the execution environment used to prepare this package. Therefore **this package has not been compiled here**. It contains no `sorry` or user-declared `axiom`, but absence of those keywords is not a substitute for a successful Lean kernel check. Please run the commands above before treating it as a checked Lean artifact.

Also, this is not yet a fully closed formal proof of every analytic step in the Python paper. Specifically, the current Lean module makes the remaining Lemma 3 and Lemma 4 analytic obligations explicit rather than hiding them inside one large premise. The Stieltjes adjacent-convergent bracket for `exp(u)E1(u)`, the trapezoidal theorem itself, and the soundness of python-flint/Arb and CPython are also outside the Lean kernel formalized here.

## Additional v28 certificate-parser hardening

The included `golomb_dickman_28.py` is based on the v28 source attached in this chat and includes two defensive changes: (a) `_safe_load()` reads at most `max_bytes + 1` from one open file descriptor before unpickling, avoiding the `getsize()`/`read()` race; and (b) `parse_certificate()` recomputes both integer quotients

```python
a = (lam_lo * 10**D) >> S
b = (lam_hi * 10**D) >> S
```

and rejects the file unless `a == b` and the printed digit string equals `str(a).zfill(D)`. It also rejects malformed interval metadata. This checks consistency between the serialized decimal digits and the dyadic interval; it does **not** authenticate the interval's numerical origin. The parser-only change is provided as `parse_certificate_hardening.patch`; the bounded-read change is included in the Python source. The byte cap limits serialized input size, but does not constitute a formal bound on unpickler memory amplification. `python -m py_compile` passed for this packaged Python copy.
