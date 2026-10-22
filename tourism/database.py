"""Build the SQLite database from the cleaned series."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .clean import load_series

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
RAW_DIR = ROOT / "data" / "raw"

ESTABLISHMENTS_CSV = RAW_DIR / "esercizi_turistici_provTO_1994-2018.csv"
ARRIVALS_CSV = RAW_DIR / "arrivi_turisti_provTO_1994-2018.csv"


def build_database(
    db_path: str | Path,
    establishments_csv: str | Path = ESTABLISHMENTS_CSV,
    arrivals_csv: str | Path = ARRIVALS_CSV,
) -> Path:
    """Create a fresh database (replacing any existing file) and load both series."""
    establishments = load_series(establishments_csv, "n_esercizi_turistici", "businesses")
    arrivals = load_series(arrivals_csv, "arrivi_totali_turisti", "tourists")

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)

    con = sqlite3.connect(db_path)
    try:
        con.executescript((SQL_DIR / "schema.sql").read_text(encoding="utf-8"))
        # int() converts numpy integers, which sqlite3 cannot bind.
        con.executemany(
            "INSERT INTO establishments (year, businesses) VALUES (?, ?)",
            [(int(y), int(v)) for y, v in zip(establishments["year"], establishments["businesses"])],
        )
        con.executemany(
            "INSERT INTO arrivals (year, tourists) VALUES (?, ?)",
            [(int(y), int(v)) for y, v in zip(arrivals["year"], arrivals["tourists"])],
        )
        con.commit()
    finally:
        con.close()
    return db_path


def connect(db_path: str | Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path)
