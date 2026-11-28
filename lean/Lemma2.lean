import Mathlib

/-!
# Лемма 2: замена переменной и точные интегралы хвостов

Замена `u(t) = exp(t - e^{-t})`, её производная и строгая монотонность,
мажоранты `gR`, `gL` и точные значения интегралов от них по `Ioi` / `Iic`.

Источник: `archive/Формальное доказательство Леммы 2 и Леммы 3.lean`,
часть «Лемма 2». Текст доказательств перенесён без изменений.
-/

namespace GolombDickman

open Real Set Filter MeasureTheory Topology


/-- Замена переменной u(t) = exp(t - e^{-t}). -/
noncomputable def u_fn (t : ℝ) : ℝ := exp (t - exp (-t))

/-- Производная u'(t) = u(t) · (1 + e^{-t}). -/
lemma hasDerivAt_u_fn (t : ℝ) :
    HasDerivAt u_fn (u_fn t * (1 + exp (-t))) t := by
  have he : HasDerivAt (fun s : ℝ => exp (-s)) (-exp (-t)) t := by
    simpa using (hasDerivAt_neg t).exp
  have h1 : HasDerivAt (fun s : ℝ => s - exp (-s)) (1 + exp (-t)) t := by
    convert (hasDerivAt_id t).sub he using 1
    · ext s; simp [id_eq]
    · ring
  change HasDerivAt (fun x : ℝ => exp (x - exp (-x)))
    (exp (t - exp (-t)) * (1 + exp (-t))) t
  simpa using h1.exp

lemma differentiable_u_fn : Differentiable ℝ u_fn := by
  unfold u_fn
  fun_prop

lemma u_fn_pos (t : ℝ) : 0 < u_fn t := exp_pos _

/-- Строгая монотонность u(t) на ℝ. -/
lemma strictMono_u_fn : StrictMono u_fn := by
  refine strictMono_of_deriv_pos (fun t => ?_)
  rw [(hasDerivAt_u_fn t).deriv]
  have hu : 0 < u_fn t := u_fn_pos t
  have he : 0 < exp (-t) := exp_pos _
  positivity

/-- Предел u(t) → +∞ при t → +∞. -/
lemma tendsto_u_fn_atTop : Tendsto u_fn atTop atTop := by
  refine tendsto_exp_atTop.comp ?_
  have hbase : Tendsto (fun t : ℝ => t + (-1 : ℝ)) atTop atTop :=
    tendsto_id.atTop_add tendsto_const_nhds
  refine tendsto_atTop_mono' atTop ?_ hbase
  filter_upwards [eventually_ge_atTop (0 : ℝ)] with t ht
  have hexp : exp (-t) ≤ 1 := by
    rw [← exp_zero]
    exact exp_le_exp.mpr (by linarith)
  linarith

/-- Предел u(t) → 0 при t → -∞. -/
lemma tendsto_u_fn_atBot : Tendsto u_fn atBot (nhds 0) := by
  refine tendsto_exp_atBot.comp ?_
  have hbase : Tendsto (fun t : ℝ => (2 : ℝ) * t) atBot atBot :=
    (tendsto_id.const_mul_atBot (by norm_num))
  refine tendsto_atBot_mono' atBot ?_ hbase
  filter_upwards [] with t
  have hexp : -t ≤ exp (-t) := by nlinarith [Real.add_one_le_exp (-t)]
  linarith

/-- Правая мажоранта g_R(t) = u(t) e^{-u(t)} (1 + e^{-t}). -/
noncomputable def gR (t : ℝ) : ℝ := u_fn t * exp (-u_fn t) * (1 + exp (-t))

/-- Левая мажоранта g_L(t) = e^γ u(t)² (1 + e^{-t}). -/
noncomputable def gL (t : ℝ) : ℝ := exp Real.eulerMascheroniConstant * (u_fn t) ^ 2 * (1 + exp (-t))

lemma gR_nonneg (t : ℝ) : 0 ≤ gR t := by
  unfold gR
  have hu := u_fn_pos t
  have he1 := exp_pos (-u_fn t)
  have he2 := exp_pos (-t)
  positivity

lemma gL_nonneg (t : ℝ) : 0 ≤ gL t := by
  unfold gL
  have hg := exp_pos Real.eulerMascheroniConstant
  have hu := u_fn_pos t
  have he := exp_pos (-t)
  positivity

/-! ### Лемма 2: точные формулы интегралов хвостов -/

