import os
from typing import Dict

from src.config import logger
from src.genetic_optimizer.gi_llm_rule_based import GILLMRuleBasedOptimizer
from src.utils.db_utils import actual_time
from src.utils.load_utils import extract_queries, load_query_file, load_schema

DATASET = "tpch"
DB_NAME = "tpch10"
POPULATION_SIZE = 20
MAX_GENERATIONS = 10
DB_TIMEOUT = 300  # seconds
VERBOSE = True


def process_query(query_name: str, query: str, schema: str) -> Dict:
    gi_llm = GILLMRuleBasedOptimizer(
        query=query,
        db_name=DB_NAME,
        schema=schema,
        population_size=POPULATION_SIZE,
        max_generations=MAX_GENERATIONS,
        verbose=VERBOSE,
    )

    pg_args = gi_llm.db_connection.args
    original_cost, _ = actual_time(sql=query, db_args=pg_args, timeout=DB_TIMEOUT)
    best_solution = gi_llm.evolve()
    final_rewrite_result = gi_llm.calcite_rewriter.rewrite(query=query, calcite_rules=best_solution.genes)
    new_cost, _ = actual_time(sql=final_rewrite_result.query, db_args=pg_args, timeout=DB_TIMEOUT)
    improved = new_cost < original_cost
    improvement_factor = original_cost / new_cost if new_cost > 0 else float("inf")
    improvement_percent = ((original_cost - new_cost) / original_cost * 100) if original_cost > 0 else 0
    best_solution_rules = [gene.name for gene in best_solution.genes]

    logger.info(f"Query: {query_name}")
    logger.info(f"Query content:\n{query}\n")
    logger.info(f"Original cost: {original_cost}")
    logger.info(f"Improved cost: {new_cost:.2f}")
    logger.info(f"Improved: {improved}")
    logger.info(f"Improvement factor: {improvement_factor:.2f}")
    logger.info(f"Improvement (%): {improvement_percent:.2f}")
    logger.info(f"Best solution rules: {best_solution_rules}")
    logger.info(f"Final rewrite query: {final_rewrite_result.query}")

    return {
        "query_name": query_name,
        "original_cost": original_cost,
        "improved_cost": new_cost,
        "improved": improved,
        "improvement_factor": improvement_factor,
        "improvement_percent": improvement_percent,
        "best_solution_rules": best_solution_rules,
        "final_rewrite_query": final_rewrite_result.query,
    }


def main():
    schema_path = os.path.join(DATASET, "create_tables.sql")
    schema = load_schema(schema_path)

    queries_dir = os.path.join(DATASET)
    templates = [t for t in os.listdir(queries_dir) if os.path.isdir(os.path.join(queries_dir, t))]
    logger.info(f"Available query templates: {templates}")

    stats = []

    for template in templates:
        logger.info(f"Processing template: {template}")
        for idx in range(2):
            file_path = os.path.join(queries_dir, template, f"{template}_{idx}.sql")
            if not os.path.exists(file_path):
                continue

            logger.info(f"Processing query {idx} for template {template}")

            sql_content = load_query_file(file_path)
            queries = extract_queries(sql_content)

            for j, query in enumerate(queries):
                name = f"{template}_{idx}_{j}" if idx > 0 else f"{template}_{idx}"
                result = process_query(name, query, schema)
                stats.append(result)
    total = len(stats)
    improved = sum(1 for s in stats if s["improved"])
    improvement_factors = [s["improvement_factor"] for s in stats]
    improvement_percentages = [s["improvement_percent"] for s in stats]
    mean_improvement_factor = sum(improvement_factors) / total if total > 0 else 0
    mean_improvement_percent = sum(improvement_percentages) / total if total > 0 else 0
    max_improvement_factor, min_improvement_factor = max(improvement_factors), min(improvement_factors)
    max_improvement_percent, min_improvement_percent = max(improvement_percentages), min(improvement_percentages)

    logger.info("=" * 40)
    logger.info(f"Total queries processed: {total}")
    logger.info(f"Queries with improved cost: {improved}")
    logger.info(f"Improvement ratio: {(improved / total * 100):.2f}%")
    logger.info(f"Mean improvement factor across all queries: {mean_improvement_factor:.2f}")
    logger.info(f"Mean improvement percentage across all queries: {mean_improvement_percent:.2f}%")
    logger.info(f"Max improvement factor: {max_improvement_factor:.2f}")
    logger.info(f"Min improvement factor: {min_improvement_factor:.2f}")
    logger.info(f"Max improvement percentage: {max_improvement_percent:.2f}")
    logger.info(f"Min improvement percentage: {min_improvement_percent:.2f}")
    logger.info("=" * 40)


if __name__ == "__main__":
    main()
