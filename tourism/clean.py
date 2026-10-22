"""Parsing and validation for the Open Data Torino tourism CSV files.

The raw files use the Italian thousands separator ("1.054" means 1,054), and the
formatting is not even consistent inside one file: the businesses series uses dots
up to 2015 but none from 2016 onwards. A normal float parse would silently turn
"1.520" into 1.52, so numbers are parsed strictly and anything unexpected fails loudly.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

_PLAIN = re.compile(r"^\d+$")
_THOUSANDS = re.compile(r"^\d{1,3}(\.\d{3})+$")


def parse_italian_int(value: object) -> int:
    """Parse "890", "1913" or "1.001.195" into an int. Anything else raises ValueError."""
    text = str(value).strip()
    if _PLAIN.match(text):
        return int(text)
    if _THOUSANDS.match(text):
        return int(text.replace(".", ""))
    raise ValueError(
        f"Cannot parse {value!r}: expected digits, optionally grouped with '.' every three digits."
    )


def validate_series(df: pd.DataFrame, value_column: str) -> None:
    """Check that a yearly series has one positive value per consecutive year."""
    if df.empty:
        raise ValueError("The file has no rows.")
    duplicated = sorted(set(df.loc[df["year"].duplicated(), "year"]))
    if duplicated:
        raise ValueError(f"Duplicate years: {duplicated}")
    years = sorted(df["year"])
    gaps = [(a, b) for a, b in zip(years, years[1:]) if b - a != 1]
    if gaps:
        raise ValueError(f"Years are not consecutive, gaps after: {[a for a, _ in gaps]}")
    if (df[value_column] <= 0).any():
        raise ValueError(f"'{value_column}' must be positive for every year.")


def load_series(path: str | Path, source_column: str, value_column: str) -> pd.DataFrame:
    """Read one yearly series and return a clean DataFrame with columns year and value_column."""
    raw = pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=False)
    raw.columns = [c.strip() for c in raw.columns]

    missing = {"Anno", source_column} - set(raw.columns)
    if missing:
        raise ValueError(f"{path}: missing column(s) {sorted(missing)}; found {list(raw.columns)}")

    df = pd.DataFrame(
        {
            "year": raw["Anno"].map(parse_italian_int),
            value_column: raw[source_column].map(parse_italian_int),
        }
    )
    df = df.sort_values("year").reset_index(drop=True)
    validate_series(df, value_column)
    return df
