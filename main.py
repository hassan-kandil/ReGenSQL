import os
import re
from typing import List, Dict
from src.genetic_optimizer.gi_only import GIOnlyOptimizer
from src.config import logger

DATASET = "tpch"
DB_NAME = "tpch10"
POPULATION_SIZE = 20
MAX_GENERATIONS = 100


def load_schema(schema_file: str) -> str:
    with open(schema_file, "r") as f:
        return f.read()


def load_query_file(path: str) -> str:
    with open(path, "r") as f:
        content = f.read()
    return re.sub(r"--.*\n", "", content)


def extract_queries(sql: str) -> List[str]:
    return [q.strip() + ";" for q in sql.split(";") if q.strip()]


def process_query(query_name: str, query: str, schema: str) -> Dict:
    gi = GIOnlyOptimizer(
        query=query,
        db_name=DB_NAME,
        schema=schema,
        population_size=POPULATION_SIZE,
        max_generations=MAX_GENERATIONS,
        verbose=True,
    )

    original_cost = gi.db_connection.pgsql_actual_time(query)
    best_solution = gi.evolve()
    final_rewrite_result = gi.calcite_rewriter.rewrite(query=query, calcite_rules=best_solution.genes)
    new_cost = gi.db_connection.pgsql_actual_time(final_rewrite_result.query)
    improved = new_cost < original_cost
    improvement_factor = original_cost / new_cost if new_cost > 0 else float("inf")
    improvement_percent = ((original_cost - new_cost) / original_cost * 100) if original_cost > 0 else 0

    logger.info(f"Query: {query_name}")
    logger.info(f"Original cost: {original_cost}")
    logger.info(f"Improved cost: {new_cost:.2f}")
    logger.info(f"Improved: {improved}")
    logger.info(f"Improvement factor: {improvement_factor:.2f}")
    logger.info(f"Improvement (%): {improvement_percent:.2f}")

    return {
        "query_name": query_name,
        "original_cost": original_cost,
        "improved_cost": new_cost,
        "improved": improved,
        "improvement_factor": improvement_factor,
        "improvement_percent": improvement_percent,
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
    mean_improvement_factor = sum(s["improvement_factor"] for s in stats) / total if total > 0 else 0
    mean_improvement_percent = sum(s["improvement_percent"] for s in stats) / total if total > 0 else 0

    logger.info("=" * 40)
    logger.info(f"Total queries processed: {total}")
    logger.info(f"Queries with improved cost: {improved}")
    logger.info(f"Improvement ratio: {(improved / total * 100):.2f}%")
    logger.info(f"Mean improvement factor across all queries: {mean_improvement_factor:.2f}")
    logger.info(f"Mean improvement percentage across all queries: {mean_improvement_percent:.2f}%")
    logger.info("=" * 40)


if __name__ == "__main__":
    main()
