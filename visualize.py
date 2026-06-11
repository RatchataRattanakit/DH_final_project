#!/usr/bin/env python3
"""
visualize.py
Generates static matplotlib charts from normalized GDELT data.
Saves PNGs to dashboard/ folder.

Run after process_data.py.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker

NORMALIZED_PATH = "data/keyword_frequency_annual_normalized.csv"
if not os.path.exists(NORMALIZED_PATH):
    print(f"ERROR: {NORMALIZED_PATH} not found. Run process_data.py first.")
    sys.exit(1)

os.makedirs("dashboard", exist_ok=True)

# Global plot style
plt.rcParams.update({
    "figure.facecolor": "#0f0f0f",
    "axes.facecolor": "#1a1a1a",
    "axes.edgecolor": "#444",
    "axes.labelcolor": "#ccc",
    "text.color": "#e8e6e1",
    "xtick.color": "#888",
    "ytick.color": "#888",
    "grid.color": "#2a2a2a",
    "grid.linewidth": 0.5,
    "font.family": "serif",
    "legend.facecolor": "#1a1a1a",
    "legend.edgecolor": "#444",
    "legend.labelcolor": "#ccc",
})

COLORS = {
    "patriotism":    "#ff6b6b",
    "china_dream":   "#f4b942",
    "nationalism":   "#4ecdc4",
    "guochao":       "#a8e6cf",
    "boycott":       "#ff8b94",
    "foreign":       "#ff6b6b",
    "domestic":      "#f4b942",
}

EVENTS = [
    {"year": 2017, "label": "THAAD\nBoycott"},
    {"year": 2019, "label": "NBA\nControversy"},
    {"year": 2021, "label": "H&M\nBoycott"},
    {"year": 2022, "label": "Winter\nOlympics"},
]

annual = pd.read_csv(NORMALIZED_PATH)

# ---------------------------------------------------------------------------
# Chart 1 — Keyword Frequency Timeline
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(13, 6))
fig.patch.set_facecolor("#0f0f0f")

kwmap = {
    "patriotism_norm":   ("Patriotism (爱国)",          COLORS["patriotism"]),
    "china_dream_norm":  ("China Dream (中国梦)",        COLORS["china_dream"]),
    "nationalism_norm":  ("Nationalism (民族主义)",       COLORS["nationalism"]),
    "guochao_norm":      ("Guochao (国潮)",              COLORS["guochao"]),
}

for col, (label, color) in kwmap.items():
    if col in annual.columns:
        ax.plot(annual["year"], annual[col], label=label, color=color,
                linewidth=2.5, marker="o", markersize=5, zorder=3)

ymax = annual[[c for c in kwmap if c in annual.columns]].max().max() * 1.15

for ev in EVENTS:
    ax.axvline(ev["year"], color="#f0a500", linestyle="--", alpha=0.55, linewidth=1, zorder=2)
    ax.text(ev["year"] + 0.08, ymax * 0.98, ev["label"], rotation=90,
            fontsize=8, color="#f0a500", va="top", ha="left")

ax.set_xlim(2014.5, 2024.8)
ax.set_ylim(0, ymax)
ax.set_xlabel("Year", fontsize=12)
ax.set_ylabel("Mentions per 100k Articles", fontsize=12)
ax.set_title("Nationalist Keyword Frequency in Chinese State Media (2015–2024)",
             fontsize=14, pad=16)
ax.legend(loc="upper left", framealpha=0.3, fontsize=10)
ax.grid(True, alpha=0.35)

plt.tight_layout()
out1 = "dashboard/chart1_keyword_frequency.png"
plt.savefig(out1, dpi=150, bbox_inches="tight", facecolor="#0f0f0f")
plt.close()
print(f"Saved: {out1}")

# ---------------------------------------------------------------------------
# Chart 2 — Pre-Xi vs Xi Era Bar Comparison
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor("#0f0f0f")

early = annual[annual["year"] <= 2018]
late  = annual[annual["year"] >= 2019]

kw_display = {
    "patriotism_norm":  "Patriotism",
    "china_dream_norm": "China Dream",
    "nationalism_norm": "Nationalism",
    "guochao_norm":     "Guochao",
}

valid_keys = [k for k in kw_display if k in annual.columns]
labels = [kw_display[k] for k in valid_keys]
early_vals = [early[k].mean() for k in valid_keys]
late_vals  = [late[k].mean()  for k in valid_keys]

x = np.arange(len(labels))
w = 0.35

bars1 = ax.bar(x - w/2, early_vals, w, label="Early Xi Era (2015–2018)",
               color="#4a4a7a", edgecolor="#666", zorder=3)
bars2 = ax.bar(x + w/2, late_vals,  w, label="Consolidated Xi Era (2019–2024)",
               color="#c41e3a", edgecolor="#e55", zorder=3)

for i, (ev, lv) in enumerate(zip(early_vals, late_vals)):
    if ev > 0:
        pct = (lv - ev) / ev * 100
        ax.text(x[i] + w/2, lv + 8, f"+{pct:.0f}%",
                ha="center", va="bottom", fontsize=11,
                color="#f4b942", fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11)
ax.set_ylabel("Avg. Mentions per 100k Articles", fontsize=12)
ax.set_title("Nationalist Language: Before vs. After Xi's Consolidation",
             fontsize=14, pad=16)
ax.legend(framealpha=0.3, fontsize=10)
ax.grid(axis="y", alpha=0.35, zorder=0)
ax.set_axisbelow(True)

plt.tight_layout()
out2 = "dashboard/chart2_era_comparison.png"
plt.savefig(out2, dpi=150, bbox_inches="tight", facecolor="#0f0f0f")
plt.close()
print(f"Saved: {out2}")

# ---------------------------------------------------------------------------
# Chart 3 — Avg Tone over Time
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(13, 5))
fig.patch.set_facecolor("#0f0f0f")

if "avg_tone" in annual.columns:
    ax.plot(annual["year"], annual["avg_tone"], color="#ff6b6b",
            linewidth=2.5, marker="o", markersize=5, label="Avg. Tone (state media)")
    ax.axhline(0, color="#666", linestyle="--", linewidth=0.8)
    ax.fill_between(annual["year"], annual["avg_tone"], 0,
                    where=annual["avg_tone"] < 0,
                    color="#ff6b6b", alpha=0.15)

    for ev in EVENTS:
        ax.axvline(ev["year"], color="#f0a500", linestyle="--", alpha=0.5, linewidth=1)

    ymin = annual["avg_tone"].min() * 1.2
    ax.set_ylim(ymin, 1.5)
    ax.set_xlim(2014.5, 2024.8)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("GDELT Tone Score (negative = hostile)", fontsize=12)
    ax.set_title("Average Tone of Chinese State Media Over Time",
                 fontsize=14, pad=16)
    ax.legend(framealpha=0.3, fontsize=10)
    ax.grid(True, alpha=0.35)
else:
    ax.text(0.5, 0.5, "avg_tone column not found in data",
            ha="center", va="center", transform=ax.transAxes, color="#888")

plt.tight_layout()
out3 = "dashboard/chart3_tone_over_time.png"
plt.savefig(out3, dpi=150, bbox_inches="tight", facecolor="#0f0f0f")
plt.close()
print(f"Saved: {out3}")

# ---------------------------------------------------------------------------
# Chart 4 — Keyword Heatmap (year × keyword)
# ---------------------------------------------------------------------------
if len(valid_keys) > 0:
    fig, ax = plt.subplots(figsize=(13, 4))
    fig.patch.set_facecolor("#0f0f0f")

    matrix = annual.set_index("year")[valid_keys].T.values.astype(float)
    years_list = annual["year"].tolist()

    im = ax.imshow(matrix, aspect="auto", cmap="Reds",
                   vmin=0, vmax=matrix.max())

    ax.set_xticks(range(len(years_list)))
    ax.set_xticklabels(years_list, fontsize=10)
    ax.set_yticks(range(len(valid_keys)))
    ax.set_yticklabels(labels, fontsize=11)

    for i in range(len(valid_keys)):
        for j in range(len(years_list)):
            val = matrix[i, j]
            text_color = "white" if val < matrix.max() * 0.6 else "#111"
            ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                    fontsize=8, color=text_color)

    for ev in EVENTS:
        if ev["year"] in years_list:
            j = years_list.index(ev["year"])
            for side in ["left", "right"]:
                ax.axvline(j + (0.5 if side == "right" else -0.5),
                           color="#f0a500", linewidth=1.5, alpha=0.8)

    plt.colorbar(im, ax=ax, shrink=0.8, label="Mentions per 100k")
    ax.set_title("Keyword Intensity Heatmap (per 100k Articles)",
                 fontsize=14, pad=16)

    plt.tight_layout()
    out4 = "dashboard/chart4_heatmap.png"
    plt.savefig(out4, dpi=150, bbox_inches="tight", facecolor="#0f0f0f")
    plt.close()
    print(f"Saved: {out4}")

print("\nVisualization complete. Static charts saved to dashboard/")
