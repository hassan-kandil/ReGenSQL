#!/usr/bin/env python3
"""
Compute convergence generation and per-generation fitness stats from a ReGenSQL JSON run,
and generate:
  1. A box plot of fitness across generations aggregated across all queries.
  2. Per-query box plots of fitness distributions across generations.

All outputs are placed inside a directory named after the JSON file (without extension).
"""

import argparse
import csv
import json
import math
import statistics
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def generation_stats(fitness_history: List[List[float]]) -> Tuple[List[float], List[float], List[float]]:
    """Return best, mean, median fitness per generation."""
    best, mean, median = [], [], []
    for gen in fitness_history:
        if not gen:
            best.append(math.nan)
            mean.append(math.nan)
            median.append(math.nan)
            continue
        best.append(min(gen))  # lower is better
        mean.append(sum(gen) / len(gen))
        median.append(statistics.median(gen))
    return best, mean, median


def compute_convergence(best_per_gen: List[float], epsilon: float, patience: int) -> int:
    """Plateau rule: relative improvement < epsilon for 'patience' generations. Returns 1-indexed convergence gen."""
    if not best_per_gen:
        return 0

    streak = 0
    for g in range(1, len(best_per_gen)):
        prev, cur = best_per_gen[g - 1], best_per_gen[g]
        if prev == 0 or math.isnan(prev) or math.isnan(cur):
            rel_impr = 0.0
        else:
            rel_impr = (prev - cur) / abs(prev)

        if rel_impr < epsilon:
            streak += 1
        else:
            streak = 0

        if streak >= patience:
            return g + 1
    return len(best_per_gen)


def summarize_query(qrec: Dict[str, Any], epsilon: float, patience: int) -> Dict[str, Any]:
    qname = qrec.get("query_name", "unknown")
    fh = qrec.get("fitness_history", [])
    if not isinstance(fh, list) or not fh:
        return {
            "query_name": qname,
            "generations": 0,
            "convergence_gen": 0,
            "best_per_gen": [],
            "mean_per_gen": [],
            "median_per_gen": [],
            "fitness_history": []
        }

    best, mean, median = generation_stats(fh)
    conv = compute_convergence(best, epsilon, patience)
    return {
        "query_name": qname,
        "generations": len(fh),
        "convergence_gen": conv,
        "best_per_gen": best,
        "mean_per_gen": mean,
        "median_per_gen": median,
        "fitness_history": fh
    }


def write_per_query_csv(outdir: Path, summary: Dict[str, Any]) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    qname = summary["query_name"]
    path = outdir / f"{qname}_per_generation.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["generation", "best_fitness", "mean_fitness", "median_fitness"])
        for i, (b, m, md) in enumerate(
            zip(summary["best_per_gen"], summary["mean_per_gen"], summary["median_per_gen"]), start=1
        ):
            w.writerow([i, b, m, md])
    return path


def write_overview_csv(outpath: Path, summaries: List[Dict[str, Any]]) -> Path:
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with outpath.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["query_name", "generations", "convergence_gen"])
        for s in summaries:
            w.writerow([s["query_name"], s["generations"], s["convergence_gen"]])
    return outpath


def aggregate_fitness_by_generation(
    summaries: List[Dict[str, Any]],
    best_only: bool = False
) -> List[List[float]]:
    """Aggregate fitness across queries per generation (all individuals or only per-query bests)."""
    max_gens = 0
    for s in summaries:
        max_gens = max(max_gens, s.get("generations", 0))

    agg: List[List[float]] = [[] for _ in range(max_gens)]

    for s in summaries:
        fh = s.get("fitness_history", [])
        if best_only:
            best = s.get("best_per_gen", [])
            for g_idx, b in enumerate(best):
                if not math.isnan(b):
                    agg[g_idx].append(b)
        else:
            for g_idx, gen in enumerate(fh):
                vals = [v for v in gen if isinstance(v, (int, float)) and not math.isnan(v)]
                agg[g_idx].extend(vals)

    return agg


