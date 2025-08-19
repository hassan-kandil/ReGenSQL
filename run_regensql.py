import argparse
import json
import os
import statistics
import time
from datetime import datetime
from typing import Dict

from src.config import init_llms, logger
from src.genetic_optimizer.gi_llm_rule_based import GILLMRuleBasedOptimizer
from src.genetic_optimizer.gi_only import GIOnlyOptimizer
from src.rbot_rewriter.model import RBotModel
from src.utils.load_utils import extract_queries, load_query_file, load_schema
from src.utils.plotting_utils import plot_fitness_boxplot, plot_fitness_summary_stats

DATASET = "tpch"
DB_NAME = "tpch10"
POPULATION_SIZE = 100
MAX_GENERATIONS = 20
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.8
DB_TIMEOUT = 300  # seconds
VERBOSE = True
PARTIAL_RUN = False
DEFAULT_IS_LLM_OPEN = True  # Use OpenAILike by default
DEFAULT_LLM_MODEL_NAME = "llama3:8b"


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Run GI Only genetic algorithm optimization on SQL queries",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--dataset", type=str, default=DATASET, help="Dataset name (directory containing queries and schema)"
    )

    parser.add_argument("--partial-run", action="store_true", default=PARTIAL_RUN, help="Run only a subset of queries")

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

    parser.add_argument(
        "--mutation-rate", type=float, default=MUTATION_RATE, help="Mutation rate for genetic algorithm"
    )

    parser.add_argument(
        "--crossover-rate", type=float, default=CROSSOVER_RATE, help="Crossover rate for genetic algorithm"
    )

    parser.add_argument("--db-timeout", type=int, default=DB_TIMEOUT, help="Database query timeout in seconds")

    parser.add_argument("--llm-enabled", action="store_true", default=False, help="Enable LLM for query optimization")

    parser.add_argument("--verbose", action="store_true", default=VERBOSE, help="Enable verbose logging")

    parser.add_argument("--no-verbose", dest="verbose", action="store_false", help="Disable verbose logging")

    parser.add_argument(
        "--plot-fitness", action="store_true", default=False, help="Generate fitness plots for each query"
    )

    parser.add_argument(
        "--use-actual-time-fitness",
        action="store_true",
        default=False,
        help="Use actual execution time for fitness evaluation instead of estimated cost",
    )

    parser.add_argument(
        "--is-llm-open",
        action="store_true",
        default=DEFAULT_IS_LLM_OPEN,
        help="Use OpenAILike for LLM model instead of OpenAI",
    )

    parser.add_argument("--llm-name", type=str, default=DEFAULT_LLM_MODEL_NAME, help="LLM model name to use")

    return parser.parse_args()


def process_query(
    query_name: str, query: str, schema: str, args: argparse.Namespace, rbot_model: RBotModel = None
) -> Dict:
    """Process a single SQL query using the GI optimizer"""
    start_time = time.time()

    # Common optimizer parameters
    optimizer_params = {
        "query": query,
        "db_name": args.db_name,
        "schema": schema,
        "db_timeout": args.db_timeout,
        "population_size": args.population_size,
        "max_generations": args.max_generations,
        "mutation_rate": args.mutation_rate,
        "crossover_rate": args.crossover_rate,
        "verbose": args.verbose,
        "use_estimated_cost_fitness": not args.use_actual_time_fitness,
    }

    # Choose optimizer based on LLM flag
    if args.llm_enabled:
        gi_optimizer = GILLMRuleBasedOptimizer(**optimizer_params, rbot_model=rbot_model)
    else:
        gi_optimizer = GIOnlyOptimizer(**optimizer_params)

    best_solution = gi_optimizer.evolve()
    final_rewrite_result = gi_optimizer.calcite_rewriter.rewrite(query=query, calcite_rules=best_solution.genes)
    applied_rules = [gene.name for gene in best_solution.genes]

    end_time = time.time()
    processing_time = end_time - start_time

    logger.info(f"Query name: {query_name}")
    logger.info(f"Original query:\n{query}\n")
    logger.info(f"Rewritten query:\n{final_rewrite_result.query}\n")
    logger.info(f"Applied rules: {applied_rules}")
    logger.info(f"Processing time: {processing_time:.2f} seconds")

    # Generate fitness plots if requested
    if args.plot_fitness and gi_optimizer.fitness_history:
        output_plots_dir = os.path.join("output", "plots")
        try:
            plot_fitness_boxplot(gi_optimizer.fitness_history, output_plots_dir, query_name)
            plot_fitness_summary_stats(gi_optimizer.fitness_history, output_plots_dir, query_name)
        except Exception as e:
            logger.warning(f"Error generating plots for {query_name}: {e}")
            raise

    return {
        "query_name": query_name,
        "original_query": query,
        "rewritten_query": final_rewrite_result.query,
        "applied_rules": applied_rules,
        "processing_time_seconds": processing_time,
        "fitness_history": gi_optimizer.fitness_history if hasattr(gi_optimizer, "fitness_history") else [],
    }


