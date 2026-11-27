#!/usr/bin/env python3
"""
Initialize a contest-agnostic mathematical modeling workspace with O(1) Layered
Relay Memory for Flagship ([F]) <-> Workhorse ([W]) model switching:
  - handoff.md  (HOT, <=80 lines, overwritten on every model switch)
  - 00_plan.md  (CANONICAL, read on demand: live rules, Q1->Qn spine, Nomenclature, Gates)
  - 01_log.md   (COLD, append-only, never preloaded: EDA provenance, dead ends, audit trail)

Usage:
    python init_project.py <project_dir> --contest "2026 APMCM" --lang en --title "Problem A"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def seal_raw_data(root: Path, force: bool = False) -> Path:
    """Compute SHA-256 baseline checksums for all original files in 00_problem/ and 01_data/raw/."""
    seal_path = root / "01_data" / ".raw_checksums.json"
    existing_files: Dict[str, Dict[str, object]] = {}
    if seal_path.is_file() and not force:
        try:
            prev = json.loads(seal_path.read_text(encoding="utf-8"))
            existing_files = dict(prev.get("files", {}))
        except Exception:
            existing_files = {}

    sealed: Dict[str, Dict[str, object]] = dict(existing_files)
    added = 0
    for rel_dir in ("00_problem", "01_data/raw"):
        d = root / rel_dir
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*")):
            if not p.is_file() or p.name.startswith("."):
                continue
            rel_key = p.relative_to(root).as_posix()
            # Never silently overwrite an already-sealed file's hash unless --force is explicit
            if rel_key in sealed and not force:
                continue
            sealed[rel_key] = {
                "sha256": _sha256_file(p),
                "bytes": p.stat().st_size,
            }
            added += 1

    payload = {
        "sealed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "Immutable SHA-256 baseline for original files in 00_problem/ and 01_data/raw/. Do not edit raw files.",
        "files": sealed,
    }
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    seal_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[SEAL]   {seal_path} ({len(sealed)} file(s) sealed, {added} newly added)")
    return seal_path


def write_if_allowed(path: Path, content: str, force: bool) -> str:
    if path.exists() and not force:
        return f"[SKIP]   {path} (already exists)"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"[CREATE] {path}"


def _ensure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def main() -> int:
    _ensure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Scaffold a dual-tier frontier mathematical modeling workspace."
    )
    parser.add_argument("project_dir", type=str, help="Target project root directory")
    parser.add_argument(
        "--contest",
        "-c",
        default="[EXTRACT FROM 00_problem/]",
        help="Contest name & year (e.g., '2026 APMCM')",
    )
    parser.add_argument(
        "--lang",
        "-l",
        choices=["en", "zh"],
        default="en",
        help="Primary paper language (en or zh, default: en)",
    )
    parser.add_argument(
        "--title",
        "-t",
        default="[TBD Problem Track / Title]",
        help="Short problem label (e.g., 'Problem A')",
    )
    parser.add_argument(
        "--lock-raw",
        action="store_true",
        help="Seal SHA-256 checksums of original files in 00_problem/ and 01_data/raw/ into 01_data/.raw_checksums.json",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing starter markdown/style files (or re-seal modified checksums when combined with --lock-raw)",
    )
    args = parser.parse_args()

    root = Path(args.project_dir).resolve()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    if args.lock_raw and (root / "00_plan.md").is_file() and not args.force:
        # Fast-path: project already initialized; seal any new original raw/problem files without touching starter docs
        seal_raw_data(root, force=False)
        return 0

    for d in [
        root / "00_problem",
        root / "01_data" / "raw",
        root / "01_data" / "clean",
        root / "02_src",
        root / "03_outputs" / "metrics",
        root / "03_outputs" / "figs",
        root / "04_paper",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    # Copy plot_style.py from skill scripts directory
    skill_plot_style = Path(__file__).resolve().parent / "plot_style.py"
    dest_plot_style = root / "02_src" / "plot_style.py"
    if skill_plot_style.exists():
        if not dest_plot_style.exists() or args.force:
            shutil.copy2(skill_plot_style, dest_plot_style)
            print(f"[COPY]   {dest_plot_style}")
        else:
            print(f"[SKIP]   {dest_plot_style} (already exists)")
    else:
        print(f"[WARN]   plot_style.py not found next to init_project.py at {skill_plot_style}")

    problem_files = sorted(p.name for p in (root / "00_problem").iterdir() if p.is_file())
    problem_listing = ", ".join(problem_files) if problem_files else "[Drop latest official files into 00_problem/]"

    handoff_md = f"""# handoff.md — HOT Relay Packet (OVERWRITE every switch | HARD CAP <= 80 lines)

- **Updated**: {now_str}
- **Current Step**: `Step 0 -> Step 1`
- **Next Role**: `[F] Flagship` (Problem Selection, EDA Review & Formulation -> Gate M)
- **Deadline Guard (<8h)?**: `NO`

