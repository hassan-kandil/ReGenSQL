# Evaluate the performance of ReGenSQL
# This script reads queries from a file, processes them using ReGenSQL, and evaluates the results.

import argparse
import os
import statistics

from src.config import init_db_config, logger
from src.database import DBArgs
from src.utils.eval_utils import evaluate_query_performance
from src.utils.json_utils import read_json, write_json


def evaluate_queries(queries_data: list[dict], pg_args: DBArgs, timeout: int) -> list[dict]:
    for query_data in queries_data:
        query_name = query_data["query_name"]
        original_query = query_data["original_query"]
        rewritten_query = query_data["rewritten_query"]

        logger.info(f"Evaluating query: {query_name}")
        performance_stats = evaluate_query_performance(pg_args, timeout, original_query, rewritten_query)

        # Update the result with performance stats
        query_data.update(performance_stats)


def collect_evaluation_statistics(queries_results: list[dict]) -> dict:
    original_exec_times = [result["original_exec_time"] for result in queries_results]
    rewritten_exec_times = [result["rewritten_exec_time"] for result in queries_results]
    final_exec_times = [result["final_exec_time"] for result in queries_results]
    total_original_time, total_rewritten_time, total_final_time = (
        sum(original_exec_times),
        sum(rewritten_exec_times),
        sum(final_exec_times),
    )
    mean_original_time, mean_rewritten_time, mean_final_time = (
        statistics.mean(original_exec_times),
        statistics.mean(rewritten_exec_times),
        statistics.mean(final_exec_times),
    )
    mean_time_improvement_percent = (mean_original_time - mean_final_time) / mean_original_time * 100
    median_original_time, median_rewritten_time, median_final_time = (
        statistics.median(original_exec_times),
        statistics.median(rewritten_exec_times),
        statistics.median(final_exec_times),
    )
    median_time_improvement_percent = (median_original_time - median_final_time) / median_original_time * 100
    min_original_time, min_rewritten_time, min_final_time = (
        min(original_exec_times),
        min(rewritten_exec_times),
        min(final_exec_times),
    )
    max_original_time, max_rewritten_time, max_final_time = (
        max(original_exec_times),
        max(rewritten_exec_times),
        max(final_exec_times),
    )

    original_75th_percentile = rewritten_75th_percentile = final_75th_percentile = None
    seventy_fifth_percentile_improvement_percent = None
    if len(original_exec_times) >= 4:
        # original_75th_percentile = statistics.quantiles(original_exec_times, n=4)[2]
        # rewritten_75th_percentile = statistics.quantiles(rewritten_exec_times, n=4)[2]
        # final_75th_percentile = statistics.quantiles(final_exec_times, n=4)[2]
        # seventy_fifth_percentile_improvement_percent = (
        #     (original_75th_percentile - final_75th_percentile) / original_75th_percentile * 100
        # )
        original_75th_percentile = sorted(original_exec_times)[int(0.75 * len(original_exec_times))]
        rewritten_75th_percentile = sorted(rewritten_exec_times)[int(0.75 * len(rewritten_exec_times))]
        final_75th_percentile = sorted(final_exec_times)[int(0.75 * len(final_exec_times))]
        seventy_fifth_percentile_improvement_percent = (
            ((original_75th_percentile - final_75th_percentile) / original_75th_percentile) * 100
        )

    original_90th_percentile = rewritten_90th_percentile = final_90th_percentile = None
    ninety_percentile_improvement_percent = None
    if len(original_exec_times) >= 10:
        original_90th_percentile = statistics.quantiles(original_exec_times, n=10)[8]
        rewritten_90th_percentile = statistics.quantiles(rewritten_exec_times, n=10)[8]
        final_90th_percentile = statistics.quantiles(final_exec_times, n=10)[8]
        ninety_percentile_improvement_percent = (
            (original_90th_percentile - final_90th_percentile) / original_90th_percentile * 100
        )

    original_95th_percentile = rewritten_95th_percentile = final_95th_percentile = None
    ninety_fifth_percentile_improvement_percent = None
    if len(original_exec_times) >= 20:
        original_95th_percentile = statistics.quantiles(original_exec_times, n=20)[18]
        rewritten_95th_percentile = statistics.quantiles(rewritten_exec_times, n=20)[18]
        final_95th_percentile = statistics.quantiles(final_exec_times, n=20)[18]
        ninety_fifth_percentile_improvement_percent = (
            (original_95th_percentile - final_95th_percentile) / original_95th_percentile * 100
        )

    improved_count = sum(1 for result in queries_results if result["is_improved"])
    statistically_significant_improved_count = sum(
        1 for result in queries_results if result["is_improved_statistically_significant"]
    )
    improvement_factors = [result["improvement_factor"] for result in queries_results]
    improvement_percentages = [result["improvement_percent"] for result in queries_results]
    mean_improvement_factor, mean_improvement_percent = statistics.mean(improvement_factors), statistics.mean(
        improvement_percentages
    )
    median_improvement_factor, median_improvement_percent = statistics.median(improvement_factors), statistics.median(
        improvement_percentages
    )
    max_improvement_factor, max_improvement_percent = max(improvement_factors), max(improvement_percentages)
    min_improvement_factor, min_improvement_percent = min(improvement_factors), min(improvement_percentages)

    logger.info(f"Total original execution time: {total_original_time}")
    logger.info(f"Total rewritten execution time: {total_rewritten_time}")
    logger.info(f"Total final execution time: {total_final_time}")
    logger.info(f"Mean original execution time: {mean_original_time}")
    logger.info(f"Mean rewritten execution time: {mean_rewritten_time}")
    logger.info(f"Mean final execution time: {mean_final_time}")
    logger.info(f"Mean time improvement percent: {mean_time_improvement_percent:.2f}%")
    logger.info(f"Median original execution time: {median_original_time}")
    logger.info(f"Median rewritten execution time: {median_rewritten_time}")
    logger.info(f"Median final execution time: {median_final_time}")
    logger.info(f"Median time improvement percent: {median_time_improvement_percent:.2f}%")
    logger.info(f"Min original execution time: {min_original_time}")
    logger.info(f"Min rewritten execution time: {min_rewritten_time}")
    logger.info(f"Min final execution time: {min_final_time}")
    logger.info(f"Max original execution time: {max_original_time}")
    logger.info(f"Max rewritten execution time: {max_rewritten_time}")
    logger.info(f"Max final execution time: {max_final_time}")
    logger.info(f"Original 75th percentile: {original_75th_percentile}")
    logger.info(f"Rewritten 75th percentile: {rewritten_75th_percentile}")
    logger.info(f"Final 75th percentile: {final_75th_percentile}")
    logger.info(f"75th percentile improvement percent: {seventy_fifth_percentile_improvement_percent:.2f}%")
    logger.info(f"Original 90th percentile: {original_90th_percentile}")
    logger.info(f"Rewritten 90th percentile: {rewritten_90th_percentile}")
    logger.info(f"Final 90th percentile: {final_90th_percentile}")
    logger.info(f"90th percentile improvement percent: {ninety_percentile_improvement_percent:.2f}%")
    logger.info(f"Original 95th percentile: {original_95th_percentile}")
    logger.info(f"Rewritten 95th percentile: {rewritten_95th_percentile}")
    logger.info(f"Final 95th percentile: {final_95th_percentile}")
    logger.info(f"95th percentile improvement percent: {ninety_fifth_percentile_improvement_percent:.2f}%")
    logger.info(f"Improved count: {improved_count}")
    logger.info(f"Statistically significant improved count: {statistically_significant_improved_count}")
    logger.info(f"Mean improvement factor: {mean_improvement_factor}")
    logger.info(f"Mean improvement percent: {mean_improvement_percent:.2f}%")
    logger.info(f"Median improvement factor: {median_improvement_factor}")
    logger.info(f"Median improvement percent: {median_improvement_percent:.2f}%")
    logger.info(f"Max improvement factor: {max_improvement_factor}")
    logger.info(f"Min improvement factor: {min_improvement_factor}")
    logger.info(f"Max improvement percent: {max_improvement_percent:.2f}%")
    logger.info(f"Min improvement percent: {min_improvement_percent:.2f}%")

    return {
        "total_original_time": total_original_time,
        "total_rewritten_time": total_rewritten_time,
        "total_final_time": total_final_time,
        "mean_original_time": mean_original_time,
        "mean_rewritten_time": mean_rewritten_time,
        "mean_final_time": mean_final_time,
        "mean_time_improvement_percent": mean_time_improvement_percent,
        "median_original_time": median_original_time,
        "median_rewritten_time": median_rewritten_time,
        "median_final_time": median_final_time,
        "median_time_improvement_percent": median_time_improvement_percent,
        "min_original_time": min_original_time,
        "min_rewritten_time": min_rewritten_time,
        "min_final_time": min_final_time,
        "max_original_time": max_original_time,
        "max_rewritten_time": max_rewritten_time,
        "max_final_time": max_final_time,
        "original_75th_percentile": original_75th_percentile,
        "rewritten_75th_percentile": rewritten_75th_percentile,
        "final_75th_percentile": final_75th_percentile,
        "75th_percentile_improvement_percent": seventy_fifth_percentile_improvement_percent,
        "original_90th_percentile": original_90th_percentile,
        "rewritten_90th_percentile": rewritten_90th_percentile,
        "final_90th_percentile": final_90th_percentile,
        "90th_percentile_improvement_percent": ninety_percentile_improvement_percent,
        "original_95th_percentile": original_95th_percentile,
        "rewritten_95th_percentile": rewritten_95th_percentile,
        "final_95th_percentile": final_95th_percentile,
        "95th_percentile_improvement_percent": ninety_fifth_percentile_improvement_percent,
        "improved_count": improved_count,
        "statistically_significant_improved_count": statistically_significant_improved_count,
        "mean_improvement_factor": mean_improvement_factor,
        "mean_improvement_percent": mean_improvement_percent,
        "median_improvement_factor": median_improvement_factor,
        "median_improvement_percent": median_improvement_percent,
        "max_improvement_factor": max_improvement_factor,
        "min_improvement_factor": min_improvement_factor,
        "max_improvement_percent": max_improvement_percent,
        "min_improvement_percent": min_improvement_percent,
    }


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Evaluate the performance of ReGenSQL by analyzing query execution times",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("output_file", type=str, help="Path to the ReGenSQL output JSON file to evaluate")

    return parser.parse_args()


def main():
    args = parse_args()
    output_path = args.output_file

    # Check if the file exists
    if not os.path.exists(output_path):
        logger.error(f"Output file not found: {output_path}")
        return

    logger.info(f"Processing output file: {output_path}")
    output_data = read_json(output_path)
    run_configuration = output_data["run_configuration"]
    pg_args = DBArgs(init_db_config(run_configuration["database"]))
    timeout = run_configuration["db_timeout"]

    evaluate_queries(output_data["run_queries"], pg_args, timeout)
    evaluation_stats = collect_evaluation_statistics(output_data["run_queries"])
    output_data["run_statistics"].update(evaluation_stats)

    # Write the updated output data back to the file
    write_json(output_data, output_path)

    logger.info(f"Evaluation results written to {output_path}")


if __name__ == "__main__":
    main()
