/-
Formal kernel for `golomb_dickman_27.py`.

This file is intentionally explicit about the trust boundary.  It formalizes:
* the exact continued-fraction recurrence and its determinant identity;
* the S-fraction coefficient pattern and its S-to-J contraction at the
  polynomial/continuant level;
* the elementary ratio estimate used by the power-series tail bound;
* the interval-hull argument used by the continued-fraction branch;
* interval arithmetic, dyadic enclosure, node-branch dispatch, quadrature
  assembly, and the common-decimal-cell certificate rule.

It does NOT pretend to verify CPython, python-flint/Arb, the implementation of
transcendental functions, the complex strip estimate, the trapezoidal theorem,
or the classical Stieltjes convergence theorem.  Those enter below as
explicit premises/structures, not as `axiom` or `sorry` declarations.

Target: Lean 4 + Mathlib 4.36.0.
-/

import Mathlib

open scoped BigOperators
open Finset

noncomputable section

namespace GolombDickman27

/-! ## 1. Exact coefficient arithmetic -/

/-- The coefficient αₙ = ⌈n/2⌉, represented as `(n+1)/2` in `Nat`. -/
def cfAlpha (n : Nat) : ℚ := (((n + 1) / 2 : Nat) : ℚ)

lemma cfAlpha_zero : cfAlpha 0 = 0 := by norm_num [cfAlpha]
lemma cfAlpha_one : cfAlpha 1 = 1 := by norm_num [cfAlpha]

lemma cfAlpha_even (m : Nat) : cfAlpha (2 * m) = (m : ℚ) := by
  have h : (2 * m + 1) / 2 = m := by omega
  dsimp [cfAlpha]
  exact_mod_cast h

lemma cfAlpha_odd (m : Nat) : cfAlpha (2 * m + 1) = (m + 1 : Nat) := by
  have h : (2 * m + 1 + 1) / 2 = m + 1 := by omega
  dsimp [cfAlpha]
  exact_mod_cast h

lemma cfAlpha_even_succ (m : Nat) : cfAlpha (2 * m + 2) = (m + 1 : Nat) := by
  have h : (2 * m + 2 + 1) / 2 = m + 1 := by omega
  dsimp [cfAlpha]
  exact_mod_cast h

lemma cfAlpha_odd_two (m : Nat) : cfAlpha (2 * m + 3) = (m + 2 : Nat) := by
  have h : (2 * m + 3 + 1) / 2 = m + 2 := by omega
  dsimp [cfAlpha]
  exact_mod_cast h

lemma cfAlpha_even_two (m : Nat) : cfAlpha (2 * m + 4) = (m + 2 : Nat) := by
  have h : (2 * m + 4 + 1) / 2 = m + 2 := by omega
  dsimp [cfAlpha]
  exact_mod_cast h

lemma cfAlpha_odd_three (m : Nat) : cfAlpha (2 * m + 5) = (m + 3 : Nat) := by
  have h : (2 * m + 5 + 1) / 2 = m + 3 := by omega
  dsimp [cfAlpha]
  exact_mod_cast h

/-- The odd/even coefficient in the production S-fraction recurrence. -/
def cfBeta (z : ℚ) (n : Nat) : ℚ := if n % 2 = 1 then 1 else z

/-! ## 2. Production continued-fraction recurrence -/

structure CFState where
  Aprev : ℚ
  Acur  : ℚ
  Bprev : ℚ
  Bcur  : ℚ
  deriving Repr

def cfStep (z : ℚ) (n : Nat) (s : CFState) : CFState :=
  { Aprev := s.Acur
    Acur  := cfBeta z n * s.Acur + cfAlpha n * s.Aprev
    Bprev := s.Bcur
    Bcur  := cfBeta z n * s.Bcur + cfAlpha n * s.Bprev }

def cfRun (z : ℚ) : Nat → CFState
  | 0 => ⟨1, z, 0, 1⟩
  | n + 1 => cfStep z (n + 1) (cfRun z n)

def cfDet (s : CFState) : ℚ := s.Acur * s.Bprev - s.Aprev * s.Bcur

