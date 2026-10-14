import json

import duckdb
import pytest

from ingest import backfill, goalies
from ingest.raw_loader import is_season_done


class FakeStats:
    """Stands in for the stats API's goalie and team reports."""

    def __init__(self, rows=2, fail_on=None):
        self.urls = []
        self.rows = rows
        self.fail_on = fail_on

    def fetch(self, url):
        if self.fail_on and self.fail_on in url:
            raise KeyboardInterrupt
        self.urls.append(url)
        return json.dumps({"data": [{"gameId": i, "secret": "x"} for i in range(min(self.rows, 3))],
                           "total": self.rows})


@pytest.fixture
def con():
    con = duckdb.connect(":memory:")
    yield con
    con.close()


def test_one_season_is_two_requests_regular_season_and_playoffs(con):
    client = FakeStats()
    assert goalies.run(20252026, client, con, verbose=False) == {goalies.GOALIE_TABLE: [2, 2]}
    assert client.urls == [goalies.goalie_url(20252026, 2), goalies.goalie_url(20252026, 3)]
    assert con.execute("SELECT count(*), min(season) FROM raw.nhl_stats__goalie_game").fetchone() == (2, 20252026)


def test_a_window_at_the_row_cap_is_refused_and_nothing_is_stored(con):
    with pytest.raises(goalies.WindowTooLargeError):
        goalies.run(20252026, FakeStats(rows=goalies.ROW_CAP), con, verbose=False)
    assert con.execute("SELECT count(*) FROM raw.nhl_stats__goalie_game").fetchone()[0] == 0


def test_rerun_with_unchanged_content_adds_nothing(con):
    goalies.run(20252026, FakeStats(), con, verbose=False)
    assert goalies.run(20252026, FakeStats(), con, verbose=False) == {goalies.GOALIE_TABLE: [2, 0]}


def test_backfill_job_goalies_logs_and_resumes(con):
    with pytest.raises(KeyboardInterrupt):
        backfill.backfill([20252026, 20242025], FakeStats(fail_on="seasonId=20242025 and gameTypeId=3"),
                          con, job=goalies)
    assert is_season_done(con, goalies.JOB, 20252026)
    assert not is_season_done(con, goalies.JOB, 20242025)
    # The schedule job's log is separate: a goalie season does not count as a schedule season.
    assert not is_season_done(con, "schedule", 20252026)

    resumed = FakeStats()
    assert backfill.backfill([20252026, 20242025], resumed, con, job=goalies) == (1, 1, 2)
    assert all("20242025" in u for u in resumed.urls)
    assert con.execute("SELECT count(*) FROM raw.nhl_stats__goalie_game").fetchone()[0] == 4


def test_team_seasons_is_one_unseasoned_row(con, capsys):
    assert goalies.load_team_seasons(FakeStats(), con) is True
    assert goalies.load_team_seasons(FakeStats(), con) is False
    assert con.execute("SELECT count(*), count(season) FROM raw.nhl_stats__team_season").fetchone() == (1, 0)
    assert "secret" not in capsys.readouterr().out


def test_progress_output_never_contains_response_content(con, capsys):
    goalies.run(20252026, FakeStats(), con)
    assert "secret" not in capsys.readouterr().out