/-- Лемма 2 (правый хвост): ∫_{t₀}^∞ u e^{-u} (1 + e^{-t}) dt = e^{-u(t₀)}. -/
theorem lemma_2_right (t₀ : ℝ) :
    ∫ t in Ioi t₀, gR t = exp (-u_fn t₀) := by
  let F : ℝ → ℝ := fun t => -exp (-u_fn t)
  have hderiv : ∀ t ∈ Ici t₀, HasDerivAt F (gR t) t := by
    intro t _
    have hu := hasDerivAt_u_fn t
    have h1 : HasDerivAt (fun s => -u_fn s) (-(u_fn t * (1 + exp (-t)))) t := hu.neg
    have h2 : HasDerivAt (fun s => exp (-u_fn s))
        (exp (-u_fn t) * (-(u_fn t * (1 + exp (-t))))) t := h1.exp
    convert h2.neg using 1
    unfold gR; ring
  have htend : Tendsto F atTop (nhds 0) := by
    have h1 : Tendsto (fun t => exp (-u_fn t)) atTop (nhds 0) :=
      tendsto_exp_atBot.comp (tendsto_neg_atTop_atBot.comp tendsto_u_fn_atTop)
    simpa [F] using h1.neg
  have hintg : IntegrableOn gR (Ioi t₀) :=
    integrableOn_Ioi_deriv_of_nonneg' hderiv (fun t _ => gR_nonneg t) htend
  have hint := integral_Ioi_of_hasDerivAt_of_tendsto' hderiv hintg htend
  simpa [F] using hint

