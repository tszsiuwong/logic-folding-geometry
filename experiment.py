#!/usr/bin/env python3
"""
Thought Experiment: 2D → 3D Wirelength Reduction for Logic Folding
==================================================================
N fully-connected cells (complete graph K_N), arranged in optimal
space-filling tiling. Compare total Manhattan wirelength between
2D grid packing and 3D box packing.

Key insight: 2D average hop distance scales as O(√N), 3D as O(∛N).
For a complete graph with N(N-1)/2 edges, total wirelength ratio
3D/2D ~ O(N^(-1/6)), approaching 0 as N → ∞.

Usage:
    python experiment.py              # run and show plot
    python experiment.py --no-plot    # text-only output
    python experiment.py --csv        # export CSV
"""

from __future__ import annotations

import math
import sys
import csv
from pathlib import Path

# ---------------------------------------------------------------------------
# Core: optimal 2D / 3D tiling
# ---------------------------------------------------------------------------

def optimal_2d_dims(n: int) -> tuple[int, int]:
    """Find the most compact rectangle (rows, cols) that can hold n cells.
    Minimises perimeter = 2*(rows+cols) subject to rows*cols >= n."""
    if n <= 0:
        return (0, 0)
    best_rows, best_cols = 1, n
    best_half_perim = n + 1
    for rows in range(1, int(math.isqrt(n)) + 2):
        cols = math.ceil(n / rows)
        if rows + cols < best_half_perim:
            best_half_perim = rows + cols
            best_rows, best_cols = rows, cols
    return best_rows, best_cols


