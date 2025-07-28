import re
from typing import List


def load_schema(schema_file: str) -> str:
    with open(schema_file, "r") as f:
        return f.read()


def load_query_file(path: str) -> str:
    with open(path, "r") as f:
        content = f.read()
    return re.sub(r"--.*\n", "", content)


def extract_queries(sql: str) -> List[str]:
    return [q.strip() + ";" for q in sql.split(";") if q.strip()]
