# Remaining items before claiming a fully machine-checked proof

1. **Compile the Lean modules.** This environment did not have `lean` or `lake`; successful compilation has not been established here.
2. **Complete Lemma 3 instantiation.** Prove monotonicity of the two displayed envelopes on the required tails, show each grid sample is bounded by its adjacent-cell integral, prove summability of the cell integrals, and identify the sum of cells with the corresponding improper integral. Then fill all fields of `Lemma3DiscreteTailProof`.
3. **Complete Lemma 4 for the actual `G`.** Formalize the entire power series defining `S`, prove the `F` and `G` composition is entire, establish the three pointwise regional bounds, evaluate/bound the three improper integrals, and prove uniform decay. Prove `cos(7/5)>0` and `thetaMax<π/2` inside Lean, rather than trusting Arb runtime checks.
4. **Prove the Stieltjes bracket.** The recurrence bridge identifies the finite convergents, but the theorem that `exp(u)E1(u)` is between adjacent S-fraction convergents remains an analytic theorem, not a consequence of the algebraic recurrence.
5. **Formalize the strip trapezoidal theorem.** The v28 numerical bound uses the Trefethen–Weideman strip theorem. It is not a theorem of the existing Lean module yet.
6. **Close the computational trust boundary.** Lean does not verify python-flint/Arb or CPython. A proof-carrying interval export or independent exact-rational checker is required to turn the Python-generated node intervals into kernel-checkable inputs.
7. **Harden certificate parsing.** `parse_certificate()` must recompute `a=(lam_lo*10**D)//(1<<S)`, `b=(lam_hi*10**D)//(1<<S)` and require `a==b` and `digits == str(a).zfill(D)`; also validate `lam_lo>0`, `lam_hi>lam_lo`, and the expected digit count.

No item above should be silently treated as discharged by the algebraic bridge.
