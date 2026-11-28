/-
Supplement to `GolombDickman27.lean` for the v28 Python implementation.

This module is deliberately split into:
  (A) closed algebraic proofs connecting the actual `cfRun` recurrence to
      the existing `sContinuant` definitions;
  (B) a proved finite/infinite sum comparison layer for Lemma 3, with the
      cell-comparison and cell-total estimates exposed as construction goals;
  (C) an explicit analytic profile for Lemma 4, exposing the regional
      envelope, integral, decay, and holomorphy obligations;
  (D) a complete rational proof of decimal-cell isolation corresponding to
      Python's integer `>> S` / floor test.

No `sorry` or `axiom` is used.  The inputs in (B) and (C) are structures whose
fields must be filled by genuine proofs before they can be instantiated.
-/

import GolombDickman27

open scoped BigOperators
open Finset

namespace GolombDickman28
open GolombDickman27

noncomputable section

/-! ## A. The missing `cfRun -> sContinuant` bridge -/

/-- Scale an S-continuant at `x = 1/z`.  `shift = 0` is the numerator;
    `shift = 1` is the denominator used by the production continued fraction. -/
def scaledS (z : ℚ) (v0 v1 : Polynomial ℚ) (shift n : Nat) : ℚ :=
  z ^ (n / 2 + shift) * Polynomial.eval z⁻¹
    (sContinuant xPoly v0 v1 n)

lemma scaledS_step
    (z : ℚ) (hz : z ≠ 0) (v0 v1 : Polynomial ℚ)
    (shift n : Nat) (hn : 1 ≤ n) :
    scaledS z v0 v1 shift (n + 1) =
      cfBeta z (n + 1) * scaledS z v0 v1 shift n +
        cfAlpha (n + 1) * scaledS z v0 v1 shift (n - 1) := by
  rcases Nat.even_or_odd n with he | ho
  · rcases he with ⟨m, hm⟩
    have hidx : n = 2 * m := by omega
    subst n
    have hmpos : 1 ≤ m := by omega
    have hs := sContinuant_step xPoly v0 v1 (2 * m - 1)
    have hs' :
        sContinuant xPoly v0 v1 (2 * m + 1) =
          sContinuant xPoly v0 v1 (2 * m) +
            Polynomial.C (m + 1 : ℚ) * xPoly *
              sContinuant xPoly v0 v1 (2 * m - 1) := by
      simpa [show 2 * m - 1 + 2 = 2 * m + 1 by omega,
        show 2 * m - 1 + 1 = 2 * m by omega, cfAlpha_odd] using hs
    have hev := congrArg (Polynomial.eval z⁻¹) hs'
    simp [Polynomial.eval_add, Polynomial.eval_mul, Polynomial.eval_C,
      Polynomial.eval_X] at hev
    dsimp [scaledS]
    rw [show (2 * m + 1) / 2 = m by omega,
      show (2 * m) / 2 = m by omega,
      show (2 * m - 1) / 2 = m - 1 by omega,
      hev]
    have hmod : (2 * m + 1) % 2 = 1 := by omega
    simp [cfBeta, cfAlpha_odd, hmod]
    field_simp [hz]
    <;> ring
  · rcases ho with ⟨m, hm⟩
    have hidx : n = 2 * m + 1 := by omega
    subst n
    have hs := sContinuant_step xPoly v0 v1 (2 * m)
    have hs' :
        sContinuant xPoly v0 v1 (2 * m + 2) =
          sContinuant xPoly v0 v1 (2 * m + 1) +
            Polynomial.C (m + 1 : ℚ) * xPoly *
              sContinuant xPoly v0 v1 (2 * m) := by
      simpa [show 2 * m + 2 = (2 * m) + 2 by omega,
        show 2 * m + 1 = (2 * m) + 1 by omega, cfAlpha_even_succ] using hs
    have hev := congrArg (Polynomial.eval z⁻¹) hs'
    simp [Polynomial.eval_add, Polynomial.eval_mul, Polynomial.eval_C,
      Polynomial.eval_X] at hev
    dsimp [scaledS]
    rw [show (2 * m + 2) / 2 = m + 1 by omega,
      show (2 * m + 1) / 2 = m by omega,
      show (2 * m) / 2 = m by omega,
      hev]
    have hmod : (2 * m + 2) % 2 = 0 := by omega
    simp [cfBeta, cfAlpha_even_succ, hmod]
    field_simp [hz]
    <;> ring

