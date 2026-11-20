#!/usr/bin/env python3
"""
End-to-end test suite for math-modeling-frontier v1.2 scripts:
  - init_project.py
  - plot_style.py (headless Agg backend)
  - sync_metrics.py (Chinese/Unicode unique macros, collision abort, orphan pruning, manifest)
  - audit_paper.py (missing-artifact hard fail, failed PDF render hard fail,
    field-by-field 00_plan.md Sec. 0 rule check, orphan table guard, section-aware Stage 2)
  - Real pdflatex compilation E2E submission test (enforced in CI via REQUIRE_LATEX_E2E=1)

Run:
    python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / ".agents" / "skills" / "math-modeling-frontier" / "scripts"
INIT_SCRIPT = SCRIPTS_DIR / "init_project.py"
PLOT_SCRIPT = SCRIPTS_DIR / "plot_style.py"
SYNC_SCRIPT = SCRIPTS_DIR / "sync_metrics.py"
AUDIT_SCRIPT = SCRIPTS_DIR / "audit_paper.py"


def run_py(script: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


class TestMathModelingFrontierPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "contest_proj"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_confirmed_plan(self, plan_path: Path) -> None:
        text = plan_path.read_text(encoding="utf-8")
        old_sec0_start = text.index("## 0.")
        old_sec1_start = text.index("## 1.")
        confirmed_sec0 = """## 0. Live Official Rules (Verified)
- **Format & Template**: English LaTeX PDF (Source: 00_problem/2026_APMCM_Notice.pdf)
- **Deadline / Window**: 96 hours ending Nov 30 09:00 UTC+8 (Source: 00_problem/2026_APMCM_Notice.pdf)
- **Hard Page / Word Limit**: No strict hard cap; target 20-28 pages (Source: 00_problem/2026_APMCM_Notice.pdf)
- **Anonymity & Metadata**: Strict blind review, zero names/school/metadata (Source: 00_problem/2026_APMCM_Notice.pdf)
- **AI Declaration Policy**: Disclose AI assistance truthfully in appendix (Source: 00_problem/2026_APMCM_Notice.pdf)
- **Required Extras (Memo / Code / Data / Plagiarism)**: Runnable appendix code; memo 已核实不适用 (Source: 00_problem/2026_APMCM_Notice.pdf)