lemma cfDet_step (z : ℚ) (n : Nat) (s : CFState) :
    cfDet (cfStep z n s) = - cfAlpha n * cfDet s := by
  simp [cfDet, cfStep]
  ring

/-- Exact continuant determinant for the coefficients used by `cf_f_hull`. -/
theorem cfDet_formula (z : ℚ) (n : Nat) :
    cfDet (cfRun z n) =
      (-1 : ℚ) ^ (n + 1) * ∏ i ∈ Finset.range n, cfAlpha (i + 1) := by
  induction n with
  | zero =>
      simp [cfRun, cfDet]
  | succ n ih =>
      simp only [cfRun]
      rw [cfDet_step, ih, Finset.prod_range_succ]
      rw [show n + 1 + 1 = (n + 1) + 1 by omega, pow_succ]
      ring

lemma cfDet_is_convergent_difference_numerator (s : CFState) :
    s.Bcur * s.Aprev - s.Bprev * s.Acur = - cfDet s := by
  simp [cfDet]
  ring

/-! ## 3. S-fraction continuants and the exact S → J contraction -/

/-- Numerator/denominator continuants of the positive S-fraction.
    `v0` is the zeroth convergent value and `v1` the first one. -/
def sContinuant (x v0 v1 : Polynomial ℚ) : Nat → Polynomial ℚ
  | 0 => v0
  | 1 => v1
  | n + 2 =>
      sContinuant x v0 v1 (n + 1) +
        Polynomial.C (cfAlpha (n + 2)) * x * sContinuant x v0 v1 n

lemma sContinuant_step (x v0 v1 : Polynomial ℚ) (n : Nat) :
    sContinuant x v0 v1 (n + 2) =
      sContinuant x v0 v1 (n + 1) +
        Polynomial.C (cfAlpha (n + 2)) * x * sContinuant x v0 v1 n := by
  rfl

/-- J-fraction coefficients after contracting α₁, α₂, ... in pairs. -/
def jBeta (m : Nat) : ℚ := ((2 * m + 3 : Nat) : ℚ)
def jAlpha (m : Nat) : ℚ := (((m + 1) * (m + 1) : Nat) : ℚ)

/-- State `(previous J-convergent, current J-convergent)`.
    The transition is exactly `Rₘ = (1+bₘx)Rₘ₋₁-aₘx²Rₘ₋₂`. -/
def jContinuantPair (x prev cur : Polynomial ℚ) : Nat → Polynomial ℚ × Polynomial ℚ
  | 0 => (prev, cur)
  | m + 1 =>
      let p := jContinuantPair x prev cur m
      (p.2,
        (1 + Polynomial.C (jBeta m) * x) * p.2 -
          Polynomial.C (jAlpha m) * x ^ 2 * p.1)

/-- The odd S-convergent's preceding odd value; at index zero this is the
    explicit `-1` convergent supplied by the caller. -/
def sOddPrevious (x v0 v1 vm1 : Polynomial ℚ) (m : Nat) : Polynomial ℚ :=
  if m = 0 then vm1 else sContinuant x v0 v1 (2 * m - 1)

/-- One two-step elimination in the S recurrence.  This is the algebraic
    heart of the S-to-J contraction. -/
