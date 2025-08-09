# Evaluate the performance of ReGenSQL
# This script reads queries from a file, processes them using ReGenSQL, and evaluates the results.

import os
import statistics
from src.database import DBArgs
from src.utils.db_utils import actual_time
from src.config import init_db_config, logger
from src.utils.json_utils import read_json, write_json

def evaluate_query_performance(pg_args: DBArgs, timeout: int, original_query: str, rewritten_query: str) -> dict:
    original_exec_time, _ = actual_time(sql=original_query, db_args=pg_args, timeout=timeout)
    rewritten_exec_time, _ = actual_time(sql=rewritten_query, db_args=pg_args, timeout=timeout)
    time_difference = original_exec_time - rewritten_exec_time
    is_improved = rewritten_exec_time < original_exec_time
    improvement_factor = rewritten_exec_time / original_exec_time if original_exec_time > 0 else float("inf") 
    improvement_percent = ((original_exec_time - rewritten_exec_time) / original_exec_time * 100) if original_exec_time > 0 else 0

    logger.info(f"Original execution time: {original_exec_time}")
    logger.info(f"Rewritten execution time: {rewritten_exec_time}")
    logger.info(f"Time difference: {time_difference}")
    logger.info(f"Improved: {is_improved}")
    logger.info(f"Improvement factor: {improvement_factor:.2f}")
    logger.info(f"Improvement (%): {improvement_percent:.2f}")

    return {
        "original_exec_time": original_exec_time,
        "rewritten_exec_time": rewritten_exec_time,
        "time_difference": time_difference,
        "is_improved": is_improved,
        "improvement_factor": improvement_factor,
        "improvement_percent": improvement_percent,
    }

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
    total_original_time = sum(original_exec_times)
    total_rewritten_time = sum(rewritten_exec_times)
    mean_original_time = statistics.mean(original_exec_times)
    mean_rewritten_time = statistics.mean(rewritten_exec_times)
    mean_time_improvement_percent = ((total_original_time - total_rewritten_time) / total_original_time * 100)
    median_original_time = statistics.median(original_exec_times)
    median_rewritten_time = statistics.median(rewritten_exec_times)
    median_time_improvement_percent = ((median_original_time - median_rewritten_time) / median_original_time * 100)
    min_original_time = min(original_exec_times)
    min_rewritten_time = min(rewritten_exec_times)
    max_original_time = max(original_exec_times)
    max_rewritten_time = max(rewritten_exec_times)

    original_75th_percentile = None
    rewritten_75th_percentile = None
    seventy_fifth_percentile_improvement_percent = None
    if len(original_exec_times) >= 4:
        original_75th_percentile = statistics.quantiles(original_exec_times, n=4)[2]
        rewritten_75th_percentile = statistics.quantiles(rewritten_exec_times, n=4)[2]
        seventy_fifth_percentile_improvement_percent = ((original_75th_percentile - rewritten_75th_percentile) / original_75th_percentile * 100)
    
    original_95th_percentile = None
    rewritten_95th_percentile = None
    ninety_fifth_percentile_improvement_percent = None
    if len(original_exec_times) >= 20:
        original_95th_percentile = statistics.quantiles(original_exec_times, n=20)[18]
        rewritten_95th_percentile = statistics.quantiles(rewritten_exec_times, n=20)[18]
        ninety_fifth_percentile_improvement_percent = ((original_95th_percentile - rewritten_95th_percentile) / original_95th_percentile * 100)

    improved_count = sum(1 for result in queries_results if result["is_improved"])
    improvent_factors = [result["improvement_factor"] for result in queries_results]
    improvement_percentages = [result["improvement_percent"] for result in queries_results]
    mean_improvement_factor = statistics.mean(improvent_factors)
    mean_improvement_percent = statistics.mean(improvement_percentages)
    median_improvement_factor = statistics.median(improvent_factors)
    median_improvement_percent = statistics.median(improvement_percentages)
    max_improvement_factor = max(improvent_factors)
    min_improvement_factor = min(improvent_factors)
    max_improvement_percent = max(improvement_percentages)
    min_improvement_percent = min(improvement_percentages)

    logger.info(f"Total original execution time: {total_original_time}")
    logger.info(f"Total rewritten execution time: {total_rewritten_time}")
    logger.info(f"Mean original execution time: {mean_original_time}")
    logger.info(f"Mean rewritten execution time: {mean_rewritten_time}")
    logger.info(f"Mean time improvement percent: {mean_time_improvement_percent:.2f}%")
    logger.info(f"Median original execution time: {median_original_time}")
    logger.info(f"Median rewritten execution time: {median_rewritten_time}")
    logger.info(f"Median time improvement percent: {median_time_improvement_percent:.2f}%")
    logger.info(f"Min original execution time: {min_original_time}")
    logger.info(f"Min rewritten execution time: {min_rewritten_time}")
    logger.info(f"Max original execution time: {max_original_time}")
    logger.info(f"Max rewritten execution time: {max_rewritten_time}")  
    logger.info(f"Original 75th percentile: {original_75th_percentile}")
    logger.info(f"Rewritten 75th percentile: {rewritten_75th_percentile}")
    logger.info(f"75th percentile improvement percent: {seventy_fifth_percentile_improvement_percent:.2f}%")
    logger.info(f"Original 95th percentile: {original_95th_percentile}")
    logger.info(f"Rewritten 95th percentile: {rewritten_95th_percentile}")
    logger.info(f"95th percentile improvement percent: {ninety_fifth_percentile_improvement_percent:.2f}%")
    logger.info(f"Improved count: {improved_count}")
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
        "mean_original_time": mean_original_time,
        "mean_rewritten_time": mean_rewritten_time,
        "mean_time_improvement_percent": mean_time_improvement_percent,
        "median_original_time": median_original_time,
        "median_rewritten_time": median_rewritten_time,
        "median_time_improvement_percent": median_time_improvement_percent,
        "min_original_time": min_original_time,
        "min_rewritten_time": min_rewritten_time,
        "max_original_time": max_original_time,
        "max_rewritten_time": max_rewritten_time,
        "original_75th_percentile": original_75th_percentile,
        "rewritten_75th_percentile": rewritten_75th_percentile,
        "75th_percentile_improvement_percent": seventy_fifth_percentile_improvement_percent,
        "original_95th_percentile": original_95th_percentile,
        "rewritten_95th_percentile": rewritten_95th_percentile,
        "95th_percentile_improvement_percent": ninety_fifth_percentile_improvement_percent,
        "improved_count": improved_count,
        "mean_improvement_factor": mean_improvement_factor,
        "mean_improvement_percent": mean_improvement_percent,
        "median_improvement_factor": median_improvement_factor,
        "median_improvement_percent": median_improvement_percent,
        "max_improvement_factor": max_improvement_factor,
        "min_improvement_factor": min_improvement_factor,
        "max_improvement_percent": max_improvement_percent,
        "min_improvement_percent": min_improvement_percent,
    }


def main():
    output_dir = "output/"

    # for output_file in os.listdir(output_dir):
    #     if not output_file.endswith(".json"):
    #         continue
    output_file = "regensql_results_GIOnly_20250805_142616.json"
    logger.info(f"Processing output file: {output_file}")
    output_path = os.path.join(output_dir, output_file)
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

