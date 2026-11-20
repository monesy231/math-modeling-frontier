#!/usr/bin/env python3
"""
End-to-end test suite for math-modeling-frontier v1.1 scripts:
  - init_project.py
  - plot_style.py (headless Agg backend)
  - sync_metrics.py
  - audit_paper.py (Stage 1 hard gates, section-aware Stage 2, handoff & plan gates)

Run:
    python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import os
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

    def _fill_confirmed_plan(self, plan_path: Path) -> None:
        text = plan_path.read_text(encoding="utf-8")
        text = text.replace("[EXTRACT FROM 00_problem/]", "Verified: English LaTeX, 25p max, Blind, AI Appendix OK")
        text = text.replace("[待核验]", "Confirmed")
        plan_path.write_text(text, encoding="utf-8")

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

        # Fresh handoff.md (Step 0 -> Step 1) must pass contract check
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

        # 1. Multi-panel figure: CI + zoom inset + tornado + heatmap + direct_label + panel labels
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

        # 2. Vector pipeline diagram
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

    def test_03_sync_metrics_macros_booktabs_and_nan_rejection(self) -> None:
        run_py(INIT_SCRIPT, str(self.root))
        metrics_dir = self.root / "03_outputs" / "metrics"
        paper_dir = self.root / "04_paper"

        (metrics_dir / "model_comparison.json").write_text(
            json.dumps({"rmse_baseline": 12.403, "rmse_proposed": 10.641, "ci_95": [12.8, 15.6], "n_samples": 12500}),
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

        macros = (paper_dir / "generated_metrics.tex").read_text(encoding="utf-8")
        self.assertIn(r"\newcommand{\ValModelComparisonRmseProposed}{10.64}", macros)
        self.assertIn(r"\newcommand{\ValModelComparisonCiNineFive}{[12.80, 15.60]}", macros)
        self.assertIn(r"\newcommand{\ValModelComparisonNSamples}{12,500}", macros)
        self.assertNotIn("sync_metrics.py", macros)

        table = (paper_dir / "generated_tables" / "comparison.tex").read_text(encoding="utf-8")
        self.assertIn(r"\begin{tabular}{lrr}", table)
        self.assertIn(r"\toprule", table)
        self.assertIn(r"\textbf{10.64}", table)
        self.assertIn(r"\textbf{0.89}", table)
        self.assertNotIn("|", table)

        # NaN must be rejected cleanly
        (metrics_dir / "bad_nan.json").write_text('{"score": NaN}', encoding="utf-8")
        res_nan = run_py(SYNC_SCRIPT, "--metrics-dir", str(metrics_dir), "--paper-dir", str(paper_dir))
        self.assertNotEqual(res_nan.returncode, 0)

    def test_04_handoff_cap_and_plan_live_rule_gates(self) -> None:
        run_py(INIT_SCRIPT, str(self.root))
        plan_path = self.root / "00_plan.md"

        # Unconfirmed 00_plan.md MUST fail --plan gate
        res_plan_fail = run_py(AUDIT_SCRIPT, "--plan", str(plan_path))
        self.assertEqual(res_plan_fail.returncode, 2)
        self.assertIn("UNVERIFIED_CONTEST_RULE", res_plan_fail.stdout)

        # Moving handoff to Step 2 while 00_plan.md is still unconfirmed MUST fail automatically
        handoff = self.root / "handoff.md"
        handoff.write_text(
            "# handoff.md\n- **Current Step**: `Step 2`\n- **Next Role**: `[W]`\n- Plan: `00_plan.md`\n",
            encoding="utf-8",
        )
        res_step2_fail = run_py(AUDIT_SCRIPT, "--check-handoff", str(handoff), "--project-root", str(self.root))
        self.assertEqual(res_step2_fail.returncode, 2)
        self.assertIn("UNVERIFIED_CONTEST_RULE", res_step2_fail.stdout)

        # Confirming 00_plan.md clears the gate
        self._fill_confirmed_plan(plan_path)
        res_step2_pass = run_py(AUDIT_SCRIPT, "--check-handoff", str(handoff), "--project-root", str(self.root))
        self.assertEqual(res_step2_pass.returncode, 0, res_step2_pass.stdout)

        # >80 lines (or >custom --max-lines) + fenced code + broken pointer MUST fail
        bloated = [
            "# handoff.md",
            "- **Current Step**: `Step 2`",
            "- **Next Role**: `[W]`",
            "```python",
            "x = 1",
            "```",
            "- Pointer: `03_outputs/metrics/missing.json`",
        ] + [f"- filler line {i}" for i in range(85)]
        handoff.write_text("\n".join(bloated), encoding="utf-8")
        res_bloat = run_py(AUDIT_SCRIPT, "--check-handoff", str(handoff), "--project-root", str(self.root))
        self.assertEqual(res_bloat.returncode, 2)
        self.assertIn("HANDOFF_BLOAT", res_bloat.stdout)
        self.assertIn("HANDOFF_CODE_PASTE", res_bloat.stdout)
        self.assertIn("HANDOFF_BROKEN_PTR", res_bloat.stdout)

        # Custom --max-lines 95 allows 92 lines if code/ptr removed
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

    def test_05_stage1_hard_gates_and_section_aware_stage2(self) -> None:
        run_py(INIT_SCRIPT, str(self.root))
        self._fill_confirmed_plan(self.root / "00_plan.md")

        metrics_dir = self.root / "03_outputs" / "metrics"
        paper_dir = self.root / "04_paper"
        src_dir = self.root / "02_src"

        # Create synced metrics, then make JSON newer to trigger STALE_METRICS_TEX
        json_path = metrics_dir / "res.json"
        json_path.write_text('{"acc": 0.91}', encoding="utf-8")
        run_py(SYNC_SCRIPT, "--metrics-dir", str(metrics_dir), "--paper-dir", str(paper_dir))
        gen_tex = paper_dir / "generated_metrics.tex"
        os.utime(gen_tex, (time.time() - 10, time.time() - 10))
        os.utime(json_path, None)

        # Hardcoded local path inside 02_src/
        (src_dir / "leaky.py").write_text('p = r"C:\\Users\\bob\\data.csv"\n', encoding="utf-8")

        # LaTeX paper testing section-aware Stage 2 suppression + Stage 1 catches
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
        # Stage 1 catches
        self.assertIn("INTERNAL_LEAK", out)
        self.assertIn("BROKEN_REF", out)
        self.assertIn("PATH_LEAK", out)
        self.assertIn("SRC_BAN", out)
        self.assertIn("STALE_METRICS_TEX", out)
        self.assertIn("LATEX_UNDEF", out)
        self.assertIn("OVERFULL_HBOX", out)

        # Stage 2 catches in Introduction
        self.assertIn("AI_SLOP", out)
        self.assertIn("D1_PREBUTTAL", out)
        self.assertIn("D3_HEDGE_STACK", out)
        self.assertIn("CHEAP_TABLE", out)

        # Stage 2 MUST suppress D2/D5 inside Limitations section AND inside lstlisting
        self.assertIn("Exempted", out)
        self.assertNotIn("D5_SELF_SABOTAGE", out)
        self.assertNotIn("D2_NON_CLAIM", out)

    def test_06_full_clean_e2e_happy_path(self) -> None:
        # 1. Init workspace
        self.assertEqual(run_py(INIT_SCRIPT, str(self.root), "--contest", "2026 APMCM", "--lang", "en").returncode, 0)
        self._fill_confirmed_plan(self.root / "00_plan.md")

        # 2. Produce real metrics + real journal figure
        metrics_dir = self.root / "03_outputs" / "metrics"
        figs_dir = self.root / "03_outputs" / "figs"
        paper_dir = self.root / "04_paper"
        (metrics_dir / "summary.json").write_text('{"rmse_drop_pct": 14.2, "ci_95": [12.8, 15.6]}', encoding="utf-8")
        (metrics_dir / "models.csv").write_text("Model,RMSE\nBaseline,12.40\nProposed,10.64\n", encoding="utf-8")

        self.assertEqual(
            run_py(PLOT_SCRIPT, "--self-test", "--lang", "en", "--out", str(figs_dir)).returncode,
            0,
        )
        self.assertEqual(
            run_py(
                SYNC_SCRIPT,
                "--metrics-dir",
                str(metrics_dir),
                "--paper-dir",
                str(paper_dir),
                "--bold-best",
                "RMSE:min",
            ).returncode,
            0,
        )

        # 3. Write clean Press-Conference LaTeX referencing generated macros, Booktabs table & figure
        tex = paper_dir / "main.tex"
        tex.write_text(
            r"""\documentclass{article}
