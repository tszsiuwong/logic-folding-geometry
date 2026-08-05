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
    """Find the most compact box (d1, d2, d3) that can hold n cells.
    Minimises half surface area d1*d2 + d2*d3 + d1*d3 subject to d1*d2*d3 >= n."""
    if n <= 0:
        return (0, 0, 0)
    best = (1, 1, n)
    best_hsa = 1 + n + n
    limit_a = int(round(n ** (1 / 3))) + 2
    for a in range(1, limit_a):
        limit_b = int(math.isqrt(n // a)) + 2
        for b in range(a, limit_b):
            c = math.ceil(n / (a * b))
            hsa = a * b + b * c + a * c
            if hsa < best_hsa:
                best_hsa = hsa
                best = (a, b, c)
    return best


def pos_3d(n: int) -> list[tuple[int, int, int]]:
    """Generate (x, y, z) positions for n cells in optimal 3D box layout."""
    d1, d2, d3 = optimal_3d_dims(n)
    positions = []
    for i in range(n):
        x = i % d1
        y = (i // d1) % d2
        z = i // (d1 * d2)
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

    perfect_cubes = [r for r in results
                     if round(r["N"] ** (1/3)) ** 3 == r["N"]]
    perfect_squares = [r for r in results
                       if round(math.isqrt(r["N"])) ** 2 == r["N"]]

    print(f"\n{'='*60}")
    print(f"Summary (N = 1..{len(results)})")
    print(f"{'='*60}")
    print(f"  Avg reduction:             {avg_reduction:>6.1f}%")
    print(f"  Max reduction:   N={max_r['N']:>3d}  {max_r['reduction_pct']:>6.1f}%  "
          f"(2D:{max_r['grid_2d']}  3D:{max_r['box_3d']})")
    print(f"  Min reduction:   N={min_r['N']:>3d}  {min_r['reduction_pct']:>6.1f}%  "
          f"(2D:{min_r['grid_2d']}  3D:{min_r['box_3d']})")

    if perfect_cubes:
        cubes_str = ", ".join(
            f"N={r['N']}: {r['reduction_pct']:.1f}%" for r in perfect_cubes
        )
        print(f"\n  Perfect cubes:   {cubes_str}")

    if perfect_squares:
        squares_str = ", ".join(
            f"N={r['N']}: {r['reduction_pct']:.1f}%" for r in perfect_squares
        )
        print(f"  Perfect squares: {squares_str}")

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
    """Generate a 2x2 figure: wirelength, ratio, reduction%, and average WL."""
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

    # Mark perfect cubes
    perfect_cubes = [n for n in Ns if round(n ** (1/3)) ** 3 == n]

    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("2D vs 3D Wirelength Comparison (N fully-connected cells)",
                 fontsize=14, fontweight="bold")

    # --- Subplot 1: Total wirelength ---
    ax = axes[0, 0]
    ax.plot(Ns, wl2, "b-", linewidth=1.2, alpha=0.8, label="2D grid")
    ax.plot(Ns, wl3, "r-", linewidth=1.2, alpha=0.8, label="3D box")
    ax.set_xlabel("N (number of cells)")
    ax.set_ylabel("Total Manhattan wirelength")
    ax.set_title("Total Wirelength (complete graph)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    # --- Subplot 2: Ratio 3D/2D ---
    ax = axes[0, 1]
    ax.plot(Ns, ratio, "g-", linewidth=1.5)
    ax.axhline(y=1.0, color="gray", linestyle="--", linewidth=0.8)
    ax.set_xlabel("N (number of cells)")
    ax.set_ylabel("Ratio (3D / 2D)")
    ax.set_title("Wirelength Ratio 3D/2D")
    ax.grid(True, alpha=0.3)
    # Highlight perfect cubes
    for cube_n in perfect_cubes:
        idx = cube_n - 1
        ax.scatter([cube_n], [ratio[idx]], color="red", s=40, zorder=5)
        ax.annotate(f"N={cube_n}", (cube_n, ratio[idx]),
                    textcoords="offset points", xytext=(0, -15), ha="center",
                    fontsize=8, color="red")

    # --- Subplot 3: Reduction % ---
    ax = axes[1, 0]
    ax.fill_between(Ns, reduction, alpha=0.3, color="green")
    ax.plot(Ns, reduction, "g-", linewidth=1.5)
    ax.set_xlabel("N (number of cells)")
    ax.set_ylabel("Reduction (%)")
    ax.set_title("Wirelength Reduction (3D vs 2D)")
    ax.grid(True, alpha=0.3)
    for cube_n in perfect_cubes:
        idx = cube_n - 1
        ax.scatter([cube_n], [reduction[idx]], color="red", s=40, zorder=5)

    # --- Subplot 4: Average WL per edge ---
    ax = axes[1, 1]
    ax.plot(Ns, avg2, "b-", linewidth=1, alpha=0.8, label="2D avg")
    ax.plot(Ns, avg3, "r-", linewidth=1, alpha=0.8, label="3D avg")
    ax.set_xlabel("N (number of cells)")
    ax.set_ylabel("Average wirelength per edge")
    ax.set_title("Average Wirelength per Edge")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Plot saved to {save_path}")
    else:
        plt.show()


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
