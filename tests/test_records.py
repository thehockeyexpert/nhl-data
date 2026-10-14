import json

import duckdb
import pytest

from ingest import records


class FakeRecords:
    """Stands in for the records site and the standings-rules endpoint."""

    def __init__(self, version=1):
        self.urls = []
        self.version = version

    def fetch(self, url):
        self.urls.append(url)
        if "standings-season" in url:
            return json.dumps({"seasons": [{"id": 20252026, "v": self.version}]})
        return json.dumps({"data": [{"id": 1, "v": self.version}], "total": 1})


@pytest.fixture
def con():
    con = duckdb.connect(":memory:")
    yield con
    con.close()


def test_each_source_is_one_request_into_its_own_table(con):
    client = FakeRecords()
    assert records.run(client, con) == dict.fromkeys(records.SOURCES, True)
    assert client.urls == list(records.SOURCES.values())
    for table in records.SOURCES:
        assert con.execute(f"SELECT count(*), count(season) FROM raw.{table}").fetchone() == (1, 0)


def test_rerun_with_unchanged_content_adds_nothing(con):
    records.run(FakeRecords(), con)
    assert records.run(FakeRecords(), con) == dict.fromkeys(records.SOURCES, False)


def test_changed_content_is_kept_as_a_new_row(con):
    records.run(FakeRecords(version=1), con)
    assert all(records.run(FakeRecords(version=2), con).values())
    assert con.execute("SELECT count(*) FROM raw.nhl_records__player").fetchone()[0] == 2


def test_progress_output_never_contains_response_content(con, capsys):
    records.run(FakeRecords(), con)
    out = capsys.readouterr().out
    assert '"v"' not in out and "data" not in out
