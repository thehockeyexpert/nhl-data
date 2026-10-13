import json

import duckdb
import pytest

from ingest import backfill, schedule, teams
from ingest.raw_loader import is_season_done


class FakeNhl:
    """Stands in for the NHL API.

    20232024 and 20242025 are normal two-week seasons. 20042005 is the cancelled
    season: no season facts, a game list of unplayed games, an empty schedule.
    """

    def __init__(self, fail_on=None):
        self.urls = []
        self.fail_on = fail_on

    def fetch(self, url):
        if self.fail_on and self.fail_on in url:
            raise KeyboardInterrupt
        self.urls.append(url)
        if "/season?" in url:
            season = int(url.rsplit("=", 1)[1])
            return json.dumps({"data": [] if season == 20042005 else [{"id": season}], "total": 0})
        if "/game?" in url:
            year = int(url.rsplit("=", 1)[1]) // 10000
            dates = [f"{year}-10-01", f"{year}-10-09"]
            return json.dumps({"data": [{"gameDate": d} for d in dates], "total": 2})
        if "/schedule/" in url:
            day = url.rsplit("/", 1)[1]
            if day.startswith("2004"):
                # Nothing was played, so the API points far ahead to the next season.
                return json.dumps({"nextStartDate": "2005-09-10", "gameWeek": []})
            following = f"{day[:8]}08" if day.endswith("-01") else f"{day[:8]}15"
            return json.dumps({"nextStartDate": following, "gameWeek": []})
        return json.dumps({"data": []})


@pytest.fixture
def con():
    con = duckdb.connect(":memory:")
    yield con
    con.close()


def rows(con, table):
    return con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]


def test_seasons_between_runs_newest_to_oldest():
    assert backfill.seasons_between(20242025, 20222023) == [20242025, 20232024, 20222023]
    with pytest.raises(ValueError):
        backfill.seasons_between(20222023, 20242025)


def test_cancelled_season_is_not_an_error(con):
    client = FakeNhl()
    counts = schedule.run(20042005, client, con, verbose=False)
    # The empty season facts response is stored as evidence, the game list is stored,
    # and the schedule is asked once and found empty.
    assert counts == {"nhl_stats__season": [1, 1], "nhl_stats__game": [1, 1], "nhl_web__schedule": [1, 1]}
    assert client.urls[-1].endswith("/schedule/2004-10-01")


def test_walk_runs_from_first_to_last_game_date(con):
    client = FakeNhl()
    schedule.run(20242025, client, con, verbose=False)
    assert [u.rsplit("/", 1)[1] for u in client.urls[2:]] == ["2024-10-01", "2024-10-08"]


def test_backfill_loads_newest_first_and_logs_each_season(con):
    client = FakeNhl()
    loaded, skipped, requests = backfill.backfill([20242025, 20232024], client, con)
    assert (loaded, skipped, requests) == (2, 0, 8)
    assert client.urls[0].endswith("season?cayenneExp=id=20242025")
    assert is_season_done(con, "schedule", 20242025) and is_season_done(con, "schedule", 20232024)


def test_rerun_skips_finished_seasons_without_any_requests(con):
    backfill.backfill([20242025, 20232024], FakeNhl(), con)
    second = FakeNhl()
    assert backfill.backfill([20242025, 20232024], second, con) == (0, 2, 0)
    assert second.urls == []


def test_stopping_midway_then_resuming_stores_nothing_twice(con):
    # Stop during the second season, after its first schedule week.
    with pytest.raises(KeyboardInterrupt):
        backfill.backfill([20242025, 20232024], FakeNhl(fail_on="schedule/2023-10-08"), con)
    assert is_season_done(con, "schedule", 20242025)
    assert not is_season_done(con, "schedule", 20232024)
    assert rows(con, "nhl_web__schedule") == 3

    resumed = FakeNhl()
    assert backfill.backfill([20242025, 20232024], resumed, con)[:2] == (1, 1)
    # Only the unfinished season was requested again, and its first week was not stored twice.
    assert not any("20242025" in u or "schedule/2024" in u for u in resumed.urls)
    assert rows(con, "nhl_web__schedule") == 4
    assert rows(con, "nhl_stats__game") == 2


def test_force_reloads_a_finished_season(con):
    backfill.backfill([20242025], FakeNhl(), con)
    again = FakeNhl()
    assert backfill.backfill([20242025], again, con, force=True)[:2] == (1, 0)
    assert len(again.urls) == 4
    assert rows(con, "nhl_web__schedule") == 2


def test_team_reference_load_has_no_season_and_is_rerunnable(con):
    assert teams.run(FakeNhl(), con) == dict.fromkeys(teams.SOURCES, True)
    assert teams.run(FakeNhl(), con) == dict.fromkeys(teams.SOURCES, False)
    assert con.execute("SELECT count(*), count(season) FROM raw.nhl_stats__team").fetchone() == (1, 0)
