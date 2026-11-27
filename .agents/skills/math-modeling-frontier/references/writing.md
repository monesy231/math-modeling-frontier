# Step 5 Spec: Isolated Press-Conference Writing, Math Depth & Editorial Craft

> **Supreme Precedence**: Official contest rules, exact prompt sub-questions, and required formats/deliverables in `00_problem/` (captured in `00_plan.md` Sec. 0) ALWAYS override any generic default below (e.g., palette, appendix scope, or page split). Concrete `❌ → ✅` contrasts enforce narrative tension, deep first-principles math, parameter provenance, and lean publication craft.

## 1. Press-Conference Prose & High-Tension Abstract (Write LAST)
- **Abstract 3-Way Calibration (Hook → Thesis + Flagship Numbers → Robustness Envelope → Action)**:
  - ❌ *Vague Fluff*: *"We build an optimization model and find the optimal policy with good robustness."*
  - ❌ *Audit-Log Clutter*: Cramming micro-caveats (`LOO-expID 45`, `2×2` sub-factorial splits, Holm/bootstrap p-values, `"under assumed masking and burden functions, V12/B500 is a candidate for field testing"`) into the front page so the Abstract reads like an apologetic verification log.
  - ✅ *High-Tension 4-Beat Award Abstract*:
    1. **Hook & Tension**: Name the exact physical/decision conflict & stakes in 1 crisp sentence.
    2. **Unified Mechanistic Thesis + Flagship Results**: State the coupled mathematical chain (`Q1 → Qn`) with headline metrics, effects, and CIs.
    3. **Compact Robustness Envelope**: Summarize stress-test survival rate / interval bounds in one clean clause (move micro-ablations, LOO caveats, and `0/1` sparse cells to *Evaluation* & *Limitations*).
    4. **Decisive Actionable Takeaway**: State concrete quantitative policy levers & real-world gain cleanly without prebuttal hedging.
- **D1–D5 Anti-Defensive Contrasts**:
  - **D1 Prebuttal**: ❌ *"We emphasize that / It should be noted that our model does not capture every factor..."* → ✅ *"The coupled ODE tracks thermal flux across three boundary regimes."*
  - **D2/D3 Hedge Stacking**: ❌ *"Although simplified, results may potentially suggest some improvement for reference only."* → ✅ *"Test RMSE drops 14.2% (95% CI: [12.8%, 15.6%], $p<0.001$)."*
  - **D4 Lab Diary**: ❌ *"We first tried exact MIP, which failed to converge, so we reluctantly switched to relaxation."* → ✅ *"Convex relaxation solves $10^4$-node instances in 1.8 s within a 1.7% optimality gap."*
  - **D5 Scattered Apologies**: ❌ Repeating caveats at the end of Sec. 2, 3, and 4 → ✅ Keep Results direct; consolidate quantitative validity boundaries + math extensions in one final *Strengths, Weaknesses & Extensions* section.

## 2. Mathematical Derivation Depth & 3-Tier Parameter/Weight Provenance
- **4-Step Derivation Arc (Zero Equation-Dropping or Metric-Recital Walls)**:
  - ❌ Dropping one isolated formula followed by 20 lines of CV numbers (`0.4003 vs 0.5148 vs 0.4530`), or leaving a modeling section with zero displayed equations.
  - ✅ Every core task section must walk the reader through: (1) **first principles / physical or probabilistic mechanism** → (2) **step-by-step derivation** into numbered governing equations / likelihoods / optimization objectives + constraints (aim for **≥ 2–4 numbered derivations per core task**) → (3) **analytical property / identifiability / closed-form corollary** (monotone envelope, Hessian/convexity, Fréchet bounds, or parameter boundary diagnosis) → (4) **solver & convergence criterion**.