theorem sContinuant_odd_step
    (x v0 v1 vm1 : Polynomial ℚ)
    (hinit : v1 = v0 + Polynomial.C (1 : ℚ) * x * vm1)
    (m : Nat) :
    sContinuant x v0 v1 (2 * m + 3) =
      (1 + Polynomial.C (jBeta m) * x) * sContinuant x v0 v1 (2 * m + 1) -
        Polynomial.C (jAlpha m) * x ^ 2 * sOddPrevious x v0 v1 vm1 m := by
  cases m with
  | zero =>
      simp [sOddPrevious, sContinuant, cfAlpha, jBeta, jAlpha, hinit]
      have h2 : Polynomial.C (2 : ℚ) = (2 : Polynomial ℚ) := Polynomial.C_eq_natCast 2
      have h3 : Polynomial.C (3 : ℚ) = (3 : Polynomial ℚ) := Polynomial.C_eq_natCast 3
      rw [h2, h3]
      ring
  | succ m =>
      have h3raw := sContinuant_step x v0 v1 (2 * m + 1)
      have h3 : sContinuant x v0 v1 (2 * m + 3) =
          sContinuant x v0 v1 (2 * m + 2) +
            Polynomial.C (m + 2 : ℚ) * x * sContinuant x v0 v1 (2 * m + 1) := by
        simpa [show (2 * m + 1) + 2 = 2 * m + 3 by omega,
          show (2 * m + 1) + 1 = 2 * m + 2 by omega, cfAlpha_odd_two] using h3raw
      have h2raw := sContinuant_step x v0 v1 (2 * m + 2)
      have h2 : sContinuant x v0 v1 (2 * m + 4) =
          sContinuant x v0 v1 (2 * m + 3) +
            Polynomial.C (m + 2 : ℚ) * x * sContinuant x v0 v1 (2 * m + 2) := by
        simpa [show (2 * m + 2) + 2 = 2 * m + 4 by omega,
          show (2 * m + 2) + 1 = 2 * m + 3 by omega, cfAlpha_even_two] using h2raw
      have h1raw := sContinuant_step x v0 v1 (2 * m + 3)
      have h1 : sContinuant x v0 v1 (2 * m + 5) =
          sContinuant x v0 v1 (2 * m + 4) +
            Polynomial.C (m + 3 : ℚ) * x * sContinuant x v0 v1 (2 * m + 3) := by
        simpa [show (2 * m + 3) + 2 = 2 * m + 5 by omega,
          show (2 * m + 3) + 1 = 2 * m + 4 by omega, cfAlpha_odd_three] using h1raw
      have hsolve : sContinuant x v0 v1 (2 * m + 2) =
          sContinuant x v0 v1 (2 * m + 3) -
            Polynomial.C (m + 2 : ℚ) * x * sContinuant x v0 v1 (2 * m + 1) := by
        rw [h3]
        ring
      have hprev : sOddPrevious x v0 v1 vm1 (m + 1) =
          sContinuant x v0 v1 (2 * m + 1) := by
        simp [sOddPrevious, show 2 * (m + 1) - 1 = 2 * m + 1 by omega]
      calc
        sContinuant x v0 v1 (2 * (m + 1) + 3) =
            sContinuant x v0 v1 (2 * m + 5) := by congr 1 <;> omega
        _ = sContinuant x v0 v1 (2 * m + 4) +
              Polynomial.C (m + 3 : ℚ) * x * sContinuant x v0 v1 (2 * m + 3) := h1
        _ = (sContinuant x v0 v1 (2 * m + 3) +
              Polynomial.C (m + 2 : ℚ) * x * sContinuant x v0 v1 (2 * m + 2)) +
              Polynomial.C (m + 3 : ℚ) * x * sContinuant x v0 v1 (2 * m + 3) := by rw [h2]
        _ = (1 + Polynomial.C (jBeta (m + 1)) * x) *
              sContinuant x v0 v1 (2 * m + 3) -
              Polynomial.C (jAlpha (m + 1)) * x ^ 2 *
                sContinuant x v0 v1 (2 * m + 1) := by
              rw [hsolve]
              simp [jBeta, jAlpha]
              have h2 : Polynomial.C (2 : ℚ) = (2 : Polynomial ℚ) := Polynomial.C_eq_natCast 2
              have h3 : Polynomial.C (3 : ℚ) = (3 : Polynomial ℚ) := Polynomial.C_eq_natCast 3
              rw [h2, h3]
              ring
        _ = (1 + Polynomial.C (jBeta (m + 1)) * x) *
              sContinuant x v0 v1 (2 * (m + 1) + 1) -
              Polynomial.C (jAlpha (m + 1)) * x ^ 2 *
                sOddPrevious x v0 v1 vm1 (m + 1) := by
              rw [hprev, show 2 * (m + 1) + 1 = 2 * m + 3 by omega]

/-- For every odd S-convergent, the two consecutive odd continuants are
    exactly the corresponding J-continuants. -/