"""
        plan_path.write_text(text[:old_sec0_start] + confirmed_sec0 + text[old_sec1_start:], encoding="utf-8")

    def test_01_init_project_scaffolding_and_handoff_pass(self) -> None:
        res = run_py(INIT_SCRIPT, str(self.root), "--contest", "2026 APMCM", "--lang", "en", "--title", "Problem A")
        self.assertEqual(res.returncode, 0, res.stderr + res.stdout)

        for rel in [
            "00_problem",
            "01_data/raw",
            "01_data/clean",
            "02_src/plot_style.py",
            "03_outputs/metrics",
            "03_outputs/figs",
            "04_paper",
            "handoff.md",
            "00_plan.md",
            "01_log.md",
            ".gitignore",
        ]:
            self.assertTrue((self.root / rel).exists(), f"Missing expected path: {rel}")

        handoff_text = (self.root / "handoff.md").read_text(encoding="utf-8")
        self.assertIn("MM Step 1", handoff_text)
        self.assertIn("<= 80 lines", handoff_text)

        chk = run_py(AUDIT_SCRIPT, "--check-handoff", str(self.root / "handoff.md"), "--project-root", str(self.root))
        self.assertEqual(chk.returncode, 0, chk.stdout + chk.stderr)

    def test_02_plot_style_all_primitives_export_pdf_and_png(self) -> None:
        sys.path.insert(0, str(SCRIPTS_DIR))
        try:
            import plot_style as ps
        finally:
            if str(SCRIPTS_DIR) in sys.path:
                sys.path.remove(str(SCRIPTS_DIR))

        out_dir = self.root / "03_outputs" / "figs"
        ps.apply_academic_style("en")

        fig, axes = ps.create_journal_fig(1, 3, width="double", height=2.65)
        x = np.linspace(0, 10, 40)
        y = np.exp(-0.2 * x)
        ps.plot_with_ci(axes[0], x, y, y - 0.05, y + 0.05, "Proposed", series_idx=0, markevery=5)
        ps.direct_label(axes[0], x[-1], y[-1], "End", series_idx=0)
        axins = ps.add_zoom_inset(axes[0], xlim=(6, 9), ylim=(0.1, 0.35))
        axins.plot(x, y, color=ps.JOURNAL_COLORS[0])
        ps.style_axis(axes[0], "Time (s)", "Error", "Convergence")

        ps.plot_tornado(axes[1], ["A", "B", "C"], [-2.0, -4.0, -1.0], [2.5, 3.5, 1.2], title="Sensitivity")
        ps.plot_diverging_heatmap(
            axes[2], np.array([[0.2, -0.5], [0.7, -0.1]]), ["X1", "X2"], ["Y1", "Y2"], title="Matrix"
        )
        ps.label_panels(axes, style="nature")
        pdf1, png1 = ps.save_fig(fig, "multi_panel_test", out_dir=str(out_dir))
        self.assertTrue(pdf1.is_file() and pdf1.stat().st_size > 1000)
        self.assertTrue(png1.is_file() and png1.stat().st_size > 1000)

        fig2, ax2 = ps.create_journal_fig(1, 1, width="double", height=2.2)
        ps.plot_pipeline_diagram(
            ax2,
            [("Stage 1", "EDA\nModel"), ("Stage 2", "Solve\nValidate"), ("Stage 3", "Draft\nAudit")],
            title="Pipeline Test",
            feedback_edge=(2, 1, "Feedback"),
        )
        pdf2, png2 = ps.save_fig(fig2, "pipeline_test", out_dir=str(out_dir))
        self.assertTrue(pdf2.is_file() and pdf2.stat().st_size > 1000)
        self.assertTrue(png2.is_file() and png2.stat().st_size > 1000)

    def test_03_sync_metrics_chinese_keys_collision_abort_and_nan(self) -> None:
        run_py(INIT_SCRIPT, str(self.root))
        metrics_dir = self.root / "03_outputs" / "metrics"
        paper_dir = self.root / "04_paper"

        # Chinese metric keys MUST generate two distinct, valid, stable ASCII LaTeX macros
        (metrics_dir / "score.json").write_text(
            json.dumps({"准确率": 0.942, "召回率": 0.887, "ci_95": [12.8, 15.6], "n_samples": 12500}, ensure_ascii=False),
            encoding="utf-8",
        )
        (metrics_dir / "comparison.csv").write_text(
            "Model,RMSE,R2\nBaseline,12.403,0.742\nProposed,10.641,0.892\n",
            encoding="utf-8",
        )

        res = run_py(
            SYNC_SCRIPT,
            "--metrics-dir",
            str(metrics_dir),
            "--paper-dir",
            str(paper_dir),
            "--decimals",
            "2",
            "--bold-best",
            "RMSE:min,R2:max",
        )
        self.assertEqual(res.returncode, 0, res.stderr + res.stdout)

        manifest = json.loads((metrics_dir / "_sync_manifest.json").read_text(encoding="utf-8"))
        zh_macros = [
            (m, meta["value"], meta["source"])
            for m, meta in manifest["macros"].items()
            if "准确率" in meta["source"] or "召回率" in meta["source"]
        ]
        self.assertEqual(len(zh_macros), 2, f"Expected 2 distinct Chinese macros, got: {zh_macros}")
        self.assertNotEqual(zh_macros[0][0], zh_macros[1][0])
        for macro_name, _, _ in zh_macros:
            self.assertRegex(macro_name, r"^[A-Za-z]+$")

        macros_tex = (paper_dir / "generated_metrics.tex").read_text(encoding="utf-8")
        self.assertIn(f"\\newcommand{{\\{zh_macros[0][0]}}}{{{zh_macros[0][1]}}}", macros_tex)
        self.assertIn(f"\\newcommand{{\\{zh_macros[1][0]}}}{{{zh_macros[1][1]}}}", macros_tex)
        self.assertIn(r"\newcommand{\ValScoreCiNineFive}{[12.80, 15.60]}", macros_tex)
        self.assertIn(r"\newcommand{\ValScoreNSamples}{12,500}", macros_tex)
        self.assertNotIn("sync_metrics.py", macros_tex)

        table = (paper_dir / "generated_tables" / "comparison.tex").read_text(encoding="utf-8")
        self.assertIn(r"\begin{tabular}{lrr}", table)
        self.assertIn(r"\textbf{10.64}", table)
        self.assertIn(r"\textbf{0.89}", table)
        self.assertNotIn("|", table)

        # Genuine macro collision (e.g. foo_bar vs foo-bar) MUST abort with exit code 2 showing BOTH keys
        (metrics_dir / "collide.json").write_text('{"foo_bar": 1.0, "foo-bar": 2.0}', encoding="utf-8")
        res_col = run_py(SYNC_SCRIPT, "--metrics-dir", str(metrics_dir), "--paper-dir", str(paper_dir))
        self.assertEqual(res_col.returncode, 2)
        self.assertIn("COLLISION", res_col.stdout)
        self.assertIn("collide.foo_bar", res_col.stdout)
        self.assertIn("collide.foo-bar", res_col.stdout)
        (metrics_dir / "collide.json").unlink()

        # NaN must abort with non-zero exit code
        (metrics_dir / "bad_nan.json").write_text('{"score": NaN}', encoding="utf-8")
        res_nan = run_py(SYNC_SCRIPT, "--metrics-dir", str(metrics_dir), "--paper-dir", str(paper_dir))
        self.assertNotEqual(res_nan.returncode, 0)

    def test_04_plan_live_rules_strict_field_validation_and_handoff_cap(self) -> None:
        run_py(INIT_SCRIPT, str(self.root))
        plan_path = self.root / "00_plan.md"

        # 1. Default template placeholders MUST fail
        res_default = run_py(AUDIT_SCRIPT, "--plan", str(plan_path))
        self.assertEqual(res_default.returncode, 2)
        self.assertIn("UNVERIFIED_CONTEST_RULE", res_default.stdout)

        # 2. Missing Section 0 completely MUST fail (cannot bypass by deleting Sec. 0)
        plan_path.write_text("# 00_plan.md\n\n## 1. Workflow\nDone.\n", encoding="utf-8")
        res_missing_sec0 = run_py(AUDIT_SCRIPT, "--plan", str(plan_path))
        self.assertEqual(res_missing_sec0.returncode, 2)
        self.assertIn("PLAN_SEC0_MISSING", res_missing_sec0.stdout)

        # 3. Empty Section 0 MUST fail (missing all 6 mandatory fields)
        plan_path.write_text("# 00_plan.md\n\n## 0. Live Official Rules\n\n## 1. Workflow\n", encoding="utf-8")
        res_empty_sec0 = run_py(AUDIT_SCRIPT, "--plan", str(plan_path))
        self.assertEqual(res_empty_sec0.returncode, 2)
        self.assertIn("MISSING_CONTEST_RULE", res_empty_sec0.stdout)

        # 4. Filled values WITHOUT explicit source or verified-N/A confirmation MUST fail
        plan_path.write_text(
            """# 00_plan.md
