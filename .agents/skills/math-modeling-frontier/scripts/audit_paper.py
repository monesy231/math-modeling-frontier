#!/usr/bin/env python3
"""
Deterministic Stage 1 (Hard Compliance), Section-Aware Stage 2 (Defensive /
AI-Slop / Cheap-Table Signals), PDF Page Renderer & Full Math-Token Scanner,
Field-by-Field 00_plan.md Live-Rule & Page-Limit Gate, Cross-Artifact Freshness
& Orphan-Table Guard, Deliverable CSV/HTML Payload Auditor, and O(1) `handoff.md`
Relay Validator (v1.6).

Exit code:
  0 = Stage 1 / Handoff / Plan checks PASS
  2 = Blocking hard failures detected (missing final artifacts, failed PDF render,
      over-page-limit PDF, unverified contest rules, orphan/stale tables, leaks,
      broken refs, unsealed raw files, or broken CSV/HTML deliverables)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

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

# Stage 1 HARD FAIL: Unfinished placeholders & unremoved official template prompts
PLACEHOLDER_PATTERNS: List[Tuple[str, str]] = [
    ("PLACEHOLDER", r"\b(?:TODO|TBD|FIXME|XXX)\b"),
    ("PLACEHOLDER", r"\[(?:待核验|待补充|待汇总|待确认|待填写|待更新|待定)\]"),
    ("PLACEHOLDER", r"(?:待(?:队长|队员|团队|人工)(?:汇总|确认|核实|补充|填写)|仍待(?:队长|队员|团队)?汇总)"),
    ("PLACEHOLDER", r"\[\?\?\]"),
    ("TEMPLATE_INSTRUCTION_LEAK", r"引用块（以\s*`?>`?\s*开头）是填写提示"),
    ("TEMPLATE_INSTRUCTION_LEAK", r"定稿时请删除"),
    ("TEMPLATE_INSTRUCTION_LEAK", r"（如：O1\s*爆品早知道）"),
    ("TEMPLATE_INSTRUCTION_LEAK", r"（例：某某大模型"),
    ("TEMPLATE_INSTRUCTION_LEAK", r"（采纳\s*/\s*修改后采纳\s*/\s*弃用）"),
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
    r"|优缺点|局限|不足|模型评价|模型改进|讨论与展望|人工智能使用|纠错记录|小结|需要说明的限制)",
    re.IGNORECASE,
)
LIMITATION_EXEMPT_CODES: Set[str] = {"D2_NON_CLAIM", "D5_SELF_SABOTAGE"}
TEX_SECTION_RX = re.compile(r"\\(?:sub){0,2}section\*?(?:\[[^\]]*\])?\{([^}]+)\}")
MD_SECTION_RX = re.compile(r"^\s{0,3}#{1,3}\s+(.+?)\s*$")
CODE_ENV_START_RX = re.compile(r"\\begin\{(?:verbatim|lstlisting|minted)\*?\}")
CODE_ENV_END_RX = re.compile(r"\\end\{(?:verbatim|lstlisting|minted)\*?\}")

# Mandatory field-by-field live official rule schema for 00_plan.md Sec. 0
REQUIRED_PLAN_RULE_FIELDS: List[Tuple[str, str]] = [
    ("Format & Template", r"(?:Format\s*&\s*Template|格式|模板)"),
    ("Deadline / Window", r"(?:Deadline|Window|截止|赛程|时间)"),
    ("Hard Page / Word Limit", r"(?:Page|Word\s*Limit|页数|字数)"),
    ("Anonymity & Metadata", r"(?:Anonymity|Metadata|匿名|盲审|元数据)"),
    ("AI Declaration Policy", r"(?:AI\s*(?:Declaration|Use|Usage|Policy)|人工智能|AI\s*声明|AI\s*政策)"),
    ("Required Extras", r"(?:Required\s*Extras|Memo|附件|代码|查重)"),
]
RULE_PLACEHOLDER_RX = re.compile(
    r"(?:\[EXTRACT FROM 00_problem/\]|\[待核验\]|\[待补充\]|^\s*(?:TBD|TODO|FIXME|XXX|N/A|NA|None|-|--|无)\s*$)",
    re.IGNORECASE,
)
RULE_SOURCE_RX = re.compile(
    r"(?:source\s*[:：]|from\s+|verified|not\s+applicable|n/a\s*\(|来源|依据|已核实|不适用|通知|章程|指南|官网|官方|notice|brochure|instructions?|rules?|guideline|https?://|\.(?:pdf|docx?|txt|md|html?)\b|00_problem/)",
    re.IGNORECASE,
)


def collect_manuscript_files(
    target: Path,
    project_root: Optional[Path] = None,
    extra_companions: Optional[List[str]] = None,
) -> List[Path]:
    files: List[Path] = []
    if target.is_file():
        files.append(target)
    elif target.is_dir():
        files.extend(
            sorted(
                p for p in target.rglob("*")
                if p.is_file() and p.suffix.lower() in {".tex", ".md"}
            )
        )

    # Auto-discover root-level official companion deliverables (作品说明单*.md, AI协作记录*.md)
    t_res = target.resolve()
    root_cand: Optional[Path] = project_root.resolve() if project_root else None
    if root_cand is None:
        if t_res.is_file() and t_res.parent.name == "04_paper":
            root_cand = t_res.parent.parent
        elif t_res.is_dir() and t_res.name == "04_paper":
            root_cand = t_res.parent

    seen_resolved = {p.resolve() for p in files}
    if root_cand and root_cand.is_dir():
        for pat in ("作品说明单*.md", "AI协作记录*.md"):
            for comp in sorted(root_cand.glob(pat)):
                if comp.is_file() and "模板" not in comp.name and comp.resolve() not in seen_resolved:
                    files.append(comp)
                    seen_resolved.add(comp.resolve())

    for raw_c in extra_companions or []:
        cp = Path(raw_c)
        if cp.is_file() and cp.resolve() not in seen_resolved:
            files.append(cp)
            seen_resolved.add(cp.resolve())

    return files


def _check_markdown_inline_math_balance(path: Path, text: str) -> List[str]:
    """
    Detect unbalanced inline '$' math delimiters in Markdown files while ignoring
    fenced code blocks, standalone/inline '$$...$$' display math, HTML comments,
    inline backtick code spans, and escaped '\\$'.
    """
    if path.suffix.lower() != ".md":
        return []

    fails: List[str] = []
    lines = text.splitlines()
    in_fence = False
    in_display_math = False
    in_html_comment = False

    para_lines: List[str] = []
    para_start = 1

    def check_block(raw_block: str, start_line: int) -> None:
        cleaned = re.sub(r"<!--.*?-->", "", raw_block, flags=re.DOTALL)
        cleaned = re.sub(r"``[^`]+``", "", cleaned)
        cleaned = re.sub(r"`[^`\n]*`", "", cleaned)
        cleaned = re.sub(r"\$\$[^$]+\$\$", "", cleaned)
        cleaned = cleaned.replace(r"\$", "")
        if cleaned.count("$") % 2 != 0:
            snippet = " ".join(raw_block.strip().split())
            if len(snippet) > 110:
                snippet = snippet[:107] + "..."
            fails.append(
                f"[MD_UNBALANCED_MATH] {path.name}:{start_line} has unbalanced inline '$' math delimiter | {snippet}"
            )

    def flush_para() -> None:
        nonlocal para_lines
        if para_lines:
            check_block("\n".join(para_lines), para_start)
            para_lines = []

    standalone_block_rx = re.compile(r"^(?:#{1,6}\s+|\|.*|\s*[-*+]\s+|\s*\d+\.\s+|\s*>\s*)")

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()

        if in_html_comment:
            if "-->" in stripped:
                in_html_comment = False
            continue
        if stripped.startswith("<!--") and "-->" not in stripped:
            flush_para()
            in_html_comment = True
            continue

        if stripped.startswith("```") or stripped.startswith("~~~"):
            flush_para()
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        if stripped == "$$":
            flush_para()
            in_display_math = not in_display_math
            continue
        if in_display_math:
            continue

        if stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) >= 4:
            flush_para()
            continue

        if not stripped or stripped in ("---", "***", "___"):
            flush_para()
            continue

        if standalone_block_rx.match(line):
            flush_para()
            check_block(line, lineno)
            continue

        if not para_lines:
            para_start = lineno
        para_lines.append(line)

    flush_para()
    if in_display_math:
        fails.append(f"[MD_UNBALANCED_MATH] {path.name}:EOF has unclosed '$$' display math block")
    return fails


def check_prose_integrity_and_companion_rules(
    files: List[Path],
) -> Tuple[List[str], List[str], List[str]]:
    """
    Check manuscript and companion deliverables for:
    1. [DEGENERATE_CHANGE] Self-contradictory '由 X 降至 X' / '从 X 升至 X' / 'increased/decreased from X to X'
       where start and end numbers are identical and units do not change.
    2. [MD_UNBALANCED_MATH] Unclosed inline '$' or '$$' math delimiters in Markdown files.
    3. [SUMMARY_OVER_60_CHARS] Official '## 02 一句话概述' section exceeding the 60-character limit.
    4. [REGISTRATION_PLACEHOLDER] Pre-submission team name / member count reminders in 作品说明单.
    """
    hard_fails: List[str] = []
    warnings: List[str] = []
    info_lines: List[str] = []

    zh_unit_pat = r"(?:m³|km|kg|ms|pp|h|s|d|%|万元|元|张|票|批|个|次|天|秒|小时)?"
    zh_degen_rx = re.compile(
        rf"(?:由|从)\s*\**(?<![\d.])([+-]?\d[\d,]*(?:\.\d+)?%?)\**\s*({zh_unit_pat})\s*"
        rf"(?:降至|升至|增至|跌至|提高到|提高至|下降到|下降至|减少到|减少至|增加到|增加至|跃升至|回落至|缩减至|改善至)\s*"
        rf"\**\1\**(?![\d.])\s*({zh_unit_pat})"
    )
    en_degen_rx = re.compile(
        r"\b(?:increased|decreased|dropped|rose|fell|improved|reduced|grew|declined|shifted|changed)\s+"
        r"from\s+\**(?<![\d.])([+-]?\d[\d,]*(?:\.\d+)?%?)\**(?:\s*([a-zA-Z%]{1,6}))?\s+"
        r"to\s+\**\1\**(?![\d.])(?:\s*([a-zA-Z%]{1,6}))?",
        re.IGNORECASE,
    )
    reg_placeholder_rx = re.compile(
        r"(?:提交前按官方报名表填写|按实际报名人数填写|（含队长，1[—–\-]4\s*人）)"
    )
    summary_sec_rx = re.compile(r"^\s*##\s*0?2\s+一句话概述\s*$")
    any_h2_rx = re.compile(r"^\s*##\s+")

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        hard_fails.extend(_check_markdown_inline_math_balance(path, text))
        lines = text.splitlines()

        for lineno, line in enumerate(lines, start=1):
            for rx in (zh_degen_rx, en_degen_rx):
                for m in rx.finditer(line):
                    u1 = (m.group(2) or "").strip()
                    u2 = (m.group(3) or "").strip()
                    if u1 and u2 and u1.lower() != u2.lower():
                        continue
                    snippet = line.strip()
                    if len(snippet) > 110:
                        snippet = snippet[:107] + "..."
                    hard_fails.append(
                        f"[DEGENERATE_CHANGE] {path.name}:{lineno} self-contradictory identical transition '{m.group(0)}' | {snippet}"
                    )

            m_reg = reg_placeholder_rx.search(line)
            if m_reg:
                warnings.append(
                    f"[REGISTRATION_PLACEHOLDER] {path.name}:{lineno} contains team registration reminder '{m_reg.group(0)}' (fill actual team name & headcount before final upload)"
                )

        # Check '## 02 一句话概述' <= 60 chars if present
        for idx, line in enumerate(lines):
            if summary_sec_rx.match(line):
                sec_lineno = idx + 1
                body_parts: List[str] = []
                for sub_line in lines[idx + 1:]:
                    if any_h2_rx.match(sub_line):
                        break
                    s = sub_line.strip()
                    if not s or s.startswith(">") or s.startswith("---"):
                        continue
                    body_parts.append(s.replace("**", ""))
                summary_text = " ".join(body_parts).strip()
                char_len = len(summary_text)
                if char_len == 0:
                    hard_fails.append(
                        f"[SUMMARY_EMPTY] {path.name}:{sec_lineno} '02 一句话概述' is empty"
                    )
                elif char_len > 60:
                    hard_fails.append(
                        f"[SUMMARY_OVER_60_CHARS] {path.name}:{sec_lineno} '02 一句话概述' has {char_len} chars (official cap <= 60): '{summary_text}'"
                    )
                else:
                    info_lines.append(
                        f"  - Executive Summary ('02 一句话概述' in {path.name}): {char_len}/60 chars"
                    )

    return hard_fails, warnings, info_lines


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
    """
    Strictly validate Section 0 of 00_plan.md field-by-field:
    - Section '## 0.' MUST exist.
    - All 6 mandatory contest rule fields MUST exist with non-placeholder values
      and an explicit source/official-notice or verified-N/A confirmation.
    """
    if not plan_path:
        return [], []
    if not plan_path.is_file():
        return [f"[PLAN_MISSING] 00_plan.md not found at: {plan_path}"], []

    text = plan_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    sec0_lines: List[Tuple[int, str]] = []
    in_sec0 = False
    sec0_found = False

    for lineno, line in enumerate(lines, start=1):
        if re.match(r"^\s*##\s*0\.", line):
            in_sec0 = True
            sec0_found = True
            continue
        if in_sec0 and re.match(r"^\s*##\s*[1-9]\.", line):
            break
        if in_sec0:
            sec0_lines.append((lineno, line))

    fails: List[str] = []
    info: List[str] = []

    if not sec0_found:
        return [f"[PLAN_SEC0_MISSING] {plan_path.name} is missing mandatory '## 0.' Live Official Rules section."], info

    # Parse bullet lines of the form "- **Field**: value" or "- Field: value"
    parsed_entries: List[Tuple[int, str, str]] = []
    bullet_rx = re.compile(r"^\s*[-*]\s*\*{0,2}([^:*：]+?)\*{0,2}\s*[:：]\s*(.*)$")
    for lineno, line in sec0_lines:
        m = bullet_rx.match(line)
        if m:
            parsed_entries.append((lineno, m.group(1).strip(), m.group(2).strip()))

    matched_count = 0
    for canonical_name, key_pat in REQUIRED_PLAN_RULE_FIELDS:
        rx = re.compile(key_pat, re.IGNORECASE)
        match_entry = next((entry for entry in parsed_entries if rx.search(entry[1])), None)
        if not match_entry:
            fails.append(f"[MISSING_CONTEST_RULE] {plan_path.name} Sec. 0 is missing required field '{canonical_name}'")
            continue

        matched_count += 1
        lineno, _, raw_val = match_entry
        val = raw_val.strip().strip("`").strip()
        if not val or RULE_PLACEHOLDER_RX.search(val):
            fails.append(
                f"[UNVERIFIED_CONTEST_RULE] {plan_path.name}:{lineno} '{canonical_name}' is empty or placeholder | {raw_val[:80]}"
            )
            continue
        if len(val) < 6:
            fails.append(
                f"[UNVERIFIED_CONTEST_RULE] {plan_path.name}:{lineno} '{canonical_name}' is too vague ('{val}'); state concrete rule + source"
            )
            continue
        if not RULE_SOURCE_RX.search(val):
            fails.append(
                f"[MISSING_RULE_SOURCE] {plan_path.name}:{lineno} '{canonical_name}' lacks explicit source or verified-N/A note | {val[:85]}"
            )

    info.append(f"  - Checked {matched_count}/{len(REQUIRED_PLAN_RULE_FIELDS)} mandatory rule field(s) in {plan_path.name} Sec. 0")
    return fails, info


def extract_plan_max_pages(plan_path: Optional[Path]) -> Optional[Tuple[int, str]]:
    """
    Extract an explicit hard page upper limit from `00_plan.md` Sec. 0's
    `Hard Page / Word Limit` bullet, returning `(max_pages, matched_phrase)` or `None`.
    """
    if not plan_path or not plan_path.is_file():
        return None
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    sec0_lines: List[str] = []
    in_sec0 = False
    for line in text.splitlines():
        if re.match(r"^\s*##\s*0\.", line):
            in_sec0 = True
            continue
        if in_sec0 and re.match(r"^\s*##\s*[1-9]\.", line):
            break
        if in_sec0:
            sec0_lines.append(line)
    if not sec0_lines:
        return None

    bullet_rx = re.compile(r"^\s*[-*]\s*\*{0,2}([^:*：]+?)\*{0,2}\s*[:：]\s*(.*)$")
    page_key_rx = re.compile(r"(?:Page|Word\s*Limit|页数|字数)", re.IGNORECASE)
    negation_rx = re.compile(
        r"(?:no\s+(?:strict\s+|hard\s+)?(?:page\s+)?(?:limit|cap)|unlimited|无(?:硬性)?(?:页数)?限制|不限页数|无页数上限)",
        re.IGNORECASE,
    )
    cap_rxs = [
        re.compile(
            r"(?:不超过|至多|不得超过|上限(?:为)?|最多|≤|<=|max(?:imum)?(?:\s+of)?|at\s+most|no\s+more\s+than|up\s+to|"
            r"(?:hard\s+)?(?:page\s+)?(?:cap|limit)(?:\s+of|\s*[:：])?)\s*(\d{1,3})\s*(?:页|pages?\b)",
            re.IGNORECASE,
        ),
        re.compile(
            r"(\d{1,3})\s*(?:页|pages?\b)\s*(?:以内|以下|上限|max\b|maximum\b|cap\b|limit\b)",
            re.IGNORECASE,
        ),
    ]
    for line in sec0_lines:
        m = bullet_rx.match(line)
        if not m or not page_key_rx.search(m.group(1)):
            continue
        val = m.group(2).strip()
        if negation_rx.search(val):
            return None
        for rx in cap_rxs:
            cm = rx.search(val)
            if cm:
                return int(cm.group(1)), cm.group(0).strip()
    return None


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

    ptr_rx = re.compile(
        r"`((?:00_problem|01_data|02_src|03_outputs|04_paper)/[^`\s*<>]+|"
        r"(?:00_plan|01_log|README)\.md|requirements\.txt|(?:作品说明单|AI协作记录)[^`\s*<>]*\.md)`"
    )
    checked: Set[str] = set()
    for m in ptr_rx.finditer(joined):
        rel = m.group(1).strip()
        if rel in checked:
            continue
        checked.add(rel)
        if not (root / rel).exists():
            fails.append(f"[HANDOFF_BROKEN_PTR] Referenced path does not exist: '{rel}' (under {root})")
    info.append(f"  - Verified {len(checked)} project pointer(s) under {root}")

    m_step = re.search(r"Current Step\*{0,2}\s*[:：]\s*`?(?:MM\s+)?Step\s*([2-6])", joined, re.IGNORECASE)
    plan_file = root / "00_plan.md"
    if m_step:
        p_fails, p_info = check_plan_live_rules(plan_file)
        fails.extend(p_fails)
        info.extend(p_info)

    return fails, info


def render_pdf_pages(pdf_path: Path, out_dir: Path, dpi: int = 150) -> Tuple[List[Path], Optional[str]]:
    """Render each PDF page to PNG for multimodal visual page-by-page inspection."""
    out_dir.mkdir(parents=True, exist_ok=True)
    # Auto-write .gitignore inside the preview directory so temporary PNGs never pollute git status / git add -A
    gitignore_path = out_dir / ".gitignore"
    if not gitignore_path.exists():
        try:
            gitignore_path.write_text("*\n", encoding="utf-8")
        except Exception:
            pass
    # Remove any stale page renders from previous runs
    for old_png in out_dir.glob("page*.png"):
        old_png.unlink(missing_ok=True)

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
        if not paths:
            return [], "PDF opened with 0 pages."
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
        if not paths:
            return [], "pdf2image produced 0 pages."
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
            rendered = sorted(out_dir.glob("page-*.png"))
            if rendered:
                return rendered, None

    gs = shutil.which("gswin64c") or shutil.which("gs")
    if gs:
        pattern = str(out_dir / "page_%02d.png")
        res = subprocess.run(
            [gs, "-dNOPAUSE", "-dBATCH", "-sDEVICE=png16m", f"-r{dpi}", f"-sOutputFile={pattern}", str(pdf_path)],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            rendered = sorted(out_dir.glob("page_*.png"))
            if rendered:
                return rendered, None

    return [], "PDF rasterization failed (no working PyMuPDF, pdf2image, pdftoppm, or ghostscript found)."


def check_latex_refs_and_figs(
    files: List[Path],
    figs_dir: Optional[Path],
) -> Tuple[List[str], List[str], List[str]]:
    hard_fails: List[str] = []
    warnings: List[str] = []
    info_lines: List[str] = []

    if figs_dir is not None and not figs_dir.is_dir():
        hard_fails.append(f"[ARTIFACT_DIR_MISSING] Figures directory not found: {figs_dir}")
        figs_dir = None

    labels: Set[str] = set()
    refs: List[Tuple[str, int, str]] = []
    included_figs: List[Tuple[str, int, str]] = []
    non_comment_lines: List[str] = []

    label_rx = re.compile(r"\\label\{([^}]+)\}")
    ref_rx = re.compile(r"\\(?:eq|auto|c|C)?ref\{([^}]+)\}")
    tex_img_rx = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
    md_img_rx = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if path.suffix.lower() == ".tex" and line.lstrip().startswith("%"):
                continue
            non_comment_lines.append(line)
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
        stem_to_filenames: Dict[str, List[str]] = {}
        for p in sorted(figs_dir.iterdir()):
            if p.is_file() and p.suffix.lower() in {".pdf", ".png", ".eps", ".svg"}:
                stem_to_filenames.setdefault(p.stem, []).append(p.name)
        disk_stems = set(stem_to_filenames.keys())
        used_stems = {Path(raw).stem for _, _, raw in included_figs}
        combined_text = "\n".join(non_comment_lines)

        for fname, lineno, raw in included_figs:
            stem = Path(raw).stem
            if stem not in disk_stems:
                warnings.append(f"[FIG_NOT_IN_FIGS_DIR] {fname}:{lineno} includes '{raw}' (stem '{stem}' not in {figs_dir})")

        cited_supp: List[str] = []
        for stem in sorted(disk_stems - used_stems):
            fnames = stem_to_filenames[stem]
            matched_fn = next(
                (
                    fn for fn in fnames
                    if re.search(rf"(?<![A-Za-z0-9_]){re.escape(fn)}(?![A-Za-z0-9_])", combined_text)
                ),
                None,
            )
            if matched_fn:
                cited_supp.append(matched_fn)
            else:
                warnings.append(f"[UNUSED_FIG] Figure '{stem}' exists in {figs_dir} but is not included in manuscript")
        if cited_supp:
            info_lines.append(f"  - Cited supplementary figure(s) by path: {', '.join(cited_supp)}")

    return hard_fails, warnings, info_lines


def check_latex_log(log_path: Optional[Path]) -> Tuple[List[str], List[str]]:
    if not log_path:
        return [], []
    if not log_path.is_file():
        return [f"[LOG_MISSING] Specified LaTeX compile log not found: {log_path}"], []

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


def check_pdf_metadata(
    pdf_path: Optional[Path],
    ban_terms: List[str],
    claim_sources: Optional[List[Tuple[str, str]]] = None,
    max_pages: Optional[int] = None,
    max_pages_source: Optional[str] = None,
) -> Tuple[List[str], List[str], List[str]]:
    if not pdf_path:
        return [], [], []
    if not pdf_path.is_file():
        return [f"[PDF_MISSING] Specified compiled PDF not found: {pdf_path}"], [], []

    hard_fails: List[str] = []
    warnings: List[str] = []
    info_lines: List[str] = []
    raw = pdf_path.read_bytes()

    page_count: Optional[int] = None
    metadata_fields: List[Tuple[str, str]] = []
    page_texts: List[Tuple[int, str]] = []
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(pdf_path))
        page_count = len(reader.pages)
        if reader.metadata:
            for k, v in reader.metadata.items():
                if v:
                    metadata_fields.append((str(k), str(v)))
        for idx, page in enumerate(reader.pages, start=1):
            try:
                page_texts.append((idx, page.extract_text() or ""))
            except Exception:
                pass
    except Exception:
        try:
            try:
                import pymupdf as fitz  # type: ignore
            except ImportError:
                import fitz  # type: ignore

            doc = fitz.open(str(pdf_path))
            page_count = len(doc)
            if doc.metadata:
                for k, v in doc.metadata.items():
                    if v:
                        metadata_fields.append((f"/{k.capitalize()}", str(v)))
            for idx, page in enumerate(doc, start=1):
                try:
                    page_texts.append((idx, page.get_text("text") or ""))
                except Exception:
                    pass
            doc.close()
        except Exception:
            pass

    if not page_count:
        pages = re.findall(rb"/Type\s*/Page\b(?!s)", raw)
        if pages:
            page_count = len(pages)
    if not metadata_fields:
        for key in (b"Author", b"Title", b"Subject", b"Keywords", b"Creator"):
            for m in re.finditer(rb"/" + key + rb"\s*\(([^)]{1,200})\)", raw):
                val = m.group(1).decode("latin-1", errors="replace").strip()
                if val:
                    metadata_fields.append(("/" + key.decode(), val))

    page_summary = str(page_count) if page_count is not None else "unknown"
    if max_pages is not None:
        page_summary += f" (hard limit <= {max_pages})"
    info_lines.append(f"  - PDF: {pdf_path.name} | Pages: {page_summary}")
    for k, v in metadata_fields:
        info_lines.append(f"  - Metadata {k}: {v}")
        if k.lower().endswith("author") and v.strip():
            warnings.append(f"[PDF_META_AUTHOR] Non-empty PDF /Author field: '{v}' (verify anonymity rules)")
        for term in ban_terms:
            if term.lower() in v.lower():
                hard_fails.append(f"[PDF_META_BAN] PDF metadata {k} contains banned term '{term}': '{v}'")
        if re.search(r"(?:[A-Za-z]:\\Users\\|/Users/|/home/)", v):
            hard_fails.append(f"[PDF_META_PATH] PDF metadata {k} leaks local path: '{v}'")

    # Scan extracted PDF page text for tofu replacement glyphs (\ufffd) and unrendered LaTeX macros
    # Note: (?![a-z]) intentionally catches merged wrapper tokens such as '\inI' (from '\in\mathcal{I}')
    # while ignoring lowercase path segments such as '\inputs' or '\init'.
    unrendered_latex_rx = re.compile(
        r"\\(?:frac|dfrac|tfrac|binom|sqrt|sum|prod|int|oint|iint|"
        r"mathbf|mathrm|mathbb|mathcal|mathscr|mathfrak|mathsf|mathtt|"
        r"textbf|textit|textrm|text|mbox|left|right|big|Big|bigg|Bigg|"
        r"toprule|midrule|bottomrule|cmidrule|multicolumn|multirow|"
        r"begin\s*\{|end\s*\{|includegraphics|label\s*\{|eqref\s*\{|autoref\s*\{|cref\s*\{|Cref\s*\{|"
        r"notin|subseteq|supseteq|subset|supset|cup|cap|setminus|emptyset|varnothing|"
        r"forall|exists|nexists|implies|impliedby|iff|mapsto|"
        r"rightarrow|leftarrow|leftrightarrow|Rightarrow|Leftarrow|Leftrightarrow|"
        r"leq|geq|neq|approx|equiv|cong|sim|simeq|propto|asymp|prec|succ|preceq|succeq|"
        r"times|cdot|cdots|ldots|dots|vdots|ddots|div|circ|oplus|otimes|odot|wedge|vee|neg|"
        r"infty|partial|nabla|ell|hbar|"
        r"hat\s*\{|check\s*\{|tilde\s*\{|bar\s*\{|vec\s*\{|dot\s*\{|ddot\s*\{|"
        r"widetilde|widehat|overline|underline|overbrace|underbrace|"
        r"lfloor|rfloor|lceil|rceil|langle|rangle|bmod|pmod|"
        r"alpha|beta|gamma|delta|varepsilon|epsilon|zeta|eta|theta|vartheta|iota|kappa|"
        r"lambda|mu|nu|xi|pi|varpi|rho|varrho|sigma|varsigma|tau|upsilon|varphi|phi|chi|psi|omega|"
        r"Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega|"
        r"in|le|ge|ne|to|pm|mp|ll|gg)(?![a-z])"
        r"|[∑∏∫]\s*[_^]\{[^}\n]{1,30}\}"
        r"|[A-Za-z0-9\)\]]\^\{[^}\n]{1,30}\}"
    )
    for pno, ptext in page_texts:
        if "\ufffd" in ptext:
            hard_fails.append(
                f"[PDF_TOFU_GLYPH] {pdf_path.name} page {pno} contains replacement character '\\ufffd' (missing font glyph)"
            )
        m_latex = unrendered_latex_rx.search(ptext)
        if m_latex:
            snippet = ptext[max(0, m_latex.start() - 20): min(len(ptext), m_latex.end() + 30)].replace("\n", " ")
            hard_fails.append(
                f"[PDF_UNRENDERED_LATEX] {pdf_path.name} page {pno} contains raw uncompiled LaTeX '{m_latex.group(0)}' | {snippet}"
            )

    # Verify hard page limit and self-claimed report page counts
    if page_count is not None and page_count > 0:
        if max_pages is not None and page_count > max_pages:
            src_note = f" ({max_pages_source})" if max_pages_source else ""
            hard_fails.append(
                f"[PDF_OVER_PAGE_LIMIT] {pdf_path.name} has {page_count} page(s), exceeding hard limit of {max_pages} page(s){src_note}"
            )

        zh_page_claim_rx = re.compile(
            r"(?<![第\d\-–—~至到/])(\d{1,3})\s*页(?:无错\s*|整洁\s*|完整\s*|正式\s*|技术\s*|建模与实验\s*|实验\s*|方案\s*|PDF\s*)+"
            r"(?:技术\s*|正式\s*|建模与实验\s*|实验\s*|方案\s*)?(?:报告|论文|PDF)"
        )
        zh_total_claim_rx = re.compile(r"(?:报告|论文|PDF)全本共\s*(\d{1,3})\s*页")
        en_page_claim_rx = re.compile(
            r"\b(\d{1,3})-page\s+(?:technical\s+|final\s+|complete\s+|modeling\s+|PDF\s+)*(?:report|paper|manuscript|PDF)\b",
            re.IGNORECASE,
        )
        all_sources: List[Tuple[str, str]] = list(claim_sources or [])
        for pno, ptext in page_texts:
            all_sources.append((f"{pdf_path.name}:page_{pno}", ptext))

        reported_mismatch_sources: Set[str] = set()
        for src_label, src_text in all_sources:
            for rx in (zh_page_claim_rx, zh_total_claim_rx, en_page_claim_rx):
                for m in rx.finditer(src_text):
                    claimed_n = int(m.group(1))
                    if claimed_n < 4:
                        continue
                    if claimed_n != page_count and src_label not in reported_mismatch_sources:
                        reported_mismatch_sources.add(src_label)
                        hard_fails.append(
                            f"[PDF_PAGE_COUNT_MISMATCH] {src_label} claims a {claimed_n}-page report ('{m.group(0)}'), "
                            f"but compiled PDF '{pdf_path.name}' has {page_count} page(s)"
                        )

        # Check for sparse trailing-page overflow on multi-page PDFs
        if page_count >= 5 and len(page_texts) == page_count:
            char_counts = [len("".join(pt.split())) for _, pt in page_texts]
            earlier = sorted(char_counts[:-1])
            median_earlier = earlier[len(earlier) // 2] if earlier else 0
            last_chars = char_counts[-1]
            if median_earlier >= 600 and last_chars < min(380, int(median_earlier * 0.35)):
                warnings.append(
                    f"[PDF_SPARSE_LAST_PAGE] {pdf_path.name} last page (page {page_count}) has only {last_chars} non-whitespace chars "
                    f"(median earlier page: {median_earlier}); check for accidental trailing page spill"
                )

    return hard_fails, warnings, info_lines


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_raw_data_integrity(project_root: Path, require_seal: bool = True) -> Tuple[List[str], List[str], List[str]]:
    """
    Verify SHA-256 immutability of original files in 00_problem/ and 01_data/raw/
    against 01_data/.raw_checksums.json created by init_project.py --lock-raw.
    Returns (hard_fails, warnings, info_lines).
    """
    fails: List[str] = []
    warns: List[str] = []
    info: List[str] = []

    root = project_root.resolve()
    seal_path = root / "01_data" / ".raw_checksums.json"
    live_originals: Set[str] = set()
    for rel_dir in ("00_problem", "01_data/raw"):
        d = root / rel_dir
        if d.is_dir():
            for p in sorted(d.rglob("*")):
                if p.is_file() and not p.name.startswith("."):
                    live_originals.add(p.relative_to(root).as_posix())

    if not seal_path.is_file():
        if require_seal and live_originals:
            fails.append(
                f"[RAW_SEAL_MISSING] {len(live_originals)} original file(s) exist in 00_problem/ or 01_data/raw/ "
                f"but '{seal_path}' is missing. Run 'init_project.py <root> --lock-raw'!"
            )
        elif require_seal:
            info.append("  - No original files found in 00_problem/ or 01_data/raw/ yet.")
        return fails, warns, info

    try:
        payload = json.loads(seal_path.read_text(encoding="utf-8"))
        sealed_files: Dict[str, Dict[str, object]] = payload.get("files", {})
    except Exception as exc:
        return [f"[RAW_SEAL_CORRUPT] Could not parse {seal_path}: {exc}"], warns, info

    verified = 0
    for rel_key, meta in sorted(sealed_files.items()):
        target = root / rel_key
        if not target.is_file():
            fails.append(f"[RAW_DATA_DELETED] Sealed original file is missing: '{rel_key}'")
            continue
        actual_hash = _sha256_file(target)
        expected_hash = str(meta.get("sha256", ""))
        if actual_hash != expected_hash:
            fails.append(
                f"[RAW_DATA_MODIFIED] Original file '{rel_key}' was altered (SHA-256 mismatch)! Restore untouched raw data."
            )
        else:
            verified += 1

    for unsealed in sorted(live_originals - set(sealed_files.keys())):
        msg = (
            f"[RAW_UNSEALED_FILE] New file '{unsealed}' is not yet in .raw_checksums.json; "
            f"run 'init_project.py <root> --lock-raw'."
        )
        if require_seal:
            fails.append(msg)
        else:
            warns.append(msg)

    info.append(f"  - Verified {verified}/{len(sealed_files)} sealed original file(s) in 00_problem/ & 01_data/raw/")
    return fails, warns, info


def check_src_paths(
    src_dir: Optional[Path],
    ban_terms: List[str],
    extra_py_dirs: Optional[List[Path]] = None,
) -> Tuple[List[str], List[str]]:
    if src_dir is None:
        return [], []
    if not src_dir.is_dir():
        return [f"[ARTIFACT_DIR_MISSING] Source code directory not found: {src_dir}"], []

    src_files_map: Dict[Path, Path] = {}
    for p in sorted(src_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in {".py", ".m", ".r", ".jl", ".sh"}:
            src_files_map[p.resolve()] = p
    for extra_dir in extra_py_dirs or []:
        if extra_dir.is_dir():
            for p in sorted(extra_dir.glob("*.py")):
                if p.is_file():
                    src_files_map.setdefault(p.resolve(), p)
    src_files = sorted(src_files_map.values(), key=lambda p: p.as_posix())

    pats = list(PATH_LEAK_PATTERNS)
    for term in ban_terms:
        pats.append(("SRC_BAN", re.escape(term)))
    hits = scan_patterns(src_files, pats)
    warns: List[str] = []

    # Guard against scripts writing/deleting inside immutable 01_data/raw/ or 00_problem/
    raw_dir_rx = re.compile(r"(?:01_data[/\\]+raw|00_problem)", re.IGNORECASE)
    raw_write_rxs = [
        re.compile(r"(?:to_csv|to_excel|to_parquet|to_json|to_pickle|to_feather|savetxt|savez?|dump)\s*\(", re.IGNORECASE),
        re.compile(r"(?:write_text|write_bytes)\s*\(", re.IGNORECASE),
        re.compile(r"open\s*\([^)]*,\s*['\"][wax+]", re.IGNORECASE),
        re.compile(r"(?:os\.remove|os\.unlink|shutil\.move|shutil\.rmtree|\.unlink)\s*\(", re.IGNORECASE),
    ]
    bare_zip_rx = re.compile(r"\bfor\s+[^:\n]+\s+in\s+(?:enumerate\s*\(\s*)?zip\s*\(([^)]+)\)")
    verifier_name_rx = re.compile(r"(?:audit|verify|check|validate)", re.IGNORECASE)
    os_font_rx = re.compile(
        r"(?:[A-Za-z]:[/\\]+Windows[/\\]+Fonts|WINDIR[^\n]*Fonts|/System/Library/Fonts|/Library/Fonts)",
        re.IGNORECASE,
    )
    font_fallback_rx = re.compile(
        r"(?:UnicodeCIDFont|STSong-Light|get_data_path|is_file\s*\(|os\.path\.isfile|os\.path\.exists|\.exists\s*\(|except\s+(?:OSError|FileNotFoundError|Exception))"
    )

    for path in src_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        is_verifier = bool(verifier_name_rx.search(path.stem))
        if path.suffix.lower() == ".py" and os_font_rx.search(text) and not font_fallback_rx.search(text):
            warns.append(
                f"[SRC_OS_FONT_HARDCODE] {path.name} references an OS-specific font directory without an apparent cross-platform fallback check"
            )
        if (
            path.suffix.lower() == ".py"
            and re.search(r're\.sub\s*\(\s*r?[\'"]\\\$\(\[\^\$\]\+\)\\\$', text)
            and re.search(r"\\\\mathcal", text)
        ):
            has_bs_assert = bool(re.search(r"""(?:['"]\\\\['"]\s+in\b|r['"]\\['"]\s+in\b)""", text))
            m_cal = re.search(r"\\\\(?:mathcal|mathrm|mathbf|mathbb)\\\{\(", text)
            m_in = re.search(r"\\\\in(?:\(\?!|\\b)", text)
            cal_before_in = bool(m_cal and m_in and m_cal.start() < m_in.start())
            if cal_before_in or not has_bs_assert:
                warns.append(
                    f"[SRC_INLINE_MATH_UNSAFE] {path.name} converts inline '$...$' math via regex without wrapper-last ordering "
                    f"and/or residual-backslash assertion ('\"\\\\\" in expr'); tokens like '\\in\\mathcal{{I}}' can leak as '\\inI'"
                )
        for lineno, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith("#"):
                continue
            if raw_dir_rx.search(line) and any(rx.search(line) for rx in raw_write_rxs):
                snippet = line.strip()[:110]
                hits.append((path.name, lineno, "SRC_WRITES_RAW", "01_data/raw or 00_problem write", snippet))
            if is_verifier:
                m_zip = bare_zip_rx.search(line)
                if m_zip and "strict" not in m_zip.group(1):
                    warns.append(
                        f"[SRC_UNSAFE_ZIP_COMPARE] {path.name}:{lineno} uses bare 'zip(...)' without 'strict=True' or 'zip_longest'; "
                        f"trailing extra rows in compared files can be silently ignored"
                    )

    fails = [
        f"[{code}] {fname}:{lineno} matched '{matched}' | {snippet}"
        for fname, lineno, code, matched, snippet in hits
    ]
    return fails, warns


def check_metrics_and_table_provenance(
    target: Optional[Path],
    files: List[Path],
    metrics_dir: Optional[Path],
    pdf_path: Optional[Path] = None,
    html_targets: Optional[List[str]] = None,
) -> List[str]:
    """
    Verify:
    1. metrics_dir exists if specified.
    2. generated_metrics.tex and generated_tables/*.tex are not older than source JSON/CSV.
    3. Compiled PDF and HTML dashboards are not older than source JSON/CSV or generated_metrics.tex (>5s tolerance).
    4. No orphan generated_tables/*.tex exists without a live source CSV.
    5. Every manuscript \\input{...generated_tables/<stem>...} has BOTH a live source CSV and .tex file.
    6. _sync_manifest.json (if present) has no deleted source JSON/CSV lingering unsynced.
    """
    if metrics_dir is None:
        return []
    if not metrics_dir.is_dir():
        return [f"[ARTIFACT_DIR_MISSING] Metrics directory not found: {metrics_dir}"]

    paper_dir = (target if target.is_dir() else target.parent) if target is not None else None
    fails: List[str] = []

    live_jsons = [p for p in metrics_dir.glob("*.json") if not p.name.startswith("_")]
    live_csvs = [p for p in metrics_dir.glob("*.csv") if not p.name.startswith("_")]
    live_all = live_jsons + live_csvs
    live_csv_stems = {p.stem for p in live_csvs}
    live_json_names = {p.name for p in live_jsons}

    newest_metric: Optional[Path] = max(live_all, key=lambda p: p.stat().st_mtime) if live_all else None

    if newest_metric is not None:
        if pdf_path is not None and pdf_path.is_file():
            if newest_metric.stat().st_mtime > pdf_path.stat().st_mtime + 5.0:
                fails.append(
                    f"[STALE_PDF_VS_METRICS] Compiled PDF '{pdf_path.name}' is older than metric file '{newest_metric.name}'. "
                    f"Rebuild PDF so manuscript numbers match latest metrics!"
                )
        for raw_ht in html_targets or []:
            for part in raw_ht.split(","):
                part = part.strip()
                if not part:
                    continue
                hp = Path(part)
                h_candidates = (
                    [hp]
                    if hp.is_file()
                    else (
                        sorted(
                            f for f in hp.rglob("*")
                            if f.is_file() and f.suffix.lower() in {".html", ".htm"} and not f.name.startswith("_")
                        )
                        if hp.is_dir()
                        else []
                    )
                )
                for hfile in h_candidates:
                    if newest_metric.stat().st_mtime > hfile.stat().st_mtime + 5.0:
                        fails.append(
                            f"[STALE_HTML_VS_METRICS] HTML dashboard '{hfile.name}' is older than metric file '{newest_metric.name}'. "
                            f"Rebuild dashboard so interactive numbers match latest metrics!"
                        )

    if paper_dir is None:
        return fails

    # Freshness: JSON -> generated_metrics.tex -> compiled PDF
    gen_metrics = paper_dir / "generated_metrics.tex"
    if gen_metrics.is_file():
        if live_jsons:
            newest_json = max(live_jsons, key=lambda p: p.stat().st_mtime)
            if newest_json.stat().st_mtime > gen_metrics.stat().st_mtime + 1.0:
                fails.append(
                    f"[STALE_METRICS_TEX] '{gen_metrics.name}' is older than '{newest_json.name}'. Re-run sync_metrics.py!"
                )
        if pdf_path is not None and pdf_path.is_file():
            if gen_metrics.stat().st_mtime > pdf_path.stat().st_mtime + 5.0:
                fails.append(
                    f"[STALE_PDF_VS_TEX] Compiled PDF '{pdf_path.name}' is older than '{gen_metrics.name}'. Re-compile PDF!"
                )

    # Freshness + orphan detection: CSV <-> generated_tables/*.tex
    tables_dir = paper_dir / "generated_tables"
    if tables_dir.is_dir():
        for csv_file in live_csvs:
            gen_tbl = tables_dir / f"{csv_file.stem}.tex"
            if gen_tbl.is_file() and csv_file.stat().st_mtime > gen_tbl.stat().st_mtime + 1.0:
                fails.append(
                    f"[STALE_TABLE_TEX] 'generated_tables/{gen_tbl.name}' is older than '{csv_file.name}'. Re-run sync_metrics.py!"
                )
        for gen_tbl in sorted(tables_dir.glob("*.tex")):
            if gen_tbl.stem not in live_csv_stems:
                fails.append(
                    f"[ORPHAN_GENERATED_TABLE] 'generated_tables/{gen_tbl.name}' has no matching '{gen_tbl.stem}.csv' in {metrics_dir}. Re-run sync_metrics.py and update manuscript!"
                )

    # Manuscript \input{...generated_tables/<stem>...} provenance verification
    tbl_input_rx = re.compile(r"\\(?:input|include)\{([^}]*generated_tables/([^}/]+?)(?:\.tex)?)\}")
    for path in files:
        if path.suffix.lower() != ".tex":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith("%"):
                continue
            for m in tbl_input_rx.finditer(line):
                raw_ref = m.group(1).strip()
                stem = m.group(2).strip()
                if stem not in live_csv_stems:
                    fails.append(
                        f"[MISSING_TABLE_SOURCE] {path.name}:{lineno} includes '{raw_ref}' but source '{stem}.csv' does not exist in {metrics_dir}"
                    )
                elif not (tables_dir / f"{stem}.tex").is_file():
                    fails.append(
                        f"[MISSING_GENERATED_TABLE] {path.name}:{lineno} includes '{raw_ref}' but 'generated_tables/{stem}.tex' is missing; run sync_metrics.py"
                    )

    # Manifest drift check (detect withdrawn JSON/CSV sources when sync_metrics wasn't re-run)
    manifest_path = metrics_dir / "_sync_manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for prev_json in manifest.get("json_sources", []):
                if prev_json not in live_json_names:
                    fails.append(
                        f"[STALE_SYNC_MANIFEST] JSON source '{prev_json}' was removed since last sync. Re-run sync_metrics.py!"
                    )
            for prev_csv in manifest.get("csv_to_table", {}).keys():
                if Path(prev_csv).stem not in live_csv_stems:
                    fails.append(
                        f"[STALE_SYNC_MANIFEST] CSV source '{prev_csv}' was removed since last sync. Re-run sync_metrics.py!"
                    )
        except Exception as exc:
            fails.append(f"[MANIFEST_CORRUPT] Could not parse {manifest_path}: {exc}")

    return fails


def summarize_metrics(metrics_dir: Optional[Path]) -> List[str]:
    if not metrics_dir or not metrics_dir.is_dir():
        return ["[WARN] Metrics directory not provided or missing; manual numeric traceability required."]
    lines: List[str] = []
    files = sorted(
        p for p in metrics_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".json", ".csv"} and not p.name.startswith("_")
    )
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


def check_deliverable_csvs(
    csv_targets: List[str],
    strict_csv: bool = False,
) -> Tuple[List[str], List[str], List[str]]:
    """
    Audit exported competition deliverable CSV files (e.g. allocation.csv, indicators.csv):
    - [CSV_MISSING] target path/dir does not exist
    - [CSV_UTF8_BOM] file starts with UTF-8 BOM (ef bb bf / utf-8-sig), which can break standard UTF-8 grading parsers
    - [CSV_EMPTY] / [CSV_RAGGED_ROW] empty header, blank column names, or inconsistent column count
    - [CSV_NAN_OR_INF] NaN / Inf / null / None / Excel error tokens in any cell
    - [CSV_EXACT_DUPLICATE_ROW] identical duplicate rows
    - [CSV_UNMERGED_DUPLICATE_KEY] unaggregated duplicate composite entity/decision-variable keys
    """
    hard_fails: List[str] = []
    warnings: List[str] = []
    info_lines: List[str] = []

    csv_files: List[Path] = []
    for raw_target in csv_targets:
        for part in raw_target.split(","):
            part = part.strip()
            if not part:
                continue
            p = Path(part)
            if not p.exists():
                hard_fails.append(f"[CSV_MISSING] Specified deliverable CSV path not found: {p}")
                continue
            if p.is_file():
                if p.suffix.lower() == ".csv":
                    csv_files.append(p)
            elif p.is_dir():
                found = sorted(f for f in p.rglob("*.csv") if f.is_file() and not f.name.startswith("_"))
                if not found:
                    warnings.append(f"[CSV_DIR_EMPTY] No .csv files found under directory: {p}")
                csv_files.extend(found)

    bad_token_rx = re.compile(r"^(?:nan|inf|-inf|\+inf|null|none|#n/a|#div/0!|#value!|#ref!|#name\?)$", re.IGNORECASE)
    decimal_float_rx = re.compile(r"^[+-]?\d+\.\d+$")
    key_name_rx = re.compile(r"(?:id|key|code|no|num|号|键|码|单|批|仓)", re.IGNORECASE)

    for csv_path in csv_files:
        raw_bytes = csv_path.read_bytes()
        has_bom = raw_bytes.startswith(b"\xef\xbb\xbf")
        if has_bom:
            bom_msg = (
                f"[CSV_UTF8_BOM] {csv_path.name} has UTF-8 BOM (utf-8-sig); standard UTF-8 grading parsers may see "
                f"'\\ufeff' on the first header column. Prefer encoding='utf-8' unless Excel BOM is required."
            )
            if strict_csv:
                hard_fails.append(bom_msg)
            else:
                warnings.append(bom_msg)

        text = raw_bytes.decode("utf-8-sig" if has_bom else "utf-8", errors="replace")
        rows = list(csv.reader(text.splitlines()))
        if not rows:
            hard_fails.append(f"[CSV_EMPTY] {csv_path.name} is empty (0 rows)")
            continue

        header = [c.strip() for c in rows[0]]
        ncols = len(header)
        if ncols == 0 or any(not h for h in header):
            hard_fails.append(f"[CSV_EMPTY_HEADER] {csv_path.name} has empty or blank column header: {header}")
            continue

        data_rows = rows[1:]
        ragged_count = 0
        bad_cell_hits: List[str] = []
        for r_idx, row in enumerate(data_rows, start=2):
            if len(row) != ncols:
                ragged_count += 1
                if ragged_count <= 3:
                    hard_fails.append(
                        f"[CSV_RAGGED_ROW] {csv_path.name}:{r_idx} has {len(row)} columns (expected {ncols})"
                    )
                continue
            for c_idx, val in enumerate(row):
                s = val.strip()
                if bad_token_rx.match(s):
                    if len(bad_cell_hits) < 5:
                        bad_cell_hits.append(f"row {r_idx} col '{header[c_idx]}'='{s}'")

        if bad_cell_hits:
            hard_fails.append(
                f"[CSV_NAN_OR_INF] {csv_path.name} contains invalid token(s): {', '.join(bad_cell_hits)}"
            )

        valid_rows = [tuple(r) for r in data_rows if len(r) == ncols]
        row_counts = Counter(valid_rows)
        exact_dups = sum(cnt - 1 for cnt in row_counts.values() if cnt > 1)
        if exact_dups > 0:
            sample_dup = next(r for r, cnt in row_counts.items() if cnt > 1)
            hard_fails.append(
                f"[CSV_EXACT_DUPLICATE_ROW] {csv_path.name} contains {exact_dups} exact duplicate row(s), e.g. {sample_dup[:4]}"
            )

        # Check for unmerged duplicate decision-variable / entity keys in allocation/ledger tables:
        # When a table has >=3 columns, 1..2 decimal-float quantity columns, and >=2 discrete non-float columns
        # (including at least one ID/key column), duplicate discrete-key tuples indicate split rows that were not merged.
        if ncols >= 3 and len(valid_rows) >= 2 and exact_dups == 0:
            float_cols: List[int] = []
            discrete_cols: List[int] = []
            sample_slice = valid_rows[: min(len(valid_rows), 500)]
            for c_idx in range(ncols):
                non_empty = [r[c_idx].strip() for r in sample_slice if r[c_idx].strip()]
                if non_empty and all(decimal_float_rx.match(v) for v in non_empty):
                    float_cols.append(c_idx)
                else:
                    discrete_cols.append(c_idx)
            has_id_col = any(key_name_rx.search(header[c]) for c in discrete_cols)
            if 1 <= len(float_cols) <= 2 and len(discrete_cols) >= 2 and has_id_col:
                key_counts = Counter(tuple(r[c] for c in discrete_cols) for r in valid_rows)
                dup_keys = [(k, cnt) for k, cnt in key_counts.items() if cnt > 1]
                if dup_keys:
                    key_names = "+".join(header[c] for c in discrete_cols)
                    sample_k, sample_cnt = dup_keys[0]
                    dup_msg = (
                        f"[CSV_UNMERGED_DUPLICATE_KEY] {csv_path.name} has {len(dup_keys)} duplicate composite key(s) "
                        f"on ({key_names}) with separate unmerged quantities (e.g. {sample_k} appears {sample_cnt}x). "
                        f"Aggregate split allocations by primary key before exporting."
                    )
                    if strict_csv:
                        hard_fails.append(dup_msg)
                    else:
                        warnings.append(dup_msg)

            # Check uniform decimal places in fixed-precision decimal-float columns (e.g. 4-decimal quantities)
            if len(valid_rows) >= 10:
                for c_idx in float_cols:
                    all_vals = [r[c_idx].strip() for r in valid_rows if r[c_idx].strip()]
                    if not all_vals or not all(decimal_float_rx.match(v) for v in all_vals):
                        continue
                    prec_counts = Counter(len(v.split(".", 1)[1]) for v in all_vals)
                    if len(prec_counts) > 1:
                        dom_prec, dom_cnt = prec_counts.most_common(1)[0]
                        if dom_cnt >= 0.9 * len(all_vals):
                            bad_row_idx, bad_val = next(
                                (idx + 2, r[c_idx].strip())
                                for idx, r in enumerate(valid_rows)
                                if r[c_idx].strip() and len(r[c_idx].strip().split(".", 1)[1]) != dom_prec
                            )
                            dec_msg = (
                                f"[CSV_INCONSISTENT_DECIMALS] {csv_path.name}:{bad_row_idx} col '{header[c_idx]}' has value "
                                f"'{bad_val}' ({len(bad_val.split('.', 1)[1])} decimals) while {dom_cnt}/{len(all_vals)} rows use {dom_prec} decimals"
                            )
                            if strict_csv:
                                hard_fails.append(dec_msg)
                            else:
                                warnings.append(dec_msg)

        info_lines.append(
            f"  - {csv_path.name}: {len(data_rows)} row(s), {ncols} col(s), encoding={'UTF-8-BOM' if has_bom else 'UTF-8'}"
        )

    return hard_fails, warnings, info_lines


def check_deliverable_html(
    html_targets: List[str],
    ban_terms: List[str],
) -> Tuple[List[str], List[str], List[str]]:
    """
    Audit self-contained offline HTML dashboard deliverables:
    - [HTML_MISSING] target path/dir does not exist
    - [HTML_EMPTY] file is empty or lacks basic HTML markup
    - [INTERNAL_LEAK] / [PATH_LEAK] / [HTML_BAN] leaked workflow tokens, local paths, or banned terms
    - [HTML_EXTERNAL_DEP] (warn) external http(s) <script src=...> or <link href=...> CDN dependency
    - [HTML_JS_SYNTAX_ERROR] inline JavaScript syntax error via `node --check` (when Node.js is available)
    """
    hard_fails: List[str] = []
    warnings: List[str] = []
    info_lines: List[str] = []

    html_files: List[Path] = []
    for raw_target in html_targets:
        for part in raw_target.split(","):
            part = part.strip()
            if not part:
                continue
            p = Path(part)
            if not p.exists():
                hard_fails.append(f"[HTML_MISSING] Specified HTML deliverable path not found: {p}")
                continue
            if p.is_file():
                if p.suffix.lower() in {".html", ".htm"}:
                    html_files.append(p)
            elif p.is_dir():
                found = sorted(
                    f for f in p.rglob("*")
                    if f.is_file() and f.suffix.lower() in {".html", ".htm"} and not f.name.startswith("_")
                )
                if not found:
                    warnings.append(f"[HTML_DIR_EMPTY] No .html/.htm files found under directory: {p}")
                html_files.extend(found)

    if not html_files:
        return hard_fails, warnings, info_lines

    leak_pats = list(INTERNAL_LEAK_PATTERNS) + list(PATH_LEAK_PATTERNS)
    for term in ban_terms:
        leak_pats.append(("HTML_BAN", re.escape(term)))
    compiled_leaks = [(code, re.compile(pat, re.IGNORECASE)) for code, pat in leak_pats]

    ext_script_rx = re.compile(r"<script\b[^>]*\bsrc\s*=\s*['\"]https?://[^'\"]+['\"]", re.IGNORECASE)
    ext_link_rx = re.compile(r"<link\b[^>]*\bhref\s*=\s*['\"]https?://[^'\"]+['\"]", re.IGNORECASE)
    script_block_rx = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.DOTALL | re.IGNORECASE)
    src_attr_rx = re.compile(r"\bsrc\s*=", re.IGNORECASE)
    type_attr_rx = re.compile(r"\btype\s*=\s*['\"]?([^'\"\s>]+)", re.IGNORECASE)
    js_types = {"", "text/javascript", "application/javascript", "module"}
    json_types = {"application/json", "application/ld+json"}
    node_exe = shutil.which("node")

    def _reject_nonfinite_json(token: str) -> None:
        raise ValueError(f"Non-standard JSON constant '{token}' (breaks browser JSON.parse)")

    for html_path in html_files:
        text = html_path.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        if not text.strip() or ("<html" not in lower and "<body" not in lower and "<script" not in lower):
            hard_fails.append(f"[HTML_EMPTY] {html_path.name} is empty or missing basic HTML markup")
            continue

        if "\ufffd" in text:
            hard_fails.append(f"[HTML_TOFU_GLYPH] {html_path.name} contains replacement character '\\ufffd'")
        if "@@DATA@@" in text:
            hard_fails.append(f"[HTML_UNREPLACED_TOKEN] {html_path.name} contains unreplaced template token '@@DATA@@'")

        for lineno, line in enumerate(text.splitlines(), start=1):
            for code, rx in compiled_leaks:
                m = rx.search(line)
                if m:
                    snippet = line.strip()
                    if len(snippet) > 110:
                        snippet = snippet[:107] + "..."
                    hard_fails.append(
                        f"[{code}] {html_path.name}:{lineno} matched '{m.group(0)}' | {snippet}"
                    )
            for ext_rx in (ext_script_rx, ext_link_rx):
                m_ext = ext_rx.search(line)
                if m_ext:
                    warnings.append(
                        f"[HTML_EXTERNAL_DEP] {html_path.name}:{lineno} references external HTTP(S) asset: {m_ext.group(0)[:100]}"
                    )

        js_blocks: List[str] = []
        json_block_count = 0
        for m_sc in script_block_rx.finditer(text):
            attrs, body = m_sc.group(1) or "", m_sc.group(2) or ""
            if src_attr_rx.search(attrs):
                continue
            m_type = type_attr_rx.search(attrs)
            sc_type = m_type.group(1).strip().lower() if m_type else ""
            if sc_type in js_types and body.strip():
                js_blocks.append(body)
            elif sc_type in json_types:
                json_block_count += 1
                if not body.strip():
                    hard_fails.append(f"[HTML_INVALID_JSON_PAYLOAD] {html_path.name} has empty <script type='{sc_type}'> block")
                else:
                    try:
                        json.loads(body, parse_constant=_reject_nonfinite_json)
                    except Exception as exc:
                        hard_fails.append(
                            f"[HTML_INVALID_JSON_PAYLOAD] {html_path.name} <script type='{sc_type}'> invalid JSON: {str(exc)[:140]}"
                        )

        js_status = "no inline JS"
        if js_blocks:
            if node_exe:
                combined_js = "\n;\n".join(js_blocks) + "\n"
                tmp_path: Optional[Path] = None
                try:
                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".js", encoding="utf-8", delete=False
                    ) as tf:
                        tf.write(combined_js)
                        tmp_path = Path(tf.name)
                    res = subprocess.run(
                        [node_exe, "--check", str(tmp_path)],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    if res.returncode != 0:
                        err_txt = (res.stderr or res.stdout or "syntax error").strip().splitlines()
                        err_snippet = " | ".join(err_txt[:3])[:160]
                        hard_fails.append(f"[HTML_JS_SYNTAX_ERROR] {html_path.name}: {err_snippet}")
                        js_status = f"JS syntax FAIL ({len(js_blocks)} script block(s))"
                    else:
                        js_status = f"JS syntax PASS via node --check ({len(js_blocks)} script block(s))"
                finally:
                    if tmp_path is not None:
                        tmp_path.unlink(missing_ok=True)
            else:
                js_status = f"{len(js_blocks)} inline JS block(s) (node not found; syntax check skipped)"

        info_lines.append(f"  - {html_path.name}: {len(text.splitlines())} line(s), {js_status}")

    return hard_fails, warnings, info_lines


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
        description="Deterministic Stage 1+2 audit scanner, PDF page renderer, plan-rule gate, and handoff validator."
    )
    parser.add_argument("paper", nargs="?", default=None, help="Path to manuscript .tex/.md file or directory")
    parser.add_argument("--metrics-dir", type=str, default=None, help="Path to 03_outputs/metrics")
    parser.add_argument("--figs-dir", type=str, default=None, help="Path to 03_outputs/figs")
    parser.add_argument("--src-dir", type=str, default=None, help="Path to 02_src/ for local-path/anonymity scan")
    parser.add_argument("--plan", type=str, default=None, help="Path to 00_plan.md to verify live contest rules")
    parser.add_argument("--verify-raw", type=str, default=None, help="Project root to verify SHA-256 immutability of 00_problem/ & 01_data/raw/")
    parser.add_argument("--log", type=str, default=None, help="Path to LaTeX compile .log file")
    parser.add_argument("--pdf", type=str, default=None, help="Path to compiled .pdf for metadata/page check")
    parser.add_argument("--max-pages", type=int, default=None, help="Hard upper PDF page limit (overrides 00_plan.md Sec. 0)")
    parser.add_argument(
        "--render-pdf",
        nargs="?",
        const="03_outputs/_pdf_previews",
        default=None,
        help="Output dir to rasterize PDF pages to PNGs (default if flag given without path: 03_outputs/_pdf_previews)",
    )
    parser.add_argument(
        "--check-csv",
        action="append",
        default=[],
        help="Deliverable CSV file or directory to audit for BOM, NaN/Inf, ragged rows, and duplicate keys (repeatable)",
    )
    parser.add_argument(
        "--strict-csv",
        action="store_true",
        help="Treat UTF-8 BOM and unmerged duplicate composite keys in deliverable CSVs as hard failures",
    )
    parser.add_argument(
        "--check-html",
        action="append",
        default=[],
        help="Offline HTML dashboard file or directory to audit for leaks, external CDNs, and inline JS syntax (repeatable)",
    )
    parser.add_argument("--check-handoff", type=str, default=None, help="Validate O(1) handoff.md relay contract")
    parser.add_argument("--max-lines", type=int, default=80, help="Hard line cap for handoff.md (default: 80)")
    parser.add_argument("--project-root", type=str, default=None, help="Project root for verifying handoff pointers")
    parser.add_argument(
        "--companion",
        action="append",
        default=[],
        help="Additional official companion markdown file(s) to audit (e.g. 作品说明单.md, AI协作记录.md)",
    )
    parser.add_argument("--ban-terms", type=str, default="", help="Comma-separated custom anonymity terms to ban")
    args = parser.parse_args()

    if (
        not args.paper
        and not args.check_handoff
        and not args.plan
        and not args.verify_raw
        and not args.check_csv
        and not args.check_html
    ):
        parser.error("Provide a manuscript path, --check-handoff, --plan, --verify-raw, --check-csv, and/or --check-html.")

    ban_terms = [t.strip() for t in args.ban_terms.split(",") if t.strip()]
    total_hard_fails = 0
    print("=" * 72)
    print("MATH MODELING FRONTIER AUDIT & RELAY VALIDATOR (v1.6)")
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
        print("\n[LIVE CONTEST RULES CHECK] (00_plan.md Sec. 0 — Field-by-Field)")
        for line in p_info:
            print(line)
        if not p_fails:
            print("  -> PASS (all 6 mandatory official rule fields verified with sources)")
        else:
            total_hard_fails += len(p_fails)
            for msg in p_fails:
                print(f"  [HARD FAIL]{msg}")

    # ---- OPTIONAL: RAW DATA IMMUTABILITY CHECK (SHA-256) ----
    raw_root: Optional[Path] = None
    require_seal = False
    if args.verify_raw:
        raw_root = Path(args.verify_raw)
        require_seal = True
    elif args.project_root and (Path(args.project_root) / "01_data" / ".raw_checksums.json").is_file():
        raw_root = Path(args.project_root)
    if raw_root is not None:
        r_fails, r_warns, r_info = verify_raw_data_integrity(raw_root, require_seal=require_seal)
        print("\n[RAW DATA IMMUTABILITY CHECK] (00_problem/ & 01_data/raw/ SHA-256)")
        for line in r_info:
            print(line)
        for w in r_warns:
            print(f"  [WARN]{w}")
        if not r_fails:
            print("  -> PASS (all sealed original files untouched)")
        else:
            total_hard_fails += len(r_fails)
            for msg in r_fails:
                print(f"  [HARD FAIL]{msg}")

    # ---- OPTIONAL: DELIVERABLE CSV INTEGRITY CHECK ----
    if args.check_csv:
        c_fails, c_warns, c_info = check_deliverable_csvs(args.check_csv, strict_csv=args.strict_csv)
        print("\n[DELIVERABLE CSV AUDIT] (Encoding, Schema, NaN/Inf & Key Uniqueness)")
        for line in c_info:
            print(line)
        for w in c_warns:
            print(f"  [WARN]{w}")
        if not c_fails:
            print("  -> PASS (0 hard CSV failures)")
        else:
            total_hard_fails += len(c_fails)
            for msg in c_fails:
                print(f"  [HARD FAIL]{msg}")

    # ---- OPTIONAL: OFFLINE HTML DASHBOARD AUDIT ----
    if args.check_html:
        h_fails, h_warns, h_info = check_deliverable_html(args.check_html, ban_terms=ban_terms)
        if not args.paper and args.metrics_dir:
            h_fails.extend(
                check_metrics_and_table_provenance(
                    None,
                    [],
                    Path(args.metrics_dir),
                    pdf_path=None,
                    html_targets=args.check_html,
                )
            )
        print("\n[DELIVERABLE HTML DASHBOARD AUDIT] (Self-Contained, Leaks, JSON Payload & JS Syntax)")
        for line in h_info:
            print(line)
        for w in h_warns:
            print(f"  [WARN]{w}")
        if not h_fails:
            print("  -> PASS (0 hard HTML failures)")
        else:
            total_hard_fails += len(h_fails)
            for msg in h_fails:
                print(f"  [HARD FAIL]{msg}")

    # ---- MANUSCRIPT AUDIT ----
    if args.paper:
        target = Path(args.paper)
        inferred_root = Path(args.project_root) if args.project_root else (Path(args.plan).resolve().parent if args.plan else None)
        files = collect_manuscript_files(target, project_root=inferred_root, extra_companions=args.companion)
        if not files:
            print(f"[ERROR] No .tex or .md files found at: {target}")
            return 2

        stage1_patterns = list(INTERNAL_LEAK_PATTERNS) + list(PATH_LEAK_PATTERNS) + list(PLACEHOLDER_PATTERNS)
        for term in ban_terms:
            stage1_patterns.append(("ANONYMITY_BAN", re.escape(term)))

        metrics_path = Path(args.metrics_dir) if args.metrics_dir else None
        figs_path = Path(args.figs_dir) if args.figs_dir else None
        src_path = Path(args.src_dir) if args.src_dir else None
        log_path = Path(args.log) if args.log else None
        pdf_path = Path(args.pdf) if args.pdf else None
        paper_dir = target if target.is_dir() else target.parent

        s1_hits = scan_patterns(files, stage1_patterns)
        prose_fails, prose_warns, prose_info = check_prose_integrity_and_companion_rules(files)
        ref_fails, fig_warns, fig_info = check_latex_refs_and_figs(files, figs_path)
        src_fails, src_warns = check_src_paths(src_path, ban_terms, extra_py_dirs=[paper_dir])
        sync_fails = check_metrics_and_table_provenance(
            target,
            files,
            metrics_path,
            pdf_path=pdf_path,
            html_targets=args.check_html,
        )
        log_fails, log_warns = check_latex_log(log_path)

        claim_sources: List[Tuple[str, str]] = [
            (p.name, p.read_text(encoding="utf-8", errors="replace"))
            for p in files
            if "协作记录" not in p.name
        ]
        for aux_p in (Path(args.plan) if args.plan else None, Path(args.check_handoff) if args.check_handoff else None):
            if aux_p and aux_p.is_file():
                claim_sources.append((aux_p.name, aux_p.read_text(encoding="utf-8", errors="replace")))

        max_pages: Optional[int] = args.max_pages
        max_pages_source: Optional[str] = "--max-pages" if max_pages is not None else None
        if max_pages is None and args.plan:
            extracted = extract_plan_max_pages(Path(args.plan))
            if extracted is not None:
                max_pages, phrase = extracted
                max_pages_source = f"00_plan.md Sec. 0: '{phrase}'"

        pdf_fails, pdf_warns, pdf_info = check_pdf_metadata(
            pdf_path,
            ban_terms,
            claim_sources=claim_sources,
            max_pages=max_pages,
            max_pages_source=max_pages_source,
        )

        render_fails: List[str] = []
        rendered_pages: List[Path] = []
        if args.render_pdf:
            if not pdf_path or not pdf_path.is_file():
                render_fails.append(
                    f"[RENDER_PDF_MISSING] --render-pdf requested but valid --pdf file is missing ({pdf_path})"
                )
            else:
                rendered_pages, err = render_pdf_pages(pdf_path, Path(args.render_pdf))
                if err or not rendered_pages:
                    render_fails.append(f"[RENDER_PDF_FAILED] {err or 'Rendered 0 pages'}")

        all_extra_fails = prose_fails + ref_fails + src_fails + sync_fails + log_fails + pdf_fails + render_fails
        all_warns = prose_warns + fig_warns + src_warns + log_warns + pdf_warns
        total_hard_fails += len(s1_hits) + len(all_extra_fails)

        print(f"\n[STAGE 1] Hard Facts, Anti-Leak, Anonymity, Refs, Code, Sync, Log, PDF & Render ({len(files)} file(s))")
        for info_ln in prose_info + fig_info:
            print(info_ln)
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

        if args.render_pdf and rendered_pages:
            print("\n[STAGE 1 PDF PAGE RENDERER]")
            print(f"  -> Rendered {len(rendered_pages)} page(s) to {args.render_pdf} for visual inspection:")
            for p in rendered_pages[:10]:
                print(f"     {p}")
            if len(rendered_pages) > 10:
                print(f"     ... ({len(rendered_pages) - 10} more pages)")

        print("\n[STAGE 1 METRICS INVENTORY FOR 10-POINT SPOT CHECK]")
        for line in summarize_metrics(metrics_path):
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
