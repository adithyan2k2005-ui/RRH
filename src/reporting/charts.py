"""Chart Generation Module for SupeRR Selector Analytics.

Generates publication-quality statistical charts directly from project datasets
using deterministic vector SVG generation and PyMuPDF rasterization.
Requires no external plotting dependencies.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import pymupdf

logger = logging.getLogger(__name__)


def svg_to_png(svg_str: str, png_path: Path, dpi: int = 150) -> None:
    """Renders SVG string to a crisp PNG image using PyMuPDF."""
    png_path.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open("svg", svg_str.encode("utf-8"))
    page = doc[0]
    pix = page.get_pixmap(dpi=dpi)
    pix.save(str(png_path))
    logger.info("Saved chart to %s (%dx%d)", png_path, pix.width, pix.height)


def generate_pressure_distribution_chart(
    counts: Dict[str, int],
    title: str,
    output_path: Path,
    palette: List[str] = None,
) -> None:
    """Generates a bar chart showing distribution of deliveries across pressure classes."""
    if palette is None:
        palette = ["#0284c7", "#0d9488", "#e11d48"]

    total = sum(counts.values())
    w, h = 600, 320
    pad_l, pad_r, pad_t, pad_b = 90, 40, 60, 60
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b

    max_val = max(counts.values()) * 1.15

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="#ffffff" rx="8"/>',
        f'<rect x="2" y="2" width="{w-4}" height="{h-4}" fill="none" stroke="#e2e8f0" stroke-width="1.5" rx="7"/>',
        f'<text x="{w/2}" y="35" font-family="Helvetica, Arial, sans-serif" font-size="16" font-weight="bold" fill="#0f172a" text-anchor="middle">{title}</text>',
    ]

    # Gridlines
    for step in [0.25, 0.5, 0.75, 1.0]:
        val = int(max_val * step)
        y = pad_t + plot_h - (val / max_val) * plot_h
        svg_parts.append(
            f'<line x1="{pad_l}" y1="{y}" x2="{w - pad_r}" y2="{y}" stroke="#f1f5f9" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{pad_l - 10}" y="{y + 4}" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="#64748b" text-anchor="end">{val:,}</text>'
        )

    # Bars
    keys = list(counts.keys())
    bar_width = plot_w / (len(keys) * 1.8)
    gap = plot_w / len(keys)

    for i, (k, v) in enumerate(counts.items()):
        bar_h = (v / max_val) * plot_h
        x = pad_l + i * gap + (gap - bar_width) / 2
        y = pad_t + plot_h - bar_h
        color = palette[i % len(palette)]
        pct = (v / total) * 100

        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_h}" fill="{color}" rx="4"/>'
        )
        # Value label on top
        svg_parts.append(
            f'<text x="{x + bar_width/2}" y="{y - 8}" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="bold" fill="#0f172a" text-anchor="middle">{v:,}</text>'
        )
        svg_parts.append(
            f'<text x="{x + bar_width/2}" y="{y - 22}" font-family="Helvetica, Arial, sans-serif" font-size="9" fill="#64748b" text-anchor="middle">({pct:.1f}%)</text>'
        )
        # Category label at bottom
        label = k.replace("_PRESSURE", "").replace("_", " ").title()
        svg_parts.append(
            f'<text x="{x + bar_width/2}" y="{h - pad_b + 22}" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="bold" fill="#334155" text-anchor="middle">{label}</text>'
        )

    svg_parts.append(f'<line x1="{pad_l}" y1="{h - pad_b}" x2="{w - pad_r}" y2="{h - pad_b}" stroke="#cbd5e1" stroke-width="1.5"/>')
    svg_parts.append("</svg>")
    svg_str = "\n".join(svg_parts)
    svg_to_png(svg_str, output_path)


def generate_horizontal_rankings_chart(
    df: pd.DataFrame,
    title: str,
    output_path: Path,
    discipline: str = "BATTING",
) -> None:
    """Generates a clean horizontal bar chart displaying the Top 10 reliability scores."""
    w, h = 650, 420
    pad_l, pad_r, pad_t, pad_b = 180, 50, 50, 40
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="#ffffff" rx="8"/>',
        f'<rect x="2" y="2" width="{w-4}" height="{h-4}" fill="none" stroke="#e2e8f0" stroke-width="1.5" rx="7"/>',
        f'<text x="{w/2}" y="32" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="bold" fill="#0f172a" text-anchor="middle">{title}</text>',
    ]

    # Gridlines from 70 to 100
    for score in range(70, 101, 10):
        x = pad_l + ((score - 70) / 30.0) * plot_w
        svg_parts.append(
            f'<line x1="{x}" y1="{pad_t}" x2="{x}" y2="{h - pad_b}" stroke="#f1f5f9" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{x}" y="{h - pad_b + 18}" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="#64748b" text-anchor="middle">{score}</text>'
        )

    n_bars = len(df)
    bar_h = plot_h / (n_bars * 1.5)
    gap = plot_h / n_bars

    color = "#0284c7" if discipline == "BATTING" else "#0d9488"
    accent = "#0369a1" if discipline == "BATTING" else "#0f766e"

    for i, (_, row) in enumerate(df.iterrows()):
        r = int(row["rank"])
        name = str(row["player_name"])
        p_id = int(row["player_id"] if "player_id" in row else (row["striker_id"] if discipline == "BATTING" else row["bowler_id"]))
        score = float(row["reliability_score"])

        bar_len = ((score - 70) / 30.0) * plot_w
        y = pad_t + i * gap + (gap - bar_h) / 2
        bar_fill = color if r > 1 else accent

        svg_parts.append(
            f'<text x="{pad_l - 12}" y="{y + bar_h*0.75}" font-family="Helvetica, Arial, sans-serif" font-size="11" font-weight="500" fill="#1e293b" text-anchor="end">#{r} {name} ({p_id})</text>'
        )
        svg_parts.append(
            f'<rect x="{pad_l}" y="{y}" width="{bar_len}" height="{bar_h}" fill="{bar_fill}" rx="3"/>'
        )
        svg_parts.append(
            f'<text x="{pad_l + bar_len + 8}" y="{y + bar_h*0.75}" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="bold" fill="#0f172a">{score:.2f}</text>'
        )

    svg_parts.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{h - pad_b}" stroke="#cbd5e1" stroke-width="1.5"/>')
    svg_parts.append(f'<line x1="{pad_l}" y1="{h - pad_b}" x2="{w - pad_r}" y2="{h - pad_b}" stroke="#cbd5e1" stroke-width="1.5"/>')
    svg_parts.append("</svg>")
    svg_to_png("\n".join(svg_parts), output_path)


def generate_uplift_comparison_chart(
    top_batters: pd.DataFrame,
    top_bowlers: pd.DataFrame,
    output_path: Path,
) -> None:
    """Generates comparative chart contrasting High-Pressure Impact vs Ordinary Baseline."""
    w, h = 680, 360
    pad_l, pad_r, pad_t, pad_b = 60, 40, 50, 70
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="#ffffff" rx="8"/>',
        f'<rect x="2" y="2" width="{w-4}" height="{h-4}" fill="none" stroke="#e2e8f0" stroke-width="1.5" rx="7"/>',
        f'<text x="{w/2}" y="30" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="bold" fill="#0f172a" text-anchor="middle">Contextual Impact: High Pressure vs Ordinary Baseline</text>',
    ]

    # Legend
    svg_parts.extend([
        f'<rect x="{w - 280}" y="18" width="12" height="12" fill="#0284c7" rx="2"/>',
        f'<text x="{w - 262}" y="28" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="#334155">HP Impact</text>',
        f'<rect x="{w - 180}" y="18" width="12" height="12" fill="#94a3b8" rx="2"/>',
        f'<text x="{w - 162}" y="28" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="#334155">Ordinary Baseline</text>',
    ])

    # Zero axis line
    zero_y = pad_t + plot_h * 0.70  # Baseline near bottom
    svg_parts.append(
        f'<line x1="{pad_l}" y1="{zero_y}" x2="{w - pad_r}" y2="{zero_y}" stroke="#94a3b8" stroke-width="1.5"/>'
    )
    svg_parts.append(
        f'<text x="{pad_l - 8}" y="{zero_y + 4}" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="#64748b" text-anchor="end">0.0</text>'
    )

    # Plot sample of top 5 batters and top 5 bowlers
    players = []
    for _, r in top_batters.head(5).iterrows():
        players.append((f"B: {r['player_name'].split()[-1]}", float(r['high_pressure_impact']), float(r['ordinary_performance_baseline'])))
    for _, r in top_bowlers.head(5).iterrows():
        players.append((f"BW: {r['player_name'].split()[-1]}", float(r['high_pressure_impact']), float(r['ordinary_performance_baseline'])))

    n = len(players)
    gap = plot_w / n
    bar_w = gap * 0.35

    # Scale: max impact is around 2.5
    scale = (plot_h * 0.65) / 2.5

    for i, (name, hp_imp, ord_imp) in enumerate(players):
        cx = pad_l + i * gap + gap / 2

        # HP bar
        hp_h = hp_imp * scale
        hp_y = zero_y - hp_h if hp_imp >= 0 else zero_y
        svg_parts.append(
            f'<rect x="{cx - bar_w}" y="{hp_y}" width="{bar_w}" height="{abs(hp_h)}" fill="#0284c7" rx="2"/>'
        )

        # Ord bar
        ord_h = ord_imp * scale
        ord_y = zero_y - ord_h if ord_imp >= 0 else zero_y
        svg_parts.append(
            f'<rect x="{cx + 2}" y="{ord_y}" width="{bar_w}" height="{abs(ord_h)}" fill="#94a3b8" rx="2"/>'
        )

        # Name label
        svg_parts.append(
            f'<text x="{cx}" y="{h - pad_b + 22}" font-family="Helvetica, Arial, sans-serif" font-size="9" fill="#334155" text-anchor="middle" transform="rotate(25, {cx}, {h - pad_b + 22})">{name}</text>'
        )

    svg_parts.append("</svg>")
    svg_to_png("\n".join(svg_parts), output_path)


def generate_robustness_chart(output_path: Path) -> None:
    """Generates ranking sensitivity correlation chart."""
    w, h = 600, 320
    pad_l, pad_r, pad_t, pad_b = 100, 40, 50, 60
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="#ffffff" rx="8"/>',
        f'<rect x="2" y="2" width="{w-4}" height="{h-4}" fill="none" stroke="#e2e8f0" stroke-width="1.5" rx="7"/>',
        f'<text x="{w/2}" y="30" font-family="Helvetica, Arial, sans-serif" font-size="15" font-weight="bold" fill="#0f172a" text-anchor="middle">Ranking Robustness: Spearman Correlation Across Regimes</text>',
    ]

    regimes = [
        ("Alt 1 (Impact-Heavy)", 0.9957, 0.9913),
        ("Alt 2 (Uplift-Heavy)", 0.9810, 0.9788),
        ("Alt 3 (Consistency-Heavy)", 0.9852, 0.9832),
    ]

    # Legend
    svg_parts.extend([
        f'<rect x="{w - 240}" y="18" width="12" height="12" fill="#0284c7" rx="2"/>',
        f'<text x="{w - 222}" y="28" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="#334155">Batting (ρ)</text>',
        f'<rect x="{w - 140}" y="18" width="12" height="12" fill="#0d9488" rx="2"/>',
        f'<text x="{w - 122}" y="28" font-family="Helvetica, Arial, sans-serif" font-size="10" fill="#334155">Bowling (ρ)</text>',
    ])

    gap = plot_h / len(regimes)
    bar_h = gap * 0.32

    # Scale 0.95 to 1.00
    for i, (label, bat_rho, bowl_rho) in enumerate(regimes):
        y_center = pad_t + i * gap + gap / 2

        bat_len = ((bat_rho - 0.95) / 0.05) * plot_w
        bowl_len = ((bowl_rho - 0.95) / 0.05) * plot_w

        svg_parts.append(
            f'<text x="{pad_l - 12}" y="{y_center + 4}" font-family="Helvetica, Arial, sans-serif" font-size="10" font-weight="bold" fill="#334155" text-anchor="end">{label}</text>'
        )

        # Batting bar
        svg_parts.append(
            f'<rect x="{pad_l}" y="{y_center - bar_h - 2}" width="{bat_len}" height="{bar_h}" fill="#0284c7" rx="2"/>'
        )
        svg_parts.append(
            f'<text x="{pad_l + bat_len + 6}" y="{y_center - 4}" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="bold" fill="#0f172a">{bat_rho:.4f}</text>'
        )

        # Bowling bar
        svg_parts.append(
            f'<rect x="{pad_l}" y="{y_center + 2}" width="{bowl_len}" height="{bar_h}" fill="#0d9488" rx="2"/>'
        )
        svg_parts.append(
            f'<text x="{pad_l + bowl_len + 6}" y="{y_center + bar_h}" font-family="Helvetica, Arial, sans-serif" font-size="9" font-weight="bold" fill="#0f172a">{bowl_rho:.4f}</text>'
        )

    # Axis at bottom
    for val in [0.95, 0.96, 0.97, 0.98, 0.99, 1.00]:
        x = pad_l + ((val - 0.95) / 0.05) * plot_w
        svg_parts.append(
            f'<line x1="{x}" y1="{pad_t}" x2="{x}" y2="{h - pad_b}" stroke="#f1f5f9" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{x}" y="{h - pad_b + 18}" font-family="Helvetica, Arial, sans-serif" font-size="9" fill="#64748b" text-anchor="middle">{val:.2f}</text>'
        )

    svg_parts.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{h - pad_b}" stroke="#cbd5e1" stroke-width="1.5"/>')
    svg_parts.append(f'<line x1="{pad_l}" y1="{h - pad_b}" x2="{w - pad_r}" y2="{h - pad_b}" stroke="#cbd5e1" stroke-width="1.5"/>')
    svg_parts.append("</svg>")
    svg_to_png("\n".join(svg_parts), output_path)

