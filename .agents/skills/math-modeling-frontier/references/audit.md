# Step 6 Spec: Independent Two-Stage Red-Team Audit & Substantive Scorecard

> **Supreme Precedence & Isolation**: Official contest rules, prompt sub-questions, and deliverable specs in `00_problem/` (captured in `00_plan.md` Sec. 0) ALWAYS take top priority over generic preferences below (generic Stage 2 cues like `APPENDIX_BLOAT` or monochrome default yield when `00_problem/` explicitly mandates otherwise). Run ONLY in a fresh read-only Flagship session (prefer a different model from the drafter). Snapshot workspace SHA-256 hashes first and run replay/perturbation probes in an isolated temp copy so sealed files stay untouched. Zero praise; do not rewrite healthy prose.

## Pre-Step: Deterministic Scan & PDF Page Rasterization
```bash
python <SKILL_DIR>/scripts/audit_paper.py <PAPER_PATH> \
  --plan 00_plan.md --verify-raw . \
  --metrics-dir 03_outputs/metrics --figs-dir 03_outputs/figs \
  --src-dir 02_src --check-csv 03_outputs/submission --strict-csv \
  --log 04_paper/main.log --pdf 04_paper/main.pdf \
  --render-pdf 03_outputs/_audit_pages \
  [--body-start-page <N>] [--max-pages <N>] [--max-appendix-pages <M>] \
  [--check-html <HTML_PATH>] --ban-terms "<optional school/name terms>"
```

## Stage 1: Prompt Compliance, Hard Facts, Fidelity & Rendered PDF (HARD GATE)
Any failure triggers **`STAGE 1 FAIL`**—STOP immediately without entering Stage 2 and list blocking fixes:
0. **Problem-Prompt & Official-Rule Traceability (#1 Priority)**: Verify every explicit & implicit prompt sub-question, required metric/policy scenario, format/anonymity/page rule, and required deliverable in `00_plan.md` Sec. 0 & Traceability Checklist is directly answered and compliant—no generic skill habit may violate or overshadow a contest rule.
1. **10-Point Numeric, Freshness & Degenerate-Prose Check**: Spot-check 10 headline numbers (Abstract, Summary Sheet, tables, captions, dashboard, Conclusion) verbatim against `03_outputs/metrics/`, verify PDF/HTML deliverables are newer than all metric JSON/CSVs, and ensure zero `"from X to X"` / `"由 X 降至 X"` template typos. Output: `Location | Paper Value | Metric File & Key | PASS/FAIL`.
2. **Math, Protocol, State-Sync & Parameter-Config Fidelity**:
   - Flag unverified/fabricated citations; verify **single-source tuned-hyperparameter propagation** into all resamples (zero silent defaults), **interior hyperparameter optima & optimizer boundary-pinning/identifiability diagnostics**, and **identical scoring/clamping & nested inner-CV protocols** across competitors & LOO checks + **orthogonalized ablations**.
   - Verify **cross-task shared-probability coherence**, **disconnected-band vs. contiguous-area checks**, **bidirectional** 2–3 entity boundary counterexamples (`>` vs `\ge`, per-grade/asymmetric caps, `threshold ± ε`), **cross-event post-settlement state invalidation** (last-trigger-cleared & sibling-retained), **same-timestamp intra-event fixed-point re-evaluation**, and **post-hoc parameter invariance**.
   - Audit **code-to-prose exactness** across report & dashboard (tie-break keys, 1-flag-1-mechanism vs. ladder labels, theorem vs. heuristic scope, open cross-period relaxation domains, dual official metric clocks, strict-priority vs. trade-off deltas, chronological split scope).
3. **Closure & Single-Source Sync**: 100% Nomenclature match; balanced `$` math; zero `??` / broken `\ref`; all final figures cited; zero drifted duplicate archival `.tex`/`.docx` vs. submission PDF.
4. **Rendered PDF, Math Glyph, Body/Appendix Budget & Portability Check**: Inspect **every PDF page** (extracted text + rendered PNGs) for overflowed equations, mid-word table wraps, tofu glyphs (`□`/`\ufffd`), **unrendered LaTeX or merged wrapper tokens** (e.g. `\inI`, `\le`, `\alpha`), clipped figures/legends, sparse trailing spills, body-vs-appendix page compliance (`--body-start-page` / `--max-pages` / `--max-appendix-pages`), claimed vs. actual page count, and cross-platform font fallback under missing-OS-font isolation.
5. **Black-Box Compliance, Companion Templates, Support ZIP & Reproducibility**: Re-verify deliverable CSVs from raw inputs (`0` violations, exact integer-scaled conservation); verify raw/official files sealed (`--verify-raw`), Support ZIP excludes raw official files (if required) and runs clean-cache cold-start byte-identical replay, zero workflow/template leaks or forged team signatures, `verify.py` AST-clean (`zip(..., strict=True)` / `zip_longest`) with replayable structured diagnostics + negative tamper probes, and offline HTML `--check-html`.

## Stage 2: Substantive Excellence Scorecard & Minimal-Surgery Polish (ONLY if Stage 1 Passes)
Score all **5 mandatory axes** (`PASS` / `REVISE`)—flagging ANY automated Stage 2 signals (`ABSTRACT_AUDIT_CLUTTER`, `THIN_MATH_DERIVATION`, `UNGROUNDED_PARAM_WEIGHT`, `APPENDIX_BLOAT`, `APPENDIX_BOILERPLATE_CODE`, `D1–D5`, `AI_SLOP`, `CHEAP_TABLE`):
1. **`ABS-ARC` (Abstract Narrative Tension)**: Does the Abstract follow the 4-beat Hook → Mechanistic Thesis + Flagship Numbers → Compact Robustness Envelope → Actionable Takeaway arc without micro-audit clutter or vague fluff?
2. **`MATH-DEPTH` (Body Math Derivation Thickness)**: Does every core modeling section derive numbered governing equations / objectives from first principles + analyze properties/identifiability (not formula-dropping or metric-recital walls)?
3. **`PARAM-GROUND` (Weight & Physical Parameter Provenance)**: Is every weight/constant explicitly Tier-1 data-identified, Tier-2 physics/literature-cited, or Tier-3 scenario-swept (zero ungrounded magic-number formulas)?
4. **`APP-LEAN` (Lean Curated Appendix)**: Is the PDF appendix concise (`<= 1.5×` body pages), containing manifest/proofs/core modeling code only (zero `build_report.py`/`plot_style.py`/`package_support.py` boilerplate)?
5. **`D1-D5` / `SLOP` / `FIG-TBL` (Prose, Visual & Monochrome Craft)**: Clean non-defensive prose, zero AI clichés, Booktabs 3-line tables, clean monochrome typography (when formal contest requires), and unclipped figures.

Output the **5-Axis Scorecard** (`Axis | Verdict (PASS/REVISE) | Concrete Finding`) AND the **Minimal-Surgery Diff Table**:
`Location | Code (ABS-ARC/MATH-DEPTH/PARAM-GROUND/APP-LEAN/D1-D5/SLOP/FIG-TBL) | Original | Surgical Replacement`
