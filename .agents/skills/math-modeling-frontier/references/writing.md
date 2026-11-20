# Step 5 Spec: Isolated Press-Conference Writing & Paper Aesthetics

> **Core Calibration**: Concrete `❌ → ✅` contrasts define exact tone and typesetting craft without restricting mathematical structure.

## 1. Press-Conference Prose (Concrete Anti-Defensive Contrasts)
- **D1 Prebuttal**: ❌ *"We emphasize that / It should be noted that our model does not capture every real factor..."* → ✅ *"The coupled ODE tracks thermal flux across three boundary regimes."*
- **D2/D3 Hedge Stacking**: ❌ *"Although simplified, results may potentially suggest some improvement for reference only."* → ✅ *"Test RMSE drops 14.2% (95% CI: [12.8%, 15.6%], $p<0.001$)."*
- **D4 Lab Diary**: ❌ *"We first tried exact MIP, which failed to converge, so we reluctantly switched to relaxation."* → ✅ *"Convex relaxation solves $10^4$-node instances in 1.8 s within a 1.7% optimality gap."*
- **D5 Scattered Apologies**: ❌ Repeating caveats at the end of Sec. 2, 3, and 4 → ✅ Keep Results direct; consolidate quantitative validity boundaries (`valid for perturbation <= 12%`) + concrete math extensions in one final *Strengths, Weaknesses & Extensions* section.

## 2. Top-Prize Structural & Math Discipline
- **Coherent Spine**: Present `Q1 → Qn` as one evolving framework (white-box core → coupled/stochastic upgrade → sensitivity stress-test → policy lever), not isolated algorithm silos.
- **Operational Assumptions**: ❌ *"Assume the provided data is accurate."* → ✅ State `Simplification + Physical/Empirical Justification + Exact Eq. Hook + Relaxation Test`.
- **Math-First & Zero-Transcription Binding**: Give 1–2 lines of intuition before key equations; never silently alter conditions, quantifiers, inequalities, or units when polishing; match `00_plan.md` Nomenclature 100%; prefer `\input{generated_metrics.tex}` macros and `generated_tables/*.tex` from `sync_metrics.py` over hand-typing numbers (eliminates stale/mistranscribed values).
- **Abstract (Write LAST, Zero Fluff)**: ❌ *"We build an optimization model and find the optimal policy with good robustness."* → ✅ *"A daily cap of 14,200 visitors cuts peak ecological stress by 34.6% (95% CI: [31.9%, 37.2%]) while preserving 89.4% net revenue; thresholds shift <3.8% under ±10% elasticity perturbation."*
- **Policy Memo** *(when requested by `00_problem/`)*: 1–1.5 pages, zero raw equations, 3 concrete levers + exact numeric thresholds + phased actions.

## 3. Journal Paper Aesthetics (Typography, Tables & Layout)
- **Booktabs 3-Line Tables Only**: ❌ Vertical lines `|` and Excel-style boxed grids → ✅ `\toprule`, `\midrule`, `\bottomrule` only; left-align text, right-align numbers with uniform decimals, units in column headers, **bold** the best model, report `mean ± std` or `[95% CI]`.
- **Clean Math & Page Rhythm**: Use upright `\mathrm{}` for non-variable subscripts and units (`14.2\,\mathrm{m/s}`); avoid 20+ line unbroken walls of text (break cleanly by mathematical sub-claim); embed native-sized figures at `\linewidth` so figure text matches body font scale.

## 4. Originality, Anti-AI-Slop & Zero Leaks
- **Paraphrase Hygiene**: Never copy prompt wording into Problem Restatement; reformulate crisply in mathematical prose.
- **Ban AI Clichés (Stay Rigorous, Not Chatty)**: Cut `With the rapid development of`, `It is well known`, `crucial/pivotal role`, `delve into`, `comprehensive framework`, `随着……飞速发展`, `众所周知`, `毋庸置疑`, `综上所述……重要意义`, unquantified `significantly`, and 3+ consecutive parallel triplets.
- **Zero Internal Leaks**: Never include `Gate`, `handoff.md`, `SKILL.md`, `00_plan`, `01_log`, `metrics.json`, `Subagent`, `3-Attempt`, `L2`, or `[F]/[W]` anywhere in text, tables, or LaTeX comments. *(Log AI usage ONLY inside an official appendix if required by `00_problem/`.)*
