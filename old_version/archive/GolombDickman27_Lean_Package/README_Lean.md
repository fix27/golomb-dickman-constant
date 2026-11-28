# Golomb–Dickman v27 — Lean 4 formal kernel

## Files

- `GolombDickman27.lean` — Lean formalization of the exact algebraic and
  certificate-assembly kernel.
- `lean-toolchain` — Lean 4 `v4.36.0`.
- `lakefile.toml` — Mathlib dependency pinned to the matching `v4.36.0` tag.
- `AUDIT_golomb_dickman_27.md` — source-code audit, concrete defects, and the
  exact boundary of what the Lean file proves.

## Build

From this directory, with network access for the first dependency download:

```bash
lake update
lake build
```

To check only the source file:

```bash
lake env lean GolombDickman27.lean
```

The working environment used to prepare this package did not contain `lean`,
`lake`, or `elan`; therefore the file has **not** been compiled here. Do not
interpret the absence of `sorry`/`axiom` declarations as evidence that an
unrun compiler check has passed. Run the commands above in a Lean environment
before relying on the file as a compiled proof artifact.

## What is formalized

The file contains proofs of:

1. The exact recurrence for `Aₙ,Bₙ` in the continued-fraction evaluator and
   the alternating continuant determinant identity.
2. Positivity of the recurrence coefficients and positivity of the `A`
   denominators for positive input `z`.
3. The polynomial S-to-J contraction for both numerator and denominator
   continuants, for every truncation depth (not merely sampled depths).
4. The adjacent power-series term ratio bound used to obtain geometric tail
   control, the symmetric remainder-hull argument, and the parity identity
   for `(-1)^K`.
5. The implication from the Stieltjes adjacent-convergent bracket plus a
   bound on the convergent gap to the symmetric continued-fraction hull.
6. Sound rational interval addition and nonnegative scaling.
7. The conversion of certified integer endpoints at scale `2^S` into a
   rational enclosure.
8. The negligible-node interval contract, sound branch dispatch, quadrature
   assembly from finite-sum/tail/discretization premises, and the common
   decimal-cell rule used to certify a digit prefix.

## What is deliberately not claimed

This is **not** a verified translation of all 3,423 Python lines. In
particular, the following still need formal proof or a separately trusted
implementation:

- `F(u)`, `E₁(u)`, the change of variables `u(t)`, and the integral identity
  for the constant;
- the complex-strip bound and the Trefethen–Weideman trapezoidal theorem;
- the left/right infinite-tail integral bounds;
- the Laguerre moment/Jacobi-resolvent identification with the exponential
  integral, Carleman determinacy, and the classical Stieltjes convergence
  and alternation theorem;
- the proof that every actual Arb operation in `python-flint` has the
  interval semantics assumed by the mathematical argument;
- the correctness of CPython floats, `math` estimates, multiprocessing,
  file I/O, checkpoint serialization, and CLI behaviour.

The Stieltjes bracketing theorem and the combined analytic/Arb assembly
facts enter as explicit premises. The Lean results show what follows from
those premises; they do not manufacture the premises. Likewise,
`NodeCertificate` is a verified interface contract: a Python branch must
still be connected to a proof that its Arb ball satisfies that contract.

The polynomial S-to-J contraction is proved independently of the classical
Stieltjes convergence theorem. It does not by itself prove that the resulting
continued fraction converges to `e^u E₁(u)`.
