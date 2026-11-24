#!/usr/bin/env python3
"""
Nature / Science / PNAS publication-grade Matplotlib styling and plot primitives
for mathematical modeling papers. Copy to `<PROJECT_ROOT>/02_src/plot_style.py`.

Key journal conventions baked into code (zero prompt bloat):
- Exact physical column widths: single (3.5 in), 1.5col (5.0 in), double (7.2 in).
- Colorblind-safe low-saturation palette paired with linestyles & markers.
- Frameless legends, hairline charcoal spines (#222222), subtle y-only gridlines.
- Multi-panel bold panel labels (`a, b, c` Nature / `A, B, C` Science).
- Ready primitives: `create_journal_fig`, `label_panels`, `plot_with_ci`,
  `plot_delta_bars`, `plot_tornado`, `plot_diverging_heatmap`, `direct_label`,
  `add_zoom_inset`, `group_close_points`.
- Dual export (vector .pdf with TrueType fonttype=42 + 300-DPI .png) + layout check.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from cycler import cycler
from matplotlib import colors as mcolors
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

# Exact Nature / Science / PNAS physical column widths (inches)
JOURNAL_WIDTHS = {
    "single": 3.50,   # ~89 mm (Nature single column)
    "1.5col": 5.00,   # ~127 mm (Nature/Science 1.5 column)
    "double": 7.20,   # ~183 mm (Nature/Science full double column)
}

# Colorblind-safe, perceptually balanced journal palette for figure data series ONLY (NPG / Okabe-Ito inspired)
JOURNAL_COLORS: List[str] = [
    "#2B4C7E",  # Deep Academic Navy
    "#D95F02",  # Burnt Vermilion
    "#009E73",  # Journal Teal (for figure curves/bars only — NEVER use green/teal for paper fonts or dashboard UI)
    "#E6AB02",  # Ochre Amber
    "#7570B3",  # Muted Indigo
    "#595959",  # Charcoal Slate
]
ACADEMIC_COLORS = JOURNAL_COLORS  # Backward-compatible alias
JOURNAL_LINESTYLES: List[str] = ["-", "--", "-.", ":", "-", "--"]
JOURNAL_MARKERS: List[str] = ["o", "s", "^", "D", "v", "P"]
ACADEMIC_LINESTYLES = JOURNAL_LINESTYLES
ACADEMIC_MARKERS = JOURNAL_MARKERS

# Minimalist academic typography, table & interactive dashboard palette (Charcoal-Ink & Oxford Slate-Navy; zero green tint)
DOCUMENT_PALETTE = {
    "heading": "#111827",      # Title, H1/H2, table caption & table header text (Deep Academic Ink)
    "subhead": "#1E3A5F",      # H3 subheadings & inline code text (Oxford Slate-Navy)
    "body": "#1A1A1A",         # Primary manuscript body text (Pure Charcoal Ink)
    "muted": "#475569",        # Subtitles, figure captions, running headers & secondary labels (Cool Slate)
    "rule": "#1E293B",         # Booktabs top/mid/bottom rules & title dividers (Dark Slate-Navy)
    "border": "#CBD5E1",       # Running header rule & card/table dividers (Neutral Light Slate)
    "surface": "#F8FAFC",      # Table alternating row shading & page background (Cool Alabaster)
    "surface_alt": "#F1F5F9",  # Code block, table header & callout banner background
    "header_bg": "#0F172A",    # Dashboard top banner background (Deep Oxford Navy)
    "accent": "#2B4C7E",       # Primary UI accent border / active indicator
    "accent_text": "#1E40AF",  # Positive delta text & interactive link color
    "accent_bg": "#EFF6FF",    # Focus table row & positive delta pill background
}


def _pick_available_font(candidates: Sequence[str]) -> Optional[str]:
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return None


def apply_academic_style(lang: str = "en", scale: float = 1.0) -> None:
    """
    Configure global Matplotlib rcParams to Nature/Science/PNAS standards.
    Args:
        lang: "en" (Arial/Helvetica sans-serif) or "zh" (CJK clean sans-serif).
        scale: Font scale multiplier (1.0 matches 7.2in double-column native print size).
    """
    lang_norm = lang.lower().strip()
    if lang_norm == "zh":
        zh_font = _pick_available_font([
            "Microsoft YaHei",
            "SimHei",
            "PingFang SC",
            "Noto Sans CJK SC",
            "Noto Sans SC",
            "Source Han Sans SC",
            "WenQuanYi Zen Hei",
            "STHeiti",
            "Songti SC",
            "Arial Unicode MS",
        ])
        font_family = [zh_font, "DejaVu Sans"] if zh_font else ["DejaVu Sans"]
    else:
        en_font = _pick_available_font(["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"])
        font_family = [en_font, "DejaVu Sans"] if en_font else ["DejaVu Sans"]

    charcoal = "#222222"
    mpl.rcParams.update({
        # Typography & vector embedding
        "font.family": "sans-serif",
        "font.sans-serif": font_family,
        "font.size": 8.5 * scale,
        "mathtext.fontset": "stixsans",
        "axes.unicode_minus": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "text.color": charcoal,

        # Canvas & spines
        "figure.figsize": (JOURNAL_WIDTHS["double"], 3.8),
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.edgecolor": charcoal,
        "axes.labelcolor": charcoal,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,

        # Subtle horizontal grid only (eliminates cheap cross-hatch clutter)
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": "#BDBDBD",
        "grid.linestyle": "--",
        "grid.linewidth": 0.5,
        "grid.alpha": 0.25,
        "axes.axisbelow": True,

        # Typography hierarchy (matches print size cleanly)
        "axes.titlesize": 9.5 * scale,
        "axes.titleweight": "bold",
        "axes.titlepad": 7.0,
        "axes.labelsize": 8.8 * scale,
        "axes.labelpad": 4.5,
        "xtick.labelsize": 8.0 * scale,
        "ytick.labelsize": 8.0 * scale,
        "xtick.color": charcoal,
        "ytick.color": charcoal,
        "xtick.major.width": 0.75,
        "ytick.major.width": 0.75,
        "xtick.major.size": 3.5,
        "ytick.major.size": 3.5,
        "xtick.direction": "out",
        "ytick.direction": "out",

        # Frameless Nature-style legend
        "legend.fontsize": 7.8 * scale,
        "legend.frameon": False,
        "legend.handlelength": 2.0,
        "legend.borderaxespad": 0.4,

        # Lines & palette
        "lines.linewidth": 1.6,
        "lines.markersize": 4.4,
        "axes.prop_cycle": cycler(color=JOURNAL_COLORS),
    })


def create_journal_fig(
    nrows: int = 1,
    ncols: int = 1,
    width: Union[str, float] = "double",
    height: Optional[float] = None,
    aspect: float = 0.62,
    **subplots_kw,
) -> Tuple[plt.Figure, Union[plt.Axes, np.ndarray]]:
    """Create a multi-panel figure sized to exact Nature/Science physical column widths."""
    w_in = JOURNAL_WIDTHS[width] if isinstance(width, str) else float(width)
    if height is None:
        h_in = (w_in / max(ncols, 1)) * aspect * nrows + (0.45 if nrows > 1 else 0.15)
        h_in = min(h_in, 9.2)
    else:
        h_in = float(height)
    subplots_kw.setdefault("constrained_layout", True)
    return plt.subplots(nrows, ncols, figsize=(w_in, h_in), **subplots_kw)


def label_panels(
    axes: Union[plt.Axes, np.ndarray, Iterable[plt.Axes]],
    style: str = "nature",
    x: float = -0.14,
    y: float = 1.08,
    fontsize: float = 10.5,
) -> None:
    """Stamp bold journal panel identifiers (`a, b, c` for Nature; `A, B, C` for Science/PNAS)."""
    flat_axes = [axes] if isinstance(axes, plt.Axes) else list(np.ravel(axes))
    base = ord("a") if style.lower() == "nature" else ord("A")
    for idx, ax in enumerate(flat_axes):
        ax.text(
            x,
            y,
            chr(base + idx),
            transform=ax.transAxes,
            fontsize=fontsize,
            fontweight="bold",
            va="top",
            ha="left",
            color="#111111",
        )


def style_axis(
    ax: plt.Axes,
    xlabel: str,
    ylabel: str,
    title: Optional[str] = None,
    legend: bool = True,
    legend_loc: str = "best",
    grid_axis: Optional[str] = "y",
) -> plt.Axes:
    """Apply clean Nature/Science axis typography, breathing margins, and frameless legend."""
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.margins(x=0.03, y=0.08)
    if grid_axis is None:
        ax.grid(False)
    else:
        ax.grid(True, axis=grid_axis, linestyle="--", linewidth=0.5, alpha=0.25)
    if legend and ax.get_legend_handles_labels()[0]:
        ax.legend(loc=legend_loc, frameon=False)
    return ax


def direct_label(
    ax: plt.Axes,
    x: float,
    y: float,
    text: str,
    series_idx: int = 0,
    dx: float = 4.0,
    dy: float = 0.0,
    fontsize: float = 7.8,
) -> None:
    """Place a clean Nature-style direct label next to a curve endpoint (eliminating bulky legends)."""
    color = JOURNAL_COLORS[series_idx % len(JOURNAL_COLORS)]
    ax.annotate(
        text,
        xy=(x, y),
        xytext=(dx, dy),
        textcoords="offset points",
        color=color,
        fontsize=fontsize,
        fontweight="bold",
        va="center",
        ha="left",
    )


def plot_with_ci(
    ax: plt.Axes,
    x: Sequence[float],
    mean: Sequence[float],
    lower: Sequence[float],
    upper: Sequence[float],
    label: str,
    series_idx: int = 0,
    markevery: Optional[int] = None,
    ci_alpha: float = 0.16,
    ci_label: Optional[str] = None,
) -> plt.Axes:
    """Plot dual-channel curve (color + linestyle + marker) with translucent uncertainty ribbon."""
    idx = series_idx % len(JOURNAL_COLORS)
    color = JOURNAL_COLORS[idx]
    ax.plot(
        x,
        mean,
        color=color,
        linestyle=JOURNAL_LINESTYLES[idx],
        marker=JOURNAL_MARKERS[idx],
        markevery=markevery,
        label=label,
    )
    ax.fill_between(x, lower, upper, color=color, alpha=ci_alpha, linewidth=0, label=ci_label)
    return ax


def plot_delta_bars(
    ax: plt.Axes,
    labels: Sequence[Union[str, int, float]],
    deltas: Sequence[float],
    ylabel: str = "Delta (Proposed - Baseline)",
    xlabel: str = "",
    title: Optional[str] = None,
    fmt: str = "+.2f",
    width: float = 0.54,
    pos_color: Optional[str] = None,
    neg_color: Optional[str] = None,
    annotate: bool = True,
) -> plt.Axes:
    """
    Plot signed difference bars (`proposed - baseline`) across scales or regimes.
    Preserves small signed gains/trade-offs that near-identical absolute bars obscure,
    with automatic y-axis headroom so direct bar-tip numbers never clip spines.
    """
    vals = np.asarray(deltas, dtype=float)
    x_pos = np.arange(len(labels))
    c_pos = pos_color or JOURNAL_COLORS[0]
    c_neg = neg_color or JOURNAL_COLORS[1]
    bar_colors = [c_pos if v >= 0 else c_neg for v in vals]

    ax.axhline(0.0, color="#64748B", linewidth=0.7, zorder=2)
    ax.bar(x_pos, vals, width=width, color=bar_colors, alpha=0.90, zorder=3)

    ymin = float(min(0.0, float(np.nanmin(vals)) if len(vals) else 0.0))
    ymax = float(max(0.0, float(np.nanmax(vals)) if len(vals) else 0.0))
    span = (ymax - ymin) if (ymax - ymin) > 1e-12 else 1.0

    if annotate:
        offset = 0.035 * span
        for idx, val in enumerate(vals):
            if np.isnan(val):
                continue
            y_txt = float(val) + (offset if val >= 0 else -offset)
            ax.text(
                idx,
                y_txt,
                format(float(val), fmt),
                ha="center",
                va="bottom" if val >= 0 else "top",
                fontsize=7.0,
                color="#1F1F1F",
            )

    ax.set_ylim(ymin - 0.22 * span, ymax + 0.24 * span)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([str(lbl) for lbl in labels])
    return style_axis(ax, xlabel=xlabel, ylabel=ylabel, title=title, legend=False, grid_axis="y")


def plot_tornado(
    ax: plt.Axes,
    labels: Sequence[str],
    low_deltas: Sequence[float],
    high_deltas: Sequence[float],
    baseline: float = 0.0,
    xlabel: str = "Output Shift (%)",
    title: Optional[str] = None,
    low_label: str = "-10% Param",
    high_label: str = "+10% Param",
) -> plt.Axes:
    """Render a publication-grade sorted horizontal tornado chart for sensitivity analysis."""
    lows = np.asarray(low_deltas, dtype=float)
    highs = np.asarray(high_deltas, dtype=float)
    spans = np.abs(highs - lows)
    order = np.argsort(spans)  # Largest impact at top

    y_pos = np.arange(len(labels))
    ord_labels = [labels[i] for i in order]
    ord_low = lows[order]
    ord_high = highs[order]

    ax.axvline(baseline, color="#222222", linewidth=0.9, zorder=3)
    ax.barh(y_pos, ord_low - baseline, left=baseline, height=0.56, color=JOURNAL_COLORS[0], alpha=0.88, label=low_label)
    ax.barh(y_pos, ord_high - baseline, left=baseline, height=0.56, color=JOURNAL_COLORS[1], alpha=0.88, label=high_label)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(ord_labels)
    style_axis(ax, xlabel=xlabel, ylabel="", title=title, legend=False, grid_axis="x")
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.24),
        ncol=2,
        frameon=False,
        fontsize=7.4,
        columnspacing=0.9,
        handlelength=1.2,
        handletextpad=0.4,
    )
    return ax


def plot_diverging_heatmap(
    ax: plt.Axes,
    matrix: np.ndarray,
    xlabels: Sequence[str],
    ylabels: Sequence[str],
    center: float = 0.0,
    cmap: str = "RdBu_r",
    fmt: str = ".2f",
    cbar_label: str = "",
    title: Optional[str] = None,
    annotate: bool = True,
) -> plt.Axes:
    """Render a zero-centered diverging heatmap with auto-contrasting cell numbers."""
    arr = np.asarray(matrix, dtype=float)
    max_dev = max(abs(float(np.nanmin(arr)) - center), abs(float(np.nanmax(arr)) - center), 1e-9)
    norm = mcolors.TwoSlopeNorm(vmin=center - max_dev, vcenter=center, vmax=center + max_dev)

    im = ax.imshow(arr, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(np.arange(len(xlabels)))
    ax.set_xticklabels(xlabels)
    ax.set_yticks(np.arange(len(ylabels)))
    ax.set_yticklabels(ylabels)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("#CCCCCC")
        spine.set_linewidth(0.6)

    if annotate:
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                val = arr[i, j]
                if np.isnan(val):
                    continue
                txt_color = "white" if abs(val - center) > 0.58 * max_dev else "#1F1F1F"
                ax.text(j, i, format(val, fmt), ha="center", va="center", color=txt_color, fontsize=7.5)

    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.outline.set_linewidth(0.6)
    cbar.ax.tick_params(labelsize=7.5, width=0.6)
    if cbar_label:
        cbar.set_label(cbar_label, fontsize=8.0)
    if title:
        ax.set_title(title)
    return ax


def plot_pipeline_diagram(
    ax: plt.Axes,
    stages: Sequence[Tuple[str, str]],
    title: Optional[str] = None,
    box_height: float = 0.56,
    feedback_edge: Optional[Tuple[int, int, str]] = None,
) -> plt.Axes:
    """
    Render a Nature-grade vector modeling roadmap / architecture diagram (Figure 1).
    Args:
        stages: Sequence of (header, multiline_body) tuples.
        feedback_edge: Optional (from_idx, to_idx, label) curved feedback arrow beneath boxes.
    """
    n = len(stages)
    if n == 0:
        return ax

    gap = 0.045
    total_w = 0.94
    box_w = (total_w - gap * (n - 1)) / n
    x0_start = 0.03
    y_bot = 0.28 if feedback_edge else 0.18
    header_h = box_height * 0.28

    centers: List[Tuple[float, float]] = []
    for idx, (header, body) in enumerate(stages):
        color = JOURNAL_COLORS[idx % len(JOURNAL_COLORS)]
        x0 = x0_start + idx * (box_w + gap)
        cx = x0 + box_w / 2.0
        centers.append((cx, y_bot))

        # Main card body
        card = FancyBboxPatch(
            (x0, y_bot),
            box_w,
            box_height,
            boxstyle="round,pad=0.012,rounding_size=0.025",
            facecolor="#FAFAFA",
            edgecolor=color,
            linewidth=1.2,
            zorder=2,
        )
        ax.add_patch(card)

        # Solid top header bar (auto-select dark or white text based on WCAG background luminance)
        hbar = FancyBboxPatch(
            (x0, y_bot + box_height - header_h),
            box_w,
            header_h,
            boxstyle="round,pad=0.012,rounding_size=0.020",
            facecolor=color,
            edgecolor=color,
            linewidth=0.8,
            zorder=3,
        )
        ax.add_patch(hbar)

        r_c, g_c, b_c = mcolors.to_rgb(color)
        lum = 0.2126 * r_c + 0.7152 * g_c + 0.0722 * b_c
        header_text_color = "#1A1A1A" if lum > 0.52 else "white"

        ax.text(
            cx,
            y_bot + box_height - header_h / 2.0,
            header,
            ha="center",
            va="center",
            color=header_text_color,
            fontsize=8.0,
            fontweight="bold",
            zorder=4,
        )
        ax.text(
            cx,
            y_bot + (box_height - header_h) / 2.0,
            body,
            ha="center",
            va="center",
            color="#222222",
            fontsize=7.3,
            linespacing=1.35,
            zorder=4,
        )

        # Forward arrow to next stage
        if idx < n - 1:
            arr = FancyArrowPatch(
                (x0 + box_w + 0.014, y_bot + box_height / 2.0),
                (x0 + box_w + gap - 0.014, y_bot + box_height / 2.0),
                arrowstyle="-|>,head_length=4.5,head_width=2.8",
                color="#444444",
                linewidth=1.1,
                zorder=5,
            )
            ax.add_patch(arr)

    if feedback_edge:
        src_i, dst_i, fb_label = feedback_edge
        x_src, y_src = centers[src_i]
        x_dst, y_dst = centers[dst_i]
        # Curve cleanly BELOW the boxes regardless of arrow direction
        rad = -0.32 if x_src > x_dst else 0.32
        fb = FancyArrowPatch(
            (x_src, y_src - 0.025),
            (x_dst, y_dst - 0.025),
            connectionstyle=f"arc3,rad={rad}",
            arrowstyle="-|>,head_length=4.5,head_width=2.8",
            color=JOURNAL_COLORS[1],
            linestyle="--",
            linewidth=1.15,
            zorder=5,
        )
        ax.add_patch(fb)
        ax.text(
            (x_src + x_dst) / 2.0,
            0.055,
            fb_label,
            ha="center",
            va="center",
            color=JOURNAL_COLORS[1],
            fontsize=7.5,
            fontweight="bold",
        )

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")
    if title:
        ax.set_title(title, pad=6.0)
    return ax


def add_zoom_inset(
    ax: plt.Axes,
    xlim: Tuple[float, float],
    ylim: Tuple[float, float],
    width: str = "36%",
    height: str = "36%",
    loc: str = "upper right",
    connect_locs: Tuple[int, int] = (2, 4),
) -> plt.Axes:
    """Create an honest local zoom inset instead of truncating main axes."""
    axins = inset_axes(ax, width=width, height=height, loc=loc, borderpad=0.9)
    axins.set_xlim(*xlim)
    axins.set_ylim(*ylim)
    axins.tick_params(labelsize=6.8, width=0.6, length=2.5)
    axins.grid(False)
    for spine in axins.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor("#555555")
        spine.set_linewidth(0.65)
    mark_inset(ax, axins, loc1=connect_locs[0], loc2=connect_locs[1], fc="none", ec="#666666", lw=0.65, ls="--")
    return axins


def group_close_points(
    ax: plt.Axes,
    points: Sequence[Tuple[float, float]],
    min_dist_pt: float = 12.0,
) -> List[List[int]]:
    """
    Cluster 2D scatter/Pareto points whose markers or labels would touch at final print size.
    Converts data coordinates to display pixels after drawing layout and runs BFS with
    threshold `min_dist_pt * dpi / 72`, returning sorted index clusters.
    """
    if not points:
        return []
    try:
        ax.figure.canvas.draw()
    except Exception:
        pass
    coords_px = ax.transData.transform(np.asarray(points, dtype=float))
    thresh_px = float(min_dist_pt) * (float(ax.figure.dpi) / 72.0)
    n = len(points)
    visited = [False] * n
    clusters: List[List[int]] = []
    for start in range(n):
        if visited[start]:
            continue
        visited[start] = True
        queue = [start]
        comp = [start]
        while queue:
            cur = queue.pop(0)
            for nxt in range(n):
                if visited[nxt]:
                    continue
                dx = float(coords_px[cur, 0] - coords_px[nxt, 0])
                dy = float(coords_px[cur, 1] - coords_px[nxt, 1])
                if float(np.hypot(dx, dy)) < thresh_px:
                    visited[nxt] = True
                    queue.append(nxt)
                    comp.append(nxt)
        clusters.append(sorted(comp))
    clusters.sort(key=lambda c: c[0])
    return clusters


def check_figure_layout(fig: plt.Figure) -> List[str]:
    """Heuristic check for out-of-frame text clipping or overlapping annotations."""
    warnings: List[str] = []
    try:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        fig_bbox = fig.get_window_extent(renderer=renderer)
    except Exception:
        return warnings

    boxes = []
    for ax in fig.get_axes():
        for txt in ax.texts:
            s = txt.get_text().strip()
            if not txt.get_visible() or not s or len(s) == 1:
                continue  # Skip single-letter panel markers intentionally placed in margins
            bb = txt.get_window_extent(renderer=renderer)
            if (
                bb.x0 < fig_bbox.x0 - 2
                or bb.x1 > fig_bbox.x1 + 2
                or bb.y0 < fig_bbox.y0 - 2
                or bb.y1 > fig_bbox.y1 + 2
            ):
                warnings.append(f"Annotation clipped at figure boundary: '{s[:30]}'")
            boxes.append((s[:30], bb))

    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if boxes[i][1].overlaps(boxes[j][1]):
                warnings.append(f"Overlapping annotations: '{boxes[i][0]}' vs '{boxes[j][0]}'")
    return warnings


def save_fig(
    fig: plt.Figure,
    name: str,
    out_dir: str = "03_outputs/figs",
    dpi: int = 300,
    close: bool = True,
    check_layout: bool = True,
) -> Tuple[Path, Path]:
    """Export figure to both vector PDF (LaTeX) and 300-DPI PNG (visual inspection)."""
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(name).stem
    pdf_path = target_dir / f"{stem}.pdf"
    png_path = target_dir / f"{stem}.png"

    if not fig.get_constrained_layout():
        try:
            fig.tight_layout()
        except Exception:
            pass

    if check_layout:
        for warn in check_figure_layout(fig):
            print(f"[LAYOUT WARN] {stem}: {warn}")

    fig.savefig(pdf_path, format="pdf", bbox_inches="tight")
    fig.savefig(png_path, format="png", dpi=dpi, bbox_inches="tight")
    if close:
        plt.close(fig)

    print(f"[FIG SAVED] {pdf_path} | {png_path}")
    return pdf_path, png_path


def _run_self_test(out_dir: str, lang: str) -> None:
    """Generate a 3-panel Nature-style showcase (CI trajectory + Tornado + Heatmap)."""
    apply_academic_style(lang=lang)
    fig, axes = create_journal_fig(1, 3, width="double", height=2.65, gridspec_kw={"width_ratios": [1.35, 1.0, 1.05]})

    # Panel a: Model comparison trajectory with 95% CI
    x = np.linspace(0, 10, 50)
    y_base = 0.85 * np.exp(-0.18 * x) + 0.25
    y_prop = 0.85 * np.exp(-0.34 * x) + 0.12
    plot_with_ci(axes[0], x, y_base, y_base - 0.06, y_base + 0.06, "Baseline", series_idx=0, markevery=7)
    plot_with_ci(axes[0], x, y_prop, y_prop - 0.04, y_prop + 0.04, "Proposed (95% CI)", series_idx=1, markevery=7)
    style_axis(
        axes[0],
        xlabel="Horizon $t$ (days)" if lang == "en" else "时间步 $t$ (天)",
        ylabel="Normalized Error" if lang == "en" else "归一化误差",
        title="Error Convergence" if lang == "en" else "误差收敛对比",
    )

    # Panel b: Sensitivity tornado chart
    params = [r"$\alpha$ (Decay)", r"$\beta$ (Cost)", r"$\gamma$ (Cap)", r"$\delta$ (Noise)"]
    plot_tornado(
        axes[1],
        labels=params,
        low_deltas=[-1.4, -3.2, -2.1, -0.7],
        high_deltas=[1.6, 3.8, 1.9, 0.9],
        xlabel="Objective Shift (%)" if lang == "en" else "目标值变化 (%)",
        title="±10% Sensitivity" if lang == "en" else "±10% 灵敏度",
    )

    # Panel c: Zero-centered diverging heatmap
    mat = np.array([[0.12, -0.45, 0.78], [-0.62, 0.05, 0.34], [0.81, -0.22, -0.51]])
    plot_diverging_heatmap(
        axes[2],
        matrix=mat,
        xlabels=["S1", "S2", "S3"],
        ylabels=["P1", "P2", "P3"],
        center=0.0,
        cbar_label=r"$\Delta$ (%)",
        title="Regime Interaction" if lang == "en" else "参数交互热力图",
    )

    label_panels(axes, style="nature", x=-0.16, y=1.10)
    save_fig(fig, f"nature_3panel_test_{lang}", out_dir=out_dir)


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    parser = argparse.ArgumentParser(description="Run Nature/Science plot_style self-test.")
    parser.add_argument("--self-test", action="store_true", help="Generate a 3-panel Nature-style showcase")
    parser.add_argument("--out", default="03_outputs/figs", help="Output directory for self-test")
    parser.add_argument("--lang", choices=["en", "zh"], default="en", help="Typography language")
    args = parser.parse_args()
    if args.self_test:
        _run_self_test(args.out, args.lang)
    else:
        print("Import this module in your figure scripts, or pass --self-test to verify.")
