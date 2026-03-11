#!/usr/bin/env python3
"""Plot generation for statistical analysis dashboard."""

import io
import warnings
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server-side rendering

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Configure Korean font support
def _set_korean_font() -> None:
    """Set matplotlib font to support Korean characters."""
    # macOS Korean fonts
    korean_fonts = ["AppleGothic", "Apple SD Gothic Neo", "NanumGothic", "Malgun Gothic"]
    available = {f.name for f in fm.fontManager.ttflist}
    for font in korean_fonts:
        if font in available:
            plt.rcParams["font.family"] = font
            plt.rcParams["axes.unicode_minus"] = False
            return
    # Fallback: suppress glyph warnings
    import warnings
    warnings.filterwarnings("ignore", message="Glyph.*missing from font")

_set_korean_font()
import matplotlib.patches as mpatches
import numpy as np
import seaborn as sns
import pandas as pd


def format_p_annotation(p_value: float) -> str:
    """
    Convert p-value to significance annotation string.

    Args:
        p_value: The p-value from the statistical test.

    Returns:
        "***" for p < 0.001, "**" for p < 0.01, "*" for p < 0.05, "ns" otherwise.
    """
    if p_value < 0.001:
        return "***"
    elif p_value < 0.01:
        return "**"
    elif p_value < 0.05:
        return "*"
    else:
        return "ns"


def add_significance_brackets(
    ax: plt.Axes,
    x_positions: list[float],
    pairs: list[tuple[int, int]],
    p_values: list[float],
    y_max: float,
    step: float = 0.05,
) -> None:
    """
    Draw significance brackets above a boxplot.

    Args:
        ax: Matplotlib axes.
        x_positions: X positions of each group (0-indexed).
        pairs: List of (group_index_a, group_index_b) tuples to annotate.
        p_values: Corresponding p-values for each pair.
        y_max: Maximum y value in the plot (to position brackets above data).
        step: Vertical step between brackets (as fraction of y range).
    """
    y_range = ax.get_ylim()[1] - ax.get_ylim()[0]
    current_y = y_max + y_range * 0.05

    for i, ((idx_a, idx_b), p_val) in enumerate(zip(pairs, p_values)):
        annotation = format_p_annotation(p_val)
        x_a = x_positions[idx_a]
        x_b = x_positions[idx_b]

        # Draw bracket
        bracket_y = current_y + i * y_range * step
        tick_height = y_range * 0.02

        # Horizontal bar
        ax.plot([x_a, x_b], [bracket_y, bracket_y], "k-", linewidth=1.0, zorder=5)
        # Left tick
        ax.plot([x_a, x_a], [bracket_y - tick_height, bracket_y], "k-", linewidth=1.0, zorder=5)
        # Right tick
        ax.plot([x_b, x_b], [bracket_y - tick_height, bracket_y], "k-", linewidth=1.0, zorder=5)

        # Annotation text
        mid_x = (x_a + x_b) / 2
        ax.text(
            mid_x,
            bracket_y + y_range * 0.01,
            annotation,
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold" if annotation != "ns" else "normal",
            color="black" if annotation != "ns" else "gray",
        )


