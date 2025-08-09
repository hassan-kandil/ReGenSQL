# Test GI LLM Rule Based Approach
import os

from src.config import logger
from src.genetic_optimizer.gi_llm_rule_based import GILLMRuleBasedOptimizer
from src.utils.db_utils import actual_time

# Example schema
# schema = "CREATE TABLE users (id INT, name VARCHAR(50), age INT);"
DATASET = "tpch"
DB_NAME = "tpch10"
POPULATION_SIZE = 20
MAX_GENERATIONS = 100
DB_TIMEOUT = 300  # seconds
VERBOSE = True

schema_path = os.path.join(DATASET, "create_tables.sql")
schema = open(schema_path, "r").read()

# Example query and tables
# query = """select
# 	l_returnflag,
# 	l_linestatus,
# 	sum(l_quantity) as sum_qty,
# 	sum(l_extendedprice) as sum_base_price,
# 	sum(l_extendedprice * (1 - l_discount)) as sum_disc_price,
# 	sum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,
# 	avg(l_quantity) as avg_qty,
# 	avg(l_extendedprice) as avg_price,
# 	avg(l_discount) as avg_disc,
# 	count(*) as count_order
# from
# 	lineitem
# where
# 	l_shipdate <= date '1998-12-01' - interval '79' day
# group by
# 	l_returnflag,
# 	l_linestatus
# order by
# 	l_returnflag,
# 	l_linestatus
# limit 1;
# """
# query2_0 = """select
# 	s_acctbal,
# 	s_name,
# 	n_name,
# 	p_partkey,
# 	p_mfgr,
# 	s_address,
# 	s_phone,
# 	s_comment
# from
# 	part,
# 	supplier,
# 	partsupp,
# 	nation,
# 	region
# where
# 	p_partkey = ps_partkey
# 	and s_suppkey = ps_suppkey
# 	and p_size = 7
# 	and p_type like '%COPPER'
# 	and s_nationkey = n_nationkey
# 	and n_regionkey = r_regionkey
# 	and r_name = 'MIDDLE EAST'
# 	and ps_supplycost = (
# 		select
# 			min(ps_supplycost)
# 		from
# 			partsupp,
# 			supplier,
# 			nation,
# 			region
# 		where
# 			p_partkey = ps_partkey
# 			and s_suppkey = ps_suppkey
# 			and s_nationkey = n_nationkey
# 			and n_regionkey = r_regionkey
# 			and r_name = 'MIDDLE EAST'
# 	)
# order by
# 	s_acctbal desc,
# 	n_name,
# 	s_name,
# 	p_partkey
# limit 100;"""

query6_0 = """select
	sum(l_extendedprice * l_discount) as revenue
from
	lineitem
where
	l_shipdate >= date '1994-01-01'
	and l_shipdate < date '1994-01-01' + interval '1' year
	and l_discount between 0.06 - 0.01 and 0.06 + 0.01
	and l_quantity < 24
limit 1;
"""
query = query6_0
print("=== GI LLM Rule Based Approach ===")
print(f"Optimizing query: {query}")
gi_llm = GILLMRuleBasedOptimizer(
    query=query,
    db_name=DB_NAME,
    schema=schema,
    population_size=POPULATION_SIZE,
    max_generations=MAX_GENERATIONS,
    verbose=VERBOSE,
)
initial_population = gi_llm.generate_initial_population()
print(f"Generated initial population with size: {len(initial_population)}")
pg_args = gi_llm.db_connection.args
original_cost, _ = actual_time(sql=query, db_args=pg_args, timeout=DB_TIMEOUT)
best_solution = gi_llm.evolve()
final_rewrite_result = gi_llm.calcite_rewriter.rewrite(query=query, calcite_rules=best_solution.genes)

new_cost, _ = actual_time(sql=final_rewrite_result.query, db_args=pg_args, timeout=DB_TIMEOUT)
improved = new_cost < original_cost
improvement_factor = original_cost / new_cost if new_cost > 0 else float("inf")
improvement_percent = ((original_cost - new_cost) / original_cost * 100) if original_cost > 0 else 0

logger.info(f"Original cost: {original_cost}")
logger.info(f"Improved cost: {new_cost:.2f}")
logger.info(f"Improved: {improved}")
logger.info(f"Improvement factor: {improvement_factor:.2f}")
logger.info(f"Improvement (%): {improvement_percent:.2f}")
logger.info(f"Best solution rules: {[gene.name for gene in best_solution.genes]}")
logger.info(f"Final rewrite query: {final_rewrite_result.query}")