\input{generated_metrics.tex}
\begin{document}
\section{Model Results}
On the holdout split, the coupled model lowers RMSE by \ValSummaryRmseDropPct{}\% (95\% CI: \ValSummaryCiNineFive{}), summarized in Table~\ref{tab:cmp} and Fig.~\ref{fig:main}.
\begin{table}\input{generated_tables/models.tex}\label{tab:cmp}\end{table}
\begin{figure}\includegraphics{nature_3panel_test_en.pdf}\label{fig:main}\end{figure}
\section{Strengths, Weaknesses, and Further Discussion}
Unfortunately, the linear approximation is merely valid within $\pm 10\%$ perturbation; we do not claim global validity beyond regime bifurcation.
\end{document}
""",
            encoding="utf-8",
        )

        # 4. Update handoff cleanly to Step 6
        (self.root / "handoff.md").write_text(
            "# handoff.md\n- **Current Step**: `Step 6`\n- **Next Role**: `[F] Flagship`\n"
            "- Metrics: `03_outputs/metrics/summary.json`\n- Paper: `04_paper/main.tex`\n"
            "## Next Session Trigger\n`使用 math-modeling-frontier 执行 MM Step 6`\n",
            encoding="utf-8",
        )

        # 5. Full audit must PASS with 0 hard fails and 0 Stage 2 prose signals
        res = run_py(
            AUDIT_SCRIPT,
            str(tex),
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
            "--pdf",
            str(figs_dir / "nature_3panel_test_en.pdf"),
        )
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("RESULT: AUTOMATED CHECKS PASS.", res.stdout)
        self.assertIn("CLEAN (0 prose triggers", res.stdout)


if __name__ == "__main__":
    unittest.main()