def plot_boxplot_across_generations(
    agg: List[List[float]],
    outpath: Path,
    title: str,
    xlabel: str,
    ylabel: str
) -> None:
    """Create and save a box plot: one box per generation over aggregated fitness values."""
    while agg and not agg[-1]:
        agg.pop()

    if not agg:
        print("No data to plot for box plot.")
        return

    plt.figure(figsize=(10, 4.5))
    plt.boxplot(agg, showfliers=False)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    n = len(agg)
    if n > 30:
        step = max(1, n // 15)
        ticks = list(range(1, n + 1, step))
        plt.xticks(ticks, ticks)

    outpath.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()
    print(f"Saved box plot to: {outpath}")


def plot_per_query(summary: Dict[str, Any], outdir: Path) -> Path:
    """
    Plot per-query box plot of fitness distributions across generations.
    Each box shows the distribution of the population's fitness at that generation.
    """
    qname = summary["query_name"]
    fh = summary["fitness_history"]
    conv = summary["convergence_gen"]

    if not fh:
        return None

    while fh and not fh[-1]:
        fh.pop()

    plt.figure(figsize=(10, 4.5))
    plt.boxplot(fh, showfliers=False)
    plt.xlabel("Generation")
    plt.ylabel("Fitness")
    plt.title(f"Fitness distribution per generation: {qname}")

    if conv > 0:
        plt.axvline(conv, color="red", linestyle="--", alpha=0.7, label="Convergence")
        plt.legend()

    n = len(fh)
    if n > 30:
        step = max(1, n // 15)
        ticks = list(range(1, n + 1, step))
        plt.xticks(ticks, ticks)

    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / f"{qname}_fitness_boxplot.png"
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()
    return outpath


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_path", type=Path, help="Path to the JSON results file")
    ap.add_argument("--epsilon", type=float, default=0.005, help="Relative improvement threshold")
    ap.add_argument("--patience", type=int, default=10, help="Consecutive generations below threshold for convergence")
    ap.add_argument("--write-csv", action="store_true", help="Write CSV files with per-generation stats and overview")
    ap.add_argument("--boxplot-best-only", action="store_true",
                    help="Aggregate only best-per-query fitness per generation for the aggregated box plot")
    args = ap.parse_args()

    # Make base output directory from json filename (no extension)
    base_outdir = Path(args.json_path.stem)
    base_outdir.mkdir(parents=True, exist_ok=True)

    csv_dir = base_outdir / "convergence_csv"
    overview_csv = base_outdir / "convergence_overview.csv"
    boxplot_out = base_outdir / "fitness_boxplot_all_queries.png"
    per_query_plots_dir = base_outdir / "per_query_plots"

    data = load_json(args.json_path)
    run_queries = data.get("run_queries", [])
    if not run_queries:
        print("No 'run_queries' found in the JSON.")
        return

    summaries = [summarize_query(q, args.epsilon, args.patience) for q in run_queries]

    print(f"# Queries processed: {len(summaries)}")
    conv_gens = [s["convergence_gen"] for s in summaries if s["convergence_gen"]]
    if conv_gens:
        print(f"Mean convergence generation: {statistics.mean(conv_gens):.2f}")
        print(f"Median convergence generation: {statistics.median(conv_gens):.0f}")
    else:
        print("No convergence information available.")

    if args.write_csv:
        csv_dir.mkdir(parents=True, exist_ok=True)
        for s in summaries:
            write_per_query_csv(csv_dir, s)
        write_overview_csv(overview_csv, summaries)
        print(f"Wrote per-query CSVs to: {csv_dir}")
        print(f"Wrote overview CSV to: {overview_csv}")

    # Aggregated box plot
    agg = aggregate_fitness_by_generation(summaries, best_only=args.boxplot_best_only)
    plot_boxplot_across_generations(
        agg,
        outpath=boxplot_out,
        title="Fitness across generations (aggregated across all queries)" + (" [best only]" if args.boxplot_best_only else ""),
        xlabel="Generation",
        ylabel="Fitness"
    )

    # Per-query box plots
    for s in summaries:
        outpath = plot_per_query(s, per_query_plots_dir)
        if outpath:
            print(f"Saved {outpath}")


if __name__ == "__main__":
    main()
