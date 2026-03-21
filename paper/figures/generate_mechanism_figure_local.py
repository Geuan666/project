#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch


OUT_DIR = Path("/root/autodl-tmp/project/paper/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)


COLORS = {
    "integration": "#4C78A8",
    "decision": "#F58518",
    "construction": "#54A24B",
    "suppression": "#E45756",
    "weak_edge": "#9E9E9E",
    "text": "#222222",
}


def add_node(ax, x: float, y: float, label: str, color: str, r: float = 0.034) -> None:
    ax.add_patch(Circle((x, y), r, facecolor=color, edgecolor="white", lw=2.0, zorder=3))
    ax.text(x, y, label, ha="center", va="center", fontsize=10, color="white", weight="bold", zorder=4)


def add_arrow(
    ax,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str,
    lw: float = 2.2,
    alpha: float = 1.0,
    rad: float = 0.0,
    style: str = "-|>",
    mutation: int = 14,
    ls: str = "-",
) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle=style,
        mutation_scale=mutation,
        linewidth=lw,
        color=color,
        alpha=alpha,
        linestyle=ls,
        connectionstyle=f"arc3,rad={rad}",
        zorder=2,
    )
    ax.add_patch(arrow)


def add_module(ax, x: float, y: float, w: float, h: float, title: str, subtitle: str, color: str) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        linewidth=2.0,
        edgecolor=color,
        facecolor=color,
        alpha=0.12,
        zorder=1,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h * 0.68, title, ha="center", va="center", fontsize=13, color=COLORS["text"], weight="bold")
    ax.text(x + w / 2, y + h * 0.30, subtitle, ha="center", va="center", fontsize=10, color=COLORS["text"])


fig = plt.figure(figsize=(9, 16), facecolor="white")
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# Title
ax.text(0.5, 0.975, "Tool-Use Decision Mechanism", ha="center", va="top", fontsize=22, weight="bold", color=COLORS["text"])
ax.text(
    0.5,
    0.948,
    "Instruction cues are integrated, converted into an output-route decision,\nthen distributed toward tool construction and direct-answer suppression.",
    ha="center",
    va="top",
    fontsize=11,
    color="#444444",
)

# Top circuit scaffold
ax.text(0.5, 0.87, "Circuit-Level View", ha="center", va="center", fontsize=16, weight="bold", color=COLORS["text"])

# Upstream/integration nodes
add_node(ax, 0.16, 0.77, "L2H14", COLORS["integration"])
add_node(ax, 0.28, 0.74, "MLP12", COLORS["integration"])

# Decision spine
add_node(ax, 0.40, 0.72, "MLP11", COLORS["decision"], r=0.042)
add_node(ax, 0.54, 0.68, "MLP16", COLORS["decision"], r=0.048)
add_node(ax, 0.68, 0.63, "MLP19", COLORS["decision"], r=0.045)

# Tool side nodes
add_node(ax, 0.80, 0.70, "L20H5", COLORS["construction"])
add_node(ax, 0.86, 0.62, "L21H12", COLORS["construction"])
add_node(ax, 0.82, 0.53, "MLP27", COLORS["construction"], r=0.04)

# Suppression side nodes
add_node(ax, 0.44, 0.54, "MLP17", COLORS["suppression"], r=0.04)
add_node(ax, 0.61, 0.49, "L23H6", COLORS["suppression"])

# Main arrows
add_arrow(ax, (0.19, 0.765), (0.37, 0.725), COLORS["integration"], lw=2.0)
add_arrow(ax, (0.31, 0.735), (0.37, 0.723), COLORS["integration"], lw=2.0)
add_arrow(ax, (0.44, 0.71), (0.50, 0.69), COLORS["decision"], lw=3.0)
add_arrow(ax, (0.58, 0.67), (0.64, 0.64), COLORS["decision"], lw=3.0)

