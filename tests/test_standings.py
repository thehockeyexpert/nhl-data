import json

import duckdb
import pytest

from ingest import backfill, standings
from ingest.raw_loader import is_season_done


class FakeWeb:
    """Stands in for api-web.nhle.com's standings-season list and standings by date."""

    def __init__(self, version=1, produced_at="2026-10-19T18:00:00Z"):
        self.urls = []
        self.version = version
        self.produced_at = produced_at

    def fetch(self, url):
        self.urls.append(url)
        if url == standings.SEASONS_URL:
            return json.dumps({"seasons": [
                {"id": 20252026, "standingsStart": "2025-10-07", "standingsEnd": "2026-04-16"},
                {"id": 20262027, "standingsStart": "2026-09-29", "standingsEnd": "2026-10-18"},
            ]})
        return json.dumps({"standingsDateTimeUtc": self.produced_at,
                           "standings": [{"teamAbbrev": {"default": "TOR"}, "divisionName": "Atlantic",
                                          "v": self.version}]})


@pytest.fixture
def con():
    con = duckdb.connect(":memory:")
    yield con
    con.close()


def test_one_season_is_one_request_on_its_first_standings_day(con):
    client = FakeWeb()
    assert standings.run(20262027, client, con, verbose=False) == {standings.STANDINGS_TABLE: [1, 1]}
    assert client.urls == [standings.SEASONS_URL, standings.standings_url("2026-09-29")]
    assert con.execute("SELECT count(*), min(season) FROM raw.nhl_web__standings").fetchone() == (1, 20262027)


def test_the_season_list_is_fetched_once_per_client(con):
    client = FakeWeb()
    standings.run(20262027, client, con, verbose=False)
    standings.run(20252026, client, con, verbose=False)
    assert client.urls.count(standings.SEASONS_URL) == 1


def test_a_season_with_no_standings_makes_no_standings_request(con):
    client = FakeWeb()
    assert standings.run(20042005, client, con, verbose=False) == {standings.STANDINGS_TABLE: [0, 0]}
    assert client.urls == [standings.SEASONS_URL]


def test_rerun_with_unchanged_content_adds_nothing(con):
    standings.run(20262027, FakeWeb(), con, verbose=False)
    assert standings.run(20262027, FakeWeb(), con, verbose=False) == {standings.STANDINGS_TABLE: [1, 0]}
    assert standings.run(20262027, FakeWeb(version=2), con, verbose=False) == {standings.STANDINGS_TABLE: [1, 1]}


def test_a_new_production_time_alone_adds_nothing(con):
    standings.run(20262027, FakeWeb(), con, verbose=False)
    later = FakeWeb(produced_at="2026-10-20T11:00:00Z")
    assert standings.run(20262027, later, con, verbose=False) == {standings.STANDINGS_TABLE: [1, 0]}


def test_backfill_job_standings_logs_each_season(con):
    backfill.backfill([20262027, 20252026], FakeWeb(), con, job=standings)
    assert is_season_done(con, standings.JOB, 20262027)
    assert is_season_done(con, standings.JOB, 20252026)


def test_progress_output_never_contains_response_content(con, capsys):
    standings.run(20262027, FakeWeb(), con)
    out = capsys.readouterr().out
    assert "Atlantic" not in out and "TOR" not in out and '"v"' not in out
