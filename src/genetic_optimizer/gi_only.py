import random
from typing import List, Tuple

from src.calcite_rewriter import CalciteRewriter
from src.config import init_db_config, logger
from src.database import Database, DBArgs
from src.utils.db_utils import actual_time

from .base import BaseGeneticAlgorithm
from .dtos import Individual, MutationType


class GIOnlyOptimizer(BaseGeneticAlgorithm):
    """GI Only Approach - evolves permutations of Calcite rules"""

    def __init__(
        self, query: str, db_name: str, schema: str, db_timeout: int, use_estimated_cost_fitness: bool = True, **kwargs
    ):
        super().__init__(**kwargs)
        self.query = query
        self.schema = schema
        self.calcite_rewriter = CalciteRewriter(schema=schema)
        self.applicable_rules = self.calcite_rewriter.match_calcite_rules(query)
        self.db_connection = Database(DBArgs(init_db_config(db_name)), timeout=db_timeout)
        self.use_estimated_cost_fitness = use_estimated_cost_fitness  # Use estimated cost for fitness evaluation

    def generate_initial_population(self) -> List[Individual]:
        """Generate random permutations of applicable rules"""
        logger.info(f"Generating initial population with {len(self.applicable_rules)} applicable rules")
        population = []

        for _ in range(self.population_size):
            # Random permutation of rules with no duplicates (including empty sequences)
            rule_sequence = random.sample(self.applicable_rules, random.randint(0, len(self.applicable_rules)))
            individual = Individual(genes=rule_sequence)
            population.append(individual)

        logger.info(f"Initial population size: {len(population)}")

        return population

    def evaluate_fitness(self, individual: Individual) -> float:
        """Apply rules via Apache Calcite and measure performance"""
        rule_sequence = individual.genes

        # Apply rules using Apache Calcite
        rewrite_result = self.calcite_rewriter.rewrite(query=self.query, calcite_rules=rule_sequence)
        if rewrite_result.query == "None":
            return float("inf")

        if self.use_estimated_cost_fitness:
            # Estimate fitness based on query cost
            fitness = self.db_connection.cost_estimation(rewrite_result.query)
        else:
            # If not using estimated cost, use actual execution time
            fitness, _ = actual_time(rewrite_result.query, self.db_connection.args, self.db_connection.timeout)

        return fitness

    def mutate(self, individual: Individual) -> Individual:
        """Insert, replace, or delete a rule"""
        rule_sequence = individual.genes.copy()
        mutation_type = random.choice(list(MutationType))

        if mutation_type == MutationType.INSERT and len(rule_sequence) < len(self.applicable_rules):
            # Insert a random rule at random position
            new_rule = random.choice(self.applicable_rules)
            position = random.randint(0, len(rule_sequence))
            rule_sequence.insert(position, new_rule)

        elif mutation_type == MutationType.REPLACE and rule_sequence:
            # Replace a random rule
            position = random.randint(0, len(rule_sequence) - 1)
            rule_sequence[position] = random.choice(self.applicable_rules)

        elif mutation_type == MutationType.DELETE and len(rule_sequence) > 1:
            # Delete a random rule
            position = random.randint(0, len(rule_sequence) - 1)
            rule_sequence.pop(position)

        return Individual(genes=rule_sequence)

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Combine two rule sequences"""
        seq1, seq2 = parent1.genes, parent2.genes

        if len(seq1) <= 1 or len(seq2) <= 1:
            return parent1, parent2

        # Single-point crossover
        point1 = random.randint(1, len(seq1) - 1)
        point2 = random.randint(1, len(seq2) - 1)

        child1_genes = seq1[:point1] + seq2[point2:]
        child2_genes = seq2[:point2] + seq1[point1:]

        return Individual(genes=child1_genes), Individual(genes=child2_genes)