## 0. Live Official Rules
- **Format & Template**: English LaTeX PDF
- **Deadline / Window**: Four days total
- **Hard Page / Word Limit**: Twenty-five pages
- **Anonymity & Metadata**: Blind submission only
- **AI Declaration Policy**: AI appendix allowed
- **Required Extras**: Code appendix needed
## 1. Workflow
""",
            encoding="utf-8",
        )
        res_nosrc = run_py(AUDIT_SCRIPT, "--plan", str(plan_path))
        self.assertEqual(res_nosrc.returncode, 2)
        self.assertIn("MISSING_RULE_SOURCE", res_nosrc.stdout)

        # 5. Properly filled fields WITH sources MUST pass
        run_py(INIT_SCRIPT, str(self.root), "--force")
        self._write_confirmed_plan(plan_path)
        res_ok = run_py(AUDIT_SCRIPT, "--plan", str(plan_path))
        self.assertEqual(res_ok.returncode, 0, res_ok.stdout)

        # 6. Handoff <= 80 lines cap & --max-lines override
        handoff = self.root / "handoff.md"
        clean_long = ["# handoff.md", "- **Current Step**: `Step 2`", "- **Next Role**: `[W]`"] + [
            f"- item {i}" for i in range(82)
        ]
        handoff.write_text("\n".join(clean_long), encoding="utf-8")
        self.assertEqual(
            run_py(AUDIT_SCRIPT, "--check-handoff", str(handoff), "--project-root", str(self.root)).returncode, 2
        )
        self.assertEqual(
            run_py(
                AUDIT_SCRIPT, "--check-handoff", str(handoff), "--project-root", str(self.root), "--max-lines", "95"
            ).returncode,
            0,
        )

    def test_05_withdrawn_csv_orphan_table_detection_and_pruning(self) -> None:
        run_py(INIT_SCRIPT, str(self.root))
        self._write_confirmed_plan(self.root / "00_plan.md")

        metrics_dir = self.root / "03_outputs" / "metrics"
        paper_dir = self.root / "04_paper"
        (metrics_dir / "kept.csv").write_text("Model,RMSE\nA,10.0\n", encoding="utf-8")
        (metrics_dir / "withdrawn.csv").write_text("Model,RMSE\nOld,15.0\n", encoding="utf-8")

        self.assertEqual(
            run_py(SYNC_SCRIPT, "--metrics-dir", str(metrics_dir), "--paper-dir", str(paper_dir)).returncode, 0
        )
        self.assertTrue((paper_dir / "generated_tables" / "withdrawn.tex").is_file())

        tex = paper_dir / "main.tex"
        tex.write_text(
            r"""\documentclass{article}
