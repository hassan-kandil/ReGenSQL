import itertools
import random
from typing import Dict, List, Tuple

from llama_index.core.async_utils import run_async_tasks
from src.calcite_rewriter import CalciteRewriter, CalciteRule
from src.config import init_db_config, init_llms, logger
from src.database import Database, DBArgs
from src.rbot_rewriter.model import RBotModel
from src.rbot_rewriter.rag_retrieve import init_docstore, rag_retrieve

from .base import BaseGeneticAlgorithm
from .dtos import Individual, MutationType


class GILLMRuleBasedOptimizer(BaseGeneticAlgorithm):
    """GI Only Approach - evolves permutations of Calcite rules"""

    RETRIEVER_TOP_K: int = 10
    CASE_BATCH: int = 5
    RULE_BATCH: int = 10

    def __init__(self, query: str, db_name: str, schema: str, db_timeout: int = 300, use_estimated_cost_fitness: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.query = query
        self.schema = schema
        self.calcite_rewriter = CalciteRewriter(schema=schema)
        self.rbot_model = RBotModel(init_llms(model_type="gpt4o-mini", load_model=True))
        self.applicable_rules = self.calcite_rewriter.match_calcite_rules(query)
        self.db_connection = Database(DBArgs(init_db_config(db_name)), timeout=db_timeout)
        self.doc_store = init_docstore()
        self.use_estimated_cost_fitness = use_estimated_cost_fitness

    def _retrieve_applicable_suggestions_and_rules(self) -> List[Tuple[str, str]]:
        """Generate examples of rewrite rules related to the query using R-Bot RAG system."""
        # Retrieve relevant rules and suggestions using RAG
        res = rag_retrieve(
            query=self.query,
            schema=self.schema,
            docstore=self.doc_store,
            embed_dim=self.rbot_model.EMBED_DIM,
            RETRIEVER_TOP_K=self.RETRIEVER_TOP_K,
        )
        rewrites, retriever_res = res["rewrites"], res["retriever_res"]
        nl_suggestions = [obj["rewrite"] for obj in rewrites["nl"]]
        normal_rules = [r for r in rewrites["calcite"] if r["type"] == "normal"]
        explore_rules = [r for r in rewrites["calcite"] if r["type"] == "explore"]
        normal_suggestions = [obj["rewrite"] for obj in normal_rules]
        strategies = normal_suggestions + nl_suggestions

        tasks = []
        # Generate strategies and select rules from cases using R-Bot model
        logger.debug(f"Generating strategies for query: {self.query}")
        tasks.append(
            self.rbot_model.gen_summarize_strategies(self.query, retriever_res, strategies, case_batch=self.CASE_BATCH)
        )
        logger.debug(f"Selecting rules for query: {self.query}")
        tasks.append(
            self.rbot_model.select_rules_from_cases(
                retriever_res, normal_rules=normal_rules, explore_rules=explore_rules
            )
        )
        logger.debug(f"Running {len(tasks)} asynchronous LLM tasks...")
        task_results = run_async_tasks(tasks)
        summarized_strategies = task_results[0]
        selected_rules: List[List[Dict[str, str]]] = task_results[1]

        logger.info(
            "RAG Suggestions and Rules Results: "
            + str({"suggestions": summarized_strategies, "selected_rules": selected_rules})
        )
        selected_rules_lst: List[Dict[str, str]] = list(itertools.chain.from_iterable(selected_rules))
        return (summarized_strategies, selected_rules_lst)

    def generate_initial_population(self) -> List[Individual]:
        """Generate the initial population of individuals based on the query and schema."""
        suggestions, applicable_rules = self._retrieve_applicable_suggestions_and_rules()
        # Generate different permutations of the suggestions and applicable_rules including empty ones
        logger.info(
            f"Generating initial population with {len(applicable_rules)} applicable rules and {len(suggestions)} suggestions"
        )
        initial_population = []
        for _ in range(self.population_size):
            # Randomly select a subset of applicable rules
            rule_sequence = random.sample(applicable_rules, random.randint(0, len(applicable_rules)))
            # Randomly select a subset of suggestions
            suggestion_sequence = random.sample(suggestions, random.randint(0, len(suggestions)))
            # Combine both sequences to form the individual's genes
            suggestions_sequence_str = "\n\n".join(
                [f'### Suggestion {i+1}:\n"""{s}"""' for i, s in enumerate(suggestion_sequence)]
            )
            relevant_rules_sequence = self.rbot_model.select_rules(self.query, suggestions_sequence_str, rule_sequence)
            arranged_relevant_rules = self.rbot_model.arrange_rules(
                self.query, suggestions_sequence_str, relevant_rules_sequence
            )
            # Create an individual with the arranged rules
            genes = [CalciteRule(name=rule_name) for rule_name in arranged_relevant_rules]
            individual = Individual(genes=genes)
            initial_population.append(individual)
        logger.info(f"Initial population size: {len(initial_population)}")
        for i, individual in enumerate(initial_population):
            # Log the genes of each individual for debugging
            logger.debug(f"Individual {i+1} genes: {individual.genes}")
        return initial_population

    def evaluate_fitness(self, individual):
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
            fitness = self.db_connection.pgsql_actual_time(rewrite_result.query)
        
        return fitness

    def crossover(self, parent1: Individual, parent2: Individual) -> Individual:
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
