---
name: math-modeling-frontier
description: >-
  Ultra-lean dual-tier mathematical modeling workflow (Flagship Thinker + Workhorse
  Executor + Flagship Reviewer). Uses O(1) layered relay memory (handoff.md /
  00_plan.md / 01_log.md) for low-context model switching, dynamic live rules from
  00_problem/, anti-stuck 3-attempt & timeout circuit breaking, pre-writing technical
  audit, isolated press-conference writing, and independent red-team auditing.
---

# Math Modeling Frontier Workflow

> **Core Rule**: Zero restriction on math, modeling, or algorithm creativity. Keep protocol overhead minimal; enforce ONLY workflow order, low-context relay memory, anti-stuck safety, zero fabrication, and non-defensive publication quality.

## 1. Dual-Tier Roles & O(1) Relay Memory (Cross-Model Handoff)

- **`[F]` Flagship (Architect & Reviewer)**: Problem selection, math formulation, paradigm choices, resolving 3-Attempt escalations, **Step 4 technical review**, and **Step 6 final audit**.
- **`[W]` Workhorse (Executor)**: Setup, data cleaning, coding, solver runs, sensitivity sweeps, plotting, and drafting from verified artifacts.
- **3-Tier Memory (Prevents Context Bloat Across Model Switches)**:
  1. `handoff.md` (**HOT — OVERWRITE every switch, HARD CAP ≤ 80 lines**, validate via `audit_paper.py --check-handoff handoff.md`): The *only* file a newly switched model reads first (`Step | Next Role | Active Task | File Pointers | Verified Headlines | Do-Not-Repeat | Next 1-Line Trigger`).
  2. `00_plan.md` (**CANONICAL — read sections on demand**): Live rules extracted from `00_problem/` (must clear all `[EXTRACT FROM 00_problem/]` / `[待核验]` tags before Gate P1), `Q1→Qn` math spine, Nomenclature, Experiment Duty Matrix, Gate status.
  3. `01_log.md` (**COLD — append-only, NEVER preload**): EDA premise stats, external data/citation provenance, dead-end / circuit-breaker archive.
  - **Pointer-Only Rule**: Never paste raw tables, CSVs, or code blocks into memory files—store exact paths to `03_outputs/metrics/*.json` and `03_outputs/figs/*.png` plus 1-line headline scalars.

## 2. Standard Modeling Workflow & 1-Line Triggers (`MM Step 1` – `MM Step 6`)

> Switching sessions requires **zero long prompts**: just type `MM Step N` (printed at the bottom of `handoff.md`). Each trigger automatically loads ONLY its step's authorized files.