\begin{document}
\section{Results}
\input{generated_tables/kept.tex}
\input{generated_tables/withdrawn.tex}
\end{document}
""",
            encoding="utf-8",
        )

        # Withdraw experiment CSV WITHOUT re-running sync_metrics.py -> audit MUST fail loudly
        (metrics_dir / "withdrawn.csv").unlink()
        res_before_sync = run_py(AUDIT_SCRIPT, str(tex), "--metrics-dir", str(metrics_dir))
        self.assertEqual(res_before_sync.returncode, 2)
        self.assertIn("ORPHAN_GENERATED_TABLE", res_before_sync.stdout)
        self.assertIn("MISSING_TABLE_SOURCE", res_before_sync.stdout)
        self.assertIn("STALE_SYNC_MANIFEST", res_before_sync.stdout)

        # Re-running sync_metrics.py MUST prune withdrawn.tex
        res_resync = run_py(SYNC_SCRIPT, "--metrics-dir", str(metrics_dir), "--paper-dir", str(paper_dir))
        self.assertEqual(res_resync.returncode, 0, res_resync.stdout)
        self.assertIn("[PRUNE]", res_resync.stdout)
        self.assertFalse((paper_dir / "generated_tables" / "withdrawn.tex").exists())

        # Audit MUST STILL fail because main.tex still \input{generated_tables/withdrawn.tex}
        res_after_sync = run_py(AUDIT_SCRIPT, str(tex), "--metrics-dir", str(metrics_dir))
        self.assertEqual(res_after_sync.returncode, 2)
        self.assertIn("MISSING_TABLE_SOURCE", res_after_sync.stdout)

    def test_06_missing_pdf_log_dirs_and_failed_render_must_hard_fail(self) -> None:
        run_py(INIT_SCRIPT, str(self.root))
        paper_dir = self.root / "04_paper"
        tex = paper_dir / "main.tex"
        tex.write_text("\\documentclass{article}\n\\begin{document}\nClean body.\n\\end{document}\n", encoding="utf-8")

        # 1. Missing --pdf and missing --log MUST return exit code 2 (NEVER 0!)
        res_missing = run_py(
            AUDIT_SCRIPT,
            str(tex),
            "--pdf",
            str(paper_dir / "nonexistent.pdf"),
            "--log",
            str(paper_dir / "nonexistent.log"),
            "--render-pdf",
            str(self.root / "03_outputs" / "_audit_pages"),
        )
        self.assertEqual(res_missing.returncode, 2)
        self.assertIn("PDF_MISSING", res_missing.stdout)
        self.assertIn("LOG_MISSING", res_missing.stdout)
        self.assertIn("RENDER_PDF_MISSING", res_missing.stdout)

        # 2. Corrupt PDF passed to --render-pdf MUST fail with RENDER_PDF_FAILED (exit code 2)
        corrupt_pdf = paper_dir / "corrupt.pdf"
        corrupt_pdf.write_bytes(b"NOT A REAL PDF FILE")
        res_corrupt = run_py(
            AUDIT_SCRIPT,
            str(tex),
            "--pdf",
            str(corrupt_pdf),
            "--render-pdf",
            str(self.root / "03_outputs" / "_audit_pages"),
        )
        self.assertEqual(res_corrupt.returncode, 2)
        self.assertIn("RENDER_PDF_FAILED", res_corrupt.stdout)

        # 3. Missing --metrics-dir / --figs-dir / --src-dir MUST hard fail
        res_dirs = run_py(
            AUDIT_SCRIPT,
            str(tex),
            "--metrics-dir",
            str(self.root / "no_metrics"),
            "--figs-dir",
            str(self.root / "no_figs"),
            "--src-dir",
            str(self.root / "no_src"),
        )
        self.assertEqual(res_dirs.returncode, 2)
        self.assertEqual(res_dirs.stdout.count("ARTIFACT_DIR_MISSING"), 3)

        # 4. Valid PDF passed to --render-pdf MUST succeed and produce page_01.png
        figs_dir = self.root / "03_outputs" / "figs"
        render_dir = self.root / "03_outputs" / "_audit_pages"
        self.assertEqual(run_py(PLOT_SCRIPT, "--self-test", "--lang", "en", "--out", str(figs_dir)).returncode, 0)
        res_ok_render = run_py(
            AUDIT_SCRIPT,
            str(tex),
            "--pdf",
            str(figs_dir / "nature_3panel_test_en.pdf"),
            "--render-pdf",
            str(render_dir),
        )
        self.assertEqual(res_ok_render.returncode, 0, res_ok_render.stdout + res_ok_render.stderr)
        self.assertTrue((render_dir / "page_01.png").is_file())

    def test_07_stage1_hard_gates_and_section_aware_stage2(self) -> None:
        run_py(INIT_SCRIPT, str(self.root))
        self._write_confirmed_plan(self.root / "00_plan.md")

        metrics_dir = self.root / "03_outputs" / "metrics"
        paper_dir = self.root / "04_paper"
        src_dir = self.root / "02_src"

        json_path = metrics_dir / "res.json"
        json_path.write_text('{"acc": 0.91}', encoding="utf-8")
        run_py(SYNC_SCRIPT, "--metrics-dir", str(metrics_dir), "--paper-dir", str(paper_dir))
        gen_tex = paper_dir / "generated_metrics.tex"
        os.utime(gen_tex, (time.time() - 10, time.time() - 10))
        os.utime(json_path, None)

        (src_dir / "leaky.py").write_text('p = r"C:\\Users\\bob\\data.csv"\n', encoding="utf-8")

        tex = paper_dir / "main.tex"
        tex.write_text(
            r"""\documentclass{article}
