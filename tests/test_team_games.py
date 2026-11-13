import json
import re
from datetime import date

import duckdb
import pytest

from ingest import backfill, team_games
from ingest.goalies import ROW_CAP, WindowTooLargeError
from ingest.raw_loader import ensure_table, is_season_done, load_response
from ingest.schedule import GAME_TABLE


class FakeStats:
    """Stands in for the team reports. Each response depends on its URL, so different requests store different rows."""

    def __init__(self, total=100):
        self.urls = []
        self.total = total

    def fetch(self, url):
        self.urls.append(url)
        return json.dumps({"data": [{"gameId": 1, "teamId": 1, "url": url}], "total": self.total})


@pytest.fixture
def con():
    """A throwaway in-memory database with a game list for 2025-26: one regular-season game a day in October.
    No playoff games yet. Nothing touches MotherDuck."""
    con = duckdb.connect(":memory:")
    ensure_table(con, GAME_TABLE)
    games = [{"id": i, "gameType": 2, "gameDate": f"2025-10-{i:02d}T00:00:00"} for i in range(1, 32)]
    load_response(con, GAME_TABLE, "game-list", 20252026, json.dumps({"data": games}))
    yield con
    con.close()


def test_a_season_is_one_request_per_report_and_game_type(con):
    client = FakeStats()
    counts = team_games.run(20252026, client, con, verbose=False)
    assert counts == {table: [2, 2] for table in team_games.REPORTS.values()}
    assert len(client.urls) == 8
    assert not any("gameDate" in url for url in client.urls)
    assert all("isGame=true" in url and "limit=-1" in url for url in client.urls)
    for report, table in team_games.REPORTS.items():
        assert con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0] == 2
        assert sum(f"/team/{report}?" in url for url in client.urls) == 2


def test_a_response_at_the_row_cap_is_refused(con):
    with pytest.raises(WindowTooLargeError):
        team_games.run(20252026, FakeStats(total=ROW_CAP), con, verbose=False)


def test_a_season_never_loaded_in_full_is_loaded_in_full_first(con):
    client = FakeStats()
    team_games.run_season(20252026, client, con, recent_days=3, today=date(2025, 10, 15), verbose=False)
    assert not any("gameDate" in url for url in client.urls)
    assert is_season_done(con, team_games.JOB, 20252026)


def test_recent_mode_asks_for_the_last_dates_before_today(con):
    team_games.run_season(20252026, FakeStats(), con, verbose=False)
    client = FakeStats()
    team_games.run_season(20252026, client, con, recent_days=3, today=date(2025, 10, 15), verbose=False)
    # Regular season only (no playoff dates yet): one request per report, Oct 12 to 14.
    assert len(client.urls) == 4
    for url in client.urls:
        assert re.findall(r'gameDate[<>]="([^"]+)"', url) == ["2025-10-12", "2025-10-14"]
        assert "gameTypeId=2" in url


def test_backfill_knows_the_job():
    assert backfill.JOBS["team_games"] is team_games
