import os

from dotenv import load_dotenv

load_dotenv()

CACHE_PATH = "cache"


def init_db_config(database: str) -> dict[str, str]:
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "dbname": database,
        "db": "postgresql",
    }
