import argparse
import os
from typing import Dict

from src.config import logger
from src.genetic_optimizer.gi_only import GIOnlyOptimizer
from src.utils.db_utils import actual_time
from src.utils.load_utils import extract_queries, load_query_file, load_schema

DATASET = "tpch"
DB_NAME = "tpch10"
POPULATION_SIZE = 50
MAX_GENERATIONS = 100
DB_TIMEOUT = 300  # seconds
VERBOSE = True


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Run GI Only genetic algorithm optimization on SQL queries",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--dataset", type=str, default=DATASET, help="Dataset name (directory containing queries and schema)"
    )

    parser.add_argument("--db-name", type=str, default=DB_NAME, help="Database name for connections")

    parser.add_argument(
        "--population-size", type=int, default=POPULATION_SIZE, help="Population size for genetic algorithm"
    )

    parser.add_argument(
        "--max-generations",
        type=int,
        default=MAX_GENERATIONS,
        help="Maximum number of generations for genetic algorithm",
    )

    parser.add_argument("--db-timeout", type=int, default=DB_TIMEOUT, help="Database query timeout in seconds")

    parser.add_argument("--verbose", action="store_true", default=VERBOSE, help="Enable verbose logging")

    parser.add_argument("--no-verbose", dest="verbose", action="store_false", help="Disable verbose logging")

    return parser.parse_args()


def process_query(query_name: str, query: str, schema: str, args) -> Dict:
    gi = GIOnlyOptimizer(
        query=query,
        db_name=args.db_name,
        schema=schema,
        db_timeout=args.db_timeout,
        population_size=args.population_size,
        max_generations=args.max_generations,
        verbose=args.verbose,
    )

    # original_cost = gi.db_connection.pgsql_actual_time(query)
    # original_cost = gi.db_connection.cost_estimation(query)
    pg_args = gi.db_connection.args
    original_cost, _ = actual_time(sql=query, db_args=pg_args, timeout=args.db_timeout)
    best_solution = gi.evolve()
    final_rewrite_result = gi.calcite_rewriter.rewrite(query=query, calcite_rules=best_solution.genes)
    # new_cost = gi.db_connection.pgsql_actual_time(final_rewrite_result.query)
    # new_cost = gi.db_connection.cost_estimation(final_rewrite_result.query)
    new_cost, _ = actual_time(sql=final_rewrite_result.query, db_args=pg_args, timeout=args.db_timeout)
    improved = new_cost < original_cost
    improvement_factor = original_cost / new_cost if new_cost > 0 else float("inf")
    improvement_percent = ((original_cost - new_cost) / original_cost * 100) if original_cost > 0 else 0
    best_solution_rules = [gene.name for gene in best_solution.genes]

    logger.info(f"Query: {query_name}")
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
    args = parse_args()

    # Log the configuration
    logger.info("Configuration:")
    logger.info(f"  Dataset: {args.dataset}")
    logger.info(f"  DB Name: {args.db_name}")
    logger.info(f"  Population Size: {args.population_size}")
    logger.info(f"  Max Generations: {args.max_generations}")
    logger.info(f"  DB Timeout: {args.db_timeout}s")
    logger.info(f"  Verbose: {args.verbose}")
    logger.info("=" * 40)

    schema_path = os.path.join(args.dataset, "create_tables.sql")
    schema = load_schema(schema_path)

    queries_dir = os.path.join(args.dataset)
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
                logger.info(f"Processing query: {name}")
                logger.debug(f"Query content:\n{query}\n")
                result = process_query(name, query, schema, args)
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