/-- One production `cfRun` step advances both continued-fraction columns. -/
lemma cfRun_two_step_B (z : ℚ) (n : Nat) :
    (cfRun z (n + 2)).Bcur =
      cfBeta z (n + 2) * (cfRun z (n + 1)).Bcur +
        cfAlpha (n + 2) * (cfRun z n).Bcur := by
  simp [cfRun, cfStep]

lemma cfRun_two_step_A (z : ℚ) (n : Nat) :
    (cfRun z (n + 2)).Acur =
      cfBeta z (n + 2) * (cfRun z (n + 1)).Acur +
        cfAlpha (n + 2) * (cfRun z n).Acur := by
  simp [cfRun, cfStep]

/-- Exact bridge for every convergent index, not only odd indices.

    The powers of `z` are important: the production recurrence alternates
    between coefficients `1,z`, while `sContinuant` is the polynomial
    recurrence in `x=1/z`. -/
theorem cfRun_to_sContinuant
    (z : ℚ) (hz : z ≠ 0) :
    ∀ n : Nat,
      (cfRun z n).Bcur = scaledS z 1 1 0 n ∧
      (cfRun z n).Acur = scaledS z 1 (1 + xPoly) 1 n := by
  intro n
  induction n using Nat.strong_induction_on with
  | h n ih =>
    cases n with
    | zero =>
        constructor <;> simp [cfRun, scaledS, sContinuant]
    | succ n =>
        cases n with
        | zero =>
            constructor
            · simp [cfRun, cfStep, cfBeta, cfAlpha, scaledS, sContinuant]
            · simp [cfRun, cfStep, cfBeta, cfAlpha, scaledS, sContinuant,
                xPoly, Polynomial.eval_add, Polynomial.eval_X]
              field_simp [hz]
              <;> ring
        | succ k =>
            have hcur := ih (k + 1) (by omega)
            have hprev := ih k (by omega)
            constructor
            · calc
                (cfRun z (k + 2)).Bcur =
                    cfBeta z (k + 2) * (cfRun z (k + 1)).Bcur +
                      cfAlpha (k + 2) * (cfRun z k).Bcur :=
                        cfRun_two_step_B z k
                _ = cfBeta z (k + 2) * scaledS z 1 1 0 (k + 1) +
                      cfAlpha (k + 2) * scaledS z 1 1 0 k := by
                        rw [hcur.1, hprev.1]
                _ = scaledS z 1 1 0 (k + 2) :=
                      (scaledS_step z hz 1 1 0 (k + 1) (by omega)).symm
            · calc
                (cfRun z (k + 2)).Acur =
                    cfBeta z (k + 2) * (cfRun z (k + 1)).Acur +
                      cfAlpha (k + 2) * (cfRun z k).Acur :=
                        cfRun_two_step_A z k
                _ = cfBeta z (k + 2) * scaledS z 1 (1 + xPoly) 1 (k + 1) +
                      cfAlpha (k + 2) * scaledS z 1 (1 + xPoly) 1 k := by
                        rw [hcur.2, hprev.2]
                _ = scaledS z 1 (1 + xPoly) 1 (k + 2) :=
                      (scaledS_step z hz 1 (1 + xPoly) 1 (k + 1) (by omega)).symm

/-- The same bridge, written without the scaling abbreviation. -/
theorem cfRun_to_sContinuant_explicit
    (z : ℚ) (hz : z ≠ 0) (n : Nat) :
    (cfRun z n).Bcur =
        z ^ (n / 2) * Polynomial.eval z⁻¹ (sNumerator n) ∧
    (cfRun z n).Acur =
        z ^ (n / 2 + 1) * Polynomial.eval z⁻¹ (sDenominator n) := by
  have h := cfRun_to_sContinuant z hz n
  simpa [scaledS, sNumerator, sDenominator] using h

