"""Run the named SQL queries and compute figures that are clearer in Python than in SQL."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .database import SQL_DIR


def load_queries(path: str | Path = SQL_DIR / "analysis.sql") -> dict[str, str]:
    """Split analysis.sql into {name: sql} using the '-- name:' markers."""
    queries: dict[str, list[str]] = {}
    current: str | None = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("-- name:"):
            current = line.split(":", 1)[1].strip()
            queries[current] = []
        elif current is not None:
            queries[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in queries.items()}


def run_query(con: sqlite3.Connection, name: str) -> pd.DataFrame:
    queries = load_queries()
    if name not in queries:
        raise KeyError(f"Unknown query {name!r}. Available: {sorted(queries)}")
    return pd.read_sql_query(queries[name], con)


def cagr(first: float, last: float, years: int) -> float:
    """Compound annual growth rate as a fraction (0.05 means 5% a year)."""
    if first <= 0 or last <= 0 or years <= 0:
        raise ValueError("first, last and years must all be positive.")
    return (last / first) ** (1 / years) - 1