- **3-Tier Parameter & Weight Provenance (Ban Ungrounded Magic-Number Formulas)**:
  - ❌ Writing arbitrary heuristic formulas or weight tables (`0.22(V/18)^{1.8}e^{-(B-100)/700}`, `0.55/0.45` cost weights, or ungrounded `[0.20, 0.55, 0.80, 1.00]` utility weights disguised as `"illustrative"` or `"prescribed"`).
  - ✅ Classify and justify **every** constant and weight explicitly using one of three tiers:
    1. **Tier 1 — Data-Identified**: Estimated via MLE, nested CV, CRITIC/entropy, or regression with SE/CI (report identifiability/boundary checks).
    2. **Tier 2 — Physics or Literature-Grounded**: Derived from conservation/acoustic/transport laws or peer-reviewed empirical exponents with explicit `\cite{...}` logged in `01_log.md`.
    3. **Tier 3 — Scenario Prior (Last Resort Only)**: Explicitly bound to physical limits, justified via domain extreme cases, and paired with a **mandatory** simplex/sensitivity sweep proving ranking invariance.
- **Operational Assumptions**: ❌ *"Assume the provided data is accurate."* → ✅ Concise table: `Simplification + Justification | Eq. Hook | Relaxation / Stress Test`.
- **Single-Source Binding, Exactness & Coherence**:
  - Maintain **one** canonical manuscript source (sync `.tex`/`.py`/`.docx` deterministically via `sync_metrics.py` + `generated_metrics.tex` / `generated_tables/*.tex` or load-time JSON assertions—never maintain drifting prose copies).
  - Match `00_plan.md` Nomenclature 100%; verify theorems against bidirectional boundary counterexamples, open cross-period relaxation domains, matched scoring/nested-CV protocols, cross-task shared-probability coherence, disconnected-band vs. contiguous-area radii, dual official metric clocks, and strict-priority vs. trade-off deltas.
- **Hard Page Budget & Safe Math Rendering**: Respect `00_plan.md` body-vs-appendix page limits (cite supplementary files instead of overflowing). In script PDF builders, apply **wrapper-last math substitution (`\in`, `\le`, Greek BEFORE `\mathcal`/`\mathrm`/`\mathbf`) + `"\\" not in expr` assertion**, cross-platform font fallbacks, and atomic staged writes. Never fabricate or auto-sign human team commitments (`*cns.*`).

## 3. Lean Curated Appendix & Support-ZIP Split
- ❌ **180-Page Raw Code Dump**: Dumping `build_report.py`, `plot_style.py`, `package_support.py`, `audit_paper.py`, `sync_metrics.py`, unit tests, or raw data tables verbatim into the PDF appendix.
- ✅ **Lean Curated PDF Appendix** (target **≤ 10–25 pages**, keep `<= 1.5×` body pages unless rules mandate full source):
  1. 1-page **Software, Environment & Reproducibility Manifest** (plus truthful AI usage note if required).
  2. Extended mathematical proofs, pseudocode, or compact overflow tables.
  3. **Core modeling, cleaning, solver & verification modules only** (strip plotting/typesetting/packaging boilerplate).
  - Package the **complete** runnable codebase, scripts, and audited outputs into the **Support ZIP** (strictly excluding official raw inputs/problem PDFs if required).

## 4. Academic Typography, Tables & Originality
- **Monochrome-First Formal Paper Aesthetics**: Default formal contest PDFs/LaTeX/Word to **pure monochrome ink (`#000000` text, headings, and Booktabs `\toprule`/`\midrule`/`\bottomrule` on `#FFFFFF`, zero vertical lines `|`, zero decorative colored boxes/tints)**. Keep colorblind-safe `JOURNAL_COLORS` inside scientific figures (with `#000000` axes/labels). Reserve `DOCUMENT_PALETTE` (Charcoal-Ink & Oxford Slate-Navy) for interactive HTML dashboards or non-monochrome technical reports. Left-align text, right-align numbers with uniform decimals, **bold** best scores, embed native-sized figures at `\linewidth`.
- **Paraphrase, Anti-AI-Slop & Zero Leaks**: Reformulate problem restatement crisply; ban AI clichés (`With the rapid development of`, `It is well known`, `crucial/pivotal role`, `delve into`, `comprehensive framework`, `随着……飞速发展`, `众所周知`, `毋庸置疑`, `综上所述……重要意义`, unquantified `significantly`); zero internal leaks (`Gate`, `handoff.md`, `SKILL.md`, `00_plan`, `01_log`, `metrics.json`, `Subagent`, `3-Attempt`, `L2`, `[F]/[W]`).
