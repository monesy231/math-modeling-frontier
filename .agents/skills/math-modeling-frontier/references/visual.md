# Step 3 Spec: Nature / Science Figure Aesthetics (Code-Enforced)

Load **only in Step 3**. All visual styling lives in `02_src/plot_style.py`—always import it and use its journal primitives instead of raw Matplotlib defaults.

## Journal Figure Standards (❌ Cheap Look → ✅ Nature / Science Craft)
- **Physical Sizing & Multi-Panel Composition**: ❌ 10 giant isolated single charts scaled down into unreadable tiny text → ✅ Compose cohesive 2–3 panel figures via `create_journal_fig(nrows, ncols, width="double"|"1.5col"|"single")` + `label_panels(axes, style="nature")` (bold **a, b, c**) so LaTeX embeds at `1.0\linewidth` with crisp native print typography.
- **Clean Layout & Direct Labels**: ❌ Heavy boxed legends + dark cross-hatch grids + neon/rainbow colors → ✅ Frameless legends (`frameon=False`) or `direct_label()`, subtle y-only gridlines, hairline charcoal spines (`#222222`), and consistent colorblind-safe palette paired with linestyles/markers across all figures.
- **Honest Uncertainty & Specialized Primitives**: ❌ Bare mean line or truncated bar y-axis → ✅ Start bars at $y=0$; plot 95% CI/IQR ribbons via `plot_with_ci()`; use `add_zoom_inset()` for local zoom, `plot_tornado()` for ±5%/±10% sensitivity, and `plot_diverging_heatmap()` (zero-centered `RdBu_r`) for correlations/interactions.
- **Figure 1 Architecture Roadmap**: ❌ AI raster image generators (blurry/garbled text) → ✅ Vector diagram via `plot_pipeline_diagram()` (or TikZ / Graphviz / Mermaid→SVG→PDF) reusing the exact `JOURNAL_COLORS` palette.
- **Dual Export & Mandatory Visual Check**: Save via `save_fig()` (`.pdf` vector + 300-DPI `.png`), then **open and inspect EVERY `.png`** for overlapping labels, clipped edges, tofu glyphs (`□□□`), or stale numbers.
