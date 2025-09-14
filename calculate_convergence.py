#!/usr/bin/env python3
"""
Compute convergence generation and per-generation fitness stats from a ReGenSQL JSON run,
and generate:
  1. A box plot of fitness across generations aggregated across all queries.
  2. Per-query box plots of fitness distributions across generations.

Also computes plateau statistics: consecutive generations where best fitness does not change
significantly (based on a relative threshold).

Replaces convergence rate with the optimum-free average (geometric) convergence rate per He & Lin (2016):
  R_dd(t) = 1 - | (f_{t+tau} - f_t) / (f_t - f_{t-tau}) | ** (1 / tau),
where f_t is the per-generation best fitness (lower is better) and tau is a window size.

We report R_dd at generation 5 when available.

All outputs are placed inside a directory named after the JSON file (without extension).
"""

import argparse
import csv
import json
import math
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
    """
    Plateau rule: relative improvement < epsilon for 'patience' consecutive generations.
    Returns 1-indexed convergence generation, or len(best_per_gen) if never converged sooner.
    Only counts lack of improvement (ignores small regressions).
    """
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
            return g + 1  # 1-indexed
    return len(best_per_gen)


def compute_plateau_stats(best_per_gen: List[float], plateau_epsilon: float) -> Dict[str, Any]:
    """
    Plateau definition for 'no significant change' between consecutive generations:
      abs(relative_change) < plateau_epsilon
    where relative_change = (cur - prev) / |prev|.
    """
    G = len(best_per_gen)
    plateau_step = [0] * G
    plateau_streak = [0] * G
    max_len = 0
    max_end = 0

    for g in range(1, G):
        prev, cur = best_per_gen[g - 1], best_per_gen[g]
        if prev == 0 or math.isnan(prev) or math.isnan(cur):
            rel_change = 0.0
        else:
            rel_change = (cur - prev) / abs(prev)

        if abs(rel_change) <= plateau_epsilon:
            plateau_step[g] = 1
            plateau_streak[g] = plateau_streak[g - 1] + 1
        else:
            plateau_step[g] = 0
            plateau_streak[g] = 0

        if plateau_streak[g] > max_len:
            max_len = plateau_streak[g]
            max_end = g + 1  # 1-indexed generation

    final_len = plateau_streak[-1] if G > 0 else 0
    return {
        "plateau_step": plateau_step,
        "plateau_streak": plateau_streak,
        "max_plateau_len": max_len,
        "max_plateau_end_gen": max_end,
        "final_plateau_len": final_len,
    }


def compute_alt_avg_conv_rate_series(
    best_per_gen: List[float],
    tau: int,
) -> List[float]:
    """
    Compute the optimum-free average (geometric) convergence rate series R_dd(t):
      R_dd(t) = 1 - | (f_{t+tau} - f_t) / (f_t - f_{t-tau}) | ** (1 / tau)
    Using 1-indexed notion for t; we store results in a 0-indexed list aligned with generations.
    Defined only when t - tau >= 0 and t + tau < G; else NaN.
    """
    G = len(best_per_gen)
    rates = [math.nan] * G
    if G == 0 or tau <= 0:
      return rates

    # Use best_per_gen as f_t; guard NaNs
    if any(math.isnan(v) for v in best_per_gen):
        return rates

    # t is 1..G; python index is t-1
    for t in range(1, G + 1):
        left = t - tau
        right = t + tau
        if left < 1 or right > G:
            # Not enough history/ahead window
            continue
        ft = best_per_gen[t - 1]
        f_left = best_per_gen[left - 1]
        f_right = best_per_gen[right - 1]

        denom = ft - f_left
        num = f_right - ft

        # If denom is zero, undefined
        if denom == 0 or math.isnan(denom) or math.isnan(num):
            continue

        ratio = abs(num / denom)
        try:
            rates[t - 1] = 1.0 - (ratio ** (1.0 / tau))
        except Exception:
            rates[t - 1] = math.nan

    return rates


def summarize_query(
    qrec: Dict[str, Any],
    epsilon: float,
    patience: int,
    plateau_epsilon: float,
    tau: int,
) -> Dict[str, Any]:
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
            "fitness_history": [],
            "plateau_step": [],
            "plateau_streak": [],
            "max_plateau_len": 0,
            "max_plateau_end_gen": 0,
            "final_plateau_len": 0,
            "avg_conv_rate_series": [],
            "avg_conv_rate_at5": math.nan,
        }

    best, mean, median = generation_stats(fh)
    conv = compute_convergence(best, epsilon, patience)
    plat = compute_plateau_stats(best, plateau_epsilon)

    # Optimum-free convergence rate (sliding window)
    avg_rate_series = compute_alt_avg_conv_rate_series(best, tau)
    avg_rate_at5 = avg_rate_series[4] if len(avg_rate_series) >= 5 else math.nan

    return {
        "query_name": qname,
        "generations": len(fh),
        "convergence_gen": conv,
        "best_per_gen": best,
        "mean_per_gen": mean,
        "median_per_gen": median,
        "fitness_history": fh,
        "avg_conv_rate_series": avg_rate_series,
        "avg_conv_rate_at5": avg_rate_at5,
        **plat,
    }


