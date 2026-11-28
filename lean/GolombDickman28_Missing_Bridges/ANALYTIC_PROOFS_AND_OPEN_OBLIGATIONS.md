# Mathematical bridge notes for v28

This note spells out the analytic arguments corresponding to the explicit Lean proof obligations. It is a mathematical derivation, not a claim that the Lean kernel has checked the complex-analysis and improper-integral arguments.

## 1. `cfRun` and the S-continuants

Write the production state at step `n` as

\[
(A_{n-1},A_n,B_{n-1},B_n),\qquad
A_0=z,\ A_{-1}=1,\ B_0=1,\ B_{-1}=0.
\]

The recurrence in the Python/Lean source is

\[
X_n=\beta_n X_{n-1}+\alpha_nX_{n-2},\quad
\alpha_n=\lceil n/2\rceil,\quad
\beta_n=\begin{cases}1&n\text{ odd},\\z&n\text{ even.}\end{cases}
\]

The S-continuants obey

\[
P_n(x)=P_{n-1}(x)+\alpha_n xP_{n-2}(x),\qquad x=1/z.
\]

Set

\[
\widetilde P_n(z)=z^{\lfloor n/2\rfloor}P_n(1/z).
\]

For odd `n=2m+1`,

\[
\widetilde P_n=z^mP_{n-1}(1/z)
 +(m+1)z^{m-1}P_{n-2}(1/z)
 =\widetilde P_{n-1}+(m+1)\widetilde P_{n-2},
\]

because `beta_n=1`. For even `n=2m`,

\[
\widetilde P_n=z^mP_{n-1}(1/z)
 +mz^{m-1}P_{n-2}(1/z)
 =z\widetilde P_{n-1}+m\widetilde P_{n-2},
\]

because `beta_n=z`. Thus `scaledS_step` is the parity split of one identity. The initial values are

\[
\widetilde P_0=1,\qquad
\widetilde P_1=P_1(1/z),
\]

which match `Bcur` for `(v0,v1)=(1,1)` and `Acur` for `(v0,v1)=(1,1+x)`, respectively (with the extra factor `z` in the denominator scaling). Strong induction then identifies both columns at every index. At odd indices the already existing `sToJ_numerator` and `sToJ_denominator` lemmas identify the contracted J-continuants.

**What this does not prove:** that the limit of these convergents equals `exp(u)E1(u)`, or that adjacent convergents bracket that analytic value. The existing `stieltjes_gap_hull` theorem is conditional on a bracket premise; the Stieltjes representation/alternation theorem must still be proved or cited as a separately trusted theorem.

## 2. Lemma 3: the discrete tails

Let

\[
u(t)=e^{t-e^{-t}},\quad q=e^{-t},
\quad u'(t)=u(t)(1+q)>0.
\]

Use the majorants

\[
g_R(t)=u(t)e^{-u(t)}(1+q),\qquad
g_L(t)=e^\gamma u(t)^2(1+q).
\]

Their logarithmic derivatives are

\[
\frac{d}{dt}\log g_R
=(1+q)(1-u)-\frac{q}{1+q}\le0
\quad\text{when }u\ge1,
\]

and

\[
\frac{d}{dt}\log g_L
=2(1+q)-\frac{q}{1+q}>0.
\]

Thus `g_R` is decreasing on the right tail and `g_L` is increasing on the left. For `h>0`,

\[
hg_R(kh)\le\int_{(k-1)h}^{kh}g_R(t)\,dt
\quad(k>K_R),
\]

and

\[
hg_L(kh)\le\int_{kh}^{(k+1)h}g_L(t)\,dt
\quad(k<-K_L).
\]

The cells are pairwise disjoint and tile the omitted half-lines. The change of variables `v=u(t)` gives

\[
\int_{K_Rh}^{\infty}g_R(t)\,dt
=\int_{u(K_Rh)}^{\infty}e^{-v}\,dv
=e^{-u(K_Rh)},
\]

and

\[
\int_{-\infty}^{-K_Lh}g_L(t)\,dt
=e^\gamma\int_0^{u(-K_Lh)}v\,dv
=\tfrac12e^\gamma u(-K_Lh)^2.
\]

Combining these with the pointwise bounds `0<G≤g_R` on the right and `0<G≤g_L` on the left proves the two tail bounds in Lemma 3.

**Lean status:** the sum comparison itself is proved in `tsum_discrete_sum_le_tail`. The exact grid samples/cells are now encoded in `Lemma3DiscreteTailProof`. The two monotonicity-to-cell inequalities, summability of cell integrals, and the improper-integral partition identities are still obligations to instantiate; they are not silently assumed to have been proved by that theorem.

## 3. Lemma 4: strip envelope calculation

Let `d=7/5`, `c=cos(d)`, and `w=x+iy`, `|y|≤d`. Put

\[
\rho=|u(w)|=\exp(x-e^{-x}\cos y),\qquad
\theta=\arg u(w)=y+e^{-x}\sin y.
\]

The numerical angle facts can be reduced to elementary rational bounds:
`π>22/7`, `e²>7`, and `sin(d)<1` imply

\[
d=7/5<11/7<\pi/2,\qquad
e^{-2}<1/7,\qquad
	heta_{\max}<7/5+1/7=54/35<11/7<\pi/2.
\]

