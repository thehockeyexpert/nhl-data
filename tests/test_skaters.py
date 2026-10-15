import json

import duckdb
import pytest

from ingest import backfill, goalies, skaters
from ingest.raw_loader import is_season_done


class FakeStats:
    """Stands in for the stats API's skater summary report."""

    def __init__(self, rows=2, fail_on=None):
        self.urls = []
        self.rows = rows
        self.fail_on = fail_on

    def fetch(self, url):
        if self.fail_on and self.fail_on in url:
            raise KeyboardInterrupt
        self.urls.append(url)
        return json.dumps({"data": [{"playerId": i, "goals": 1} for i in range(min(self.rows, 3))],
                           "total": self.rows})


@pytest.fixture
def con():
    con = duckdb.connect(":memory:")
    yield con
    con.close()


def test_one_season_is_two_requests_regular_season_and_playoffs(con):
    client = FakeStats()
    assert skaters.run(20252026, client, con, verbose=False) == {skaters.SKATER_TABLE: [2, 2]}
    assert client.urls == [skaters.skater_url(20252026, 2), skaters.skater_url(20252026, 3)]
    assert "skater/summary?isAggregate=false&isGame=false" in client.urls[0]
    assert con.execute("SELECT count(*), min(season) FROM raw.nhl_stats__skater_season").fetchone() == (2, 20252026)


def test_a_window_at_the_row_cap_is_refused_and_nothing_is_stored(con):
    with pytest.raises(goalies.WindowTooLargeError):
        skaters.run(20252026, FakeStats(rows=goalies.ROW_CAP), con, verbose=False)
    assert con.execute("SELECT count(*) FROM raw.nhl_stats__skater_season").fetchone()[0] == 0


def test_rerun_with_unchanged_content_adds_nothing(con):
    skaters.run(20252026, FakeStats(), con, verbose=False)
    assert skaters.run(20252026, FakeStats(), con, verbose=False) == {skaters.SKATER_TABLE: [2, 0]}


def test_backfill_job_skaters_logs_and_resumes_separately_from_goalies(con):
    with pytest.raises(KeyboardInterrupt):
        backfill.backfill([20252026, 20242025], FakeStats(fail_on="seasonId=20242025 and gameTypeId=3"),
                          con, job=skaters)
    assert is_season_done(con, skaters.JOB, 20252026)
    assert not is_season_done(con, skaters.JOB, 20242025)
    assert not is_season_done(con, goalies.JOB, 20252026)

    resumed = FakeStats()
    loaded, skipped, requests = backfill.backfill([20252026, 20242025], resumed, con, job=skaters)
    assert (loaded, skipped, requests) == (1, 1, 2)
    assert all("seasonId=20242025" in url for url in resumed.urls)


def test_the_backfill_command_offers_the_skaters_job():
    assert backfill.JOBS["skaters"] is skaters