def pos_2d(n: int) -> list[tuple[int, int]]:
    """Generate (x, y) positions for n cells in optimal 2D grid layout."""
    _, cols = optimal_2d_dims(n)
    return [(i % cols, i // cols) for i in range(n)]


def optimal_3d_dims(n: int) -> tuple[int, int, int]:
    """2-die stack: find optimal a×b rectangle for ceil(n/2) cells per layer,
    then stack two layers → a×b×2."""
    if n <= 0:
        return (0, 0, 0)
    per_layer = math.ceil(n / 2)
    a, b = optimal_2d_dims(per_layer)
    return (a, b, 2)


def pos_3d(n: int) -> list[tuple[int, int, int]]:
    """2-die stack: first ceil(n/2) cells on die 0, rest on die 1.
    Each die uses the same optimal 2D grid for its cells."""
    per_layer = math.ceil(n / 2)
    _, cols = optimal_2d_dims(per_layer)
    positions = []
    for i in range(n):
        z = 0 if i < per_layer else 1
        local_i = i if i < per_layer else i - per_layer
        x = local_i % cols
        y = local_i // cols
        positions.append((x, y, z))
    return positions


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def manhattan_2d(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def manhattan_3d(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def total_wirelength(positions: list, dist_fn, n: int) -> int:
    """Sum of Manhattan distances over all N*(N-1)/2 pairs (complete graph)."""
    total = 0
    for i in range(n):
        pi = positions[i]
        for j in range(i + 1, n):
            total += dist_fn(pi, positions[j])
    return total


def avg_wirelength(total_wl: int, n: int) -> float:
    """Average wirelength per edge."""
    num_edges = n * (n - 1) / 2
    return total_wl / num_edges if num_edges > 0 else 0.0


# ---------------------------------------------------------------------------
# Experiment runner
# ---------------------------------------------------------------------------

def run_experiment(n_max: int = 100) -> list[dict]:
    """Run the comparison for N = 1 .. n_max. Returns list of result dicts."""
    results = []
    for n in range(1, n_max + 1):
        p2 = pos_2d(n)
        p3 = pos_3d(n)
        r2, c2 = optimal_2d_dims(n)
        d1, d2, d3 = optimal_3d_dims(n)

        wl2 = total_wirelength(p2, manhattan_2d, n)
        wl3 = total_wirelength(p3, manhattan_3d, n)
        ratio = wl3 / wl2 if wl2 > 0 else 1.0
        reduction = (1 - ratio) * 100

        results.append({
            "N": n,
            "wl_2d": wl2,
            "wl_3d": wl3,
            "avg_2d": avg_wirelength(wl2, n),
            "avg_3d": avg_wirelength(wl3, n),
            "ratio": ratio,
            "reduction_pct": reduction,
            "grid_2d": f"{r2}x{c2}",
            "box_3d": f"{d1}x{d2}x{d3}",
        })
    return results


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_table(results: list[dict]):
    """Pretty-print results table."""
    header = f"{'N':>4}  {'2D_grid':>7}  {'3D_box':>9}  {'WL_2D':>10}  {'WL_3D':>10}  {'ratio':>7}  {'reduction':>9}"
    print(header)
    print("-" * len(header))

    # Print all for N <= 30, then every 5th
    for r in results:
        n = r["N"]
        if n <= 30 or n % 5 == 0:
            print(
                f"{n:>4}  {r['grid_2d']:>7}  {r['box_3d']:>9}  "
                f"{r['wl_2d']:>10}  {r['wl_3d']:>10}  "
                f"{r['ratio']:>7.4f}  {r['reduction_pct']:>8.1f}%"
            )


def print_summary(results: list[dict]):
    """Print key summary statistics."""
    max_r = max(results, key=lambda x: x["reduction_pct"])
    min_r = min(results, key=lambda x: x["reduction_pct"])
    avg_reduction = sum(r["reduction_pct"] for r in results) / len(results)

    print(f"\n{'='*60}")
    print(f"Summary (N = 1..{len(results)})")
    print(f"{'='*60}")
    print(f"  Avg reduction:             {avg_reduction:>6.1f}%")
    print(f"  Max reduction:   N={max_r['N']:>3d}  {max_r['reduction_pct']:>6.1f}%  "
          f"(2D:{max_r['grid_2d']}  3D:{max_r['box_3d']})")
    print(f"  Min reduction:   N={min_r['N']:>3d}  {min_r['reduction_pct']:>6.1f}%  "
          f"(2D:{min_r['grid_2d']}  3D:{min_r['box_3d']})")
    print(f"{'='*60}")


def export_csv(results: list[dict], path: str = "output/results.csv"):
    """Export results to CSV."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["N", "wl_2d", "wl_3d", "avg_2d", "avg_3d",
                  "ratio", "reduction_pct", "grid_2d", "box_3d"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nCSV exported to {path}")


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

def plot_results(results: list[dict], save_path: str | None = None):
    """Generate separate figures: wirelength, ratio, reduction%, average WL."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
    except ImportError:
        print("matplotlib not installed. Install with: pip install matplotlib")
        return

    Ns = [r["N"] for r in results]
    wl2 = [r["wl_2d"] for r in results]
    wl3 = [r["wl_3d"] for r in results]
    avg2 = [r["avg_2d"] for r in results]
    avg3 = [r["avg_3d"] for r in results]
    ratio = [r["ratio"] for r in results]
    reduction = [r["reduction_pct"] for r in results]

    # --- Figure 1: Total wirelength ---
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(Ns, wl2, "b-", linewidth=1.2, alpha=0.8, label="2D grid")
    ax1.plot(Ns, wl3, "r-", linewidth=1.2, alpha=0.8, label="3D (2-die)")
    ax1.set_xlabel("N (number of cells)"); ax1.set_ylabel("Total Manhattan wirelength")
    ax1.set_title("Total Wirelength (complete graph)"); ax1.legend(); ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    fig1.tight_layout()
    if save_path:
        p = Path(save_path); fig1.savefig(p.parent / f"{p.stem}_wl{p.suffix}", dpi=150, bbox_inches="tight")

    # --- Figure 2: Ratio 3D/2D ---
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ax2.plot(Ns, ratio, "g-", linewidth=1.5)
    ax2.axhline(y=1.0, color="gray", linestyle="--", linewidth=0.8, label="2D baseline")
    ax2.set_xlabel("N (number of cells)"); ax2.set_ylabel("Ratio (3D / 2D)")
    ax2.set_title("Wirelength Ratio 3D/2D"); ax2.legend(); ax2.grid(True, alpha=0.3)
    fig2.tight_layout()
    if save_path:
        p = Path(save_path); fig2.savefig(p.parent / f"{p.stem}_ratio{p.suffix}", dpi=150, bbox_inches="tight")

    # --- Figure 3: Reduction % ---
    fig3, ax3 = plt.subplots(figsize=(8, 5))
    ax3.fill_between(Ns, reduction, alpha=0.3, color="green")
    ax3.plot(Ns, reduction, "g-", linewidth=1.5)
    ax3.set_xlabel("N (number of cells)"); ax3.set_ylabel("Reduction (%)")
    ax3.set_title("Wirelength Reduction (3D vs 2D)"); ax3.grid(True, alpha=0.3)
    fig3.tight_layout()
    if save_path:
        p = Path(save_path); fig3.savefig(p.parent / f"{p.stem}_reduction{p.suffix}", dpi=150, bbox_inches="tight")

    # --- Figure 4: Average WL per edge ---
    fig4, ax4 = plt.subplots(figsize=(8, 5))
    ax4.plot(Ns, avg2, "b-", linewidth=1, alpha=0.8, label="2D avg")
    ax4.plot(Ns, avg3, "r-", linewidth=1, alpha=0.8, label="3D avg")
    ax4.set_xlabel("N (number of cells)"); ax4.set_ylabel("Average wirelength per edge")
    ax4.set_title("Average Wirelength per Edge"); ax4.legend(); ax4.grid(True, alpha=0.3)
    fig4.tight_layout()
    if save_path:
        p = Path(save_path); fig4.savefig(p.parent / f"{p.stem}_avg{p.suffix}", dpi=150, bbox_inches="tight")

    if not save_path:
        plt.show()
    else:
        print(f"Plots saved to {Path(save_path).parent}/")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    n_max = 100
    do_plot = True
    do_csv = False

    args = sys.argv[1:]
    for a in args:
        if a == "--no-plot":
            do_plot = False
        elif a == "--csv":
            do_csv = True
        elif a.startswith("--n="):
            n_max = int(a.split("=")[1])

    results = run_experiment(n_max)
    print_table(results)
    print_summary(results)

    if do_csv:
        export_csv(results)

    if do_plot:
        plot_results(results, save_path="output/plot.png")


if __name__ == "__main__":
    main()