Hence `c=cos(d)>0` and `kappa=cos(thetaMax)>0`, and
`kappaPrime=kappa*exp(-exp(-2))>0`. These elementary numeric inequalities are
not yet Lean theorems in the package; the Python code currently confirms the
corresponding strict inequalities using Arb.

### Region I: `x≤0`

Here `rho≤e^{-c}<1`. From

\[
F(u)=e^\gamma u\exp(-2u+S(u)),\qquad
S(u)=\sum_{j\ge2}\frac{(-u)^j}{j\,j!},
\]

and

\[
\sum_{j\ge2}\frac{1}{j\,j!}
\le\frac12\sum_{j\ge2}\frac1{j!}
=\frac{e-2}{2},
\]

we obtain `|F(u)|≤C1 |u|`, where

\[
C_1=e^{\gamma+2+(e-2)/2}.
\]

Consequently

\[
|G(w)|\le C_1e^{2x-2ce^{-x}}(1+e^{-x}).
\]

With `s=e^{-x}` and `s^{-3}≤1` for `s≥1`,

\[
\begin{aligned}
\int_{-\infty}^0|G(x+iy)|dx
&\le C_1\int_1^\infty\frac{1+s}{s^3}e^{-2cs}ds\\
&\le C_1e^{-2c}\left(\frac1c+\frac1{4c^2}\right)=M_1.
\end{aligned}
\]

### Region II: `0≤x≤2`

Because `cos y≥0`, `rho≤e^x≤e²`, and `|1+e^{-w}|≤2`. Also

\[
\sum_{j\ge2}\frac{\rho^j}{j\,j!}
\le\frac12e^\rho.
\]

Therefore

\[
|G(w)|\le 2e^\gamma e^4
\exp\left(2e^2+\tfrac12e^{e^2}\right)=B_2,
\]

and the interval has length two, so

\[
\int_0^2|G(x+iy)|dx\le2B_2=M_2.
\]

### Region III: `x≥2`

We have

\[
|\theta|\le\theta_{\max}=d+e^{-2}\sin d<\pi/2,
\quad\kappa=\cos\theta_{\max}>0.
\]

Also `rho≥e^{x-e^{-2}}`, hence

\[
\Re u(w)\ge\kappa\rho\ge\kappa'e^x,
\qquad \kappa'=\kappa e^{-e^{-2}}.
\]

In the right half-plane,

\[
E_1(u)=\int_0^\infty\frac{e^{-(u+r)}}{u+r}\,dr,
\qquad |u+r|\ge|u|=\rho,
\]

so `|E1(u)|≤1/rho≤e^{e^{-2}-2}`. Using `F(u)=exp(-u-E1(u))`,

\[
|F(u)|\le e^{e^{e^{-2}-2}}e^{-\kappa\rho}.
\]

Since `rho≤e^x` and `1+e^{-x}≤1+e^{-2}`,

\[
|G(w)|\le e^{e^{e^{-2}-2}}(1+e^{-2})e^x e^{-\kappa'e^x}.
\]

The substitution `s=e^x` gives

\[
\int_2^\infty|G(x+iy)|dx
\le e^{e^{e^{-2}-2}}(1+e^{-2})\frac{e^{-\kappa'e^2}}{\kappa'}=M_3.
\]

Summing the three regions yields `M=M1+M2+M3` uniformly over the strip.

### Entire-ness and uniform decay

`u(w)=exp(w-exp(-w))` is entire. The series defining `S` converges uniformly on every compact set because for `|u|≤R` it is dominated by `sum R^j/j!`; hence `S` is entire. Composition and products of entire functions show that `G` is entire. The Region I and Region III envelopes tend to zero as `x→−∞` and `x→+∞`, respectively, uniformly for `|y|≤d`. The middle region is bounded. This proves the uniform horizontal decay needed by the strip trapezoidal theorem.

**Lean status:** `GolombDickman28_Bridge.lean` records the exact constants/envelopes and makes the required facts named fields of `Lemma4StripWitness`. The pointwise estimates, improper integral evaluations, entire-ness of the series-defined `G`, and uniform decay have not yet been reduced to Mathlib kernel proofs in this package. The numeric facts `cos(7/5)>0` and `thetaMax<π/2` also need a machine-checked inequality proof (the Python Arb checks are not a Lean proof).

## 4. Decimal boundary isolation

The Python code computes, with positive integers,

\[
a=\left\lfloor\frac{\lambda_{lo}10^D}{2^S}\right\rfloor,
\qquad
b=\left\lfloor\frac{\lambda_{hi}10^D}{2^S}\right\rfloor.
\]

Its test `a == b` says both scaled endpoints lie in one half-open cell `[a,a+1)`. Since `lambda_lo/2^S ≤ lambda ≤ lambda_hi/2^S` and `10^D>0`, monotonicity gives

\[
a\le10^D\lambda<a+1.
\]

Thus no decimal boundary `j/10^D` lies inside the certified interval, and the integer part `floor(10^D*lambda)` is unique. `nat_division_decimal_cell` proves the quotient/floor fact from Euclidean division; `dyadic_certificate_decimal_isolation` transports it through the dyadic enclosure to `InNatDecimalCell`; `nat_decimal_cell_unique` proves uniqueness of the nonnegative label.

This theorem assumes the published endpoints really enclose `lambda`. It does not prove that the Python Arb values are sound. The packaged hardened `parse_certificate()` does recompute both integer quotients and checks that the printed `digits` match the common decimal cell; this is a consistency check only, not authentication of the numerical origin of the endpoints.
