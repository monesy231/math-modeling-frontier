# Step 6 Spec: Independent Two-Stage Red-Team Audit

> **Isolation**: Run ONLY in a fresh read-only Flagship session (prefer a different model from the drafter). Zero praise; do not rewrite healthy prose.

## Pre-Step: Deterministic Scan & PDF Page Rasterization
```bash
python <SKILL_DIR>/scripts/audit_paper.py <PAPER_PATH> \
  --plan 00_plan.md --verify-raw . \
  --metrics-dir 03_outputs/metrics --figs-dir 03_outputs/figs \
  --src-dir 02_src --check-csv 03_outputs/submission --strict-csv \
  --log 04_paper/main.log --pdf 04_paper/main.pdf \
  --render-pdf 03_outputs/_audit_pages \
  [--max-pages <N>] [--check-html <HTML_PATH>] \
  --ban-terms "<optional school/name terms>"
```

## Stage 1: Hard Facts, L3 Fidelity & Rendered PDF (HARD GATE)
Any failure triggers **`STAGE 1 FAIL`**—STOP immediately without entering Stage 2 and list blocking fixes:
1. **10-Point Numeric & Degenerate-Prose Check**: Spot-check 10 headline numbers (Abstract, tables, captions, companion sheets, Conclusion) verbatim against `03_outputs/metrics/`; ensure zero degenerate `"from X to X"` / `"由 X 降至 X"` template typos. Output: `Location | Paper Value | Metric File & Key | PASS/FAIL`.
2. **L3 Math, State, Code-to-Prose & Selection Fidelity**: Flag unverified/fabricated citations; verify **bidirectional** 2–3 entity boundary counterexamples (`>` vs `\ge`, asymmetric caps, `threshold ± ε`) and **post-settlement cache/state invalidation** (both last-trigger-cleared and sibling-retained); test **post-hoc parameter invariance** (perturbing post-hoc-only parameters leaves online decisions identical); audit **code-to-prose exactness** across report & dashboard (baseline tie-break keys, 1-flag-1-mechanism ablation labels, theorem vs. inspired-heuristic scope, open cross-period relaxation domains, static-snapshot vs. dynamic bounds); verify **dual official metric definitions**, strict-priority vs. trade-off deltas across all deduplicated candidates, and chronological split scope.
3. **Closure**: 100% Nomenclature match (no symbol overloading; separate solver surrogate from official metric); sequential numbering; zero `??` or broken `\ref`; all final figures discussed or cited in text.
4. **Rendered PDF, Page Budget & Portability Check**: Verify compile log + inspect **every PDF page** for overflowed equations, mid-word table wraps, tofu/missing glyphs (`□`/`\ufffd`), unrendered LaTeX tokens, clipped figures, sparse trailing-page spills, **hard page-limit compliance** (including embedded companion sheets), exact agreement between claimed and actual PDF page count, and **cross-platform font fallback** in script PDF builders.
5. **Compliance, Companion Templates, Reproducibility & Verifier Integrity**: Verify all raw/official files sealed (`--verify-raw`), zero internal workflow leaks or template prompts (`定稿时请删除`), verified registration/team fields, `<=60`-char summary, clean UTF-8 non-BOM deliverable CSVs (`--strict-csv`), **clean-cache cold-start byte-identical replay**, `verify.py` validating **replayable structured diagnostic evidence** (tested by swapping valid-looking reasons) plus negative probes (extra trailing rows, corrupted indicators, missing deliverables), and offline HTML dashboard `--check-html` + wide/narrow viewport checks.

## Stage 2: Minimal-Surgery Polish (ONLY if Stage 1 is 100% Green)
1. Check completeness (explicit/implicit sub-questions, used assumptions, verified statistical premises, persuasive Baseline/sensitivity).
2. Clean remaining D1–D5 defensive phrasing, cheap/AI-slop clichés, non-booktabs boxed tables, and low-density Abstract sentences.
3. Output **ONLY** a minimal-surgery diff table:
   `Location | Code (MATH/D1-D5/SLOP/ABS) | Original | Surgical Replacement`