/-- At odd indices the existing S-to-J contraction applies directly. -/
theorem cfRun_odd_to_J
    (z : ℚ) (hz : z ≠ 0) (m : Nat) :
    (cfRun z (2 * m + 1)).Bcur =
        z ^ m * Polynomial.eval z⁻¹ (jNumerator m) ∧
    (cfRun z (2 * m + 1)).Acur =
        z ^ (m + 1) * Polynomial.eval z⁻¹ (jDenominator m) := by
  have h := cfRun_to_sContinuant z hz (2 * m + 1)
  constructor
  · simpa [scaledS, sNumerator, show (2 * m + 1) / 2 = m by omega,
      sToJ_numerator] using h.1
  · simpa [scaledS, sDenominator, show (2 * m + 1) / 2 + 1 = m + 1 by omega,
      sToJ_denominator] using h.2

/-- Ratio form used by `cf_f_hull`; the only extra condition is that the
    evaluated S-denominator is nonzero. -/
theorem cfRun_ratio_to_sContinuant
    (z : ℚ) (hz : z ≠ 0) (n : Nat)
    (hden : Polynomial.eval z⁻¹ (sDenominator n) ≠ 0) :
    (cfRun z n).Bcur / (cfRun z n).Acur =
      z⁻¹ * (Polynomial.eval z⁻¹ (sNumerator n) /
        Polynomial.eval z⁻¹ (sDenominator n)) := by
  have h := cfRun_to_sContinuant_explicit z hz n
  rw [h.1, h.2]
  dsimp [sNumerator, sDenominator, scaledS]
  simp only [pow_succ]
  field_simp [hz, hden]
  <;> ring

/-! ## B. Lemma 3: discrete sums from cell majorants -/

/-- The finite algebraic core of the integral-test argument.
    `cell` is the integral (or another certified upper area) assigned to
    the interval adjacent to each sample. -/
structure FiniteCellMajorant {ι : Type*} [DecidableEq ι]
    (I : Finset ι) (sample cell : ι → ℝ) (tail : ℝ) where
  sample_nonneg : ∀ i ∈ I, 0 ≤ sample i
  sample_le_cell : ∀ i ∈ I, sample i ≤ cell i
  cell_sum_le_tail : (∑ i in I, cell i) ≤ tail

theorem finite_discrete_sum_le_tail
    {ι : Type*} [DecidableEq ι]
    (I : Finset ι) (sample cell : ι → ℝ) (tail : ℝ)
    (H : FiniteCellMajorant I sample cell tail) :
    0 ≤ (∑ i in I, sample i) ∧ (∑ i in I, sample i) ≤ tail := by
  constructor
  · exact Finset.sum_nonneg fun i hi => H.sample_nonneg i hi
  · calc
      (∑ i in I, sample i) ≤ ∑ i in I, cell i :=
        Finset.sum_le_sum fun i hi => H.sample_le_cell i hi
      _ ≤ tail := H.cell_sum_le_tail

/-- Infinite version of the same comparison.  This is the exact theorem
    needed after the monotone-cell estimates and the cell-partition limit
    have established a summable majorant. -/