/-- Лемма 2 (левый хвост): ∫_{-∞}^{t₀} e^γ u² (1 + e^{-t}) dt = ½ e^γ u(t₀)². -/
theorem lemma_2_left (t₀ : ℝ) :
    ∫ t in Iic t₀, gL t = (1 / 2) * exp Real.eulerMascheroniConstant * (u_fn t₀) ^ 2 := by
  let C := (1 / 2) * exp Real.eulerMascheroniConstant
  let F : ℝ → ℝ := fun t => C * (u_fn t) ^ 2
  have hderiv : ∀ t ∈ Iic t₀, HasDerivAt F (gL t) t := by
    intro t _
    have hu := hasDerivAt_u_fn t
    have hpow : HasDerivAt (fun s => (u_fn s) ^ 2) (2 * u_fn t ^ 1 * (u_fn t * (1 + exp (-t)))) t :=
      hu.pow 2
    convert hpow.const_mul C using 1
    unfold gL; dsimp [C]; ring
  have htend : Tendsto F atBot (nhds 0) := by
    have hpow : Tendsto (fun t => (u_fn t) ^ 2) atBot (nhds 0) := by
      simpa using tendsto_u_fn_atBot.pow 2
    simpa [F] using hpow.const_mul C
  have hderivG : ∀ x ∈ Ici (-t₀), HasDerivAt (fun y : ℝ => -F (-y)) (gL (-x)) x := by
    intro x hx
    change -t₀ ≤ x at hx
    have hx' : -x ∈ Iic t₀ := by change -x ≤ t₀; linarith
    have hFx := hderiv (-x) hx'
    convert (hFx.scomp x (hasDerivAt_neg' x)).neg using 1
    · ext y; rfl
    · simp
  have htendG : Tendsto (fun x : ℝ => -F (-x)) atTop (nhds 0) :=
    (htend.comp tendsto_neg_atTop_atBot).neg
  have hintg_pos : IntegrableOn (fun x : ℝ => gL (-x)) (Ioi (-t₀)) :=
    integrableOn_Ioi_deriv_of_nonneg' hderivG (fun x _ => gL_nonneg (-x)) htendG
  have hintg : IntegrableOn gL (Iic t₀) := by
    have hpre : IntegrableOn (gL ∘ Neg.neg) (Neg.neg ⁻¹' Iic t₀) := by
      have hIci : IntegrableOn (fun x : ℝ => gL (-x)) (Ici (-t₀)) :=
        (integrableOn_Ici_iff_integrableOn_Ioi).2 hintg_pos
      simpa [Function.comp_def] using hIci
    exact (MeasurePreserving.integrableOn_comp_preimage
      (Measure.measurePreserving_neg volume) (Homeomorph.neg ℝ).measurableEmbedding).1 hpre
  have hint := integral_Iic_of_hasDerivAt_of_tendsto' hderiv hintg htend
  simpa [F, C] using hint


/-! ### Вспомогательные свойства монотонности мажорант -/

/-- Функция x ↦ x e^{-x} убывает при x ≥ 1. -/
lemma antitoneOn_mul_exp_neg : AntitoneOn (fun x : ℝ => x * exp (-x)) (Ici 1) := by
  refine antitoneOn_of_deriv_nonpos (convex_Ici 1) ?_ ?_ ?_
  · exact (continuous_id.mul (continuous_exp.comp continuous_neg)).continuousOn
  · exact ((differentiable_id.mul (differentiable_exp.comp differentiable_neg))).differentiableOn
  · intro x hx
    rw [interior_Ici] at hx
    have hd : HasDerivAt (fun s : ℝ => s * exp (-s)) ((1 - x) * exp (-x)) x := by
      have h1 : HasDerivAt (fun s : ℝ => exp (-s)) (-exp (-x)) x := by
        simpa using (hasDerivAt_neg x).exp
      convert (hasDerivAt_id x).mul h1 using 1
      · ext s; simp [id_eq]
      · simp [id_eq]; ring
    rw [hd.deriv]
    have hx1 : 1 < x := by simpa using hx
    have h1 : 1 - x ≤ 0 := by linarith
    have h2 : 0 ≤ exp (-x) := exp_nonneg _
    exact mul_nonpos_of_nonpos_of_nonneg h1 h2

/-- Правая мажоранта g_R(t) убывает на луче {t | 1 ≤ u(t)}. -/
lemma antitoneOn_gR : AntitoneOn gR {t : ℝ | 1 ≤ u_fn t} := by
  intro t₁ ht₁ t₂ ht₂ hle
  unfold gR
  have hu_le : u_fn t₁ ≤ u_fn t₂ := strictMono_u_fn.monotone hle
  have h1 : u_fn t₂ * exp (-u_fn t₂) ≤ u_fn t₁ * exp (-u_fn t₁) :=
    antitoneOn_mul_exp_neg ht₁ ht₂ hu_le
  have h2 : 1 + exp (-t₂) ≤ 1 + exp (-t₁) := by
    have : exp (-t₂) ≤ exp (-t₁) := exp_le_exp.mpr (neg_le_neg hle)
    linarith
  have hpos1 : 0 ≤ u_fn t₂ * exp (-u_fn t₂) := by
    have := u_fn_pos t₂; have := exp_pos (-u_fn t₂); positivity
  have hpos2 : 0 ≤ 1 + exp (-t₂) := by
    have := exp_pos (-t₂); positivity
  exact mul_le_mul h1 h2 hpos2 (le_trans hpos1 h1)

/-- Левая мажоранта g_L(t) возрастает на всей оси ℝ. -/
lemma monotone_gL : Monotone gL := by
  refine monotone_of_deriv_nonneg ?_ (fun t => ?_)
  · exact ((differentiable_const (exp Real.eulerMascheroniConstant)).mul
      (differentiable_u_fn.pow 2)).mul
      ((differentiable_const (1 : ℝ)).add (differentiable_exp.comp differentiable_neg))
  have hu := hasDerivAt_u_fn t
  have he : HasDerivAt (fun s : ℝ => 1 + exp (-s)) (-exp (-t)) t := by
    simpa using ((hasDerivAt_neg t).exp).const_add 1
  have hprod : HasDerivAt (fun s => (u_fn s) ^ 2 * (1 + exp (-s)))
      ((2 * u_fn t ^ 1 * (u_fn t * (1 + exp (-t)))) * (1 + exp (-t)) +
       (u_fn t) ^ 2 * (-exp (-t))) t :=
    (hu.pow 2).mul he
  have hd : HasDerivAt gL
      (exp Real.eulerMascheroniConstant *
       ((2 * u_fn t ^ 1 * (u_fn t * (1 + exp (-t)))) * (1 + exp (-t)) +
        (u_fn t) ^ 2 * (-exp (-t)))) t :=
    by
      convert hprod.const_mul (exp Real.eulerMascheroniConstant) using 1
      ext s
      simp [gL]
      ring
  rw [hd.deriv]
  have hpos_g : 0 ≤ exp Real.eulerMascheroniConstant := exp_nonneg _
  have hpos_u : 0 ≤ (u_fn t) ^ 2 := sq_nonneg _
  have he_pos : 0 < exp (-t) := exp_pos (-t)
  have h_inner : 0 ≤ 2 * (1 + exp (-t)) ^ 2 - exp (-t) := by
    nlinarith [sq_nonneg (exp (-t))]
  have h_eq : (2 * u_fn t ^ 1 * (u_fn t * (1 + exp (-t)))) * (1 + exp (-t)) +
              (u_fn t) ^ 2 * (-exp (-t)) =
              (u_fn t) ^ 2 * (2 * (1 + exp (-t)) ^ 2 - exp (-t)) := by ring
  rw [h_eq]
  exact mul_nonneg hpos_g (mul_nonneg hpos_u h_inner)

end GolombDickman
