import pandas as pd
import pytest

from tourism.analysis import cagr, load_queries, run_query
from tourism.database import ARRIVALS_CSV, ESTABLISHMENTS_CSV
from tourism.clean import load_series
from tourism.report import build_findings


@pytest.fixture(scope="module")
def series():
    """The same data, read straight with pandas, to cross-check the SQL results."""
    a = load_series(ARRIVALS_CSV, "arrivi_totali_turisti", "tourists")
    e = load_series(ESTABLISHMENTS_CSV, "n_esercizi_turistici", "businesses")
    return a.merge(e, on="year")


class TestCagr:
    def test_doubling_in_one_year(self):
        assert cagr(100, 200, 1) == pytest.approx(1.0)

    def test_ten_percent_a_year(self):
        assert cagr(100, 121, 2) == pytest.approx(0.10)

    def test_no_change(self):
        assert cagr(50, 50, 10) == pytest.approx(0.0)

    @pytest.mark.parametrize("args", [(0, 10, 1), (10, 0, 1), (10, 10, 0), (-1, 5, 2)])
    def test_rejects_invalid_input(self, args):
        with pytest.raises(ValueError):
            cagr(*args)


def test_all_queries_are_found():
    assert set(load_queries()) == {
        "yearly_growth", "biggest_arrival_changes", "years_with_declines",
        "five_year_periods", "peak_tourists_per_business",
    }


def test_unknown_query_name(con):
    with pytest.raises(KeyError):
        run_query(con, "nope")


def test_yearly_growth_matches_pandas(con, series):
    sql = run_query(con, "yearly_growth")
    expected = (series["tourists"].pct_change() * 100).round(1)
    assert pd.isna(sql.loc[0, "tourists_yoy_pct"])  # no previous year for the first row
    assert sql["tourists_yoy_pct"].iloc[1:].tolist() == pytest.approx(expected.iloc[1:].tolist(), abs=0.051)


def test_years_with_declines_match_pandas(con, series):
    sql = run_query(con, "years_with_declines")
    t_fell = series.loc[series["tourists"].diff() < 0, "year"].tolist()
    b_fell = series.loc[series["businesses"].diff() < 0, "year"].tolist()
    assert sql.loc[sql["tourists_fell"] == 1, "year"].tolist() == t_fell
    assert sql.loc[sql["businesses_fell"] == 1, "year"].tolist() == b_fell
    assert t_fell  # the real data does contain declines, so this test is not vacuous


def test_biggest_changes_are_sorted_by_size(con, series):
    sql = run_query(con, "biggest_arrival_changes")
    assert len(sql) == 5
    sizes = sql["change_pct"].abs().tolist()
    assert sizes == sorted(sizes, reverse=True)
    pct = series["tourists"].pct_change().abs()
    assert sql.loc[0, "year"] == int(series.loc[pct.idxmax(), "year"])


def test_five_year_periods(con, series):
    sql = run_query(con, "five_year_periods")
    assert sql["period"].tolist() == ["1994-1998", "1999-2003", "2004-2008", "2009-2013", "2014-2018"]
    first_block = series[series["year"].between(1994, 1998)]["tourists"].mean()
    assert sql.loc[0, "avg_tourists"] == pytest.approx(first_block, abs=0.5)


def test_peak_query_returns_three_rows_in_descending_order(con):
    sql = run_query(con, "peak_tourists_per_business")
    assert len(sql) == 3
    assert sql["tourists_per_business"].is_monotonic_decreasing


def test_findings_text_contains_the_real_numbers(con):
    text = build_findings(con)
    assert "941,970" in text and "2,505,985" in text
    assert "890" in text and "1,916" in text
    assert "Read with care" in text
