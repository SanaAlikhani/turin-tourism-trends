import sqlite3

import pytest

from tourism.database import build_database


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    """A database built from the real raw files, shared by all tests."""
    return build_database(tmp_path_factory.mktemp("db") / "tourism.sqlite")


@pytest.fixture()
def con(db_path):
    connection = sqlite3.connect(db_path)
    yield connection
    connection.close()