\begin{document}
\section{Introduction}
With the rapid development of modeling, we emphasize that our method may potentially help.
After Gate R, see Fig.~\ref{fig:nonexistent}.
\begin{tabular}{|l|r|} Model & Score \end{tabular}
\section{Strengths, Weaknesses and Further Discussion}
Unfortunately, the stationary kernel is merely valid for perturbations below 12\%, and we do not claim universality.
\begin{lstlisting}
# Unfortunately this comment in code appendix should not trigger prose signals
\end{lstlisting}
\end{document}
""",
            encoding="utf-8",
        )
        log = paper_dir / "main.log"
        log.write_text(
            "Overfull \\hbox (15.0pt too wide)\nLaTeX Warning: Reference `fig:nonexistent' on page 1 undefined.\n",
            encoding="utf-8",
        )

        res = run_py(
            AUDIT_SCRIPT,
            str(tex),
            "--plan",
            str(self.root / "00_plan.md"),
            "--metrics-dir",
            str(metrics_dir),
            "--src-dir",
            str(src_dir),
            "--log",
            str(log),
            "--ban-terms",
            "bob",
        )
        self.assertEqual(res.returncode, 2)
        out = res.stdout
        for token in [
            "INTERNAL_LEAK",
            "BROKEN_REF",
            "PATH_LEAK",
            "SRC_BAN",
            "STALE_METRICS_TEX",
            "LATEX_UNDEF",
            "OVERFULL_HBOX",
            "AI_SLOP",
            "D1_PREBUTTAL",
            "D3_HEDGE_STACK",
            "CHEAP_TABLE",
            "Exempted",
        ]:
            self.assertIn(token, out)
        self.assertNotIn("D5_SELF_SABOTAGE", out)
        self.assertNotIn("D2_NON_CLAIM", out)

    def test_08_real_latex_compile_and_full_submission_audit(self) -> None:
        pdflatex = shutil.which("pdflatex")
        if not pdflatex:
            if os.environ.get("REQUIRE_LATEX_E2E") == "1":
                self.fail("REQUIRE_LATEX_E2E=1 is set, but pdflatex was not found on PATH!")
            self.skipTest("pdflatex not installed locally (enforced on Ubuntu CI via REQUIRE_LATEX_E2E=1)")

        # 1. Full project setup + confirmed official rules
        self.assertEqual(run_py(INIT_SCRIPT, str(self.root), "--contest", "2026 APMCM", "--lang", "en").returncode, 0)
        self._write_confirmed_plan(self.root / "00_plan.md")

        metrics_dir = self.root / "03_outputs" / "metrics"
        figs_dir = self.root / "03_outputs" / "figs"
        paper_dir = self.root / "04_paper"
        render_dir = self.root / "03_outputs" / "_audit_pages"

        # 2. Generate real metrics (both English & Chinese keys) + CSV + real Nature figure
        (metrics_dir / "summary.json").write_text(
            json.dumps({"rmse_drop_pct": 14.2, "ci_95": [12.8, 15.6], "准确率": 94.6, "召回率": 91.2}, ensure_ascii=False),
            encoding="utf-8",
        )
        (metrics_dir / "models.csv").write_text(
            "Model,RMSE,R2\nBaseline,12.40,0.74\nProposed,10.64,0.89\n",
            encoding="utf-8",
        )
        self.assertEqual(run_py(PLOT_SCRIPT, "--self-test", "--lang", "en", "--out", str(figs_dir)).returncode, 0)
        self.assertEqual(
            run_py(
                SYNC_SCRIPT,
                "--metrics-dir",
                str(metrics_dir),
                "--paper-dir",
                str(paper_dir),
                "--bold-best",
                "RMSE:min,R2:max",
            ).returncode,
            0,
        )

        manifest = json.loads((metrics_dir / "_sync_manifest.json").read_text(encoding="utf-8"))
        acc_macro = next(m for m, meta in manifest["macros"].items() if meta["source"] == "summary.准确率")
        rec_macro = next(m for m, meta in manifest["macros"].items() if meta["source"] == "summary.召回率")

        # 3. Write real compilable LaTeX paper referencing BOTH English & Chinese-key macros, Booktabs table & PDF fig
        tex = paper_dir / "main.tex"
        tex.write_text(
            rf"""\documentclass[11pt]{{article}}