theorem sToJ_pair
    (x v0 v1 vm1 : Polynomial ℚ)
    (hinit : v1 = v0 + Polynomial.C (1 : ℚ) * x * vm1) :
    ∀ m : Nat,
      sContinuant x v0 v1 (2 * m + 1) = (jContinuantPair x vm1 v1 m).2 ∧
      sOddPrevious x v0 v1 vm1 m = (jContinuantPair x vm1 v1 m).1 := by
  intro m
  induction m with
  | zero =>
      constructor <;> simp [sContinuant, sOddPrevious, jContinuantPair]
  | succ m ih =>
      have hstep := sContinuant_odd_step x v0 v1 vm1 hinit m
      have hidx₁ : 2 * (m + 1) + 1 = 2 * m + 3 := by omega
      constructor
      · rw [hidx₁, hstep, ih.1, ih.2]
        simp [jContinuantPair]
      · have hidx₂ : 2 * (m + 1) - 1 = 2 * m + 1 := by omega
        simpa [sOddPrevious, hidx₂, ih.1, jContinuantPair]

abbrev xPoly : Polynomial ℚ := Polynomial.X

def sNumerator (n : Nat) : Polynomial ℚ := sContinuant xPoly 1 1 n
def sDenominator (n : Nat) : Polynomial ℚ := sContinuant xPoly 1 (1 + xPoly) n

def jNumerator (m : Nat) : Polynomial ℚ :=
  (jContinuantPair xPoly 0 1 m).2

def jDenominator (m : Nat) : Polynomial ℚ :=
  (jContinuantPair xPoly 1 (1 + xPoly) m).2

theorem sToJ_numerator (m : Nat) :
    sNumerator (2 * m + 1) = jNumerator m := by
  have hinit : (1 : Polynomial ℚ) =
      1 + Polynomial.C (1 : ℚ) * xPoly * (0 : Polynomial ℚ) := by simp
  exact (sToJ_pair xPoly 1 1 0 hinit m).1

theorem sToJ_denominator (m : Nat) :
    sDenominator (2 * m + 1) = jDenominator m := by
  have hinit : (1 + xPoly : Polynomial ℚ) =
      1 + Polynomial.C (1 : ℚ) * xPoly * 1 := by
    have h1 : Polynomial.C (1 : ℚ) = (1 : Polynomial ℚ) := Polynomial.C_eq_natCast 1
    rw [h1]
    ring
  exact (sToJ_pair xPoly 1 (1 + xPoly) 1 hinit m).1

/-! ## 4. Positive coefficient and determinant consequences -/

theorem cfAlpha_pos (n : Nat) (hn : 1 ≤ n) : 0 < cfAlpha n := by
  unfold cfAlpha
  have h : 0 < (n + 1) / 2 := by omega
  exact_mod_cast h

theorem cfBeta_pos (z : ℚ) (hz : 0 < z) (n : Nat) :
    0 < cfBeta z n := by
  by_cases h : n % 2 = 1
  · simp [cfBeta, h]
  · simp [cfBeta, h, hz]

theorem cfRun_A_positive (z : ℚ) (hz : 0 < z) :
    ∀ n : Nat, 0 < (cfRun z n).Aprev ∧ 0 < (cfRun z n).Acur := by
  intro n
  induction n with
  | zero =>
      constructor
      · norm_num [cfRun]
      · simpa [cfRun] using hz
  | succ n ih =>
      constructor
      · change 0 < (cfRun z n).Acur
        exact ih.2
      · change 0 < cfBeta z (n + 1) * (cfRun z n).Acur +
          cfAlpha (n + 1) * (cfRun z n).Aprev
        exact add_pos
          (mul_pos (cfBeta_pos z hz (n + 1)) ih.2)
          (mul_pos (cfAlpha_pos (n + 1) (by omega)) ih.1)

theorem jAlpha_pos (m : Nat) : 0 < jAlpha m := by
  unfold jAlpha
  positivity

theorem jBeta_pos (m : Nat) : 0 < jBeta m := by
  unfold jBeta
  positivity

/-! ## 5. Power-series term ratio and symmetric remainder -/

