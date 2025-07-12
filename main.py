import os
import re
from typing import List, Dict


from src.genetic_optimizer.gi_only import GIOnlyApproach

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
    gi = GIOnlyApproach(
        query=query, db_name=DB_NAME, schema=schema, population_size=POPULATION_SIZE, max_generations=MAX_GENERATIONS
    )

    original_cost = gi.db_connection.cost_estimation(query)
    best_solution = gi.evolve()
    improved = best_solution.fitness < original_cost
    improvement_percent = ((original_cost - best_solution.fitness) / original_cost * 100) if original_cost > 0 else 0

    print("--" * 20)
    print(f"Query: {query_name}")
    print(f"Original cost: {original_cost}")
    print(f"Improved cost: {best_solution.fitness:.2f}")
    print(f"Improved: {improved}")
    print(f"Improvement (%): {improvement_percent:.2f}")
    print("--" * 20)

    return {
        "query_name": query_name,
        "original_cost": original_cost,
        "improved_cost": best_solution.fitness,
        "improved": improved,
        "improvement_percent": improvement_percent,
    }


def main():
    schema_path = os.path.join(DATASET, "create_tables.sql")
    schema = load_schema(schema_path) if os.path.exists(schema_path) else "DUMMY_SCHEMA"

    queries_dir = os.path.join(DATASET)
    templates = [t for t in os.listdir(queries_dir) if os.path.isdir(os.path.join(queries_dir, t))]
    print("Available query templates:", templates)

    stats = []

    for template in templates:
        print(f"Processing template: {template}")
        for idx in range(2):
            file_path = os.path.join(queries_dir, template, f"{template}_{idx}.sql")
            if not os.path.exists(file_path):
                continue

            print("--" * 20)
            print(f"Processing query {idx} for template {template}")

            sql_content = load_query_file(file_path)
            queries = extract_queries(sql_content)

            for j, query in enumerate(queries):
                name = f"{template}_{idx}_{j}" if idx > 0 else f"{template}_{idx}"
                result = process_query(name, query, schema)
                stats.append(result)

    total = len(stats)
    improved = sum(1 for s in stats if s["improved"])
    mean_improvement = sum(s["improvement_percent"] for s in stats) / total if total > 0 else 0

    print("\n" + "=" * 40)
    print(f"Total queries processed: {total}")
    print(f"Queries with improved cost: {improved}")
    print(f"Improvement ratio: {(improved / total * 100):.2f}%")
    print(f"Mean improvement across all queries: {mean_improvement:.2f}%")
    print("=" * 40)


if __name__ == "__main__":
    main()