def collect_statistics(stats: Dict, total_run_time: float) -> Dict:
    if not stats:
        return {
            "total_queries": 0,
            "mean_processing_time_seconds": 0,
            "median_processing_time_seconds": 0,
            "min_processing_time_seconds": 0,
            "max_processing_time_seconds": 0,
            "total_processing_time_seconds": 0,
            "total_run_time_seconds": total_run_time,
        }
    # Calculate statistics
    processing_times = [stat["processing_time_seconds"] for stat in stats]

    run_statistics = {
        "total_queries": len(stats),
        "mean_processing_time_seconds": statistics.mean(processing_times),
        "median_processing_time_seconds": statistics.median(processing_times),
        "min_processing_time_seconds": min(processing_times),
        "max_processing_time_seconds": max(processing_times),
        "total_processing_time_seconds": sum(processing_times),
        "total_run_time_seconds": total_run_time,
    }

    # Add percentiles if we have enough data
    if len(processing_times) >= 4:
        run_statistics["75th_percentile_processing_time_seconds"] = statistics.quantiles(processing_times, n=4)[2]

    if len(processing_times) >= 20:
        run_statistics["95th_percentile_processing_time_seconds"] = statistics.quantiles(processing_times, n=20)[18]

    return run_statistics


def write_run_json_output(output_data: Dict):
    """Write the run results to a JSON file"""
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Generate output filename with timestamp
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    strategy = output_data["run_configuration"]["optimization_strategy"]
    output_filename = f"regensql_results_{strategy}_{timestamp_str}.json"
    output_path = os.path.join(output_dir, output_filename)

    # Write JSON output
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Run results written to: {output_path}")
    logger.info("=" * 40)


def main():
    args = parse_args()

    # Record start time for the entire run
    run_start_time = time.time()
    run_timestamp = datetime.now().isoformat()

    rbot_model = None
    if args.llm_enabled:
        logger.info("LLM optimization enabled. Initializing RBot model...")
        # Initialize the RBot model with the specified LLM
        rbot_model = RBotModel(init_llms(llm_name=args.llm_name, is_llm_open=args.is_llm_open, load_model=True))

    # Log the configuration
    logger.info("Configuration:")
    logger.info(f"  Dataset: {args.dataset}")
    logger.info(f"  DB Name: {args.db_name}")
    logger.info(f"  Population Size: {args.population_size}")
    logger.info(f"  Max Generations: {args.max_generations}")
    logger.info(f"  Mutation Rate: {args.mutation_rate}")
    logger.info(f"  Crossover Rate: {args.crossover_rate}")
    logger.info(f"  Use Actual Time Fitness: {args.use_actual_time_fitness}")
    logger.info(f"  DB Timeout: {args.db_timeout}s")
    logger.info(f"  LLM Enabled: {args.llm_enabled}")
    logger.info(f"  LLM Open Source: {args.is_llm_open}")
    logger.info(f"  LLM Model: {args.llm_name}")
    logger.info(f"  Verbose: {args.verbose}")
    logger.info(f"  Partial Run: {args.partial_run}")
    logger.info(f"  Plot Fitness: {args.plot_fitness}")
    logger.info("=" * 40)

    schema_path = os.path.join(args.dataset, "create_tables.sql")
    schema = load_schema(schema_path)

    queries_dir = os.path.join(args.dataset)
    templates = [t for t in os.listdir(queries_dir) if os.path.isdir(os.path.join(queries_dir, t))]
    logger.info(f"Available query templates: {templates}")

    stats = []
    queries_max_idx = 1 if args.partial_run else 2
    for template in templates:
        logger.info(f"Processing template: {template}")
        for idx in range(queries_max_idx):
            file_path = os.path.join(queries_dir, template, f"{template}_{idx}.sql")
            if not os.path.exists(file_path):
                continue

            logger.info(f"Processing query {idx} for template {template}")

            sql_content = load_query_file(file_path)
            queries = extract_queries(sql_content)

            for j, query in enumerate(queries):
                name = f"{template}_{idx}_{j}" if j > 0 else f"{template}_{idx}"
                result = process_query(name, query, schema, args, rbot_model)
                stats.append(result)

    total = len(stats)
    run_end_time = time.time()
    total_run_time = run_end_time - run_start_time

    logger.info("=" * 40)
    logger.info(f"Total queries processed: {total}")
    logger.info(f"Total run time: {total_run_time:.2f} seconds")

    run_statistics = collect_statistics(stats, total_run_time)

    # Create output JSON
    output_data = {
        "run_timestamp": run_timestamp,
        "run_configuration": {
            "dataset": args.dataset,
            "database": args.db_name,
            "schema": args.dataset,
            "optimization_strategy": "GILLMRuleBased" if args.llm_enabled else "GIOnly",
            "llm_enabled": args.llm_enabled,
            "llm_model_name": args.llm_name,
            "is_llm_open": args.is_llm_open,
            "population_size": args.population_size,
            "max_generations": args.max_generations,
            "mutation_rate": args.mutation_rate,
            "crossover_rate": args.crossover_rate,
            "use_estimated_cost_fitness": not args.use_actual_time_fitness,
            "db_timeout": args.db_timeout,
            "verbose": args.verbose,
            "partial_run": args.partial_run,
            "plot_fitness": args.plot_fitness,
        },
        "run_statistics": run_statistics,
        "run_queries": stats,
    }

    write_run_json_output(output_data)


if __name__ == "__main__":
    main()