def create_boxplot(
    data_dict: dict[str, np.ndarray],
    title: str,
    y_label: str,
    sig_pairs: list[tuple[str, str, float]],
    alpha: float = 0.05,
) -> bytes:
    """
    Create a box plot with individual data points and significance brackets.

    Args:
        data_dict: {group_name: values_array}
        title: Plot title.
        y_label: Y-axis label.
        sig_pairs: List of (group_a_name, group_b_name, p_value) for brackets.
        alpha: Significance level (used for title annotation).

    Returns:
        PNG image as bytes.
    """
    n_groups = len(data_dict)
    fig_width = max(6.0, n_groups * 1.5)
    fig, ax = plt.subplots(figsize=(fig_width, 6))

    group_names = list(data_dict.keys())
    group_values = [data_dict[name] for name in group_names]

    # Color palette: first group (control) in gray, rest in muted colors
    palette = ["#888888"] + sns.color_palette("muted", n_colors=max(n_groups - 1, 1)).as_hex()
    if len(palette) < n_groups:
        palette = sns.color_palette("muted", n_colors=n_groups).as_hex()

    # Build DataFrame for seaborn
    data_rows = []
    for name, values in data_dict.items():
        for v in values:
            data_rows.append({"group": name, "value": float(v)})
    df_plot = pd.DataFrame(data_rows)

    # Box plot
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sns.boxplot(
            data=df_plot,
            x="group",
            y="value",
            order=group_names,
            palette=palette,
            width=0.5,
            fliersize=0,
            ax=ax,
            linewidth=1.5,
        )

        # Strip plot overlay (individual data points)
        sns.stripplot(
            data=df_plot,
            x="group",
            y="value",
            order=group_names,
            palette=palette,
            size=4,
            alpha=0.6,
            jitter=True,
            ax=ax,
        )

    # Calculate y_max for bracket placement
    all_values = np.concatenate([v for v in group_values if len(v) > 0])
    y_max = float(np.max(all_values)) if len(all_values) > 0 else 1.0
    y_min = float(np.min(all_values)) if len(all_values) > 0 else 0.0

    # Set y limits with some padding
    y_range = max(y_max - y_min, 0.1)
    ax.set_ylim(y_min - y_range * 0.1, y_max + y_range * 0.4)

    # Add significance brackets
    if sig_pairs:
        x_positions = list(range(n_groups))
        name_to_idx = {name: i for i, name in enumerate(group_names)}

        pairs_idx = []
        p_vals = []
        for grp_a, grp_b, p_val in sig_pairs:
            if grp_a in name_to_idx and grp_b in name_to_idx:
                pairs_idx.append((name_to_idx[grp_a], name_to_idx[grp_b]))
                p_vals.append(p_val)

        if pairs_idx:
            add_significance_brackets(ax, x_positions, pairs_idx, p_vals, y_max)

    # Labels and formatting
    ax.set_title(title, fontsize=12, pad=10)
    ax.set_xlabel("")
    ax.set_ylabel(y_label, fontsize=11)
    tick_labels = [name if len(name) <= 15 else name[:13] + ".." for name in group_names]
    ax.set_xticks(range(n_groups))
    ax.set_xticklabels(
        tick_labels,
        rotation=15 if n_groups > 4 else 0,
        ha="right" if n_groups > 4 else "center",
        fontsize=9,
    )

    # Add sample size below each box
    for i, (name, values) in enumerate(data_dict.items()):
        ax.text(
            i,
            y_min - y_range * 0.08,
            f"N={len(values)}",
            ha="center",
            va="top",
            fontsize=8,
            color="#555555",
        )

    # Add alpha annotation
    ax.text(
        0.98, 0.02,
        f"α = {alpha}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color="#777777",
    )

    plt.tight_layout()

    # Export to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def create_significance_heatmap(
    columns: list[str],
    pairwise_results: dict[tuple[str, str], dict],
    alpha: float = 0.05,
) -> bytes:
    """
    Create a pairwise significance heatmap.

    Color scheme:
      - White: ns (not significant)
      - Light blue: * (p < 0.05)
      - Blue: ** (p < 0.01)
      - Dark blue: *** (p < 0.001)
      - "-" on diagonal

    Args:
        columns: List of column/group names.
        pairwise_results: Dict mapping (col_a, col_b) to result dicts with p_value.
        alpha: Significance level.

    Returns:
        PNG image as bytes.
    """
    n = len(columns)
    if n < 2:
        # Return a blank image if fewer than 2 columns
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.text(0.5, 0.5, "데이터 부족", ha="center", va="center", transform=ax.transAxes)
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100)
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    # Build p-value matrix
    p_matrix = np.ones((n, n))  # 1.0 = not significant
    annotation_matrix = [["" for _ in range(n)] for _ in range(n)]

    col_to_idx = {col: i for i, col in enumerate(columns)}

    for i in range(n):
        annotation_matrix[i][i] = "-"
        p_matrix[i][i] = np.nan

    for (col_a, col_b), result in pairwise_results.items():
        if col_a not in col_to_idx or col_b not in col_to_idx:
            continue
        i, j = col_to_idx[col_a], col_to_idx[col_b]
        p_val = result.get("p_value")
        if p_val is not None:
            p_matrix[i][j] = float(p_val)
            p_matrix[j][i] = float(p_val)
            annotation_matrix[i][j] = format_p_annotation(float(p_val))
            annotation_matrix[j][i] = format_p_annotation(float(p_val))

    # Color mapping: lower p = darker blue
    # Convert p-values to color levels: ns=0, *=1, **=2, ***=3
    color_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                color_matrix[i][j] = np.nan
                continue
            p = p_matrix[i][j]
            if p < 0.001:
                color_matrix[i][j] = 3
            elif p < 0.01:
                color_matrix[i][j] = 2
            elif p < 0.05:
                color_matrix[i][j] = 1
            else:
                color_matrix[i][j] = 0

    fig_size = max(5, n * 0.9)
    fig, ax = plt.subplots(figsize=(fig_size, fig_size))

    # Custom colormap: white -> light blue -> blue -> dark blue
    from matplotlib.colors import LinearSegmentedColormap
    colors = ["#FFFFFF", "#AED6F1", "#2980B9", "#1A5276"]
    cmap = LinearSegmentedColormap.from_list("significance", colors, N=4)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        im = ax.imshow(color_matrix, cmap=cmap, vmin=0, vmax=3, aspect="auto")

    # Add text annotations
    for i in range(n):
        for j in range(n):
            text = annotation_matrix[i][j]
            if text:
                color = "white" if color_matrix[i][j] >= 2 else "black"
                ax.text(j, i, text, ha="center", va="center",
                       fontsize=10, color=color, fontweight="bold" if text != "-" else "normal")

    # Axis labels
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    short_names = [c if len(c) <= 12 else c[:10] + ".." for c in columns]
    ax.set_xticklabels(short_names, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(short_names, fontsize=9)

    ax.set_title("쌍별 유의성 히트맵 (Pairwise Significance)", fontsize=12, pad=10)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor="#FFFFFF", edgecolor="gray", label="ns (p ≥ 0.05)"),
        mpatches.Patch(facecolor="#AED6F1", label="* (p < 0.05)"),
        mpatches.Patch(facecolor="#2980B9", label="** (p < 0.01)"),
        mpatches.Patch(facecolor="#1A5276", label="*** (p < 0.001)"),
    ]
    ax.legend(handles=legend_elements, loc="upper right",
              bbox_to_anchor=(1.3, 1), fontsize=8)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


if __name__ == "__main__":
    # Quick smoke test
    import numpy as np

    rng = np.random.default_rng(42)
    test_data = {
        "Control": rng.normal(1.0, 0.2, 25),
        "Treat A": rng.normal(0.8, 0.2, 20),
        "Treat B": rng.normal(0.9, 0.3, 18),
    }

    sig_pairs = [("Control", "Treat A", 0.004), ("Control", "Treat B", 0.12)]
    png_bytes = create_boxplot(test_data, "Test Plot", "Measurement Value", sig_pairs)
    print(f"박스플롯 PNG 크기: {len(png_bytes)} bytes")

    pairwise = {
        ("Control", "Treat A"): {"p_value": 0.004},
        ("Control", "Treat B"): {"p_value": 0.12},
        ("Treat A", "Treat B"): {"p_value": 0.31},
    }
    heatmap_bytes = create_significance_heatmap(list(test_data.keys()), pairwise)
    print(f"히트맵 PNG 크기: {len(heatmap_bytes)} bytes")
    print("시각화 테스트 완료")
