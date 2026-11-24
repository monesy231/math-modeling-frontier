# Step 6 Spec: Independent Two-Stage Red-Team Audit

> **Isolation**: Run ONLY in a fresh read-only Flagship session (prefer a different model from the drafter). Snapshot all workspace SHA-256 hashes first and run any replay/perturbation probes in an isolated temp copy so sealed project files stay untouched. Zero praise; do not rewrite healthy prose.

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
1. **10-Point Numeric, Freshness & Degenerate-Prose Check**: Spot-check 10 headline numbers (Abstract, tables, captions, companion sheets, dashboard, Conclusion) verbatim against `03_outputs/metrics/`, verify PDF/HTML deliverables are newer than all metric JSON/CSVs, and ensure zero degenerate `"from X to X"` / `"由 X 降至 X"` template typos. Output: `Location | Paper Value | Metric File & Key | PASS/FAIL`.
2. **L3 Math, State Sync, Code-to-Prose & Selection Fidelity**: Flag unverified/fabricated citations; verify **bidirectional** 2–3 entity boundary counterexamples (`>` vs `\ge`, per-grade/asymmetric caps, `threshold ± ε`), **cross-event post-settlement state invalidation** (both last-trigger-cleared and sibling-retained), AND **same-timestamp intra-event fixed-point re-evaluation** (heterogeneous-priority co-opening entities leave zero single-pass deferral residue); test **post-hoc parameter invariance** (perturbing post-hoc-only parameters leaves online decisions byte-identical); audit **code-to-prose exactness** across report & dashboard (baseline tie-break keys, 1-flag-1-mechanism vs. ladder labels, theorem vs. inspired-heuristic scope, open cross-period relaxation domains, static first-deadline snapshots vs. online bounds); verify **dual official metric clocks**, strict-priority vs. trade-off deltas, non-dominance across deduplicated candidates, and chronological split scope.
3. **Closure**: 100% Nomenclature match (no symbol overloading; separate solver surrogate from official metric); balanced inline `$` math; sequential numbering; zero `??` or broken `\ref`; all final figures discussed or cited in text.
4. **Rendered PDF, Math Glyph, Page Budget & Portability Check**: Verify compile log + inspect **every PDF page** (both extracted text and rendered PNGs) for overflowed equations, mid-word table wraps, tofu/missing glyphs (`□`/`\ufffd`), **any unrendered LaTeX command or merged wrapper token** (e.g. `\inI`, `\le`, `\alpha`), clipped figures, sparse trailing-page spills, **hard page-limit compliance** (counting embedded companion sheets), exact agreement between claimed and actual PDF page count, and **cross-platform font fallback** (`UnicodeCIDFont` / bundled TTF) tested under missing-OS-font isolation.
5. **Black-Box Compliance, Companion Templates, Reproducibility & Verifier Integrity**: Re-verify deliverable CSVs against raw `.xlsx`/`.csv` inputs via an independent black-box check (`0` constraint violations, exact integer-scaled conservation, zero-denominator safety); verify all raw/official files sealed (`--verify-raw`), zero workflow leaks, template prompts (`定稿时请删除`), or unfinished deferrals (`待汇总`), verified team fields, `<=60`-char summary, clean UTF-8 non-BOM + uniform-decimal deliverable CSVs (`--strict-csv`), **clean-cache cold-start byte-identical replay**, `verify.py` validating **replayable structured diagnostic evidence** (tested by mutating/swapping valid-looking reasons or protected IDs) plus negative probes (extra trailing rows, corrupted indicators, missing deliverables), and offline HTML dashboard `--check-html` (finite JSON payloads, `node --check`, wide/narrow viewports).

## Stage 2: Minimal-Surgery Polish (ONLY if Stage 1 is 100% Green)
1. Check completeness (explicit/implicit sub-questions, used assumptions, verified statistical premises, persuasive Baseline/sensitivity).
2. Clean remaining D1–D5 defensive phrasing, cheap/AI-slop clichés, non-booktabs boxed tables, and low-density Abstract sentences.
3. Output **ONLY** a minimal-surgery diff table:
   `Location | Code (MATH/D1-D5/SLOP/ABS) | Original | Surgical Replacement`
