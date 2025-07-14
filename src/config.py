import os
import logging

from dotenv import load_dotenv


load_dotenv()

CACHE_PATH = "cache"


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("regensql.log"), logging.StreamHandler()],
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
