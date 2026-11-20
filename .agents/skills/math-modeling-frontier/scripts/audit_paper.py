#!/usr/bin/env python3
"""
Deterministic Stage 1 (Hard Compliance), Section-Aware Stage 2 (Defensive /
AI-Slop / Cheap-Table Signals), PDF Page Renderer (for multimodal page-by-page
inspection), 00_plan.md Live-Rule Gate, and O(1) `handoff.md` Relay Validator.

Exit code:
  0 = Stage 1 / Handoff / Plan checks PASS
  2 = Blocking hard failures detected (must fix before proceeding)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple

# Stage 1 HARD FAIL: Internal workflow term leaks
INTERNAL_LEAK_PATTERNS: List[Tuple[str, str]] = [
    ("INTERNAL_LEAK", r"\bGate\s*(?:M|P1|P2|R|W)\b"),
    ("INTERNAL_LEAK", r"\bSKILL\.md\b"),
    ("INTERNAL_LEAK", r"\bhandoff\.md\b"),
    ("INTERNAL_LEAK", r"\b00_plan\.md\b"),
    ("INTERNAL_LEAK", r"\b01_log\.md\b"),
    ("INTERNAL_LEAK", r"\b01_findings\.md\b"),
    ("INTERNAL_LEAK", r"\b02_progress\.md\b"),
    ("INTERNAL_LEAK", r"\bmetrics\.json\b"),
    ("INTERNAL_LEAK", r"\bbaseline\.json\b"),
    ("INTERNAL_LEAK", r"\bSubagent\b"),
    ("INTERNAL_LEAK", r"\bW-Draft\b"),
    ("INTERNAL_LEAK", r"\bW-Audit\b"),
    ("INTERNAL_LEAK", r"\b3-Attempt\b"),
    ("INTERNAL_LEAK", r"\bCircuit\s+Breaker\b"),
    ("INTERNAL_LEAK", r"\bAnti-Defensive\b"),
    ("INTERNAL_LEAK", r"L[123]\s*降级"),
]

# Stage 1 HARD FAIL: Anonymity & local path leaks
PATH_LEAK_PATTERNS: List[Tuple[str, str]] = [
    ("PATH_LEAK", r"[A-Za-z]:\\Users\\"),
    ("PATH_LEAK", r"/Users/[A-Za-z0-9._-]+/"),
    ("PATH_LEAK", r"/home/[A-Za-z0-9._-]+/"),
    ("PATH_LEAK", r"file:///"),
]

# Stage 1 HARD FAIL: Unfinished placeholders
PLACEHOLDER_PATTERNS: List[Tuple[str, str]] = [
    ("PLACEHOLDER", r"\b(?:TODO|TBD|FIXME|XXX)\b"),
    ("PLACEHOLDER", r"\[待核验\]"),
    ("PLACEHOLDER", r"\[待补充\]"),
    ("PLACEHOLDER", r"\[\?\?\]"),
]

# Stage 2 STYLE SIGNAL: D1-D5 Defensive writing triggers (EN + ZH)
DEFENSIVE_PATTERNS: List[Tuple[str, str]] = [
    ("D1_PREBUTTAL", r"\b(?:We emphasize that|It should be noted that|To avoid misunderstanding|A potential concern is)\b"),
    ("D1_PREBUTTAL", r"(?:需要强调的是|值得注意的是，我们并非|为避免误解|需要指出的是，本文并不)"),
    ("D2_NON_CLAIM", r"\b(?:We do not claim|does not claim|should not be interpreted as|for reference only|cannot solve all)\b"),
    ("D2_NON_CLAIM", r"(?:仅供参考|不能解决现实中所有|并非宣称|由于(?:时间|数据)(?:和|与)?(?:数据|时间)?有限)"),
    ("D3_HEDGE_STACK", r"\b(?:may potentially|might potentially|appears to some extent|could possibly suggest|somewhat helpful)\b"),
    ("D3_HEDGE_STACK", r"(?:或许在某种程度上|可能在一定程度上暗示|似乎略微)"),
    ("D4_EXCUSE_DIARY", r"\b(?:we first tried|failed to converge|reluctantly switched|lower score is likely due to|remains encouraging despite)\b"),
    ("D4_EXCUSE_DIARY", r"(?:我们最初尝试了|一直不收敛|无奈改用|勉强跑通|误差偏大可能是因为)"),
    ("D5_SELF_SABOTAGE", r"\b(?:unfortunately|merely|only a rough approximation|highly simplified)\b"),
    ("D5_SELF_SABOTAGE", r"(?:遗憾的是|仅仅做了高度简化|本文模型较为粗糙)"),
]

# Stage 2 STYLE SIGNAL: High-frequency AI-slop clichés & cheap table borders
AI_SLOP_PATTERNS: List[Tuple[str, str]] = [
    ("AI_SLOP", r"\bWith the rapid development of\b"),
    ("AI_SLOP", r"\bhas attracted widespread attention\b"),
    ("AI_SLOP", r"\bIt is well known that\b"),
    ("AI_SLOP", r"\bplays? a (?:crucial|pivotal|vital) role\b"),
    ("AI_SLOP", r"\bdelve(?:s|d|ing)? into\b"),
    ("AI_SLOP", r"\bcomprehensive framework\b"),
    ("AI_SLOP", r"\btapestry\b"),
    ("AI_SLOP", r"\bunprecedented\b"),
    ("AI_SLOP", r"随着.{1,20}(?:飞速发展|不断进步|快速发展)"),
    ("AI_SLOP", r"众所周知"),
    ("AI_SLOP", r"毋庸置疑"),
    ("AI_SLOP", r"综上所述.{0,12}(?:重要(?:的)?(?:理论|现实|实践)?意义)"),
    ("CHEAP_TABLE", r"\\begin\{tabular\}\{[^}]*\|"),
]

# Section headings where legitimate discussion of boundaries/weaknesses is expected
LIMITATION_SECTION_RX = re.compile(
    r"(?:strengths?|weakness|limitation|further\s+discussion|future\s+work|report\s+on\s+use\s+of\s+ai|ai\s+usage"
    r"|优缺点|局限|不足|模型评价|模型改进|讨论与展望|人工智能使用)",
    re.IGNORECASE,
)
LIMITATION_EXEMPT_CODES: Set[str] = {"D2_NON_CLAIM", "D5_SELF_SABOTAGE"}
TEX_SECTION_RX = re.compile(r"\\(?:sub){0,2}section\*?(?:\[[^\]]*\])?\{([^}]+)\}")
MD_SECTION_RX = re.compile(r"^\s{0,3}#{1,3}\s+(.+?)\s*$")
CODE_ENV_START_RX = re.compile(r"\\begin\{(?:verbatim|lstlisting|minted)\*?\}")
CODE_ENV_END_RX = re.compile(r"\\end\{(?:verbatim|lstlisting|minted)\*?\}")


def collect_manuscript_files(target: Path) -> List[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(
            p for p in target.rglob("*")
            if p.is_file() and p.suffix.lower() in {".tex", ".md"}
        )
    return []


def scan_patterns(
    files: List[Path],
    patterns: List[Tuple[str, str]],
    case_insensitive: bool = True,
) -> List[Tuple[str, int, str, str, str]]:
    """Unfiltered line-by-line scanner used for Stage 1 hard gates (zero exemptions)."""
    flags = re.IGNORECASE if case_insensitive else 0
    compiled = [(code, re.compile(pat, flags)) for code, pat in patterns]
    hits: List[Tuple[str, int, str, str, str]] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for code, rx in compiled:
                m = rx.search(line)
                if m:
                    snippet = line.strip()
                    if len(snippet) > 110:
                        snippet = snippet[:107] + "..."
                    hits.append((path.name, lineno, code, m.group(0), snippet))
    return hits


def scan_stage2_section_aware(
    files: List[Path],
    patterns: List[Tuple[str, str]],
) -> Tuple[List[Tuple[str, int, str, str, str]], int]:
    """
    Section-aware Stage 2 prose scanner:
    - Skips LaTeX preamble (before \\begin{document} if present), comments, and code blocks.
    - Suppresses D2/D5 false positives inside dedicated Limitations / Weaknesses / AI Report sections.
    Returns (hits, suppressed_count).
    """
    compiled = [(code, re.compile(pat, re.IGNORECASE)) for code, pat in patterns]
    hits: List[Tuple[str, int, str, str, str]] = []
    suppressed = 0

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        is_tex = path.suffix.lower() == ".tex"
        has_begin_doc = is_tex and any(r"\begin{document}" in ln for ln in lines)

        in_body = not has_begin_doc
        in_code_env = False
        in_md_fence = False
        in_limitation_section = False

        for lineno, line in enumerate(lines, start=1):
            stripped = line.strip()

            if has_begin_doc and not in_body:
                if r"\begin{document}" in line:
                    in_body = True
                continue

            if is_tex:
                if stripped.startswith("%"):
                    continue
                if CODE_ENV_START_RX.search(line):
                    in_code_env = True
                    continue
                if in_code_env:
                    if CODE_ENV_END_RX.search(line):
                        in_code_env = False
                    continue
                m_sec = TEX_SECTION_RX.search(line)
                if m_sec:
                    in_limitation_section = bool(LIMITATION_SECTION_RX.search(m_sec.group(1)))
            else:
                if stripped.startswith("```"):
                    in_md_fence = not in_md_fence
                    continue
                if in_md_fence:
                    continue
                m_sec = MD_SECTION_RX.match(line)
                if m_sec:
                    in_limitation_section = bool(LIMITATION_SECTION_RX.search(m_sec.group(1)))

            for code, rx in compiled:
                m = rx.search(line)
                if not m:
                    continue
                if in_limitation_section and code in LIMITATION_EXEMPT_CODES:
                    suppressed += 1
                    continue
                snippet = stripped if len(stripped) <= 110 else stripped[:107] + "..."
                hits.append((path.name, lineno, code, m.group(0), snippet))

    return hits, suppressed


def check_plan_live_rules(plan_path: Optional[Path]) -> Tuple[List[str], List[str]]:
    """Verify Section 0 of 00_plan.md has no unextracted or unverified official contest rules."""
    if not plan_path:
        return [], []
    if not plan_path.is_file():
        return [f"[PLAN_MISSING] 00_plan.md not found at: {plan_path}"], []

    text = plan_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    in_sec0 = False
    sec0_found = False
    fails: List[str] = []
    info: List[str] = []

    for lineno, line in enumerate(lines, start=1):
        if re.match(r"^\s*##\s*0\.", line):
            in_sec0 = True
            sec0_found = True
            continue
        if in_sec0 and re.match(r"^\s*##\s*[1-9]\.", line):
            break
        if in_sec0:
            if "[EXTRACT FROM 00_problem/]" in line or "[待核验]" in line:
                fails.append(
                    f"[UNVERIFIED_CONTEST_RULE] {plan_path.name}:{lineno} still unresolved | {line.strip()[:95]}"
                )

    if not sec0_found:
        info.append(f"  - Note: No '## 0.' Live Official Rules section found in {plan_path.name}")
    else:
        info.append(f"  - Checked Live Official Rules in {plan_path.name}")
    return fails, info


def validate_handoff(
    handoff_path: Path,
    project_root: Optional[Path] = None,
    max_lines: int = 80,
) -> Tuple[List[str], List[str]]:
    """Enforce O(1) handoff.md relay contract: <=max_lines, zero fenced code blocks, valid pointers."""
    fails: List[str] = []
    info: List[str] = []
    if not handoff_path.is_file():
        return [f"[HANDOFF_MISSING] File not found: {handoff_path}"], info

    root = project_root.resolve() if project_root else handoff_path.resolve().parent
    lines = handoff_path.read_text(encoding="utf-8", errors="replace").splitlines()
    info.append(f"  - File: {handoff_path} | Lines: {len(lines)}/{max_lines}")

    if len(lines) > max_lines:
        fails.append(f"[HANDOFF_BLOAT] {handoff_path.name} has {len(lines)} lines (hard cap <= {max_lines}). Overwrite compactly!")

    joined = "\n".join(lines)
    if "```" in joined:
        fails.append(f"[HANDOFF_CODE_PASTE] {handoff_path.name} contains fenced code blocks (```). Store file pointers only!")

    for required in ("Current Step", "Next Role"):
        if required.lower() not in joined.lower():
            fails.append(f"[HANDOFF_FIELD] Missing required header '{required}' in {handoff_path.name}")

    ptr_rx = re.compile(r"`((?:00_problem|01_data|02_src|03_outputs|04_paper)/[^`\s*<>]+|(?:00_plan|01_log)\.md)`")
    checked: Set[str] = set()
    for m in ptr_rx.finditer(joined):
        rel = m.group(1).strip()
        if rel in checked:
            continue
        checked.add(rel)
        if not (root / rel).exists():
            fails.append(f"[HANDOFF_BROKEN_PTR] Referenced path does not exist: '{rel}' (under {root})")
    info.append(f"  - Verified {len(checked)} project pointer(s) under {root}")

    # If relay has moved to Step 2+, automatically verify 00_plan.md Sec. 0 has no unconfirmed rules
    m_step = re.search(r"Current Step\*{0,2}:\s*`?Step\s*([2-6])", joined, re.IGNORECASE)
    plan_file = root / "00_plan.md"
    if m_step and plan_file.is_file():
        p_fails, p_info = check_plan_live_rules(plan_file)
        fails.extend(p_fails)
        info.extend(p_info)

    return fails, info


def render_pdf_pages(pdf_path: Path, out_dir: Path, dpi: int = 150) -> Tuple[List[Path], Optional[str]]:
    """Render each PDF page to PNG for multimodal visual page-by-page inspection."""
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        try:
            import pymupdf as fitz  # type: ignore
        except ImportError:
            import fitz  # type: ignore

        doc = fitz.open(str(pdf_path))
        paths: List[Path] = []
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        for idx, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=mat)
            p = out_dir / f"page_{idx:02d}.png"
            pix.save(str(p))
            paths.append(p)
        doc.close()
        return paths, None
    except Exception:
        pass

    try:
        from pdf2image import convert_from_path  # type: ignore

        images = convert_from_path(str(pdf_path), dpi=dpi)
        paths = []
        for idx, img in enumerate(images, start=1):
            p = out_dir / f"page_{idx:02d}.png"
            img.save(str(p), "PNG")
            paths.append(p)
        return paths, None
    except Exception:
        pass

    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        prefix = out_dir / "page"
        res = subprocess.run(
            [pdftoppm, "-png", "-r", str(dpi), str(pdf_path), str(prefix)],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            return sorted(out_dir.glob("page-*.png")), None

    gs = shutil.which("gswin64c") or shutil.which("gs")
    if gs:
        pattern = str(out_dir / "page_%02d.png")
        res = subprocess.run(
            [gs, "-dNOPAUSE", "-dBATCH", "-sDEVICE=png16m", f"-r{dpi}", f"-sOutputFile={pattern}", str(pdf_path)],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            return sorted(out_dir.glob("page_*.png")), None

    return [], "No PDF rasterizer found (tried PyMuPDF, pdf2image, pdftoppm, ghostscript)."


def check_latex_refs_and_figs(
    files: List[Path],
    figs_dir: Optional[Path],
) -> Tuple[List[str], List[str]]:
    hard_fails: List[str] = []
    warnings: List[str] = []

    labels: Set[str] = set()
    refs: List[Tuple[str, int, str]] = []
    included_figs: List[Tuple[str, int, str]] = []

    label_rx = re.compile(r"\\label\{([^}]+)\}")
    ref_rx = re.compile(r"\\(?:eq|auto|c|C)?ref\{([^}]+)\}")
    tex_img_rx = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
    md_img_rx = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if path.suffix.lower() == ".tex" and line.lstrip().startswith("%"):
                continue
            for m in label_rx.finditer(line):
                labels.add(m.group(1).strip())
            for m in ref_rx.finditer(line):
                for key in m.group(1).split(","):
                    refs.append((path.name, lineno, key.strip()))
            for m in tex_img_rx.finditer(line):
                included_figs.append((path.name, lineno, m.group(1).strip()))
            for m in md_img_rx.finditer(line):
                included_figs.append((path.name, lineno, m.group(1).strip()))

    for fname, lineno, key in refs:
        if key and key not in labels:
            hard_fails.append(f"[BROKEN_REF] {fname}:{lineno} references undefined label '{key}'")

    if figs_dir and figs_dir.is_dir():
        disk_stems = {
            p.stem for p in figs_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".pdf", ".png", ".eps", ".svg"}
        }
        used_stems = {Path(raw).stem for _, _, raw in included_figs}

        for fname, lineno, raw in included_figs:
            stem = Path(raw).stem
            if stem not in disk_stems:
                warnings.append(f"[FIG_NOT_IN_FIGS_DIR] {fname}:{lineno} includes '{raw}' (stem '{stem}' not in {figs_dir})")

        for stem in sorted(disk_stems - used_stems):
            warnings.append(f"[UNUSED_FIG] Figure '{stem}' exists in {figs_dir} but is not included in manuscript")

    return hard_fails, warnings


def check_latex_log(log_path: Optional[Path]) -> Tuple[List[str], List[str]]:
    if not log_path:
        return [], []
    if not log_path.is_file():
        return [], [f"[LOG_MISSING] Compile log not found at {log_path}"]

    hard_fails: List[str] = []
    warnings: List[str] = []
    text = log_path.read_text(encoding="utf-8", errors="replace")

    for lineno, line in enumerate(text.splitlines(), start=1):
        s = line.strip()
        if "Undefined control sequence" in s or s.startswith("! "):
            hard_fails.append(f"[LATEX_ERROR] {log_path.name}:{lineno} {s[:110]}")
        elif re.search(r"LaTeX Warning:\s*(?:Reference|Citation)\s+`[^']+'\s+.*undefined", s):
            hard_fails.append(f"[LATEX_UNDEF] {log_path.name}:{lineno} {s[:110]}")
        else:
            m = re.search(r"Overfull \\hbox \(([0-9.]+)pt too wide\)", s)
            if m and float(m.group(1)) >= 10.0:
                warnings.append(f"[OVERFULL_HBOX] {log_path.name}:{lineno} {s[:110]}")

    return hard_fails, warnings


def check_pdf_metadata(pdf_path: Optional[Path], ban_terms: List[str]) -> Tuple[List[str], List[str], List[str]]:
    if not pdf_path:
        return [], [], []
    if not pdf_path.is_file():
        return [], [f"[PDF_MISSING] Compiled PDF not found at {pdf_path}"], []

    hard_fails: List[str] = []
    warnings: List[str] = []
    info_lines: List[str] = []
    raw = pdf_path.read_bytes()

    page_count: Optional[int] = None
    metadata_fields: List[Tuple[str, str]] = []
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(pdf_path))
        page_count = len(reader.pages)
        if reader.metadata:
            for k, v in reader.metadata.items():
                if v:
                    metadata_fields.append((str(k), str(v)))
    except Exception:
        pages = re.findall(rb"/Type\s*/Page\b(?!s)", raw)
        if pages:
            page_count = len(pages)
        for key in (b"Author", b"Title", b"Subject", b"Keywords", b"Creator"):
            for m in re.finditer(rb"/" + key + rb"\s*\(([^)]{1,200})\)", raw):
                val = m.group(1).decode("latin-1", errors="replace").strip()
                if val:
                    metadata_fields.append(("/" + key.decode(), val))

    info_lines.append(f"  - PDF: {pdf_path.name} | Estimated Pages: {page_count if page_count is not None else 'unknown'}")
    for k, v in metadata_fields:
        info_lines.append(f"  - Metadata {k}: {v}")
        if k.lower().endswith("author") and v.strip():
            warnings.append(f"[PDF_META_AUTHOR] Non-empty PDF /Author field: '{v}' (verify anonymity rules)")
        for term in ban_terms:
            if term.lower() in v.lower():
                hard_fails.append(f"[PDF_META_BAN] PDF metadata {k} contains banned term '{term}': '{v}'")
        if re.search(r"(?:[A-Za-z]:\\Users\\|/Users/|/home/)", v):
            hard_fails.append(f"[PDF_META_PATH] PDF metadata {k} leaks local path: '{v}'")

    return hard_fails, warnings, info_lines


def check_src_paths(src_dir: Optional[Path], ban_terms: List[str]) -> List[str]:
    if not src_dir or not src_dir.is_dir():
        return []
    src_files = sorted(
        p for p in src_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".py", ".m", ".r", ".jl", ".sh"}
    )
    pats = list(PATH_LEAK_PATTERNS)
    for term in ban_terms:
        pats.append(("SRC_BAN", re.escape(term)))
    hits = scan_patterns(src_files, pats)
    return [
        f"[{code}] {fname}:{lineno} matched '{matched}' | {snippet}"
        for fname, lineno, code, matched, snippet in hits
    ]


def check_metrics_sync_freshness(target: Path, metrics_dir: Optional[Path]) -> List[str]:
    if not metrics_dir or not metrics_dir.is_dir():
        return []
    paper_dir = target if target.is_dir() else target.parent
    fails: List[str] = []

    json_files = list(metrics_dir.glob("*.json"))
    gen_metrics = paper_dir / "generated_metrics.tex"
    if gen_metrics.is_file() and json_files:
        newest_json = max(json_files, key=lambda p: p.stat().st_mtime)
        if newest_json.stat().st_mtime > gen_metrics.stat().st_mtime + 1.0:
            fails.append(
                f"[STALE_METRICS_TEX] '{gen_metrics.name}' is older than '{newest_json.name}'. Re-run sync_metrics.py!"
            )

    tables_dir = paper_dir / "generated_tables"
    if tables_dir.is_dir():
        for csv_file in metrics_dir.glob("*.csv"):
            gen_tbl = tables_dir / f"{csv_file.stem}.tex"
            if gen_tbl.is_file() and csv_file.stat().st_mtime > gen_tbl.stat().st_mtime + 1.0:
                fails.append(
                    f"[STALE_TABLE_TEX] 'generated_tables/{gen_tbl.name}' is older than '{csv_file.name}'. Re-run sync_metrics.py!"
                )
    return fails


def summarize_metrics(metrics_dir: Optional[Path]) -> List[str]:
    if not metrics_dir or not metrics_dir.is_dir():
        return ["[WARN] Metrics directory not found or not provided; manual numeric traceability required."]
    lines: List[str] = []
    files = sorted(p for p in metrics_dir.iterdir() if p.is_file() and p.suffix.lower() in {".json", ".csv"})
    if not files:
        return [f"[WARN] No .json or .csv metric files found in {metrics_dir}"]
    for p in files:
        if p.suffix.lower() == ".json":
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                keys = list(data.keys())[:8] if isinstance(data, dict) else [f"list(len={len(data)})"]
                lines.append(f"  - {p.name}: keys={keys}")
            except Exception as exc:
                lines.append(f"  - {p.name}: [JSON PARSE ERROR: {exc}]")
        else:
            row_count = max(0, len(p.read_text(encoding="utf-8", errors="replace").splitlines()) - 1)
            lines.append(f"  - {p.name}: CSV ({row_count} data rows)")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic Stage 1+2 audit scanner, PDF page renderer, plan-rule gate, and handoff validator."
    )
    parser.add_argument("paper", nargs="?", default=None, help="Path to manuscript .tex/.md file or directory")
    parser.add_argument("--metrics-dir", type=str, default=None, help="Path to 03_outputs/metrics")
    parser.add_argument("--figs-dir", type=str, default=None, help="Path to 03_outputs/figs")
    parser.add_argument("--src-dir", type=str, default=None, help="Path to 02_src/ for local-path/anonymity scan")
    parser.add_argument("--plan", type=str, default=None, help="Path to 00_plan.md to verify live contest rules")
    parser.add_argument("--log", type=str, default=None, help="Path to LaTeX compile .log file")
    parser.add_argument("--pdf", type=str, default=None, help="Path to compiled .pdf for metadata/page check")
    parser.add_argument("--render-pdf", type=str, default=None, help="Output dir to rasterize PDF pages to PNGs")
    parser.add_argument("--check-handoff", type=str, default=None, help="Validate O(1) handoff.md relay contract")
    parser.add_argument("--max-lines", type=int, default=80, help="Hard line cap for handoff.md (default: 80)")
    parser.add_argument("--project-root", type=str, default=None, help="Project root for verifying handoff pointers")
    parser.add_argument("--ban-terms", type=str, default="", help="Comma-separated custom anonymity terms to ban")
    args = parser.parse_args()

    if not args.paper and not args.check_handoff and not args.plan:
        parser.error("Provide a manuscript path, --check-handoff <handoff.md>, and/or --plan <00_plan.md>.")

    total_hard_fails = 0
    print("=" * 72)
    print("MATH MODELING FRONTIER AUDIT & RELAY VALIDATOR (v1.1)")
    print("=" * 72)

    # ---- OPTIONAL: O(1) HANDOFF RELAY CHECK ----
    if args.check_handoff:
        h_fails, h_info = validate_handoff(
            Path(args.check_handoff),
            Path(args.project_root) if args.project_root else None,
            max_lines=args.max_lines,
        )
        print(f"\n[HANDOFF CONTRACT CHECK] (Hard Cap <= {args.max_lines} lines | Pointer-Only)")
        for line in h_info:
            print(line)
        if not h_fails:
            print("  -> PASS (O(1) relay contract intact)")
        else:
            total_hard_fails += len(h_fails)
            for msg in h_fails:
                print(f"  [HARD FAIL]{msg}")

    # ---- OPTIONAL: 00_plan.md LIVE RULE CONFIRMATION CHECK ----
    if args.plan:
        p_fails, p_info = check_plan_live_rules(Path(args.plan))
        print("\n[LIVE CONTEST RULES CHECK] (00_plan.md Sec. 0)")
        for line in p_info:
            print(line)
        if not p_fails:
            print("  -> PASS (all live official rules confirmed)")
        else:
            total_hard_fails += len(p_fails)
            for msg in p_fails:
                print(f"  [HARD FAIL]{msg}")

    # ---- MANUSCRIPT AUDIT ----
    if args.paper:
        target = Path(args.paper)
        files = collect_manuscript_files(target)
        if not files:
            print(f"[ERROR] No .tex or .md files found at: {target}")
            return 1

        ban_terms = [t.strip() for t in args.ban_terms.split(",") if t.strip()]
        stage1_patterns = list(INTERNAL_LEAK_PATTERNS) + list(PATH_LEAK_PATTERNS) + list(PLACEHOLDER_PATTERNS)
        for term in ban_terms:
            stage1_patterns.append(("ANONYMITY_BAN", re.escape(term)))

        s1_hits = scan_patterns(files, stage1_patterns)
        ref_fails, fig_warns = check_latex_refs_and_figs(files, Path(args.figs_dir) if args.figs_dir else None)
        src_fails = check_src_paths(Path(args.src_dir) if args.src_dir else None, ban_terms)
        sync_fails = check_metrics_sync_freshness(target, Path(args.metrics_dir) if args.metrics_dir else None)
        log_fails, log_warns = check_latex_log(Path(args.log) if args.log else None)
        pdf_path = Path(args.pdf) if args.pdf else None
        pdf_fails, pdf_warns, pdf_info = check_pdf_metadata(pdf_path, ban_terms)

        all_extra_fails = ref_fails + src_fails + sync_fails + log_fails + pdf_fails
        all_warns = fig_warns + log_warns + pdf_warns
        total_hard_fails += len(s1_hits) + len(all_extra_fails)

        print(f"\n[STAGE 1] Hard Facts, Anti-Leak, Anonymity, Refs, Code, Sync, Log & PDF ({len(files)} file(s))")
        if not s1_hits and not all_extra_fails:
            print("  -> PASS (0 hard failures)")
        else:
            for fname, lineno, code, matched, snippet in s1_hits:
                print(f"  [HARD FAIL][{code}] {fname}:{lineno} matched '{matched}' | {snippet}")
            for msg in all_extra_fails:
                print(f"  [HARD FAIL]{msg}")

        if all_warns:
            print("\n[STAGE 1 WARNINGS]")
            for w in all_warns:
                print(f"  {w}")

        if pdf_info:
            print("\n[STAGE 1 PDF SUMMARY]")
            for line in pdf_info:
                print(line)

        if args.render_pdf and pdf_path and pdf_path.is_file():
            pages, err = render_pdf_pages(pdf_path, Path(args.render_pdf))
            print("\n[STAGE 1 PDF PAGE RENDERER]")
            if err:
                print(f"  [WARN] {err}")
            else:
                print(f"  -> Rendered {len(pages)} page(s) to {args.render_pdf} for visual inspection:")
                for p in pages[:10]:
                    print(f"     {p}")
                if len(pages) > 10:
                    print(f"     ... ({len(pages) - 10} more pages)")

        print("\n[STAGE 1 METRICS INVENTORY FOR 10-POINT SPOT CHECK]")
        for line in summarize_metrics(Path(args.metrics_dir) if args.metrics_dir else None):
            print(line)

        s2_hits, suppressed = scan_stage2_section_aware(files, DEFENSIVE_PATTERNS + AI_SLOP_PATTERNS)
        print("\n[STAGE 2 SIGNALS] Section-Aware Defensive (D1-D5), AI-Slop & Cheap Tables")
        if suppressed > 0:
            print(f"  (Exempted {suppressed} legitimate D2/D5 match(es) inside dedicated Limitations/AI-Report sections)")
        if not s2_hits:
            print("  -> CLEAN (0 prose triggers; still perform semantic Stage 2 audit)")
        else:
            print(f"  -> Found {len(s2_hits)} signal(s) for surgical review:")
            for fname, lineno, code, matched, snippet in s2_hits:
                print(f"  [SIGNAL][{code}] {fname}:{lineno} matched '{matched}' | {snippet}")

    print("\n" + "=" * 72)
    if total_hard_fails > 0:
        print(f"RESULT: FAIL ({total_hard_fails} blocking issue(s)). Fix before proceeding.")
        return 2
    print("RESULT: AUTOMATED CHECKS PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