# Decision annotations
ax.text(0.46, 0.755, "earliest stable\nroute writer", ha="center", va="bottom", fontsize=9, color=COLORS["decision"])
ax.text(0.54, 0.735, "shared amplifier", ha="center", va="bottom", fontsize=9, color=COLORS["decision"])
ax.text(0.69, 0.685, "late fanout hub", ha="center", va="bottom", fontsize=9, color=COLORS["decision"])

# Strong fork edge
add_arrow(ax, (0.53, 0.64), (0.46, 0.57), COLORS["suppression"], lw=3.2)
ax.text(0.48, 0.61, "strong fork", ha="left", va="center", fontsize=9, color=COLORS["suppression"], rotation=-28)

# Weak fanout edges from MLP19
add_arrow(ax, (0.71, 0.64), (0.77, 0.69), COLORS["construction"], lw=1.9, alpha=0.85)
add_arrow(ax, (0.71, 0.62), (0.83, 0.62), COLORS["construction"], lw=1.9, alpha=0.85)
add_arrow(ax, (0.70, 0.60), (0.79, 0.54), COLORS["construction"], lw=1.9, alpha=0.85)
add_arrow(ax, (0.69, 0.59), (0.60, 0.50), COLORS["suppression"], lw=1.8, alpha=0.85)
ax.text(0.77, 0.585, "parallel fanout", ha="center", va="center", fontsize=9, color=COLORS["weak_edge"])

# Mid explanation band
band = FancyBboxPatch(
    (0.08, 0.40),
    0.84,
    0.08,
    boxstyle="round,pad=0.02,rounding_size=0.025",
    linewidth=1.5,
    edgecolor="#D0D0D0",
    facecolor="#F7F7F7",
)
ax.add_patch(band)
ax.text(
    0.50,
    0.44,
    "A continuous route score is formed on MLP11 -> MLP16 -> MLP19.\nIt is not a fixed cross-layer vector; it is progressively re-encoded and then distributed downstream.",
    ha="center",
    va="center",
    fontsize=11,
    color=COLORS["text"],
)

# Bottom module boxes
add_module(ax, 0.06, 0.20, 0.20, 0.12, "Instruction\nIntegration", "bind opening cue,\nfunction body,\nfilename", COLORS["integration"])
add_module(ax, 0.30, 0.20, 0.20, 0.12, "Output-Route\nDecision", "MLP11 -> MLP16 -> MLP19\ncontinuous route score", COLORS["decision"])
add_module(ax, 0.56, 0.24, 0.18, 0.10, "Tool-Call\nConstruction", "tool route\nstrengthened", COLORS["construction"])
add_module(ax, 0.56, 0.08, 0.18, 0.10, "Tool-Call\nSuppression", "direct-answer route\nstrengthened", COLORS["suppression"])

# Bottom arrows
add_arrow(ax, (0.26, 0.26), (0.30, 0.26), COLORS["integration"], lw=2.2)
add_arrow(ax, (0.50, 0.27), (0.56, 0.29), COLORS["construction"], lw=2.6)
add_arrow(ax, (0.50, 0.23), (0.56, 0.14), COLORS["suppression"], lw=2.8)
ax.text(0.535, 0.305, "tool route", ha="left", va="bottom", fontsize=10, color=COLORS["construction"])
ax.text(0.535, 0.145, "direct-answer route", ha="left", va="bottom", fontsize=10, color=COLORS["suppression"])

# Footer
ax.text(
    0.5,
    0.035,
    "Current mechanistic picture: a shared decision spine first forms an output-route preference,\nthen forks toward direct-answer suppression and fans out toward tool-side construction.",
    ha="center",
    va="center",
    fontsize=10,
    color="#555555",
)

svg_path = OUT_DIR / "mechanism_figure_local_v1.svg"
png_path = OUT_DIR / "mechanism_figure_local_v1.png"
pdf_path = OUT_DIR / "mechanism_figure_local_v1.pdf"

fig.savefig(svg_path, bbox_inches="tight")
fig.savefig(pdf_path, bbox_inches="tight")
fig.savefig(png_path, dpi=220, bbox_inches="tight")
print(svg_path)
print(pdf_path)
print(png_path)
