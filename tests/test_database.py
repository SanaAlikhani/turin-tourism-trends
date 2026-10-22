import sqlite3

import pytest

from tourism.database import build_database


def test_row_counts(con):
    assert con.execute("SELECT COUNT(*) FROM establishments").fetchone()[0] == 25
    assert con.execute("SELECT COUNT(*) FROM arrivals").fetchone()[0] == 25


def test_view_joins_and_computes_ratio(con):
    year, businesses, tourists, ratio = con.execute(
        "SELECT year, businesses, tourists, tourists_per_business FROM tourism_yearly WHERE year = 1994"
    ).fetchone()
    assert (businesses, tourists) == (890, 941970)
    assert ratio == pytest.approx(round(941970 / 890, 1))


def test_primary_key_blocks_duplicate_years(con):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO arrivals (year, tourists) VALUES (1994, 5)")


@pytest.mark.parametrize("value", [0, -3])
def test_check_constraint_blocks_non_positive_values(con, value):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO establishments (year, businesses) VALUES (2030, ?)", (value,))


def test_rebuilding_replaces_the_old_database(tmp_path):
    target = tmp_path / "t.sqlite"
    build_database(target)
    build_database(target)  # second run must not fail on existing tables
    con = sqlite3.connect(target)
    assert con.execute("SELECT COUNT(*) FROM arrivals").fetchone()[0] == 25
    con.close()