## Active Task (Next Turn Only)
1. Extract live contest rules from `00_problem/` into `00_plan.md` Sec. 0 (clear all `[EXTRACT FROM 00_problem/]` tags).
2. Audit `01_data/raw/` columns & supplementary methods (`01_log.md`), and log real domain DOIs/URLs for physics & weights.
3. Self-play 2–3 paradigms, lock `Q1 -> Qn` **Math Derivation Spine** & **Parameter & Weight Provenance Table** in `00_plan.md`, then pause at **Gate M**.

## File Pointers (Read On Demand — Never Paste Raw Data Here)
- Problem & official rules: `00_problem/` ({problem_listing})
- Raw data: `01_data/raw/`
- Canonical plan & symbols: `00_plan.md`
- Verified metrics: `03_outputs/metrics/` (none yet)
- Verified figures: `03_outputs/figs/` (none yet)

## Verified Headline Facts
- Workspace initialized (`{args.contest}` | `{args.lang.upper()}`).

## Open Blockers / Do-Not-Repeat (Max 3 Items)
- None yet.

## Next Session Trigger (Copy 1 Line Into Next Model)
`使用 math-modeling-frontier 执行 MM Step 1`
"""

    plan_md = f"""# 00_plan.md — Canonical Rules, Prompt Traceability, Math Spine & Gates (Read On Demand)

- **Initialized**: {now_str} | **Contest**: {args.contest} | **Problem**: {args.title} | **Lang**: {args.lang.upper()}
- **Priority Hierarchy**: `00_problem/ Official Rules & Problem Questions > Explicit Deliverables > Generic Skill Defaults`

## 0. Live Official Rules (Extracted from `00_problem/` — state concrete rule + source file, or `已核实不适用 (Source: <notice>)`)
- **Format & Template**: `[EXTRACT FROM 00_problem/]` *(include monochrome/color typography norm if specified)*
- **Deadline / Window**: `[EXTRACT FROM 00_problem/]`
- **Hard Page / Word Limit**: `[EXTRACT FROM 00_problem/]` *(separate body vs. appendix cap & whether companion sheets count)*
- **Anonymity & Metadata**: `[EXTRACT FROM 00_problem/]`
- **AI Declaration Policy**: `[EXTRACT FROM 00_problem/]` *(standalone AI sheet / human-signature commitment rules)*
- **Required Extras (Memo / Code / Data / Plagiarism / Support ZIP Exclusions / Dual Clocks)**: `[EXTRACT FROM 00_problem/]`

### Prompt Sub-Question & Requirement Traceability Checklist
| Prompt Requirement / Sub-Q | Official Deliverable / Metric / Format | Model & Paper Section | Verified? |
| :--- | :--- | :--- | :--- |
| Q1: `[EXTRACT FROM 00_problem/]` | | | `PENDING` |

## 1. Workflow Gate Tracker (Step 0 -> Step 6)

| Step & Gate | Owner | Scope | Status | Evidence Pointer |
| :--- | :--- | :--- | :--- | :--- |
| **Step 0 · Setup** | `[W]` | Workspace + live rules from `00_problem/` | `IN_PROGRESS` | `00_plan.md` |
| **Step 1 · Gate M** | `[F]` | Track choice, EDA, derivation spine, parameter provenance, HIL | `PENDING` | `00_plan.md`, `01_log.md` |
| **Step 2 · Gate P1** | `[W]` | Reproducible cleaning + full `Q1->Qn` Baseline + commit | `PENDING` | `03_outputs/metrics/baseline.json` |
| **Step 3 · Gate P2** | `[W]` | Matched-protocol upgrades, ablations, sensitivity, visuals + commit | `PENDING` | `03_outputs/metrics/`, `figs/` |
| **Step 4 · Gate R** | `[F]` | **Pre-Writing Technical & Math Audit** (substance + fidelity) | `PENDING` | `handoff.md` |
| **Step 5 · W-Draft** | `[W/F]` | Isolated press-conference draft + lean curated appendix + PDF | `PENDING` | `04_paper/` |
| **Step 6 · W-Audit** | `[F]` | Independent read-only Stage 1 + 5-axis Stage 2 audit + seal | `PENDING` | Audit report |

## 2. Coherent `Q1 -> Qn` Math Derivation Spine, Cohort Accounting & Baseline Route
- **Q1**: [First-principles governing equations, likelihood/objective & analytical properties]
- **Q2**: [Coupled / upgraded formulation inheriting Q1 + identifiability checks]
- **Q3**: [Stochastic / sensitivity / policy extension]
- **Cross-Task Shared Interfaces & Single-Source Tuned Config**: [Shared occurrence probabilities / parameters across tasks; single config source propagated to all resamples]
- **Cohort, Precision & Causality Contract**: [Item vs. entity cohort + fixed denominators; carryover conservation; integer-scaled units; causal decision-time vs. post-hoc parameters]
- **Global Baseline Path (Gate P1)**: [Minimal end-to-end `Q1 -> Qn` script chain + independent raw-input `verify.py`]

