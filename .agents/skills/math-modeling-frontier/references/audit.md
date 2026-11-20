# Step 6 Spec: Independent Two-Stage Red-Team Audit

> **Isolation**: Run ONLY in a fresh read-only Flagship session (prefer a different model from the drafter). Zero praise; do not rewrite healthy prose.

## Pre-Step: Deterministic Scan & PDF Page Rasterization
```bash
python <SKILL_DIR>/scripts/audit_paper.py <PAPER_PATH> \
  --plan 00_plan.md --verify-raw . \
  --metrics-dir 03_outputs/metrics --figs-dir 03_outputs/figs \
  --src-dir 02_src --log 04_paper/main.log --pdf 04_paper/main.pdf \
  --render-pdf 03_outputs/_audit_pages \
  --ban-terms "<optional school/name terms>"
```

## Stage 1: Hard Facts, L3 Fidelity & Rendered PDF (HARD GATE)
Any failure triggers **`STAGE 1 FAIL`**—STOP immediately without entering Stage 2 and list blocking fixes:
1. **10-Point Numeric Check**: Spot-check 10 headline numbers (Abstract, tables, captions, Conclusion) verbatim against `03_outputs/metrics/`. Output: `Location | Paper Value | Metric File & Key | PASS/FAIL`.
2. **L3 Citation & Claim Fidelity**: Flag unverified/fabricated citations; verify every table/figure/reference truly supports the claim's direction and strength.
3. **Closure**: 100% Nomenclature match (no symbol overloading); sequential numbering; zero `??` or broken `\ref`; all final figures discussed in text.
4. **Rendered PDF Page-by-Page Check**: Verify compile log + inspect **every PDF page** for overflowed equations, broken tables, clipped/garbled figures, orphan headings, and exact page limits from `00_plan.md`.
5. **Compliance**: Zero internal workflow leaks, strict anonymity (body + code + PDF metadata), all official attachments from `00_problem/` present.

## Stage 2: Minimal-Surgery Polish (ONLY if Stage 1 is 100% Green)
1. Check completeness (explicit/implicit sub-questions, used assumptions, verified statistical premises, persuasive Baseline/sensitivity).
2. Clean remaining D1–D5 defensive phrasing, cheap/AI-slop clichés, non-booktabs boxed tables, and low-density Abstract sentences.
3. Output **ONLY** a minimal-surgery diff table:
   `Location | Code (MATH/D1-D5/SLOP/ABS) | Original | Surgical Replacement`
