#!/bin/bash

# Bash script to run RegenSQL experiments with different parameter configurations
# This script runs partial experiments (subset of queries) to test various genetic algorithm parameters

set -e  # Exit on any error

# Default parameters (based on the constants in run_regensql.py)
DEFAULT_DATASET="tpch"
DEFAULT_DB_NAME="tpch10"
DEFAULT_POPULATION_SIZE=100
DEFAULT_MAX_GENERATIONS=20
DEFAULT_MUTATION_RATE=0.1
DEFAULT_CROSSOVER_RATE=0.8
DEFAULT_DB_TIMEOUT=300

# Experiment parameters
PARTIAL_RUN="--partial-run"  # Run only subset of queries

echo "Starting RegenSQL Genetic Algorithm Parameter Experiments"
echo "=========================================================="
echo "Default Parameters:"
echo "  Dataset: $DEFAULT_DATASET"
echo "  DB Name: $DEFAULT_DB_NAME"
echo "  Population Size: $DEFAULT_POPULATION_SIZE"
echo "  Max Generations: $DEFAULT_MAX_GENERATIONS"
echo "  Mutation Rate: $DEFAULT_MUTATION_RATE"
echo "  Crossover Rate: $DEFAULT_CROSSOVER_RATE"
echo "  DB Timeout: $DEFAULT_DB_TIMEOUT"
echo "  Partial Run: Enabled"
echo ""

# Function to run a single experiment
run_experiment() {
    local experiment_name="$1"
    local args="$2"
    
    echo "Running experiment: $experiment_name"
    echo "Command: python run_regensql.py $args"
    echo "----------------------------------------"
    
    # Run the experiment and capture any errors
    if python run_regensql.py $args; then
        echo "✅ Experiment '$experiment_name' completed successfully"
    else
        echo "❌ Experiment '$experiment_name' failed with exit code $?"
    fi
    echo ""
}

# Create logs directory if it doesn't exist
mkdir -p logs

echo "🧬 EXPERIMENT SET 1: Crossover Rate Variations"
echo "=============================================="

# 1. Crossover Rate Experiments (keeping other params default)
run_experiment "crossover_0.8" "$PARTIAL_RUN --crossover-rate 0.8"
run_experiment "crossover_0.6" "$PARTIAL_RUN --crossover-rate 0.6"
run_experiment "crossover_0.4" "$PARTIAL_RUN --crossover-rate 0.4"
run_experiment "crossover_0.2" "$PARTIAL_RUN --crossover-rate 0.2"

echo "🧬 EXPERIMENT SET 2: Mutation Rate Variations"
echo "============================================="

# 2. Mutation Rate Experiments (keeping other params default)
run_experiment "mutation_0.1" "$PARTIAL_RUN --mutation-rate 0.1"
run_experiment "mutation_0.3" "$PARTIAL_RUN --mutation-rate 0.3"
run_experiment "mutation_0.5" "$PARTIAL_RUN --mutation-rate 0.5"
run_experiment "mutation_0.7" "$PARTIAL_RUN --mutation-rate 0.7"

echo "🧬 EXPERIMENT SET 3: Population Size Variations"
echo "==============================================="

# 3. Population Size Experiments (keeping other params default)
run_experiment "population_100" "$PARTIAL_RUN --population-size 100"
run_experiment "population_75" "$PARTIAL_RUN --population-size 75"
run_experiment "population_50" "$PARTIAL_RUN --population-size 50"
run_experiment "population_25" "$PARTIAL_RUN --population-size 25"

echo "🎉 All experiments completed!"
echo "=============================="
echo "Results can be found in the 'output' directory."
echo "Logs can be found in the 'logs' directory."
echo ""
echo "Experiment Summary:"
echo "- Crossover Rate: 4 experiments (0.8, 0.6, 0.4, 0.2)"
echo "- Mutation Rate: 4 experiments (0.1, 0.3, 0.5, 0.7)" 
echo "- Population Size: 4 experiments (100, 75, 50, 25)"
echo "- Total: 12 experiments"
echo "- All experiments used 20 generations and partial run mode"
echo "=========================================================="