/-- The absolute ratio of adjacent `u^n/(n n!)` terms is at most 1/2
    once `2u ≤ n+1`.  This is the exact inequality used in Lemma 1(d). -/
theorem seriesTermRatio_le_half
    (u : ℝ) (n : Nat) (hu : 0 ≤ u) (hsmall : 2 * u ≤ (n : ℝ) + 1) :
    u * (n : ℝ) / ((n : ℝ) + 1) ^ 2 ≤ (1 : ℝ) / 2 := by
  have hden : 0 < (n : ℝ) + 1 := by positivity
  have hn : (n : ℝ) ≤ (n : ℝ) + 1 := by linarith
  have hratio : (n : ℝ) / ((n : ℝ) + 1) ≤ 1 :=
    (div_le_iff₀ hden).2 (by linarith)
  have huratio : u / ((n : ℝ) + 1) ≤ (1 : ℝ) / 2 :=
    (div_le_iff₀ hden).2 (by linarith)
  calc
    u * (n : ℝ) / ((n : ℝ) + 1) ^ 2 =
        (u / ((n : ℝ) + 1)) * ((n : ℝ) / ((n : ℝ) + 1)) := by
          field_simp [ne_of_gt hden]
          <;> ring
    _ ≤ (u / ((n : ℝ) + 1)) * 1 :=
          mul_le_mul_of_nonneg_left hratio (by positivity)
    _ = u / ((n : ℝ) + 1) := by ring
    _ ≤ (1 : ℝ) / 2 := huratio

theorem symmetric_remainder_inclusion
    (partialVal remainder radius : ℝ) (hrem : |remainder| ≤ radius) :
    partialVal - radius ≤ partialVal + remainder ∧
      partialVal + remainder ≤ partialVal + radius := by
  have habs := abs_le.mp hrem
  constructor <;> linarith

theorem even_power_neg_one (k : Nat) (hk : Even k) :
    (-1 : ℚ) ^ k = 1 := by
  rcases hk with ⟨m, rfl⟩
  simp [pow_mul]

theorem odd_power_neg_one (k : Nat) (hk : Odd k) :
    (-1 : ℚ) ^ k = -1 := by
  rcases hk with ⟨m, rfl⟩
  simp [pow_add, pow_mul]

/-- Magnitude used in Lemma 1(c) for the asymptotic expansion remainder. -/
def asymptoticRemainderBound (K : Nat) (u : ℝ) : ℝ :=
  (K.factorial : ℝ) / u ^ (K + 1)

theorem asymptoticRemainderBound_pos (K : Nat) (u : ℝ) (hu : 0 < u) :
    0 < asymptoticRemainderBound K u := by
  unfold asymptoticRemainderBound
  positivity

/-! ## 6. Continued-fraction hull (Stieltjes theorem supplied as a premise) -/

/-- If two consecutive convergents bracket the target and their distance is
    bounded by `D`, then the symmetric Arb-style ball around the newest
    convergent contains the target. -/
theorem stieltjes_gap_hull
    (previous current target gap : ℝ)
    (hbracket : (previous ≤ target ∧ target ≤ current) ∨
                (current ≤ target ∧ target ≤ previous))
    (hgap : |current - previous| ≤ gap) :
    current - gap ≤ target ∧ target ≤ current + gap := by
  have hgap' := abs_le.mp hgap
  have hgap_nonneg : 0 ≤ gap := le_trans (abs_nonneg (current - previous)) hgap
  rcases hbracket with h₁ | h₂
  · constructor <;> linarith
  · constructor <;> linarith

/-- This is the exact mathematical contract needed from the classical
    Stieltjes convergence/alternation theorem.  It is deliberately a
    parameter, not asserted as a proved theorem of this file. -/
def StieltjesBracketPremise (target previous current : ℝ) : Prop :=
  (previous ≤ target ∧ target ≤ current) ∨
  (current ≤ target ∧ target ≤ previous)

/-! ## 7. Rational interval arithmetic model -/

structure QInterval where
  lo : ℚ
  hi : ℚ
  ordered : lo ≤ hi
  deriving Repr

def QContains (I : QInterval) (x : ℚ) : Prop := I.lo ≤ x ∧ x ≤ I.hi

