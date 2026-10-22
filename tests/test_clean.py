import pytest

from tourism.clean import load_series, parse_italian_int, validate_series
from tourism.database import ARRIVALS_CSV, ESTABLISHMENTS_CSV


class TestParseItalianInt:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("890", 890),
            ("1913", 1913),            # no separator (the 2016-2018 rows)
            ("1.054", 1054),
            ("1.520", 1520),           # a trailing zero must survive, a float parse would give 1.52
            ("941.970", 941970),
            ("1.001.195", 1001195),
            (" 2.505.985 ", 2505985),  # surrounding whitespace
        ],
    )
    def test_valid(self, text, expected):
        assert parse_italian_int(text) == expected

    @pytest.mark.parametrize("text", ["", "abc", "1,054", "1.5", "12.34", "1..054", "-5", "1.0545"])
    def test_invalid_values_fail_loudly(self, text):
        with pytest.raises(ValueError):
            parse_italian_int(text)


def write_csv(tmp_path, text, newline="\n", encoding="utf-8"):
    path = tmp_path / "series.csv"
    path.write_bytes(text.replace("\n", newline).encode(encoding))
    return path


class TestLoadSeries:
    def test_mixed_formats_in_one_file(self, tmp_path):
        path = write_csv(tmp_path, "Anno,valore\n2014,1.797\n2015,1.893\n2016,1913\n")
        df = load_series(path, "valore", "n")
        assert df["n"].tolist() == [1797, 1893, 1913]

    def test_handles_windows_line_endings_and_bom(self, tmp_path):
        path = write_csv(tmp_path, "Anno,valore\n2000,10\n2001,20\n", newline="\r\n", encoding="utf-8-sig")
        assert load_series(path, "valore", "n")["n"].tolist() == [10, 20]

    def test_sorts_by_year(self, tmp_path):
        path = write_csv(tmp_path, "Anno,valore\n2001,20\n2000,10\n")
        assert load_series(path, "valore", "n")["year"].tolist() == [2000, 2001]

    def test_missing_column(self, tmp_path):
        path = write_csv(tmp_path, "Anno,altro\n2000,10\n")
        with pytest.raises(ValueError, match="missing column"):
            load_series(path, "valore", "n")

    def test_duplicate_year(self, tmp_path):
        path = write_csv(tmp_path, "Anno,valore\n2000,10\n2000,11\n")
        with pytest.raises(ValueError, match="Duplicate"):
            load_series(path, "valore", "n")

    def test_gap_in_years(self, tmp_path):
        path = write_csv(tmp_path, "Anno,valore\n2000,10\n2002,12\n")
        with pytest.raises(ValueError, match="consecutive"):
            load_series(path, "valore", "n")

    def test_zero_value_rejected(self, tmp_path):
        path = write_csv(tmp_path, "Anno,valore\n2000,0\n2001,5\n")
        with pytest.raises(ValueError, match="positive"):
            load_series(path, "valore", "n")

    def test_empty_file(self, tmp_path):
        path = write_csv(tmp_path, "Anno,valore\n")
        with pytest.raises(ValueError, match="no rows"):
            load_series(path, "valore", "n")


class TestRealData:
    def test_establishments(self):
        df = load_series(ESTABLISHMENTS_CSV, "n_esercizi_turistici", "businesses")
        assert len(df) == 25
        assert (df["year"].min(), df["year"].max()) == (1994, 2018)
        assert df.set_index("year")["businesses"].loc[[1994, 2003, 2016, 2018]].tolist() == [890, 1054, 1913, 1916]

    def test_arrivals(self):
        df = load_series(ARRIVALS_CSV, "arrivi_totali_turisti", "tourists")
        assert len(df) == 25
        assert df.set_index("year")["tourists"].loc[[1994, 1996, 2018]].tolist() == [941970, 1001195, 2505985]

    def test_validate_series_accepts_real_shape(self):
        df = load_series(ARRIVALS_CSV, "arrivi_totali_turisti", "tourists")
        validate_series(df, "tourists")
