#!/usr/bin/env python3
"""
Zero-transcription sync from `03_outputs/metrics/` (.json / .csv) to LaTeX:
  1. Flattens every JSON scalar into valid, unique, deterministic LaTeX macros
     in `04_paper/generated_metrics.tex`. Non-ASCII (e.g., Chinese) keys receive
     stable base-26 ASCII hashes; any remaining macro collision aborts with
     exit code 2 displaying both colliding source keys.
  2. Converts every CSV table into a publication-grade Booktabs 3-line table
     in `04_paper/generated_tables/<stem>.tex`, prunes orphan tables whose
     source CSV was deleted, and persists provenance to
     `03_outputs/metrics/_sync_manifest.json`.

Usage:
    python sync_metrics.py --metrics-dir 03_outputs/metrics --paper-dir 04_paper
    python sync_metrics.py --metrics-dir 03_outputs/metrics --paper-dir 04_paper --decimals 3 --bold-best RMSE:min,R2:max
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
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


def _stable_alpha_hash(text: str, length: int = 8) -> str:
    """Encode SHA-256 digest of text into a deterministic ASCII-letter-only tag (A-Z)."""
    digest = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")
    chars: List[str] = []
    for _ in range(length):
        chars.append(chr(ord("A") + (digest % 26)))
        digest //= 26
    return "".join(chars)


def to_latex_macro_name(parts: List[str]) -> str:
    """
    Convert an arbitrary file/key path (including Chinese/Unicode keys) into a
    valid ASCII-letter-only, stable, unique LaTeX macro name.
    """
    tokens: List[str] = []
    for raw in parts:
        s = str(raw).strip()
        if not s:
            continue
        has_non_ascii = any(ord(ch) > 127 for ch in s)
        ascii_segs = [seg for seg in re.split(r"[^A-Za-z0-9]+", s) if seg]
        for seg in ascii_segs:
            converted = "".join(DIGIT_WORDS[ch] if ch.isdigit() else ch for ch in seg)
            tokens.append(converted[0].upper() + converted[1:])
        if has_non_ascii or not ascii_segs:
            # Deterministic base-26 tag guarantees uniqueness for Chinese/Unicode keys
            tokens.append(f"U{_stable_alpha_hash(s, length=8)}")
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
        return "% Empty table source\n"

    headers = [h.strip() for h in rows[0]]
    body = [r for r in rows[1:] if any(cell.strip() for cell in r)]
    ncols = len(headers)

    col_numeric: List[bool] = []
    col_nums: List[List[Optional[float]]] = []
    for c in range(ncols):
        vals = [_parse_float(r[c]) if c < len(r) else None for r in body]
        non_empty = [r[c].strip() for r in body if c < len(r) and r[c].strip()]
        parsed = [v for v in vals if v is not None]
        is_num = bool(non_empty) and len(parsed) >= 0.8 * len(non_empty)
        col_numeric.append(is_num)
        col_nums.append(vals)

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
        description="Sync 03_outputs/metrics (.json/.csv) into LaTeX macros, Booktabs tables, and provenance manifest."
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

    # 1. JSON -> generated_metrics.tex (ignore internal _*.json manifests)
    json_files = sorted(p for p in metrics_dir.glob("*.json") if not p.name.startswith("_"))
    macro_entries: List[Tuple[str, str, str]] = []
    seen_macros: Dict[str, str] = {}
    collisions: List[Tuple[str, str, str]] = []

    for jf in json_files:
        data = json.loads(jf.read_text(encoding="utf-8"))
        entries: List[Tuple[str, str, str]] = []
        flatten_json(data, [jf.stem], args.decimals, entries)
        for macro, val, src in entries:
            if macro in seen_macros:
                collisions.append((macro, seen_macros[macro], src))
                continue
            seen_macros[macro] = src
            macro_entries.append((macro, val, src))

    if collisions:
        print("[ERROR] Macro name collision detected! Aborting sync to prevent silent metric loss:")
        for macro, first_src, second_src in collisions:
            print(f"  [COLLISION] '\\{macro}' collided between '{first_src}' and '{second_src}'")
        return 2

    metrics_tex_path = paper_dir / "generated_metrics.tex"
    tex_lines = [
        "% Auto-generated numeric macros — include via \\input{generated_metrics.tex}",
        "",
    ]
    for macro, val, _ in macro_entries:
        tex_lines.append(f"\\newcommand{{\\{macro}}}{{{val}}}")
    metrics_tex_path.write_text("\n".join(tex_lines) + "\n", encoding="utf-8")
    print(f"[SYNC] Wrote {len(macro_entries)} macro(s) -> {metrics_tex_path}")
    for macro, val, src in macro_entries[:25]:
        print(f"       \\{macro} = {val}  ({src})")
    if len(macro_entries) > 25:
        print(f"       ... ({len(macro_entries) - 25} more in _sync_manifest.json)")

    # 2. CSV -> generated_tables/*.tex (Booktabs 3-line tables) + prune withdrawn orphan tables
    csv_files = sorted(p for p in metrics_dir.glob("*.csv") if not p.name.startswith("_"))
    tables_dir = paper_dir / "generated_tables"
    active_stems = {cf.stem for cf in csv_files}
    csv_to_table: Dict[str, str] = {}

    if tables_dir.is_dir():
        for existing_tex in sorted(tables_dir.glob("*.tex")):
            if existing_tex.stem not in active_stems:
                existing_tex.unlink()
                print(f"[PRUNE] Removed orphan table without source CSV: {existing_tex}")

    if csv_files:
        tables_dir.mkdir(parents=True, exist_ok=True)
        for cf in csv_files:
            out_tex = tables_dir / f"{cf.stem}.tex"
            out_tex.write_text(csv_to_booktabs(cf, args.decimals, bold_rules), encoding="utf-8")
            csv_to_table[cf.name] = f"generated_tables/{cf.stem}.tex"
            print(f"[TABLE] {cf.name} -> {out_tex}")

    # 3. Persist sync provenance manifest in 03_outputs/metrics/_sync_manifest.json (keeps 04_paper blind-clean)
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "json_sources": [jf.name for jf in json_files],
        "csv_to_table": csv_to_table,
        "macros": {macro: {"value": val, "source": src} for macro, val, src in macro_entries},
    }
    manifest_path = metrics_dir / "_sync_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[MANIFEST] Wrote provenance index -> {manifest_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
