import typing as t
import logging
from scipy import stats
import json
import os

from src.config import CACHE_PATH
from src.database import DBArgs, Database


def actual_time(sql: str, db_args: DBArgs, timeout: int) -> t.Tuple[float, t.List[float]]:
    if sql not in db_args.cache:
        times = []
        for i in range(5):
            db = Database(db_args, timeout)
            latency = db.pgsql_actual_time(sql)
            if latency == -1:
                return float("inf"), [float("inf")] * 5
            if latency == timeout * 1000 and i == 0:
                times = [latency] * 5
                break
            times.append(latency)
        sorted_times = sorted(times)
        actual_time = sum(sorted_times[1:-1]) / 3
        db_args.cache[sql] = {"time": actual_time, "times": times}
        with open(os.path.join(CACHE_PATH, f"{db_args.dbname}.jsonl"), "a") as f:
            f.write(json.dumps({"sql": sql, "time": actual_time, "times": times}) + "\n")
    return db_args.cache[sql]["time"], db_args.cache[sql]["times"]


def actual_time_once(sql: str, db_args: DBArgs, timeout: int) -> float:
    if sql not in db_args.cache:
        db = Database(db_args, timeout)
        latency = db.pgsql_actual_time(sql)
        if latency == -1:
            return float("inf")
        db_args.cache[sql] = {"time": latency}
        with open(os.path.join(CACHE_PATH, f"{db_args.dbname}.jsonl"), "a") as f:
            f.write(json.dumps({"sql": sql, "time": latency}) + "\n")
    return db_args.cache[sql]["time"]
