from scipy import stats
from src.config import logger
from src.database import DBArgs
from src.utils.db_utils import actual_time


def is_execution_time_difference_significant(
    original_times: list[float], rewritten_times: list[float], alternative: str = "greater", threshold: float = 0.05
) -> bool:
    """
    Check if the difference in execution times is statistically significant.

    Args:
        original_times (list[float]): List of execution times for the original query.
        rewritten_times (list[float]): List of execution times for the rewritten query.
        alternative (str): The alternative hypothesis ('greater', 'less', or 'two-sided').
        threshold (float): Significance level for the test.

    Returns:
        bool: True if the difference is statistically significant, False otherwise.
    """
    _, p_value = stats.ttest_ind(original_times, rewritten_times, alternative=alternative)
    return bool(p_value < threshold)


def check_is_query_improved(input_cost: float, output_cost: float) -> bool:
    """
    Check if the rewritten query is an improvement over the original query.

    Args:
        input_cost (float): The cost of the original query.
        output_cost (float): The cost of the rewritten query.

    Returns:
        bool: True if the rewritten query is an improvement, False otherwise.
    """
    return output_cost != float("inf") and output_cost < input_cost


def evaluate_query_performance(pg_args: DBArgs, timeout: int, original_query: str, rewritten_query: str) -> dict:
    original_exec_time, original_exec_times = actual_time(sql=original_query, db_args=pg_args, timeout=timeout)
    rewritten_exec_time, rewritten_exec_times = actual_time(sql=rewritten_query, db_args=pg_args, timeout=timeout)
    is_improved = check_is_query_improved(original_exec_time, rewritten_exec_time)
    is_improved_statistically_significant = is_execution_time_difference_significant(
        original_exec_times, rewritten_exec_times
    )
    if not is_improved:
        logger.info(
            f"Rewritten query is not an improvement over the original query: {original_exec_time} vs {rewritten_exec_time}, keeping original execution time."
        )
        final_exec_time = original_exec_time
    else:
        logger.info(
            f"Rewritten query is an improvement over the original query: {original_exec_time} vs {rewritten_exec_time}, using rewritten execution time."
        )
        final_exec_time = rewritten_exec_time
    time_difference = original_exec_time - final_exec_time
    improvement_factor = final_exec_time / original_exec_time if original_exec_time > 0 else float("inf")
    improvement_percent = (
        ((original_exec_time - final_exec_time) / original_exec_time * 100) if original_exec_time > 0 else 0
    )

    logger.info(f"Original execution time: {original_exec_time}")
    logger.info(f"Rewritten execution time: {rewritten_exec_time}")
    logger.info(f"Final execution time: {final_exec_time}")
    logger.info(f"Time difference: {time_difference}")
    logger.info(f"Improved: {is_improved}")
    logger.info(f"Statistically significant improved: {is_improved_statistically_significant}")
    logger.info(f"Improvement factor: {improvement_factor:.2f}")
    logger.info(f"Improvement (%): {improvement_percent:.2f}")

    return {
        "original_exec_time": original_exec_time,
        "rewritten_exec_time": rewritten_exec_time,
        "final_exec_time": final_exec_time,
        "time_difference": time_difference,
        "is_improved": bool(is_improved),
        "is_improved_statistically_significant": bool(is_improved_statistically_significant),
        "improvement_factor": improvement_factor,
        "improvement_percent": improvement_percent,
    }