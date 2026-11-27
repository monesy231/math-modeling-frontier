#!/usr/bin/env python3
"""
End-to-end test suite for math-modeling-frontier v2.0 scripts:
  - init_project.py (O(1) workspace + Prompt Traceability + Parameter Provenance + SHA-256 raw seal)
  - plot_style.py (headless Agg backend + monochrome palette + legend collision guard + group_close_points + plot_delta_bars)
  - sync_metrics.py (Chinese/Unicode unique macros, collision abort, deep-array NaN guard, BOM tolerance, orphan pruning, manifest)
  - audit_paper.py (missing-artifact hard fail, failed PDF render hard fail,
    field-by-field 00_plan.md Sec. 0 rule & body-vs-appendix page-limit gate,
    appendix source-listing LaTeX exemption, AST zip-strict verifier check,
    Stage 2 substantive checks [ABSTRACT_AUDIT_CLUTTER, THIN_MATH_DERIVATION,
    UNGROUNDED_PARAM_WEIGHT, APPENDIX_BLOAT, APPENDIX_BOILERPLATE_CODE],
    full math-token PDF scan including merged '\\inI', Markdown '$' balance,
    PDF/HTML vs metrics freshness gate, HTML JSON payload validation, cited
    supplementary figures, cross-platform font & inline-math builder guards,
    deliverable CSV decimal consistency, raw-data seal, orphan table guard)
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

        fig3, ax3 = ps.create_journal_fig(1, 1, width="single", height=2.2)
        ax3.scatter([0.1, 0.102, 0.85], [0.2, 0.201, 0.85])
        ax3.set_xlim(0.0, 1.0)
        ax3.set_ylim(0.0, 1.0)
        clusters = ps.group_close_points(ax3, [(0.1, 0.2), (0.102, 0.201), (0.85, 0.85)], min_dist_pt=12.0)
        self.assertEqual(clusters, [[0, 1], [2]])
        ps.plt.close(fig3)

        fig4, ax4 = ps.create_journal_fig(1, 1, width="single", height=2.2)
        ps.plot_delta_bars(ax4, ["5d", "10d", "20d", "40d"], [1.02, 0.81, 0.86, -0.15], ylabel="Gain (pp)")
        pdf4, png4 = ps.save_fig(fig4, "delta_bars_test", out_dir=str(out_dir))
        self.assertTrue(pdf4.is_file() and pdf4.stat().st_size > 1000)
        self.assertTrue(png4.is_file() and png4.stat().st_size > 1000)

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

        # NaN must abort with non-zero exit code (both scalar and deep >6-item array)
        (metrics_dir / "bad_nan.json").write_text('{"score": NaN}', encoding="utf-8")
        res_nan = run_py(SYNC_SCRIPT, "--metrics-dir", str(metrics_dir), "--paper-dir", str(paper_dir))
        self.assertNotEqual(res_nan.returncode, 0)
        (metrics_dir / "bad_nan.json").write_text(
            '{"scenarios": [1, 2, 3, 4, 5, 6, 7, {"gain": Infinity}]}', encoding="utf-8-sig"
        )
        res_deep_inf = run_py(SYNC_SCRIPT, "--metrics-dir", str(metrics_dir), "--paper-dir", str(paper_dir))
        self.assertNotEqual(res_deep_inf.returncode, 0)
        (metrics_dir / "bad_nan.json").unlink()

        # Clean UTF-8-BOM JSON must still sync cleanly
        (metrics_dir / "bom_ok.json").write_text('{"bom_metric": 3.14}', encoding="utf-8-sig")
        self.assertEqual(run_py(SYNC_SCRIPT, "--metrics-dir", str(metrics_dir), "--paper-dir", str(paper_dir)).returncode, 0)

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
        self.assertTrue((render_dir / ".gitignore").is_file())

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

        # Restore notice.txt, verify dropping an unsealed mid-contest file hard-fails until re-locked
        prob_pdf.write_text("Official Contest Notice 2026\n", encoding="utf-8")
        extra_tmpl = self.root / "00_problem" / "extra_template.md"
        extra_tmpl.write_text("# Official Companion Template\n", encoding="utf-8")
        res_unsealed_new = run_py(AUDIT_SCRIPT, "--verify-raw", str(self.root))
        self.assertEqual(res_unsealed_new.returncode, 2)
        self.assertIn("RAW_UNSEALED_FILE", res_unsealed_new.stdout)
        self.assertEqual(run_py(INIT_SCRIPT, str(self.root), "--lock-raw").returncode, 0)
        res_relocked = run_py(AUDIT_SCRIPT, "--verify-raw", str(self.root))
        self.assertEqual(res_relocked.returncode, 0, res_relocked.stdout)

        # Test static code guard against scripts overwriting 01_data/raw/
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

    def test_10_deliverable_csv_auditor(self) -> None:
        self.assertEqual(run_py(INIT_SCRIPT, str(self.root)).returncode, 0)
        self.assertTrue((self.root / ".gitattributes").is_file())

        out_dir = self.root / "03_outputs" / "deliverables"
        out_dir.mkdir(parents=True, exist_ok=True)
        alloc_csv = out_dir / "allocation.csv"

        # 1. Clean UTF-8 CSV without BOM or duplicate keys -> PASS with 0 warnings
        alloc_csv.write_text(
            "提单号,子仓,提货时刻,配货方数,批次键\n"
            "B-001,101,2026-10-02 00:00:00,10.5000,10\n"
            "B-002,260,2026-10-02 00:00:00,8.2500,11\n",
            encoding="utf-8",
        )
        res_clean = run_py(AUDIT_SCRIPT, "--check-csv", str(out_dir), "--strict-csv")
        self.assertEqual(res_clean.returncode, 0, res_clean.stdout)
        self.assertIn("PASS (0 hard CSV failures)", res_clean.stdout)

        # 2. UTF-8 BOM (utf-8-sig) + unmerged duplicate decision-variable keys -> WARN by default, FAIL under --strict-csv
        alloc_csv.write_text(
            "提单号,子仓,提货时刻,配货方数,批次键\n"
            "B-001,101,2026-10-02 00:00:00,6.0000,10\n"
            "B-001,101,2026-10-02 00:00:00,4.5000,10\n",
            encoding="utf-8-sig",
        )
        res_warn = run_py(AUDIT_SCRIPT, "--check-csv", str(alloc_csv))
        self.assertEqual(res_warn.returncode, 0)
        self.assertIn("CSV_UTF8_BOM", res_warn.stdout)
        self.assertIn("CSV_UNMERGED_DUPLICATE_KEY", res_warn.stdout)

        res_strict = run_py(AUDIT_SCRIPT, "--check-csv", str(alloc_csv), "--strict-csv")
        self.assertEqual(res_strict.returncode, 2)
        self.assertIn("CSV_UTF8_BOM", res_strict.stdout)
        self.assertIn("CSV_UNMERGED_DUPLICATE_KEY", res_strict.stdout)

        # 3. NaN/Inf or exact duplicate row -> HARD FAIL even without --strict-csv
        alloc_csv.write_text(
            "提单号,子仓,提货时刻,配货方数,批次键\n"
            "B-001,101,2026-10-02 00:00:00,NaN,10\n"
            "B-002,260,2026-10-02 00:00:00,8.2500,11\n"
            "B-002,260,2026-10-02 00:00:00,8.2500,11\n",
            encoding="utf-8",
        )
        res_bad = run_py(AUDIT_SCRIPT, "--check-csv", str(alloc_csv))
        self.assertEqual(res_bad.returncode, 2)
        self.assertIn("CSV_NAN_OR_INF", res_bad.stdout)
        self.assertIn("CSV_EXACT_DUPLICATE_ROW", res_bad.stdout)

    def test_11_companion_rules_degenerate_change_and_page_mismatch(self) -> None:
        self.assertEqual(run_py(INIT_SCRIPT, str(self.root)).returncode, 0)
        paper_md = self.root / "04_paper" / "report.md"
        companion_md = self.root / "作品说明单.md"
        verifier_py = self.root / "02_src" / "audit_submission.py"

        # 1. Bad prose: degenerate "由 X 降至 X", >60-char summary, template instruction leak, unsafe zip, and page mismatch
        paper_md.write_text(
            "# 建模与实验报告\n\n"
            "反事实对照表明全期满票由 2,586 票降至 2,586，且误差 decreased from 14.2% to 14.2%。\n"
            "已生成 15 页技术报告。\n",
            encoding="utf-8",
        )
        companion_md.write_text(
            "# 作品说明单\n"
            "> 引用块（以 `>` 开头）是填写提示，定稿时请删除。\n\n"
            "## 01 队伍与赛题\n"
            "| 队伍名称 | 参赛队名（提交前按官方报名表填写） |\n\n"
            "## 02 一句话概述\n"
            "这是一段故意超过六十个字符限制的一句话概述文本，用来测试自动化终审脚本能否精准拦截作品说明单字数超标的问题并给出明确报错提示信息。\n",
            encoding="utf-8",
        )
        verifier_py.write_text(
            "def check_rows(sr, br):\n"
            "    for s_row, b_row in zip(sr, br):\n"
            "        assert s_row == b_row\n",
            encoding="utf-8",
        )
        pdf_path = self.root / "04_paper" / "report.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj << /Type /Page >> endobj\n")

        res_fail = run_py(
            AUDIT_SCRIPT,
            str(paper_md),
            "--src-dir",
            str(self.root / "02_src"),
            "--pdf",
            str(pdf_path),
        )
        self.assertEqual(res_fail.returncode, 2)
        self.assertIn("DEGENERATE_CHANGE", res_fail.stdout)
        self.assertIn("TEMPLATE_INSTRUCTION_LEAK", res_fail.stdout)
        self.assertIn("SUMMARY_OVER_60_CHARS", res_fail.stdout)
        self.assertIn("PDF_PAGE_COUNT_MISMATCH", res_fail.stdout)
        self.assertIn("REGISTRATION_PLACEHOLDER", res_fail.stdout)
        self.assertIn("SRC_UNSAFE_ZIP_COMPARE", res_fail.stdout)

        # 2. Clean prose: valid transition "由 2,589 票降至 2,586", unit conversion "由 2,586 万元降至 2,586 元",
        #    <=60-char summary, zip_longest in verifier, and no page-count mismatch -> PASS
        paper_md.write_text(
            "# 建模与实验报告\n\n"
            "反事实对照表明全期满票由 2,589 票降至 2,586（单位换算示例：由 2,586 万元降至 2,586 元）。\n",
            encoding="utf-8",
        )
        companion_md.write_text(
            "# 作品说明单\n\n"
            "## 02 一句话概述\n"
            "针对跨境空运货源与舱位提单动态配载，提出因果时域滚动拼载算法RH-MWRA，2.2s达成100%评估满票并五维占优。\n",
            encoding="utf-8",
        )
        verifier_py.write_text(
            "from itertools import zip_longest\n"
            "def check_rows(sr, br):\n"
            "    for s_row, b_row in zip_longest(sr, br):\n"
            "        assert s_row == b_row\n",
            encoding="utf-8",
        )
        res_ok = run_py(
            AUDIT_SCRIPT,
            str(paper_md),
            "--src-dir",
            str(self.root / "02_src"),
            "--pdf",
            str(pdf_path),
        )
        self.assertEqual(res_ok.returncode, 0, res_ok.stdout)
        self.assertIn("58/60 chars", res_ok.stdout)

    def test_12_v15_page_limit_supp_figs_font_portability_and_html_audit(self) -> None:
        from matplotlib.backends.backend_pdf import PdfPages
        import matplotlib.pyplot as plt

        self.assertEqual(run_py(INIT_SCRIPT, str(self.root)).returncode, 0)
        plan_path = self.root / "00_plan.md"
        paper_dir = self.root / "04_paper"
        figs_dir = self.root / "03_outputs" / "figs"
        src_dir = self.root / "02_src"

        def write_plan_with_page_rule(rule_line: str) -> None:
            plan_path.write_text(
                "# 00_plan.md\n\n"
                "## 0. Live Official Rules\n"
                "- **Format & Template**: Markdown + PDF (Source: 00_problem/notice.md)\n"
                "- **Deadline / Window**: Dec 9 23:59 (Source: 00_problem/notice.md)\n"
                f"- **Hard Page / Word Limit**: {rule_line}\n"
                "- **Anonymity & Metadata**: Verified team header (Source: 00_problem/notice.md)\n"
                "- **AI Declaration Policy**: Log AI usage (Source: 00_problem/notice.md)\n"
                "- **Required Extras**: Runnable code + CSV (Source: 00_problem/notice.md)\n\n"
                "## 1. Workflow\n",
                encoding="utf-8",
            )

        # 1. Generate real 12-page PDF and prepare embedded, path-cited supplementary, and orphan figures
        pdf_12 = paper_dir / "report.pdf"
        with PdfPages(pdf_12) as pp:
            for idx in range(12):
                fig_p = plt.figure(figsize=(3.5, 2.5))
                fig_p.text(0.5, 0.5, f"Page {idx + 1}", ha="center", va="center")
                pp.savefig(fig_p)
                plt.close(fig_p)

        for fname in ("fig_embed.png", "fig_supp.png", "fig_orphan.png"):
            (figs_dir / fname).write_bytes(b"PNG_PLACEHOLDER")

        paper_md = paper_dir / "report.md"
        paper_md.write_text(
            "# Report\n\n"
            "![Main Figure](../03_outputs/figs/fig_embed.png)\n\n"
            "Full dynamics appear in supplementary file `03_outputs/figs/fig_supp.png`.\n",
            encoding="utf-8",
        )

        # 2. Unguarded OS font path in 04_paper/build_report.py triggers [SRC_OS_FONT_HARDCODE]
        builder_py = paper_dir / "build_report.py"
        builder_py.write_text(
            'FONT_PATH = r"C:\\Windows\\Fonts\\simhei.ttf"\n',
            encoding="utf-8",
        )

        # 10-page hard cap in 00_plan.md MUST fail 12-page PDF with PDF_OVER_PAGE_LIMIT
        write_plan_with_page_rule("一般不超过 10 页，一句话概述 <= 60 字（Source: 00_problem/notice.md）")
        res_over = run_py(
            AUDIT_SCRIPT,
            str(paper_md),
            "--plan",
            str(plan_path),
            "--figs-dir",
            str(figs_dir),
            "--src-dir",
            str(src_dir),
            "--pdf",
            str(pdf_12),
        )
        self.assertEqual(res_over.returncode, 2)
        self.assertIn("PDF_OVER_PAGE_LIMIT", res_over.stdout)
        self.assertIn("SRC_OS_FONT_HARDCODE", res_over.stdout)
        self.assertIn("Cited supplementary figure(s) by path: fig_supp.png", res_over.stdout)
        self.assertIn("Figure 'fig_orphan'", res_over.stdout)
        self.assertNotIn("Figure 'fig_embed'", res_over.stdout)
        self.assertNotIn("Figure 'fig_supp'", res_over.stdout)

        # --max-pages 12 overrides and passes; adding font fallback clears SRC_OS_FONT_HARDCODE
        builder_py.write_text(
            "from pathlib import Path\n"
            'p = Path(r"C:\\Windows\\Fonts\\simhei.ttf")\n'
            'font_name = "Custom" if p.is_file() else "STSong-Light"\n',
            encoding="utf-8",
        )
        res_override = run_py(
            AUDIT_SCRIPT,
            str(paper_md),
            "--plan",
            str(plan_path),
            "--figs-dir",
            str(figs_dir),
            "--src-dir",
            str(src_dir),
            "--pdf",
            str(pdf_12),
            "--max-pages",
            "12",
        )
        self.assertEqual(res_override.returncode, 0, res_override.stdout)
        self.assertIn("Pages: 12 (hard limit <= 12)", res_override.stdout)
        self.assertNotIn("SRC_OS_FONT_HARDCODE", res_override.stdout)

        # Soft target range with explicit no-limit phrase MUST NOT trigger PDF_OVER_PAGE_LIMIT
        write_plan_with_page_rule("No strict hard cap; target 20-28 pages (Source: 00_problem/notice.md)")
        res_soft = run_py(
            AUDIT_SCRIPT,
            str(paper_md),
            "--plan",
            str(plan_path),
            "--pdf",
            str(pdf_12),
        )
        self.assertEqual(res_soft.returncode, 0, res_soft.stdout)
        self.assertNotIn("PDF_OVER_PAGE_LIMIT", res_soft.stdout)

        # 3. Offline HTML dashboard audit (--check-html)
        html_path = self.root / "03_outputs" / "dashboard.html"
        html_path.write_text(
            "<!doctype html><html><head>\n"
            '<script src="https://cdn.example.com/lib.js"></script>\n'
            "</head><body><p>Ready after Gate R</p>\n"
            "<script>const broken = {;</script>\n"
            "</body></html>\n",
            encoding="utf-8",
        )
        res_html_bad = run_py(AUDIT_SCRIPT, "--check-html", str(html_path))
        self.assertEqual(res_html_bad.returncode, 2)
        self.assertIn("INTERNAL_LEAK", res_html_bad.stdout)
        self.assertIn("HTML_EXTERNAL_DEP", res_html_bad.stdout)
        if shutil.which("node"):
            self.assertIn("HTML_JS_SYNTAX_ERROR", res_html_bad.stdout)

        html_path.write_text(
            "<!doctype html><html><body><div id='app'></div>\n"
            "<script>const metrics = {fill: 1.0}; console.log(metrics.fill);</script>\n"
            "</body></html>\n",
            encoding="utf-8",
        )
        res_html_ok = run_py(AUDIT_SCRIPT, "--check-html", str(html_path))
        self.assertEqual(res_html_ok.returncode, 0, res_html_ok.stdout)
        self.assertIn("PASS (0 hard HTML failures)", res_html_ok.stdout)
        self.assertNotIn("[WARN]", res_html_ok.stdout)

    def test_13_v16_math_glyph_freshness_json_payload_and_csv_decimals(self) -> None:
        import pymupdf as fitz  # type: ignore

        self.assertEqual(run_py(INIT_SCRIPT, str(self.root)).returncode, 0)
        self._write_confirmed_plan(self.root / "00_plan.md")
        paper_dir = self.root / "04_paper"
        metrics_dir = self.root / "03_outputs" / "metrics"
        src_dir = self.root / "02_src"

        # 1. PDF containing merged '\inI' (from '\in\mathcal{I}') MUST fail with PDF_UNRENDERED_LATEX
        bad_pdf = paper_dir / "report.pdf"
        doc_bad = fitz.open()
        p1 = doc_bad.new_page()
        p1.insert_text((72, 100), r"Cohort total Q=∑i\inIqi has unrendered set membership.")
        doc_bad.save(str(bad_pdf))
        doc_bad.close()

        # Unbalanced inline '$' in report.md + unfinished '待队长汇总' in AI协作记录.md + unsafe inline math in build_report.py
        paper_md = paper_dir / "report.md"
        paper_md.write_text(
            "# Report\n\n"
            "Valid cardinality $|\\mathcal{J}| = 10$, but broken inline math $Q = \\sum_{i \\in I} q_i here.\n",
            encoding="utf-8",
        )
        ai_log_md = self.root / "AI协作记录.md"
        ai_log_md.write_text(
            "# AI 协作记录\n\n## 03 成本与时间\n新增投入和费用仍待队长汇总。\n",
            encoding="utf-8",
        )
        builder_py = paper_dir / "build_report.py"
        builder_py.write_text(
            "import re\n"
            "def conv(text):\n"
            "    def repl(m):\n"
            "        e = m.group(1)\n"
            "        e = re.sub(r'\\\\mathcal\\{([A-Za-z]+)\\}', r'\\1', e)\n"
            "        e = re.sub(r'\\\\in(?![a-zA-Z])', '∈', e)\n"
            "        return e\n"
            "    return re.sub(r'\\$([^$]+)\\$', repl, text)\n",
            encoding="utf-8",
        )

        res_v16_fail = run_py(
            AUDIT_SCRIPT,
            str(paper_md),
            "--plan",
            str(self.root / "00_plan.md"),
            "--src-dir",
            str(src_dir),
            "--pdf",
            str(bad_pdf),
        )
        self.assertEqual(res_v16_fail.returncode, 2)
        self.assertIn("PDF_UNRENDERED_LATEX", res_v16_fail.stdout)
        self.assertIn("MD_UNBALANCED_MATH", res_v16_fail.stdout)
        self.assertIn("PLACEHOLDER", res_v16_fail.stdout)
        self.assertIn("SRC_INLINE_MATH_UNSAFE", res_v16_fail.stdout)

        # 2. Clean PDF (including Python f-string code snippet and '\inputs' path text), balanced Markdown,
        #    finalized AI协作记录.md, and wrapper-last + zero-backslash assertion in build_report.py -> PASS
        doc_ok = fitz.open()
        p_ok = doc_ok.new_page()
        p_ok.insert_text((72, 100), "Rendered math Q = sum i in I q_i and code f'page_{idx:02d}.png' in 02_src\\inputs.py")
        doc_ok.save(str(bad_pdf))
        doc_ok.close()

        paper_md.write_text(
            "# Report\n\n"
            "Balanced math $|\\mathcal{J}| = 2,034$, $Q = \\sum_{i \\in \\mathcal{I}} q_i$, and literal \\$25 cost (`$HOME`).\n",
            encoding="utf-8",
        )
        ai_log_md.write_text(
            "# AI 协作记录\n\n## 03 成本与时间\n累计 16 小时，合计 25 美元。\n",
            encoding="utf-8",
        )
        builder_py.write_text(
            "import re\n"
            "def conv(text):\n"
            "    def repl(m):\n"
            "        e = m.group(1)\n"
            "        e = re.sub(r'\\\\in(?![a-zA-Z])', '∈', e)\n"
            "        e = re.sub(r'\\\\mathcal\\{([A-Za-z]+)\\}', r'\\1', e)\n"
            '        if "\\\\" in e:\n'
            "            raise ValueError(e)\n"
            "        return e\n"
            "    return re.sub(r'\\$([^$]+)\\$', repl, text)\n",
            encoding="utf-8",
        )

        res_v16_ok = run_py(
            AUDIT_SCRIPT,
            str(paper_md),
            "--plan",
            str(self.root / "00_plan.md"),
            "--src-dir",
            str(src_dir),
            "--pdf",
            str(bad_pdf),
        )
        self.assertEqual(res_v16_ok.returncode, 0, res_v16_ok.stdout)
        self.assertNotIn("SRC_INLINE_MATH_UNSAFE", res_v16_ok.stdout)

        # 3. Stale PDF & HTML vs newer metrics JSON + invalid NaN JSON payload in HTML dashboard
        html_dash = self.root / "03_outputs" / "dashboard.html"
        html_dash.write_text(
            "<!doctype html><html><body>"
            '<script type="application/json" id="data">{"fill": NaN}</script>'
            "<script>console.log(1);</script></body></html>",
            encoding="utf-8",
        )
        res_bad_json = run_py(AUDIT_SCRIPT, "--check-html", str(html_dash))
        self.assertEqual(res_bad_json.returncode, 2)
        self.assertIn("HTML_INVALID_JSON_PAYLOAD", res_bad_json.stdout)

        html_dash.write_text(
            "<!doctype html><html><body>"
            '<script type="application/json" id="data">{"fill": 1.0}</script>'
            "<script>console.log(1);</script></body></html>",
            encoding="utf-8",
        )
        old_ts = time.time() - 30.0
        os.utime(bad_pdf, (old_ts, old_ts))
        os.utime(html_dash, (old_ts, old_ts))
        (metrics_dir / "fresh.json").write_text('{"fill": 1.0}', encoding="utf-8")

        res_stale = run_py(
            AUDIT_SCRIPT,
            str(paper_md),
            "--metrics-dir",
            str(metrics_dir),
            "--pdf",
            str(bad_pdf),
            "--check-html",
            str(html_dash),
        )
        self.assertEqual(res_stale.returncode, 2)
        self.assertIn("STALE_PDF_VS_METRICS", res_stale.stdout)
        self.assertIn("STALE_HTML_VS_METRICS", res_stale.stdout)

        # Touch PDF and HTML so they are newer than metrics -> PASS
        os.utime(bad_pdf, None)
        os.utime(html_dash, None)
        res_fresh = run_py(
            AUDIT_SCRIPT,
            str(paper_md),
            "--metrics-dir",
            str(metrics_dir),
            "--pdf",
            str(bad_pdf),
            "--check-html",
            str(html_dash),
        )
        self.assertEqual(res_fresh.returncode, 0, res_fresh.stdout)

        # 4. Deliverable CSV decimal-precision outlier & handoff 'MM Step 6' + companion pointer check
        csv_file = self.root / "03_outputs" / "alloc.csv"
        rows = ["提单号,子仓,配货方数"] + [f"B-{i:02d},W1,10.0000" for i in range(11)] + ["B-99,W1,10.00001"]
        csv_file.write_text("\n".join(rows) + "\n", encoding="utf-8")
        res_dec_warn = run_py(AUDIT_SCRIPT, "--check-csv", str(csv_file))
        self.assertEqual(res_dec_warn.returncode, 0)
        self.assertIn("CSV_INCONSISTENT_DECIMALS", res_dec_warn.stdout)
        res_dec_strict = run_py(AUDIT_SCRIPT, "--check-csv", str(csv_file), "--strict-csv")
        self.assertEqual(res_dec_strict.returncode, 2)
        self.assertIn("CSV_INCONSISTENT_DECIMALS", res_dec_strict.stdout)

        handoff = self.root / "handoff.md"
        handoff.write_text(
            "# handoff.md\n"
            "- **Current Step**: MM Step 6\n"
            "- **Next Role**: [Done]\n"
            "- **File Pointers**: `AI协作记录.md`、`作品说明单_missing.md`\n",
            encoding="utf-8",
        )
        res_ho_broken = run_py(AUDIT_SCRIPT, "--check-handoff", str(handoff), "--project-root", str(self.root))
        self.assertEqual(res_ho_broken.returncode, 2)
        self.assertIn("HANDOFF_BROKEN_PTR", res_ho_broken.stdout)
        self.assertIn("Checked 6/6 mandatory rule field(s)", res_ho_broken.stdout)

    def test_14_v20_substantive_quality_appendix_body_limit_and_plot_legend(self) -> None:
        import pymupdf as fitz  # type: ignore

        self.assertEqual(run_py(INIT_SCRIPT, str(self.root)).returncode, 0)
        plan_text = (self.root / "00_plan.md").read_text(encoding="utf-8")
        self.assertIn("Prompt Sub-Question & Requirement Traceability Checklist", plan_text)
        self.assertIn("Parameter Provenance", plan_text)
        self._write_confirmed_plan(self.root / "00_plan.md")

        paper_dir = self.root / "04_paper"
        src_dir = self.root / "02_src"

        # 1. PDF body-start-page, appendix code-listing exemption, --max-appendix-pages, and bloat/boilerplate signals
        # Layout: p1 Summary, p2 TOC, p3-6 Body (4 pages), p7-40 Appendix (34 pages, > 1.5x body and > 30p)
        pdf_40 = paper_dir / "submission.pdf"
        doc = fitz.open()
        doc.new_page().insert_text((72, 100), "Summary Page\nKey findings here.")
        doc.new_page().insert_text((72, 100), "Table of Contents\n1. Model ... 1\nAppendix ... 5")
        for b_idx in range(4):
            doc.new_page().insert_text((72, 100), f"Body Section {b_idx + 1}\nClean rendered body text.")
        doc.new_page().insert_text(
            (72, 100),
            "Appendix A\nA.1 Source Code Listings\nbuild_report.py\n" + r"latex_token = '\\in\\mathcal{I}'",
        )
        for a_idx in range(33):
            doc.new_page().insert_text(
                (72, 100),
                f"02_src/solver_{a_idx}.py\n" + r"expr = re.sub(r'\\in', 'in', s) + r'\alpha'",
            )
        doc.save(str(pdf_40))
        doc.close()

        clean_tex = paper_dir / "main.tex"
        clean_tex.write_text("\\documentclass{article}\n\\begin{document}\nShort clean paper.\n\\end{document}\n", encoding="utf-8")

        # Body = 4 pages <= 5 -> PASS Stage 1, but PDF Stage 2 flags APPENDIX_BLOAT & APPENDIX_BOILERPLATE_CODE
        res_body_ok = run_py(
            AUDIT_SCRIPT,
            str(clean_tex),
            "--pdf",
            str(pdf_40),
            "--body-start-page",
            "3",
            "--max-pages",
            "5",
        )
        self.assertEqual(res_body_ok.returncode, 0, res_body_ok.stdout)
        self.assertIn("Main body: 4 page(s) starting at page 3; appendix starts on page 7", res_body_ok.stdout)
        self.assertIn("Appendix source-listing pages exempted from LaTeX scan: 34 page(s)", res_body_ok.stdout)
        self.assertIn("APPENDIX_BLOAT", res_body_ok.stdout)
        self.assertIn("APPENDIX_BOILERPLATE_CODE", res_body_ok.stdout)

        # Body = 4 pages > 3 -> HARD FAIL PDF_OVER_PAGE_LIMIT; Appendix = 34 > 20 -> HARD FAIL PDF_APPENDIX_OVER_LIMIT
        res_body_over = run_py(
            AUDIT_SCRIPT,
            str(clean_tex),
            "--pdf",
            str(pdf_40),
            "--body-start-page",
            "3",
            "--max-pages",
            "3",
            "--max-appendix-pages",
            "20",
        )
        self.assertEqual(res_body_over.returncode, 2)
        self.assertIn("PDF_OVER_PAGE_LIMIT", res_body_over.stdout)
        self.assertIn("PDF_APPENDIX_OVER_LIMIT", res_body_over.stdout)

        # Unrendered LaTeX inside BODY page MUST still hard-fail even with appendix exemption active
        doc_bad_body = fitz.open()
        doc_bad_body.new_page().insert_text((72, 100), "Summary")
        doc_bad_body.new_page().insert_text((72, 100), "Contents")
        doc_bad_body.new_page().insert_text((72, 100), r"Body leak x \in\mathcal{I} here.")
        bad_body_pdf = paper_dir / "bad_body.pdf"
        doc_bad_body.save(str(bad_body_pdf))
        doc_bad_body.close()
        res_bad_body = run_py(
            AUDIT_SCRIPT,
            str(clean_tex),
            "--pdf",
            str(bad_body_pdf),
            "--body-start-page",
            "3",
            "--max-pages",
            "10",
        )
        self.assertEqual(res_bad_body.returncode, 2)
        self.assertIn("PDF_UNRENDERED_LATEX", res_bad_body.stdout)

        # 2. Substantive Stage 2 signals on a full-length manuscript (.tex) vs. polished counterpart
        filler_para = " ".join(["acoustic propagation and behavioral response dynamics across marine habitats"] * 60)
        bad_tex = paper_dir / "bad_substantive.tex"
        bad_tex.write_text(
            "\\documentclass{article}\n\\begin{document}\n"
            "\\begin{abstract}\n"
            "In a 2\\times2 factorial design, Holm adjustment yields p=0.013. Nested LOO-45 bootstrap "
            "gives OOF NLL 1.31. Under the assumed masking function, V12/B500 is a candidate for field testing.\n"
            "\\end{abstract}\n"
            "\\section{Task 1: Acoustic Model}\n"
            f"{filler_para}\n"
            "\\section{Task 2: Propagation Model}\n"
            f"{filler_para}\n"
            "\\section{Task 3: Policy Optimization}\n"
            "Using the assumed masking function and illustrative weights, we evaluate:\n"
            "\\begin{equation}\n"
            "\\eta(V,B) = 0.2412 (V/18)^{1.835} \\exp(-(B-100)/700.5).\n"
            "\\end{equation}\n"
            f"{filler_para}\n"
            "\\appendix\n\\section{Appendix}\n"
            "\\lstinputlisting{build_report.py}\n"
            "\\end{document}\n",
            encoding="utf-8",
        )
        res_subst_bad = run_py(AUDIT_SCRIPT, str(bad_tex))
        self.assertEqual(res_subst_bad.returncode, 0, res_subst_bad.stdout)
        self.assertIn("ABSTRACT_AUDIT_CLUTTER", res_subst_bad.stdout)
        self.assertIn("THIN_MATH_DERIVATION", res_subst_bad.stdout)
        self.assertIn("UNGROUNDED_PARAM_WEIGHT", res_subst_bad.stdout)
        self.assertIn("APPENDIX_BOILERPLATE_CODE", res_subst_bad.stdout)

        # Polished manuscript: clean 4-beat abstract, >=6 display equations covering modeling sections,
        # calibrated/cited equations, and core modeling script only in appendix -> CLEAN
        eq_block = lambda idx: (
            f"\\begin{{equation}}\ny_{{{idx}}} = \\alpha_{{{idx}}} x_{{{idx}}} + \\beta_{{{idx}}}.\n\\end{{equation}}\n"
        )
        good_tex = paper_dir / "good_substantive.tex"
        good_tex.write_text(
            "\\documentclass{article}\n\\begin{document}\n"
            "\\begin{abstract}\n"
            "Oceanic vessel noise compresses penguin communication corridors by 42\\%. "
            "Coupling grazing acoustic decay with truncated lognormal latency predicts a 174 m calm effective radius "
            "that preserves 89.8\\% active corridor area under a 12 kn speed cap and 500 m setback.\n"
            "\\end{abstract}\n"
            "\\section{Task 1: Acoustic Model}\n"
            f"{filler_para}\n{eq_block(1)}{eq_block(2)}"
            "\\section{Task 2: Propagation Model}\n"
            f"{filler_para}\n{eq_block(3)}{eq_block(4)}"
            "\\section{Task 3: Policy Optimization}\n"
            "Fitted via maximum likelihood and calibrated in Table 1 \\cite{ref1}:\n"
            "\\begin{equation}\n"
            "\\eta(V,B) = 0.2412 (V/18)^{1.835} \\exp(-(B-100)/700.5).\n"
            "\\end{equation}\n"
            f"{filler_para}\n{eq_block(5)}"
            "\\appendix\n\\section{Appendix}\n"
            "\\lstinputlisting{../02_src/run_experiments.py}\n"
            "\\end{document}\n",
            encoding="utf-8",
        )
        res_subst_ok = run_py(AUDIT_SCRIPT, str(good_tex))
        self.assertEqual(res_subst_ok.returncode, 0, res_subst_ok.stdout)
        self.assertIn("CLEAN (0 prose/substantive triggers", res_subst_ok.stdout)

        # 3. Multi-line AST zip(..., strict=True) verifier check
        verify_py = src_dir / "verify_multi.py"
        verify_py.write_text(
            "def chk(a, b):\n"
            "    for x, y in enumerate(\n"
            "        zip(a, b)\n"
            "    ):\n"
            "        assert x >= 0 and y == y\n",
            encoding="utf-8",
        )
        res_zip_warn = run_py(AUDIT_SCRIPT, str(good_tex), "--src-dir", str(src_dir))
        self.assertEqual(res_zip_warn.returncode, 0)
        self.assertIn("SRC_UNSAFE_ZIP_COMPARE", res_zip_warn.stdout)

        verify_py.write_text(
            "def chk(a, b):\n"
            "    for x, y in enumerate(\n"
            "        zip(a, b, strict=True)\n"
            "    ):\n"
            "        assert x >= 0 and y == y\n",
            encoding="utf-8",
        )
        res_zip_ok = run_py(AUDIT_SCRIPT, str(good_tex), "--src-dir", str(src_dir))
        self.assertEqual(res_zip_ok.returncode, 0)
        self.assertNotIn("SRC_UNSAFE_ZIP_COMPARE", res_zip_ok.stdout)

        # 4. plot_style.py monochrome palette + legend-on-text collision check
        sys.path.insert(0, str(SCRIPTS_DIR))
        try:
            import plot_style as ps
        finally:
            if str(SCRIPTS_DIR) in sys.path:
                sys.path.remove(str(SCRIPTS_DIR))

        self.assertEqual(ps.DOCUMENT_PALETTE_MONOCHROME["heading"], "#000000")
        self.assertEqual(ps.DOCUMENT_PALETTE_MONOCHROME["surface"], "#FFFFFF")
        fig_leg, ax_leg = ps.create_journal_fig(1, 1, width="single", height=2.2)
        ax_leg.plot([0, 1], [0, 1], label="Series A")
        ax_leg.legend(loc="upper left")
        ax_leg.text(0.05, 0.92, "Colliding Legend Label", transform=ax_leg.transAxes)
        warns_leg = ps.check_figure_layout(fig_leg)
        ps.plt.close(fig_leg)
        self.assertTrue(any("Legend" in w for w in warns_leg), f"Expected legend overlap warning, got: {warns_leg}")


if __name__ == "__main__":
    unittest.main()
