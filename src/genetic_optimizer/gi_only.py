import random
from typing import List, Tuple
from .base import BaseGeneticAlgorithm
from .dtos import CalciteRule, Individual, MutationType


class GIOnlyApproach(BaseGeneticAlgorithm):
    """GI Only Approach - evolves permutations of Calcite rules"""

    def __init__(self, available_rules: List[CalciteRule], **kwargs):
        super().__init__(**kwargs)
        self.available_rules = available_rules

    def generate_initial_population(self, query: str) -> List[Individual]:
        """Generate random permutations of applicable rules"""
        population = []

        # Get rules applicable to this query
        applicable_rules = self._get_applicable_rules(query)

        for _ in range(self.population_size):
            # Random permutation of rules
            rule_sequence = random.sample(applicable_rules, random.randint(1, len(applicable_rules)))
            individual = Individual(genes=rule_sequence)
            population.append(individual)

        return population

    def _get_applicable_rules(self, query: str) -> List[CalciteRule]:
        """Determine which rules are applicable to the query"""
        # This would contain actual logic to determine applicable rules
        # For now, return all available rules
        return self.available_rules.copy()

    def evaluate_fitness(self, individual: Individual, query: str) -> float:
        """Apply rules via Apache Calcite and measure performance"""
        rule_sequence = individual.genes

        # Apply rules using Apache Calcite
        optimized_query = self._apply_calcite_rules(query, rule_sequence)

        # Measure performance (execution time, cost, etc.)
        fitness = self._measure_query_performance(optimized_query)

        return fitness

    def _apply_calcite_rules(self, query: str, rules: List[CalciteRule]) -> str:
        """Apply Calcite rules to the query"""
        # This would interface with Apache Calcite
        # For now, return a placeholder
        optimized_query = query
        for rule in rules:
            # Apply rule transformation
            optimized_query = f"/* Applied {rule.name} */ {optimized_query}"
        return optimized_query

    def _measure_query_performance(self, query: str) -> float:
        """Measure query performance (higher is better)"""
        # This would measure actual query execution time, cost, etc.
        # For now, return a random fitness
        return random.random()

    def mutate(self, individual: Individual) -> Individual:
        """Insert, replace, or delete a rule"""
        rule_sequence = individual.genes.copy()
        mutation_type = random.choice(list(MutationType))

        if mutation_type == MutationType.INSERT and len(rule_sequence) < len(self.available_rules):
            # Insert a random rule at random position
            new_rule = random.choice(self.available_rules)
            position = random.randint(0, len(rule_sequence))
            rule_sequence.insert(position, new_rule)

        elif mutation_type == MutationType.REPLACE and rule_sequence:
            # Replace a random rule
            position = random.randint(0, len(rule_sequence) - 1)
            rule_sequence[position] = random.choice(self.available_rules)

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
