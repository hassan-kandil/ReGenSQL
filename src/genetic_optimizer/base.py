import random
import abc
from typing import List, Tuple, Optional

from .dtos import Individual


class BaseGeneticAlgorithm(abc.ABC):
    """Abstract base class for genetic algorithm implementations"""

    def __init__(
        self,
        population_size: int = 50,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        max_generations: int = 100,
        verbose: bool = False,
    ):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.max_generations = max_generations
        self.verbose = verbose
        self.population: List[Individual] = []
        self.best_individual: Optional[Individual] = None
        self.generation = 0
        self.verbose = verbose

    @abc.abstractmethod
    def generate_initial_population(self) -> List[Individual]:
        """Generate initial population for the given query"""
        pass

    @abc.abstractmethod
    def evaluate_fitness(self, individual: Individual) -> float:
        """Evaluate fitness of an individual"""
        pass

    @abc.abstractmethod
    def mutate(self, individual: Individual) -> Individual:
        """Mutate an individual"""
        pass

    @abc.abstractmethod
    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Perform crossover between two parents"""
        pass

    def selection(self, population: List[Individual], k: int = 3) -> Individual:
        """Tournament selection (minimization - select individual with lowest fitness)"""
        tournament = random.sample(population, min(k, len(population)))
        return min(tournament, key=lambda x: x.fitness or float("inf"))

    def evolve(self) -> Individual:
        """Main evolution loop"""
        # Initialize population
        self.population = self.generate_initial_population()

        # Evaluate initial population
        for individual in self.population:
            individual.fitness = self.evaluate_fitness(individual)

        self.best_individual = min(self.population, key=lambda x: x.fitness or float("inf"))

        for generation in range(self.max_generations):
            self.generation = generation
            new_population = []

            # Elitism - keep best individual (lowest cost)
            new_population.append(self.best_individual)

            while len(new_population) < self.population_size:
                # Selection
                parent1 = self.selection(self.population)
                parent2 = self.selection(self.population)

                # Crossover
                if random.random() < self.crossover_rate:
                    child1, child2 = self.crossover(parent1, parent2)
                else:
                    child1, child2 = parent1, parent2

                # Mutation
                if random.random() < self.mutation_rate:
                    child1 = self.mutate(child1)
                if random.random() < self.mutation_rate:
                    child2 = self.mutate(child2)

                new_population.extend([child1, child2])

            # Trim population to exact size
            new_population = new_population[: self.population_size]

            # Evaluate new population
            for individual in new_population:
                if individual.fitness is None:
                    individual.fitness = self.evaluate_fitness(individual)

            self.population = new_population
            current_best = min(self.population, key=lambda x: x.fitness or float("inf"))

            if current_best.fitness < (self.best_individual.fitness or float("inf")):
                self.best_individual = current_best

            # Optional: print progress
            if generation % 10 == 0 and self.verbose:
                print(f"Generation {generation}: Best cost = {self.best_individual.fitness:.2f}")

        return self.best_individual