def qAdd (I J : QInterval) : QInterval :=
  ⟨I.lo + J.lo, I.hi + J.hi, by linarith [I.ordered, J.ordered]⟩

theorem qAdd_sound (I J : QInterval) (x y : ℚ)
    (hI : QContains I x) (hJ : QContains J y) :
    QContains (qAdd I J) (x + y) := by
  unfold QContains at hI hJ ⊢
  dsimp [qAdd]
  constructor <;> linarith [hI.1, hI.2, hJ.1, hJ.2]

def qScale (a : ℚ) (I : QInterval) (ha : 0 ≤ a) : QInterval :=
  ⟨a * I.lo, a * I.hi, mul_le_mul_of_nonneg_left I.ordered ha⟩

theorem qScale_sound (a : ℚ) (I : QInterval) (ha : 0 ≤ a)
    (x : ℚ) (hI : QContains I x) :
    QContains (qScale a I ha) (a * x) := by
  change a * I.lo ≤ a * x ∧ a * x ≤ a * I.hi
  constructor
  · exact mul_le_mul_of_nonneg_left hI.1 ha
  · exact mul_le_mul_of_nonneg_left hI.2 ha

/-! ## 8. Dyadic integer endpoints and decimal-cell certification -/

def pow2Q (S : Nat) : ℚ := (2 : ℚ) ^ S

theorem dyadic_integer_enclosure
    (S : Nat) (L H : Int) (x : ℚ)
    (hscale : 0 < pow2Q S)
    (hL : (L : ℚ) ≤ x * pow2Q S)
    (hH : x * pow2Q S ≤ (H : ℚ)) :
    (L : ℚ) / pow2Q S ≤ x ∧ x ≤ (H : ℚ) / pow2Q S := by
  constructor
  · exact (div_le_iff₀ hscale).2 (by simpa [mul_comm] using hL)
  · exact (le_div_iff₀ hscale).2 hH

/-- The certificate's floor test is a common-cell test, not rounding:
    if both endpoints lie in the same half-open interval `[n,n+1)`, then
    every enclosed value has the same integer part. -/
theorem common_decimal_cell
    (scale lo hi value : ℚ) (n : Int)
    (hscale : 0 ≤ scale)
    (hlo : (n : ℚ) ≤ scale * lo)
    (hhi : scale * hi < (n : ℚ) + 1)
    (henc : lo ≤ value ∧ value ≤ hi) :
    (n : ℚ) ≤ scale * value ∧ scale * value < (n : ℚ) + 1 := by
  have hlo' := mul_le_mul_of_nonneg_left henc.1 hscale
  have hhi' := mul_le_mul_of_nonneg_left henc.2 hscale
  constructor <;> linarith

/-! ## 9. Node branch contracts -/

/-- A real interval carrying the same semantic postcondition as a successful
    `node_ball`: inclusion and a strict radius/width requirement. -/
structure NodeCertificate (target eps : ℝ) where
  lo : ℝ
  hi : ℝ
  ordered : lo ≤ hi
  contains_lo : lo ≤ target
  contains_hi : target ≤ hi
  radius_ok : (hi - lo) / 2 < eps

/-- The negligible-node branch returns the symmetric ball `[0,U]`. -/
def skipNodeCertificate
    (target eps U : ℝ)
    (hlo : 0 ≤ target)
    (hhi : target ≤ U)
    (hU : 0 ≤ U)
    (hrad : U / 2 < eps) : NodeCertificate target eps :=
  ⟨0, U, hU, hlo, hhi, by nlinarith⟩

inductive NodeMethod
  | skip
  | series
  | continuedFraction
  | asymptotic
  deriving DecidableEq, Repr

/-- Dispatch cannot destroy correctness: every selectable branch must
    already return a `NodeCertificate`.  Heuristic routing only picks one. -/
def dispatchNode {target eps : ℝ}
    (method : NodeMethod)
    (skip series cf asym : NodeCertificate target eps) :
    NodeCertificate target eps :=
  match method with
  | .skip => skip
  | .series => series
  | .continuedFraction => cf
  | .asymptotic => asym

