import json

import duckdb
import pytest

from ingest import backfill, goalies, shootouts
from ingest.raw_loader import is_season_done


class FakeStats:
    """Stands in for the stats API's skater shootout report."""

    def __init__(self, rows=2):
        self.urls = []
        self.rows = rows

    def fetch(self, url):
        self.urls.append(url)
        return json.dumps({"data": [{"playerId": i, "shootoutGoals": 1} for i in range(min(self.rows, 3))],
                           "total": self.rows})


@pytest.fixture
def con():
    con = duckdb.connect(":memory:")
    yield con
    con.close()


def test_one_season_is_one_regular_season_request(con):
    client = FakeStats()
    assert shootouts.run(20252026, client, con, verbose=False) == {shootouts.SHOOTOUT_TABLE: [1, 1]}
    assert client.urls == [shootouts.shootout_url(20252026)]
    assert "gameTypeId=2" in client.urls[0]


def test_seasons_before_shootouts_make_no_request(con):
    client = FakeStats()
    assert shootouts.run(20042005, client, con, verbose=False) == {shootouts.SHOOTOUT_TABLE: [0, 0]}
    assert client.urls == []


def test_a_capped_response_is_refused(con):
    with pytest.raises(goalies.WindowTooLargeError):
        shootouts.run(20252026, FakeStats(rows=goalies.ROW_CAP), con, verbose=False)


def test_an_unchanged_response_adds_nothing(con):
    shootouts.run(20252026, FakeStats(), con, verbose=False)
    assert shootouts.run(20252026, FakeStats(), con, verbose=False) == {shootouts.SHOOTOUT_TABLE: [1, 0]}


def test_backfill_job_shootouts_logs_its_seasons(con):
    backfill.backfill([20252026], FakeStats(), con, job=shootouts)
    assert is_season_done(con, shootouts.JOB, 20252026)
    assert backfill.JOBS["shootouts"] is shootouts