def write_per_query_csv(outdir: Path, summary: Dict[str, Any]) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    qname = summary["query_name"]
    path = outdir / f"{qname}_per_generation.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "generation",
            "best_fitness",
            "mean_fitness",
            "median_fitness",
            "plateau_step",       # 1 if no significant change from previous generation, else 0
            "plateau_streak",     # consecutive count of plateau steps up to this generation
            "avg_conv_rate_alt_Rt", # optimum-free geometric average convergence rate up to gen t (windowed)
        ])
        for i, (b, m, md, ps, pst, rt) in enumerate(
            zip(
                summary["best_per_gen"],
                summary["mean_per_gen"],
                summary["median_per_gen"],
                summary["plateau_step"],
                summary["plateau_streak"],
                summary["avg_conv_rate_series"],
            ),
            start=1,
        ):
            w.writerow([i, b, m, md, ps, pst, rt])
    return path


def write_overview_csv(outpath: Path, summaries: List[Dict[str, Any]]) -> Path:
    outpath.parent.mkdir(parents=True, exist_ok=True)
    with outpath.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "query_name",
            "generations",
            "convergence_gen",
            "max_plateau_len",
            "max_plateau_end_gen",
            "final_plateau_len",
            "avg_conv_rate_at5",  # R_dd(t) at generation 5 (NaN if undefined)
        ])
        for s in summaries:
            w.writerow([
                s["query_name"],
                s["generations"],
                s["convergence_gen"],
                s["max_plateau_len"],
                s["max_plateau_end_gen"],
                s["final_plateau_len"],
                s.get("avg_conv_rate_at5", math.nan),
            ])
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


def plot_per_query(summary: Dict[str, Any], outdir: Path) -> Optional[Path]:
    """
    Plot per-query box plot of fitness distributions across generations.
    Each box shows the distribution of the population's fitness at that generation.
    """
    qname = summary["query_name"]
    fh = summary["fitness_history"]
    conv = summary["convergence_gen"]

    if not fh:
        return None

    # Trim empty tail gens if any
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
    ap.add_argument("--epsilon", type=float, default=0.005, help="Relative improvement threshold (e.g., 0.005 = 0.5%) for convergence rule")
    ap.add_argument("--patience", type=int, default=10, help="Consecutive generations below threshold to declare convergence")
    ap.add_argument("--plateau-epsilon", type=float, default=None, help="Relative change threshold for 'no significant change' plateau; defaults to --epsilon if not set")
    ap.add_argument("--tau", type=int, default=5, help="Window size (generations) for optimum-free convergence rate R_dd(t)")
    ap.add_argument("--write-csv", action="store_true", help="Write CSV files with per-generation stats and an overview")
    ap.add_argument("--boxplot-best-only", action="store_true",
                    help="Aggregate only best-per-query fitness per generation for the aggregated box plot")
    args = ap.parse_args()

    plateau_eps = args.plateau_epsilon if args.plateau_epsilon is not None else args.epsilon

    # Base output directory from json filename (no extension)
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

    summaries = [
        summarize_query(q, args.epsilon, args.patience, plateau_eps, args.tau)
        for q in run_queries
    ]

    # Print summary
    print(f"# Queries processed: {len(summaries)}")
    conv_gens = [s["convergence_gen"] for s in summaries if s["convergence_gen"]]
    if conv_gens:
        print(f"Mean convergence generation: {statistics.mean(conv_gens):.2f}")
        print(f"Median convergence generation: {statistics.median(conv_gens):.0f}")
    else:
        print("No convergence information available.")

    # Report average of R_dd(5) where available
    r5_values = [
        s.get("avg_conv_rate_at5")
        for s in summaries
        if s.get("avg_conv_rate_at5") is not None and not math.isnan(s.get("avg_conv_rate_at5"))
    ]
    if r5_values:
        print(f"Mean R_dd(5): {statistics.mean(r5_values):.4f}")
        print(f"Median R_dd(5): {statistics.median(r5_values):.4f}")
    else:
        print("R_dd(5) unavailable for all queries (need at least 10 generations when tau=5).")

    # CSV outputs
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