theorem dispatchNode_sound {target eps : ℝ}
    (method : NodeMethod)
    (skip series cf asym : NodeCertificate target eps) :
    (dispatchNode method skip series cf asym).lo ≤ target ∧
      target ≤ (dispatchNode method skip series cf asym).hi := by
  cases method with
  | skip => exact ⟨skip.contains_lo, skip.contains_hi⟩
  | series => exact ⟨series.contains_lo, series.contains_hi⟩
  | continuedFraction => exact ⟨cf.contains_lo, cf.contains_hi⟩
  | asymptotic => exact ⟨asym.contains_lo, asym.contains_hi⟩

/-! ## 10. End-to-end quadrature assembly -/

/-- Abstract form of the assembly theorem used after the analytic work:
    the finite trapezoidal sum is enclosed, the omitted tails are
    nonnegative and bounded, and the trapezoidal discretization error is
    symmetric. -/
theorem quadrature_assembly_sound
    (h finiteLo finiteSum finiteHi tail tailL tailR disc lambda : ℚ)
    (hh : 0 ≤ h)
    (hfinite : finiteLo ≤ finiteSum ∧ finiteSum ≤ finiteHi)
    (htail : 0 ≤ tail ∧ tail ≤ tailL + tailR)
    (htailL : 0 ≤ tailL)
    (htailR : 0 ≤ tailR)
    (hdisc : -disc ≤ lambda - (h * finiteSum + tail) ∧
              lambda - (h * finiteSum + tail) ≤ disc) :
    h * finiteLo - disc ≤ lambda ∧
      lambda ≤ h * finiteHi + tailL + tailR + disc := by
  have hlow := mul_le_mul_of_nonneg_left hfinite.1 hh
  have hhigh := mul_le_mul_of_nonneg_left hfinite.2 hh
  constructor <;> linarith

/-! ## 11. Explicit analytic trust boundary -/

/-- The following record packages the non-algebraic facts which the Python
    implementation obtains from analysis and trusted interval arithmetic.

    A value of this structure must be constructed from proofs of:
    * the substitution `λ = ∫ G`;
    * the strip bound for `G` and the trapezoidal theorem;
    * both one-sided tail bounds;
    * sound Arb enclosures for every evaluated node and constant.

    This file does not construct such a value automatically. -/
structure AnalyticAssemblyPremises (h finiteLo finiteHi tailL tailR disc lambda : ℚ) where
  step_pos : 0 < h
  finite_interval_is_sound :
    ∀ finiteSum tail,
      finiteLo ≤ finiteSum → finiteSum ≤ finiteHi →
      0 ≤ tail → tail ≤ tailL + tailR →
      (-disc ≤ lambda - (h * finiteSum + tail) ∧
        lambda - (h * finiteSum + tail) ≤ disc)
  left_tail_nonneg : 0 ≤ tailL
  right_tail_nonneg : 0 ≤ tailR
  disc_nonneg : 0 ≤ disc

/-- Given the analytic/Arb assembly premises and the finite node sum,
    obtain the global interval used by the integer certificate layer. -/
theorem analytic_assembly_to_interval
    (h finiteLo finiteHi tailL tailR disc lambda finiteSum tail : ℚ)
    (P : AnalyticAssemblyPremises h finiteLo finiteHi tailL tailR disc lambda)
    (hfiniteLo : finiteLo ≤ finiteSum)
    (hfiniteHi : finiteSum ≤ finiteHi)
    (htailLo : 0 ≤ tail)
    (htailHi : tail ≤ tailL + tailR) :
    h * finiteLo - disc ≤ lambda ∧
      lambda ≤ h * finiteHi + tailL + tailR + disc := by
  have hdisc := P.finite_interval_is_sound finiteSum tail
    hfiniteLo hfiniteHi htailLo htailHi
  exact quadrature_assembly_sound h finiteLo finiteSum finiteHi tail tailL tailR disc lambda
    (le_of_lt P.step_pos)
    ⟨hfiniteLo, hfiniteHi⟩
    ⟨htailLo, htailHi⟩
    P.left_tail_nonneg P.right_tail_nonneg hdisc

end GolombDickman27