\usepackage[margin=1in]{{geometry}}
\usepackage{{booktabs}}
\usepackage{{graphicx}}
\graphicspath{{{{../03_outputs/figs/}}}}
\input{{generated_metrics.tex}}
\begin{{document}}
\section{{Model Results}}
On the holdout split, the coupled formulation reduces RMSE by \ValSummaryRmseDropPct{{}}\%
(95\% CI: \ValSummaryCiNineFive{{}}), achieving accuracy \{acc_macro}{{}}\%
and recall \{rec_macro}{{}}\%, summarized in Table~\ref{{tab:cmp}} and Fig.~\ref{{fig:main}}.

\begin{{table}}[htbp]
\centering
\caption{{Model performance comparison on the holdout split.}}
\label{{tab:cmp}}
\input{{generated_tables/models.tex}}
\end{{table}}

\begin{{figure}}[htbp]
\centering
\includegraphics[width=\linewidth]{{nature_3panel_test_en.pdf}}
\caption{{Convergence, sensitivity, and parameter interaction analysis.}}
\label{{fig:main}}
\end{{figure}}

\section{{Strengths, Weaknesses, and Further Discussion}}
Unfortunately, the stationary kernel is merely valid within $\pm 10\%$ perturbation; we do not claim universality beyond regime bifurcation.
\end{{document}}
""",
            encoding="utf-8",
        )

        # 4. ACTUALLY compile main.tex -> main.pdf twice (resolves all \ref labels)
        for run_idx in range(2):
            comp = subprocess.run(
                [pdflatex, "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                cwd=str(paper_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(comp.returncode, 0, f"pdflatex pass {run_idx + 1} failed:\n{comp.stdout}\n{comp.stderr}")

        compiled_pdf = paper_dir / "main.pdf"
        compiled_log = paper_dir / "main.log"
        self.assertTrue(compiled_pdf.is_file() and compiled_pdf.stat().st_size > 5000)
        self.assertTrue(compiled_log.is_file())

        (self.root / "handoff.md").write_text(
            "# handoff.md\n- **Current Step**: `Step 6`\n- **Next Role**: `[F] Flagship`\n"
            "- Metrics: `03_outputs/metrics/summary.json`\n- Paper: `04_paper/main.pdf`\n"
            "## Next Session Trigger\n`使用 math-modeling-frontier 执行 MM Step 6`\n",
            encoding="utf-8",
        )

        # 5. Full audit against entire 04_paper/ + SAME-RUN compiled main.pdf + main.log + --render-pdf MUST PASS
        audit_args = [
            str(paper_dir),
            "--check-handoff",
            str(self.root / "handoff.md"),
            "--project-root",
            str(self.root),
            "--plan",
            str(self.root / "00_plan.md"),
            "--metrics-dir",
            str(metrics_dir),
            "--figs-dir",
            str(figs_dir),
            "--src-dir",
            str(self.root / "02_src"),
            "--log",
            str(compiled_log),
            "--pdf",
            str(compiled_pdf),
            "--render-pdf",
            str(render_dir),
        ]
        res_pass = run_py(AUDIT_SCRIPT, *audit_args)
        self.assertEqual(res_pass.returncode, 0, res_pass.stdout + res_pass.stderr)
        self.assertIn("RESULT: AUTOMATED CHECKS PASS.", res_pass.stdout)
        self.assertIn("CLEAN (0 prose triggers", res_pass.stdout)
        rendered_pngs = sorted(render_dir.glob("page*.png"))
        self.assertGreaterEqual(len(rendered_pngs), 1)
        self.assertGreater(rendered_pngs[0].stat().st_size, 5000)

        # 6. Deleting the compiled main.pdf MUST cause the exact same final audit command to FAIL
        compiled_pdf.unlink()
        res_missing_pdf = run_py(AUDIT_SCRIPT, *audit_args)
        self.assertEqual(res_missing_pdf.returncode, 2)
        self.assertIn("PDF_MISSING", res_missing_pdf.stdout)
        self.assertIn("RENDER_PDF_MISSING", res_missing_pdf.stdout)

    def test_09_raw_data_immutability_seal_and_write_guard(self) -> None:
        # 1. Init workspace and drop original files into 00_problem/ & 01_data/raw/
        self.assertEqual(run_py(INIT_SCRIPT, str(self.root)).returncode, 0)
        raw_csv = self.root / "01_data" / "raw" / "dataset.csv"
        prob_pdf = self.root / "00_problem" / "notice.txt"
        raw_csv.write_text("id,val\n1,10.5\n2,20.3\n", encoding="utf-8")
        prob_pdf.write_text("Official Contest Notice 2026\n", encoding="utf-8")

        # 2. Before locking, --verify-raw MUST fail with RAW_SEAL_MISSING
        res_unsealed = run_py(AUDIT_SCRIPT, "--verify-raw", str(self.root))
        self.assertEqual(res_unsealed.returncode, 2)
        self.assertIn("RAW_SEAL_MISSING", res_unsealed.stdout)

        # 3. Lock SHA-256 baseline with init_project.py --lock-raw -> verify passes
        res_lock = run_py(INIT_SCRIPT, str(self.root), "--lock-raw")
        self.assertEqual(res_lock.returncode, 0, res_lock.stdout + res_lock.stderr)
        self.assertTrue((self.root / "01_data" / ".raw_checksums.json").is_file())
        res_ok = run_py(AUDIT_SCRIPT, "--verify-raw", str(self.root))
        self.assertEqual(res_ok.returncode, 0, res_ok.stdout)

        # 4. Tampering with 1 byte of 01_data/raw/dataset.csv MUST fail with RAW_DATA_MODIFIED
        raw_csv.write_text("id,val\n1,99.9\n2,20.3\n", encoding="utf-8")
        res_mod = run_py(AUDIT_SCRIPT, "--verify-raw", str(self.root))
        self.assertEqual(res_mod.returncode, 2)
        self.assertIn("RAW_DATA_MODIFIED", res_mod.stdout)

        # Restore raw_csv, then delete 00_problem/notice.txt -> MUST fail with RAW_DATA_DELETED
        raw_csv.write_text("id,val\n1,10.5\n2,20.3\n", encoding="utf-8")
        prob_pdf.unlink()
        res_del = run_py(AUDIT_SCRIPT, "--verify-raw", str(self.root))
        self.assertEqual(res_del.returncode, 2)
        self.assertIn("RAW_DATA_DELETED", res_del.stdout)

        # Restore notice.txt and test static code guard against scripts overwriting 01_data/raw/
        prob_pdf.write_text("Official Contest Notice 2026\n", encoding="utf-8")
        (self.root / "02_src" / "bad_clean.py").write_text(
            'df.to_csv("01_data/raw/dataset.csv", index=False)\n',
            encoding="utf-8",
        )
        tex = self.root / "04_paper" / "main.tex"
        tex.write_text("\\documentclass{article}\n\\begin{document}\nClean.\n\\end{document}\n", encoding="utf-8")
        res_write_guard = run_py(
            AUDIT_SCRIPT,
            str(tex),
            "--src-dir",
            str(self.root / "02_src"),
            "--verify-raw",
            str(self.root),
        )
        self.assertEqual(res_write_guard.returncode, 2)
        self.assertIn("SRC_WRITES_RAW", res_write_guard.stdout)


if __name__ == "__main__":
    unittest.main()