theorem tsum_discrete_sum_le_tail
    {ι : Type*} [Countable ι]
    (sample cell : ι → ℝ) (tail : ℝ)
    (hsample_nonneg : ∀ i, 0 ≤ sample i)
    (hsample_le_cell : ∀ i, sample i ≤ cell i)
    (hcell_summable : Summable cell)
    (hcell_tail : (∑' i, cell i) ≤ tail) :
    Summable sample ∧ 0 ≤ (∑' i, sample i) ∧ (∑' i, sample i) ≤ tail := by
  have hsample_summable : Summable sample :=
    Summable.of_nonneg_of_le hsample_nonneg hsample_le_cell hcell_summable
  have htsum := tsum_le_tsum hsample_le_cell hsample_summable hcell_summable
  exact ⟨hsample_summable, tsum_nonneg hsample_nonneg, le_trans htsum hcell_tail⟩

/-- The exact real change of variables used in Lemma 3. -/
def lemma3U (t : ℝ) : ℝ := Real.exp (t - Real.exp (-t))

def lemma3RightEnvelope (t : ℝ) : ℝ :=
  lemma3U t * Real.exp (-lemma3U t) * (1 + Real.exp (-t))

def lemma3LeftEnvelope (gamma t : ℝ) : ℝ :=
  Real.exp gamma * (lemma3U t) ^ 2 * (1 + Real.exp (-t))

def lemma3RightSample (h : ℝ) (KR n : Nat) : ℝ :=
  h * lemma3RightEnvelope (((KR + n + 1 : Nat) : ℝ) * h)

def lemma3RightCell (h : ℝ) (KR n : Nat) : ℝ :=
  ∫ t in (((KR + n : Nat) : ℝ) * h)..(((KR + n + 1 : Nat) : ℝ) * h),
    lemma3RightEnvelope t

def lemma3LeftSample (gamma h : ℝ) (KL n : Nat) : ℝ :=
  h * lemma3LeftEnvelope gamma (-(((KL + n + 1 : Nat) : ℝ) * h))

def lemma3LeftCell (gamma h : ℝ) (KL n : Nat) : ℝ :=
  ∫ t in (-(((KL + n + 1 : Nat) : ℝ) * h))..(-(((KL + n : Nat) : ℝ) * h)),
    lemma3LeftEnvelope gamma t

def lemma3RightTail (h : ℝ) (KR : Nat) : ℝ :=
  Real.exp (-lemma3U ((KR : ℝ) * h))

def lemma3LeftTail (gamma h : ℝ) (KL : Nat) : ℝ :=
  (Real.exp gamma / 2) * (lemma3U (-((KL : ℝ) * h))) ^ 2

/-- Lemma 3's explicit proof obligations for the actual v28 grid.

    `rightSample` is the omitted sum with k = KR+1+n.  Its cell is
    [(KR+n)h,(KR+n+1)h].  `leftSample` uses k = -KL-1-n and its cell is
    [(-KL-1-n)h,(-KL-n)h].  Thus the two families tile exactly the two
    omitted half-lines; they are no longer abstract unnamed sequences.

    The fields `*_cell_bound` are the monotone-function integral-test steps;
    `*_cells_tail` are the cell-partition/change-of-variable steps.  These
    four estimates must be instantiated for the displayed envelopes before
    this package can be used as a proof of Lemma 3. -/
structure Lemma3DiscreteTailProof (gamma h : ℝ) (KL KR : Nat) where
  step_pos : 0 < h
  right_start_ge_one : 1 ≤ lemma3U ((KR : ℝ) * h)
  right_nonneg : ∀ n, 0 ≤ lemma3RightSample h KR n
  right_cell_bound : ∀ n,
    lemma3RightSample h KR n ≤ lemma3RightCell h KR n
  right_cells_summable : Summable (lemma3RightCell h KR)
  right_cells_tail : (∑' n, lemma3RightCell h KR n) ≤ lemma3RightTail h KR
  left_nonneg : ∀ n, 0 ≤ lemma3LeftSample gamma h KL n
  left_cell_bound : ∀ n,
    lemma3LeftSample gamma h KL n ≤ lemma3LeftCell gamma h KL n
  left_cells_summable : Summable (lemma3LeftCell gamma h KL)
  left_cells_tail : (∑' n, lemma3LeftCell gamma h KL n) ≤
    lemma3LeftTail gamma h KL

theorem lemma3_discrete_tails
    (gamma h : ℝ) (KL KR : Nat)
    (H : Lemma3DiscreteTailProof gamma h KL KR) :
    Summable (lemma3RightSample h KR) ∧
      0 ≤ (∑' n, lemma3RightSample h KR n) ∧
      (∑' n, lemma3RightSample h KR n) ≤ lemma3RightTail h KR ∧
    Summable (lemma3LeftSample gamma h KL) ∧
      0 ≤ (∑' n, lemma3LeftSample gamma h KL n) ∧
      (∑' n, lemma3LeftSample gamma h KL n) ≤ lemma3LeftTail gamma h KL := by
  have hr := tsum_discrete_sum_le_tail
    (lemma3RightSample h KR) (lemma3RightCell h KR) (lemma3RightTail h KR)
    H.right_nonneg H.right_cell_bound H.right_cells_summable H.right_cells_tail
  have hl := tsum_discrete_sum_le_tail
    (lemma3LeftSample gamma h KL) (lemma3LeftCell gamma h KL)
    (lemma3LeftTail gamma h KL)
    H.left_nonneg H.left_cell_bound H.left_cells_summable H.left_cells_tail
  exact ⟨hr.1, hr.2.1, hr.2.2, hl.1, hl.2.1, hl.2.2⟩

/-! ## C. Lemma 4: explicit strip constants and analytic obligations -/

def stripD : ℝ := 7 / 5
def stripC : ℝ := Real.cos stripD
def stripThetaMax : ℝ := stripD + Real.exp (-2) * Real.sin stripD
def stripKappa : ℝ := Real.cos stripThetaMax
def stripKappaPrime : ℝ := stripKappa * Real.exp (-Real.exp (-2))

def stripC1 (gamma : ℝ) : ℝ :=
  Real.exp (gamma + 2 + (Real.exp 1 - 2) / 2)

def stripM1 (gamma : ℝ) : ℝ :=
  stripC1 gamma * Real.exp (-2 * stripC) *
    (1 / stripC + 1 / (4 * stripC ^ 2))

def stripM2 (gamma : ℝ) : ℝ :=
  4 * Real.exp gamma * Real.exp 4 *
    Real.exp (2 * Real.exp 2 + Real.exp (Real.exp 2) / 2)

def stripM3 : ℝ :=
  Real.exp (Real.exp (Real.exp (-2) - 2)) * (1 + Real.exp (-2)) *
    Real.exp (-stripKappaPrime * Real.exp 2) / stripKappaPrime

def stripM (gamma : ℝ) : ℝ := stripM1 gamma + stripM2 gamma + stripM3

lemma strip_constants_positive (gamma : ℝ)
    (hc : 0 < stripC) (hk : 0 < stripKappa) :
    0 < stripC1 gamma ∧ 0 < stripKappaPrime ∧
      0 < stripM1 gamma ∧ 0 < stripM2 gamma ∧ 0 < stripM3 ∧ 0 < stripM gamma := by
  have hkp : 0 < stripKappaPrime := by
    unfold stripKappaPrime
    positivity
  constructor
  · unfold stripC1
    positivity
  constructor
  · exact hkp
  constructor
  · unfold stripM1
    positivity
  constructor
  · unfold stripM2
    positivity
  constructor
  · unfold stripM3
    positivity
  · unfold stripM
    positivity

/-- The three real envelopes appearing in the proof of Lemma 4.  The first
    applies on `t ≤ 0`, the second on `0 ≤ t ≤ 2`, and the third on `t ≥ 2`. -/
def stripLeftEnvelope (gamma t : ℝ) : ℝ :=
  stripC1 gamma * Real.exp (2 * t - 2 * stripC * Real.exp (-t)) *
    (1 + Real.exp (-t))

def stripMiddleEnvelope (gamma : ℝ) : ℝ :=
  2 * Real.exp gamma * Real.exp 4 *
    Real.exp (2 * Real.exp 2 + Real.exp (Real.exp 2) / 2)

def stripRightEnvelope (t : ℝ) : ℝ :=
  Real.exp (Real.exp (Real.exp (-2) - 2)) * (1 + Real.exp (-2)) *
    Real.exp t * Real.exp (-stripKappaPrime * Real.exp t)

/-- Explicit, proof-bearing interface for Lemma 4.  `left_integral_bound`,
    `middle_integral_bound`, `right_integral_bound` and `line_bound` are not
    numerical assumptions hidden in a black box: they are the exact four
    obligations that must be filled from the three region estimates and the
    partition of the real line.  `entire` and `uniform_decay` are the other
    hypotheses of the trapezoidal theorem. -/
structure Lemma4StripWitness (G : ℂ → ℂ) (gamma : ℝ) where
  entire : Differentiable ℂ G
  uniform_decay : ∀ ε : ℝ, 0 < ε → ∃ R : ℝ, ∀ x y : ℝ,
    |y| ≤ stripD → R ≤ |x| → ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖ < ε
  horizontal_integrable : ∀ y : ℝ, |y| < stripD →
    Integrable (fun x : ℝ => ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖)
  left_pointwise_envelope : ∀ x y : ℝ, |y| ≤ stripD → x ≤ 0 →
    ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖ ≤ stripLeftEnvelope gamma x
  middle_pointwise_envelope : ∀ x y : ℝ, |y| ≤ stripD → 0 < x → x < 2 →
    ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖ ≤ stripMiddleEnvelope gamma
  right_pointwise_envelope : ∀ x y : ℝ, |y| ≤ stripD → 2 ≤ x →
    ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖ ≤ stripRightEnvelope x
  left_integral_bound : ∀ y : ℝ, |y| < stripD →
    (∫ x : ℝ, if x ≤ 0 then ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖ else 0) ≤ stripM1 gamma
  middle_integral_bound : ∀ y : ℝ, |y| < stripD →
    (∫ x : ℝ, if 0 < x ∧ x < 2 then ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖ else 0) ≤ stripM2 gamma
  right_integral_bound : ∀ y : ℝ, |y| < stripD →
    (∫ x : ℝ, if 2 ≤ x then ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖ else 0) ≤ stripM3
  line_split_bound : ∀ y : ℝ, |y| < stripD,
    (∫ x : ℝ, ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖) ≤
      (∫ x : ℝ, if x ≤ 0 then ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖ else 0) +
      (∫ x : ℝ, if 0 < x ∧ x < 2 then ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖ else 0) +
      (∫ x : ℝ, if 2 ≤ x then ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖ else 0)

theorem lemma4_horizontal_bound
    (G : ℂ → ℂ) (gamma : ℝ) (H : Lemma4StripWitness G gamma) :
    ∀ y : ℝ, |y| < stripD →
      Integrable (fun x : ℝ => ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖) ∧
      (∫ x : ℝ, ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖) ≤ stripM gamma := by
  intro y hy
  constructor
  · exact H.horizontal_integrable y hy
  · have hs := H.line_split_bound y hy
    have hl := H.left_integral_bound y hy
    have hm := H.middle_integral_bound y hy
    have hr := H.right_integral_bound y hy
    unfold stripM
    linarith

/-- The decay and line-norm consequences required by the strip trapezoidal
    theorem, with the *same* constants used in `make_plan`/`strip_constants`. -/
def TrefethenStripHypotheses (G : ℂ → ℂ) (gamma : ℝ) : Prop :=
  Differentiable ℂ G ∧
  (∀ ε : ℝ, 0 < ε → ∃ R : ℝ, ∀ x y : ℝ,
    |y| ≤ stripD → R ≤ |x| → ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖ < ε) ∧
  (∀ y : ℝ, |y| < stripD →
    Integrable (fun x : ℝ => ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖) ∧
    (∫ x : ℝ, ‖G ((x : ℂ) + (y : ℂ) * Complex.I)‖) ≤ stripM gamma)

theorem lemma4_to_trapezoid_hypotheses
    (G : ℂ → ℂ) (gamma : ℝ) (H : Lemma4StripWitness G gamma) :
    TrefethenStripHypotheses G gamma := by
  exact ⟨H.entire, H.uniform_decay, lemma4_horizontal_bound G gamma H⟩

/-! ## D. Decimal boundary isolation -/

/-- A scaled value is in the half-open decimal cell with integer label `n`. -/
def InDecimalCell (scale x : ℚ) (n : ℤ) : Prop :=
  (n : ℚ) ≤ scale * x ∧ scale * x < (n : ℚ) + 1

/-- Nat-indexed decimal cell, matching Python's nonnegative integer quotient. -/
def InNatDecimalCell (scale x : ℚ) (n : Nat) : Prop :=
  (n : ℚ) ≤ scale * x ∧ scale * x < (n : ℚ) + 1

theorem decimal_cell_unique
    (scale x : ℚ) (n m : ℤ)
    (hn : InDecimalCell scale x n)
    (hm : InDecimalCell scale x m) : n = m := by
  by_contra hne
  rcases lt_or_gt_of_ne hne with hnm | hmn
  · have hstep : n + 1 ≤ m := by omega
    have hstepQ : (n : ℚ) + 1 ≤ (m : ℚ) := by exact_mod_cast hstep
    change (n : ℚ) ≤ scale * x ∧ scale * x < (n : ℚ) + 1 at hn
    change (m : ℚ) ≤ scale * x ∧ scale * x < (m : ℚ) + 1 at hm
    linarith
  · have hstep : m + 1 ≤ n := by omega
    have hstepQ : (m : ℚ) + 1 ≤ (n : ℚ) := by exact_mod_cast hstep
    change (n : ℚ) ≤ scale * x ∧ scale * x < (n : ℚ) + 1 at hn
    change (m : ℚ) ≤ scale * x ∧ scale * x < (m : ℚ) + 1 at hm
    linarith

theorem nat_decimal_cell_unique
    (scale x : ℚ) (n m : Nat)
    (hn : InNatDecimalCell scale x n)
    (hm : InNatDecimalCell scale x m) : n = m := by
  by_contra hne
  rcases lt_or_gt_of_ne hne with hnm | hmn
  · have hstep : n + 1 ≤ m := by omega
    have hstepQ : (n : ℚ) + 1 ≤ (m : ℚ) := by exact_mod_cast hstep
    change (n : ℚ) ≤ scale * x ∧ scale * x < (n : ℚ) + 1 at hn
    change (m : ℚ) ≤ scale * x ∧ scale * x < (m : ℚ) + 1 at hm
    linarith
  · have hstep : m + 1 ≤ n := by omega
    have hstepQ : (m : ℚ) + 1 ≤ (n : ℚ) := by exact_mod_cast hstep
    change (n : ℚ) ≤ scale * x ∧ scale * x < (n : ℚ) + 1 at hn
    change (m : ℚ) ≤ scale * x ∧ scale * x < (m : ℚ) + 1 at hm
    linarith

theorem decimal_cell_upper_margin_positive
    (scale lo hi : ℚ) (n : ℤ)
    (hlo : (n : ℚ) ≤ scale * lo)
    (hhi : scale * hi < (n : ℚ) + 1) :
    0 ≤ scale * lo - n ∧ 0 < (n : ℚ) + 1 - scale * hi := by
  constructor <;> linarith

/-- If both dyadic endpoints have the same Euclidean quotient after the
    `10^D` scaling, the whole certified interval misses the next decimal
    boundary.  This is the exact mathematical meaning of `a == b` in
    `certify()`, provided the endpoints are nonnegative. -/
lemma nat_division_decimal_cell
    (N d q : Nat) (hd : 0 < d) (hq : q = N / d) :
    (q : ℚ) ≤ (N : ℚ) / d ∧ (N : ℚ) / d < (q : ℚ) + 1 := by
  have hmod : N % d < d := Nat.mod_lt N hd
  have hdecomp : N % d + d * (N / d) = N := Nat.mod_add_div N d
  rw [← hq] at hdecomp
  have hmodQ : ((N % d : Nat) : ℚ) < (d : ℚ) := by exact_mod_cast hmod
  have hremQ : 0 ≤ ((N % d : Nat) : ℚ) := by positivity
  have hdecompQ : ((N % d : Nat) : ℚ) + (d : ℚ) * (q : ℚ) = (N : ℚ) := by
    exact_mod_cast hdecomp
  have hdQ : (0 : ℚ) < (d : ℚ) := by exact_mod_cast hd
  constructor
  · exact (le_div_iff₀ hdQ).2 (by nlinarith [hdecompQ, hremQ])
  · exact (div_lt_iff₀ hdQ).2 (by nlinarith [hdecompQ, hmodQ])

theorem dyadic_certificate_decimal_isolation
    (S D loInt hiInt n : Nat) (x : ℚ)
    (hfloor_lo : n = (loInt * 10 ^ D) / (2 ^ S))
    (hfloor_hi : n = (hiInt * 10 ^ D) / (2 ^ S))
    (hlo : (loInt : ℚ) / (2 ^ S) ≤ x)
    (hhi : x ≤ (hiInt : ℚ) / (2 ^ S)) :
    InNatDecimalCell (10 ^ D) x n := by
  have hden : 0 < 2 ^ S := by positivity
  have hlowCell := nat_division_decimal_cell
    (loInt * 10 ^ D) (2 ^ S) n hden hfloor_lo
  have hhighCell := nat_division_decimal_cell
    (hiInt * 10 ^ D) (2 ^ S) n hden hfloor_hi
  change (n : ℚ) ≤ (10 ^ D : ℚ) * x ∧
      (10 ^ D : ℚ) * x < (n : ℚ) + 1
  have hdenQ : (0 : ℚ) < (2 : ℚ) ^ S := by positivity
  have hloQ : (loInt : ℚ) ≤ x * ((2 : ℚ) ^ S) :=
    (div_le_iff₀ hdenQ).1 hlo
  have hhiQ : x * ((2 : ℚ) ^ S) ≤ (hiInt : ℚ) :=
    (le_div_iff₀ hdenQ).1 hhi
  have hscale_nonneg : 0 ≤ (10 ^ D : ℚ) := by positivity
  have hloScaled := mul_le_mul_of_nonneg_right hloQ hscale_nonneg
  have hhiScaled := mul_le_mul_of_nonneg_right hhiQ hscale_nonneg
  have hlow' : (n : ℚ) ≤
      (loInt : ℚ) * (10 ^ D : ℚ) / ((2 : ℚ) ^ S) := by
    simpa [Nat.cast_mul, Nat.cast_pow] using hlowCell.1
  have hhigh' :
      (hiInt : ℚ) * (10 ^ D : ℚ) / ((2 : ℚ) ^ S) < (n : ℚ) + 1 := by
    simpa [Nat.cast_mul, Nat.cast_pow] using hhighCell.2
  have hscaledLo :
      (loInt : ℚ) * (10 ^ D : ℚ) / ((2 : ℚ) ^ S) ≤
        (10 ^ D : ℚ) * x := by
    apply (div_le_iff₀ hdenQ).2
    nlinarith [hloScaled]
  have hscaledHi :
      (10 ^ D : ℚ) * x ≤
        (hiInt : ℚ) * (10 ^ D : ℚ) / ((2 : ℚ) ^ S) := by
    apply (le_div_iff₀ hdenQ).2
    nlinarith [hhiScaled]
  exact ⟨le_trans hlow' hscaledLo,
    lt_of_le_of_lt hscaledHi hhigh'⟩

theorem decimal_interval_all_values_same_cell
    (scale lo hi value : ℚ) (n : ℤ)
    (hscale : 0 ≤ scale)
    (hlo : (n : ℚ) ≤ scale * lo)
    (hhi : scale * hi < (n : ℚ) + 1)
    (henc : lo ≤ value ∧ value ≤ hi) :
    InDecimalCell scale value n := by
  exact common_decimal_cell scale lo hi value n hscale hlo hhi henc

/-! ## E. End-to-end conditional composition -/

/-- Once Lemma 3 supplies the two tail bounds and Lemma 4 supplies the strip
    estimate (and the trapezoidal theorem supplies the discretisation bound),
    the existing interval assembly theorem can be used without silently
    absorbing these steps into an unnamed premise. -/
structure ExplicitAnalyticInputs
    (h finiteLo finiteHi tailL tailR disc lambda : ℚ) where
  strip : 0 < h
  finite_nodes : ∀ finiteSum tail,
    finiteLo ≤ finiteSum → finiteSum ≤ finiteHi →
    0 ≤ tail → tail ≤ tailL + tailR →
      (-disc ≤ lambda - (h * finiteSum + tail) ∧
        lambda - (h * finiteSum + tail) ≤ disc)
  tailL_nonneg : 0 ≤ tailL
  tailR_nonneg : 0 ≤ tailR
  disc_nonneg : 0 ≤ disc

theorem explicit_analytic_assembly
    (h finiteLo finiteHi tailL tailR disc lambda finiteSum tail : ℚ)
    (H : ExplicitAnalyticInputs h finiteLo finiteHi tailL tailR disc lambda)
    (hfiniteLo : finiteLo ≤ finiteSum)
    (hfiniteHi : finiteSum ≤ finiteHi)
    (htailLo : 0 ≤ tail)
    (htailHi : tail ≤ tailL + tailR) :
    h * finiteLo - disc ≤ lambda ∧
      lambda ≤ h * finiteHi + tailL + tailR + disc := by
  exact analytic_assembly_to_interval h finiteLo finiteHi tailL tailR disc lambda
    finiteSum tail
    { step_pos := H.strip, finite_interval_is_sound := H.finite_nodes,
      left_tail_nonneg := H.tailL_nonneg,
      right_tail_nonneg := H.tailR_nonneg, disc_nonneg := H.disc_nonneg }
    hfiniteLo hfiniteHi htailLo htailHi

end

end GolombDickman28