- **Step 0 `[W]` Setup & Live Rules**: Run [init_project.py](./scripts/init_project.py) (and `--lock-raw` once official files & raw data are placed in `00_problem/` and `01_data/raw/` to seal SHA-256 checksums). Read `00_problem/` and record exact live rules + sources in `00_plan.md`.
- **`MM Step 1` (`[F]` Track Choice, EDA & Modeling → `Gate M`)**: *(Zero reference files loaded—full native IQ.)* If multiple tracks exist, compare data/feasibility and pick one. Inspect raw data & statistical premises (`01_log.md`), self-play 2–3 distinct paradigms, design one coherent `Q1→Qn` math spine + minimal end-to-end Baseline path in `00_plan.md`. Write `handoff.md` → **HIL pause for user approval**.
- **`MM Step 2` (`[W]` Cleaning & End-to-End Baseline → `Gate P1`)**: Reproducible cleaning (`01_data/clean/`) + full `Q1→Qn` Baseline (`02_src/`, **relative paths only**, `seed=42`, `NaN/Inf`/bound/unit assertions → `03_outputs/metrics/baseline.json`). **No deep single-Q tuning until full Baseline passes.** On pass: `git commit` + overwrite `handoff.md`.
- **`MM Step 3` (`[W]` Upgrades, Validation & Visuals → `Gate P2`)**: Load ONLY [visual.md](./references/visual.md) + `02_src/plot_style.py`. Run upgraded models, Baseline comparison, ablation, uncertainty intervals (95% CI / MC), and ±5%–±10% sensitivity sweeps → persist ALL numbers to `03_outputs/metrics/` and sync LaTeX macros/tables via [sync_metrics.py](./scripts/sync_metrics.py). Export dual `.pdf` + 300-DPI `.png` figures and **visually inspect every `.png`**. On pass: `git commit` + overwrite `handoff.md` for `[F]`.
- **`MM Step 4` (`[F]` Pre-Writing Technical Audit → `Gate R`, Must Pass Before Writing)**: *(Zero reference files loaded.)* Flagship inspects `handoff.md`, `00_plan.md`, `metrics/`, and `figs/` for math coherence, physical/economic plausibility, residual contradictions, premise validity, and missing evidence. Any defect → overwrite `handoff.md` back to `[W]` to fix & re-run; only when `Gate R = PASS` enter Step 5.
- **`MM Step 5` (`[W/F]` Isolated Paper Drafting → `Gate W-Draft`)**: Open a **fresh session**. Read `handoff.md`, `00_plan.md`, `metrics/`, `figs/`, and load **ONLY** [writing.md](./references/writing.md) *(FORBIDDEN to load `audit.md` or frame around reviewers)*. Draft body cleanly, write quantified Abstract **last**, compile PDF + required official attachments.
- **`MM Step 6` (`[F]` Independent Red-Team Audit & Seal → `Gate W-Audit`)**: Open a **fresh read-only Flagship session** *(prefer a different model from the drafter)* loading **ONLY** [audit.md](./references/audit.md). Run [audit_paper.py](./scripts/audit_paper.py) (`--plan 00_plan.md`, `--metrics-dir`, `--figs-dir`, `--src-dir`, `--log`, `--pdf`, `--render-pdf`) → Stage 1 Hard Gate (fail blocks Stage 2) → Stage 2 minimal-surgery diff → seal final PDF.

## 3. Six Hard Guardrails (Mechanical Only)

1. **Anti-Stuck & Dynamic Pivot**: Always smoke-test heavy solvers on small `N` with explicit time-limits first. Debug via `Repro → Root Cause → Single Fix` (no blind tweaks, no `try/except: pass`). After **3 failed root-cause fixes** on one bottleneck, timeout, **or assumption-breaking data/residual anomaly**, **STOP (Attempt #4 forbidden)** → hand back to `[F]` via `handoff.md` to rethink or pivot `L1 (Exact) → L2 (Mechanism approximation + gap/residual bound) → L3 (Analytical bounds / MC interval)`. Log dead ends in `01_log.md` only.
2. **Immutable Raw Data & Zero Fabrication**: `00_problem/` and `01_data/raw/` are **STRICTLY READ-ONLY** (never overwrite, rename, or delete raw files; save all cleaned/derived outputs exclusively under `01_data/clean/`). Every paper number MUST come verbatim from `03_outputs/metrics/`; external data and citations MUST be real and logged in `01_log.md`.
3. **Verify Before Claim**: Never report "done/passed" without observed exit code `0`, passing assertions, fresh outputs, and visual `.png` check.
4. **No Shortcut Excuses**: Never skip Baseline, sensitivity sweeps, PNG checks, or re-verification after edits.
5. **Zero Internal Leaks**: Never mention `Gate`, `handoff.md`, `SKILL.md`, `00_plan`, `01_log`, `metrics.json`, `[F]/[W]`, `3-Attempt`, or `L2` inside the manuscript.
6. **Deadline Guard (<8h)**: Freeze new modeling → lock verified `metrics/` → priority: `missing key plots > quantified abstract > Stage 1 audit + PDF check > seal`. Tag skipped checks `[CONSTRAINED DELIVERY]`.
