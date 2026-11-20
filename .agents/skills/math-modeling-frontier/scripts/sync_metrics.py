#!/usr/bin/env python3
"""
Zero-transcription sync from `03_outputs/metrics/` (.json / .csv) to LaTeX:
  1. Flattens every JSON scalar into LaTeX macros in `04_paper/generated_metrics.tex`
     so Abstract, body, and captions auto-update when solver scripts re-run.
  2. Converts every CSV table into a publication-grade Booktabs 3-line table
     (zero vertical lines, right-aligned numbers, optional bold best cell)
     in `04_paper/generated_tables/<stem>.tex`.

Usage:
    python sync_metrics.py --metrics-dir 03_outputs/metrics --paper-dir 04_paper
    python sync_metrics.py --metrics-dir 03_outputs/metrics --paper-dir 04_paper --decimals 3 --bold-best RMSE:min,R2:max
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DIGIT_WORDS = {
    "0": "Zero",
    "1": "One",
    "2": "Two",
    "3": "Three",
    "4": "Four",
    "5": "Five",
    "6": "Six",
    "7": "Seven",
    "8": "Eight",
    "9": "Nine",
}


def to_latex_macro_name(parts: List[str]) -> str:
    """Convert arbitrary file/key path into a valid ASCII-letter-only LaTeX macro name."""
    tokens: List[str] = []
    for raw in parts:
        # Split on non-alphanumeric chars
        for seg in re.split(r"[^A-Za-z0-9]+", str(raw)):
            if not seg:
                continue
            converted = "".join(DIGIT_WORDS[ch] if ch.isdigit() else ch for ch in seg)
            tokens.append(converted[0].upper() + converted[1:])
    stem = "".join(tokens) or "Unnamed"
    return f"Val{stem}"


def escape_latex(text: str) -> str:
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    out = text
    for old, new in replacements:
        out = out.replace(old, new)
    return out


def format_scalar(val: Any, decimals: int) -> str:
    if isinstance(val, bool):
        return "True" if val else "False"
    if isinstance(val, int):
        return f"{val:,}" if abs(val) >= 10000 else str(val)
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            raise ValueError(f"Invalid non-finite float in metrics: {val}")
        if val != 0.0 and abs(val) < 1e-3:
            return f"{val:.2e}"
        return f"{val:.{decimals}f}"
    return escape_latex(str(val))


def flatten_json(obj: Any, prefix: List[str], decimals: int, out: List[Tuple[str, str, str]]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten_json(v, prefix + [str(k)], decimals, out)
    elif isinstance(obj, list):
        # Record 2-element numeric intervals cleanly as [a, b], plus individual elements for small lists
        if len(obj) == 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in obj):
            macro = to_latex_macro_name(prefix)
            formatted = f"[{format_scalar(obj[0], decimals)}, {format_scalar(obj[1], decimals)}]"
            out.append((macro, formatted, ".".join(prefix)))
        elif len(obj) <= 6:
            for idx, item in enumerate(obj):
                flatten_json(item, prefix + [str(idx)], decimals, out)
    elif obj is not None:
        macro = to_latex_macro_name(prefix)
        out.append((macro, format_scalar(obj, decimals), ".".join(prefix)))


def _parse_float(s: str) -> Optional[float]:
    cleaned = s.strip().replace(",", "").rstrip("%")
    try:
        v = float(cleaned)
        return None if (math.isnan(v) or math.isinf(v)) else v
    except ValueError:
        return None


def csv_to_booktabs(
    csv_path: Path,
    decimals: int,
    bold_rules: Dict[str, str],
) -> str:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return f"% Empty CSV: {csv_path.name}\n"

    headers = [h.strip() for h in rows[0]]
    body = [r for r in rows[1:] if any(cell.strip() for cell in r)]
    ncols = len(headers)

    # Detect numeric columns for right alignment
    col_numeric: List[bool] = []
    col_nums: List[List[Optional[float]]] = []
    for c in range(ncols):
        vals = [_parse_float(r[c]) if c < len(r) else None for r in body]
        non_empty = [r[c].strip() for r in body if c < len(r) and r[c].strip()]
        parsed = [v for v in vals if v is not None]
        is_num = bool(non_empty) and len(parsed) >= 0.8 * len(non_empty)
        col_numeric.append(is_num)
        col_nums.append(vals)

    # Identify best row index per bold_rules (case-insensitive header match)
    best_cells: Dict[int, int] = {}
    for c, h in enumerate(headers):
        mode = bold_rules.get(h.lower())
        if not mode:
            continue
        valid = [(r_idx, v) for r_idx, v in enumerate(col_nums[c]) if v is not None]
        if not valid:
            continue
        best_row = min(valid, key=lambda t: t[1])[0] if mode == "min" else max(valid, key=lambda t: t[1])[0]
        best_cells[c] = best_row

    col_spec = "".join("r" if is_num else "l" for is_num in col_numeric)
    lines = [
        "% Auto-generated Booktabs table — do not hand-edit numeric cells",
        f"\\begin{{tabular}}{{{col_spec}}}",
        "\\toprule",
        " & ".join(f"\\textbf{{{escape_latex(h)}}}" for h in headers) + r" \\",
        "\\midrule",
    ]

    for r_idx, row in enumerate(body):
        cells: List[str] = []
        for c in range(ncols):
            raw = row[c].strip() if c < len(row) else ""
            if col_numeric[c] and col_nums[c][r_idx] is not None and not raw.endswith("%") and "." in raw:
                cell_str = format_scalar(col_nums[c][r_idx], decimals)
            else:
                cell_str = escape_latex(raw)
            if best_cells.get(c) == r_idx:
                cell_str = f"\\textbf{{{cell_str}}}"
            cells.append(cell_str)
        lines.append(" & ".join(cells) + r" \\")

    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    return "\n".join(lines)


def parse_bold_rules(spec: str) -> Dict[str, str]:
    rules: Dict[str, str] = {}
    if not spec.strip():
        return rules
    for item in spec.split(","):
        if ":" not in item:
            continue
        col, mode = item.split(":", 1)
        m = mode.strip().lower()
        if m in {"min", "max"}:
            rules[col.strip().lower()] = m
    return rules


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync 03_outputs/metrics (.json/.csv) into LaTeX macros and Booktabs tables."
    )
    parser.add_argument("--metrics-dir", default="03_outputs/metrics", help="Metrics directory")
    parser.add_argument("--paper-dir", default="04_paper", help="Paper directory for generated .tex outputs")
    parser.add_argument("--decimals", type=int, default=2, help="Default decimal precision for floats (default: 2)")
    parser.add_argument(
        "--bold-best",
        default="",
        help="Optional comma-separated column bold rules, e.g. 'RMSE:min,MAE:min,R2:max'",
    )
    args = parser.parse_args()

    metrics_dir = Path(args.metrics_dir)
    paper_dir = Path(args.paper_dir)
    if not metrics_dir.is_dir():
        print(f"[ERROR] Metrics directory not found: {metrics_dir}")
        return 1

    paper_dir.mkdir(parents=True, exist_ok=True)
    bold_rules = parse_bold_rules(args.bold_best)

    # 1. JSON -> generated_metrics.tex
    json_files = sorted(metrics_dir.glob("*.json"))
    macro_entries: List[Tuple[str, str, str]] = []
    seen_macros: Dict[str, str] = {}
    for jf in json_files:
        data = json.loads(jf.read_text(encoding="utf-8"))
        entries: List[Tuple[str, str, str]] = []
        flatten_json(data, [jf.stem], args.decimals, entries)
        for macro, val, src in entries:
            if macro in seen_macros:
                print(f"[WARN] Duplicate macro name '\\{macro}' ({src} vs {seen_macros[macro]}), skipping duplicate.")
                continue
            seen_macros[macro] = src
            macro_entries.append((macro, val, src))

    metrics_tex_path = paper_dir / "generated_metrics.tex"
    tex_lines = [
        "% Auto-generated numeric macros — include via \\input{generated_metrics.tex}",
        "",
    ]
    for macro, val, src in macro_entries:
        tex_lines.append(f"\\newcommand{{\\{macro}}}{{{val}}}")
    metrics_tex_path.write_text("\n".join(tex_lines) + "\n", encoding="utf-8")
    print(f"[SYNC] Wrote {len(macro_entries)} macro(s) -> {metrics_tex_path}")
    for macro, val, src in macro_entries[:20]:
        print(f"       \\{macro} = {val}  ({src})")
    if len(macro_entries) > 20:
        print(f"       ... ({len(macro_entries) - 20} more in {metrics_tex_path.name})")

    # 2. CSV -> generated_tables/*.tex (Booktabs 3-line tables)
    csv_files = sorted(metrics_dir.glob("*.csv"))
    tables_dir = paper_dir / "generated_tables"
    if csv_files:
        tables_dir.mkdir(parents=True, exist_ok=True)
        for cf in csv_files:
            out_tex = tables_dir / f"{cf.stem}.tex"
            out_tex.write_text(csv_to_booktabs(cf, args.decimals, bold_rules), encoding="utf-8")
            print(f"[TABLE] {cf.name} -> {out_tex}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