## 3. Actor-Critic Paradigm Trade-Off
| Paradigm | Core Idea | Fatal Assumption / Data Risk | Verdict |
| :--- | :--- | :--- | :--- |
| A | | | |
| B | | | |
| C | | | |

## 4. Operational Assumptions, Parameter Provenance & Unified Nomenclature
| ID | Assumption + Justification | Eq. Hook | Relaxation / Sensitivity Test |
| :--- | :--- | :--- | :--- |
| A1 | | | |

| Param / Weight | Value / Form | Tier (`Data` / `Physics-Lit` / `Scenario`) | Source / Calibration (`01_log.md` DOI/CV) | Sensitivity Sweep |
| :--- | :--- | :--- | :--- | :--- |
| $w_1$ | | | | |

| Symbol | Definition | Unit / Domain | First Used |
| :--- | :--- | :--- | :--- |
| $t$ | Time index | - | Sec. 3 |

## 5. Experiment Duty Matrix
| Exp | Duty | Design / Sweep | Metric Pointer (`03_outputs/metrics/`) | Fig / Table |
| :--- | :--- | :--- | :--- | :--- |
| E1 | Premise & Relaxation Bounds | Conservation / VIF / open cross-period bounds | `eda_diagnostics.json` | Fig. 1 / Tab. 1 |
| E2 | Two-Tier Baseline vs. Proposed | Naive + strong greedy + bootstrap & MC intervals | `model_comparison.json` | Tab. 2 / Fig. 3 |
| E3 | 1-Flag-1-Mechanism Ablation | Single-factor switches + counterfactual toggle-off | `ablation.json` | Tab. 2 |
| E4 | Stress (±5%, ±10%) & Frontiers | Parameter/delay shocks + priority/Pareto ranking | `sensitivity.json`, `pareto_sweep.json` | Fig. 4 / Fig. 5 |
| E5 | Chronological & Tamper Audit | Lock-then-replay + prefix causality + state/tamper probes | `chronological.json`, `audit_probes.json` | Tab. 4 / App. |
"""

    log_md = f"""# 01_log.md — Cold Archival Ledger (Append-Only — NEVER Preload Into Normal Turns)

- **Project**: {args.contest} — {args.title} | **Created**: {now_str}

## 1. EDA & Statistical Premise Diagnostics
<!-- Append raw file SHA-256 notes, shapes, missingness, and statistical/conservation premise checks below -->

## 2. External Data & Literature Provenance (Verifiable Real Sources Only)
<!-- Append real DOIs, official URLs, and retrieval timestamps below -->

## 3. Dynamic Pivots & 3-Attempt Circuit-Breaker Archive (Internal Only — NEVER Narrate in Paper)
| Timestamp | Sub-Problem | Root Cause | Attempts (#1-#3) | Pivot (`L2`/`L3`) | Positive Paper Framing |
| :--- | :--- | :--- | :--- | :--- | :--- |
| - | - | - | - | - | - |
"""

    gitignore = """# Python
__pycache__/
*.py[cod]
.venv/
venv/
.ipynb_checkpoints/

# LaTeX build artifacts
*.aux
*.bbl
*.blg
*.fdb_latexmk
*.fls
*.log
*.out
*.synctex.gz
*.toc
*.lof
*.lot
*.nav
*.snm

# Audit scratch renders & PDF page previews
03_outputs/_audit_pages/
03_outputs/_pdf_previews/
_page_previews/
*_page_previews/
.pdf_previews/

# OS
.DS_Store
Thumbs.db
"""

    gitattributes = """* text=auto eol=lf
*.png binary
*.pdf binary
*.jpg binary
*.jpeg binary
*.xlsx binary
*.xls binary
*.zip binary
"""

    for target, content in [
        (root / "handoff.md", handoff_md),
        (root / "00_plan.md", plan_md),
        (root / "01_log.md", log_md),
        (root / ".gitignore", gitignore),
        (root / ".gitattributes", gitattributes),
    ]:
        print(write_if_allowed(target, content, args.force))

    # Automatically seal original files if present in 00_problem/ or 01_data/raw/ (or when --lock-raw is set)
    has_originals = any(
        p.is_file() and not p.name.startswith(".")
        for rel_dir in ("00_problem", "01_data/raw")
        for p in (root / rel_dir).rglob("*")
    )
    if args.lock_raw or has_originals:
        seal_raw_data(root, force=args.force)

    print(f"\n[DONE] Dual-tier workspace ready at: {root}")
    print(f"       Hot relay: handoff.md (<=80 lines) | Canonical: 00_plan.md | Cold: 01_log.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
