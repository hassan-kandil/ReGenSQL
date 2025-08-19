import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.llms.openai_like import OpenAILike
from src.rbot_rewriter.prompts import *

load_dotenv()

CACHE_PATH = "cache"
CASE_RULES_PATH = "stackoverflow-rewrite-rules-query-optimization.jsonl"

# Generate a unique log file name based on the current timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_name = f"logs/regensql_{timestamp}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file_name), logging.StreamHandler()],
)
logger = logging.getLogger("regensql_logger")


def init_db_config(database: str) -> dict[str, str]:
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "dbname": database,
        "db": "postgresql",
    }


def init_llms(llm_name: str = "llama3:8b", is_llm_open: bool = True, load_model: bool = True) -> dict[str, str]:
    print(f"Initializing LLMs with model: {llm_name}")
    if load_model:
        logger.info("Initializing gte-Qwen2-1.5B-instruct embedding model...")
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="Alibaba-NLP/gte-Qwen2-1.5B-instruct", max_length=131072
        )
    embed_dim = 1536

    if load_model:
        if is_llm_open:
            logger.info("Initializing OpenAILike...")
            Settings.llm = OpenAILike(
                model=llm_name,
                api_base="http://localhost:11434/v1",
                api_key="no_key",  # required, but unused
                is_chat_model=True,
                timeout=3600,
            )
        else:
            logger.info("Initializing OpenAI...")
            Settings.llm = OpenAI(model=llm_name)

    return {
        "GEN_CASE_REWRITE_SYS_PROMPT": GEN_CASE_REWRITE_SYS_PROMPT,
        "GEN_CASE_REWRITE_USER_PROMPT": GEN_CASE_REWRITE_USER_PROMPT,
        "SELECT_CASE_RULE_SYS_PROMPT": SELECT_CASE_RULE_SYS_PROMPT,
        "SELECT_CASE_RULE_USER_PROMPT": SELECT_CASE_RULE_USER_PROMPT,
        "CLUSTER_REWRITE_SYS_PROMPT": CLUSTER_REWRITE_SYS_PROMPT,
        "CLUSTER_REWRITE_USER_PROMPT": CLUSTER_REWRITE_USER_PROMPT,
        "SUMMARIZE_REWRITE_SYS_PROMPT": SUMMARIZE_REWRITE_SYS_PROMPT,
        "SUMMARIZE_REWRITE_USER_PROMPT": SUMMARIZE_REWRITE_USER_PROMPT,
        "SELECT_RULES_SYS_PROMPT": SELECT_RULES_SYS_PROMPT,
        "SELECT_RULES_USER_PROMPT": SELECT_RULES_USER_PROMPT,
        "ARRANGE_RULE_SETS_SYS_PROMPT": ARRANGE_RULE_SETS_SYS_PROMPT,
        "ARRANGE_RULE_SETS_USER_PROMPT": ARRANGE_RULE_SETS_USER_PROMPT,
        "ARRANGE_RULES_SYS_PROMPT": ARRANGE_RULES_SYS_PROMPT,
        "ARRANGE_RULES_USER_PROMPT": ARRANGE_RULES_USER_PROMPT,
        "REARRANGE_RULES_SYS_PROMPT": REARRANGE_RULES_SYS_PROMPT,
        "REARRANGE_RULES_USER_PROMPT": REARRANGE_RULES_USER_PROMPT,
        "SELECT_ARRANGE_RULES_SYS_PROMPT": SELECT_ARRANGE_RULES_SYS_PROMPT,
        "SELECT_ARRANGE_RULES_USER_PROMPT": SELECT_ARRANGE_RULES_USER_PROMPT,
        "RAG_SELECT_ARRANGE_RULES_SYS_PROMPT": RAG_SELECT_ARRANGE_RULES_SYS_PROMPT,
        "RAG_SELECT_ARRANGE_RULES_USER_PROMPT": RAG_SELECT_ARRANGE_RULES_USER_PROMPT,
        "EMBED_DIM": embed_dim,
    }
