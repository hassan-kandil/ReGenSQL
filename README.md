# ReGenSQL: ReGenSQL: A Hybrid Query Rewrite Framework with Genetic Improvement and Large Language Models

ReGenSQL is a novel SQL query optimization system that combines genetic algorithms, rule-based query rewriting, and large language models (LLMs) to automatically discover and apply effective query optimization strategies. The system evolves optimal sequences of Apache Calcite rewrite rules to improve query performance.

## Overview

ReGenSQL introduces two primary optimization strategies:

1. **GI-Only**: Pure genetic algorithm approach that evolves sequences of Calcite rewrite rules
2. **GI-LLM-Rule-Based**: Hybrid approach that leverages LLMs to guide rule selection and sequencing within the genetic algorithm framework

## Code Structure

```
ReGenSQL/
├── src/                              # Core system implementation
│   ├── genetic_optimizer/           # Genetic algorithm implementations
│   │   ├── base.py                  # Abstract base class for GA
│   │   ├── gi_only.py              # Pure genetic algorithm optimizer
│   │   └── gi_llm_rule_based.py    # LLM-guided genetic optimizer
│   ├── calcite_rewriter/           # Apache Calcite integration
│   ├── rbot_rewriter/              # LLM-based rewriter components
│   ├── database/                   # Database connection and utilities
│   └── utils/                      # Utility functions
├── CalciteRewrite/                 # Java-based Calcite rule engine
├── tpch/                          # TPC-H benchmark queries and schema
├── tests/                         # Unit and integration tests
├── knowledge-base/                # Rule clustering and knowledge functions
└── chroma_db/                     # Vector database for RAG
```

## Requirements

### System Requirements
- Python 3.9+
- Java 11+ (for Apache Calcite)
- PostgreSQL 14+ (or other supported database)

### Python Dependencies
```bash
pip install -r requirements.txt
```

Key dependencies include:
- `chromadb`: Vector database for embeddings
- `llama-index`: LLM and embedding framework
- `jpype1`: Java-Python integration
- `scipy`: Statistical analysis
- `matplotlib`: Plotting and visualization
- `psycopg2`: PostgreSQL connectivity

## 🛠️ Installation

1. **Clone the repository**:
```bash
git clone https://github.com/hassan-kandil/ReGenSQL.git
cd ReGenSQL
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure database connection**:
```bash
# Update src/config.py with your database credentials
# Ensure PostgreSQL is running and accessible
```

4. **Set up OpenAI API key** (optional, for LLM features):
```bash
# Option 1: Set environment variable
export OPENAI_API_KEY="your-openai-api-key-here"

# Option 2: Add to your shell profile (permanent)
echo 'export OPENAI_API_KEY="your-openai-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# Option 3: Create a .env file in the project root
echo "OPENAI_API_KEY=your-openai-api-key-here" > .env
```

5. **Create cache directory** (for storing database execution latencies):
```bash
mkdir -p cache
```

6. **Set up embeddings database** (optional, for LLM features):
```bash
python rag_gen.py 
```

## Usage

### Basic Query Optimization

**Run GI-Only optimization**:
```bash
python run_regensql.py --dataset tpch --db-name tpch10 --population-size 50 --max-generations 20
```

**Run GI-LLM-Rule-Based optimization**:
```bash
python run_regensql.py --dataset tpch --db-name tpch10 --llm-enabled --llm-name gpt-4o --population-size 50 --max-generations 20
```

### Command Line Options

```bash
python run_regensql.py [OPTIONS]

Options:
  --dataset TEXT              Dataset name (default: tpch)
  --db-name TEXT              Database name (default: tpch10)
  --population-size INTEGER   GA population size (default: 50)
  --max-generations INTEGER   Maximum generations (default: 20)
  --mutation-rate FLOAT       Mutation rate (default: 0.5)
  --crossover-rate FLOAT      Crossover rate (default: 0.8)
  --llm-enabled              Enable LLM-guided optimization
  --llm-name TEXT            LLM model name (default: gpt-4o-mini)
  --use-actual-time-fitness  Use actual execution time for fitness
  --partial-run              Run on subset of queries (for testing)
  --verbose                  Enable verbose logging
  --plot-fitness            Generate fitness evolution plots
```

### Evaluation

**Evaluate optimization results**:
```bash
python evaluate_regensql.py output/regensql_results_[timestamp].json
```

This will:
- Execute original and rewritten queries
- Measure execution times
- Perform statistical significance testing
- Generate comprehensive performance reports

### Output Format

Results are saved in JSON format with detailed statistics in output directory:
```json
{
  "run_timestamp": "2024-XX-XX",
  "run_configuration": {...},
  "run_statistics": {
    "total_queries": 22,
    "mean_improvement_percent": 15.3,
    "statistically_significant_improved_count": 18
  },
  "run_queries": [...]
}
```

## Dataset Support

### TPC-H Benchmark
- Included queries and schema
- Standard performance benchmark
- You can download the dataset from the following link: [TPC-H](https://github.com/gregrahn/tpch-kit)


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

