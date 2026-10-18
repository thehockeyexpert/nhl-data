import json
import re
from datetime import date

import duckdb
import pytest

from ingest import backfill, skater_games
from ingest.goalies import ROW_CAP
from ingest.raw_loader import ensure_table, is_season_done, load_response
from ingest.schedule import GAME_TABLE


class FakeStats:
    """Stands in for the per-game skater report. rows_per_day sets how many rows each date returns."""

    def __init__(self, rows_per_day=36, fail_on=None):
        self.urls = []
        self.rows_per_day = rows_per_day
        self.fail_on = fail_on

    def fetch(self, url):
        if self.fail_on and self.fail_on in url:
            raise KeyboardInterrupt
        self.urls.append(url)
        first, last = re.findall(r'gameDate[<>]="(\d{4}-\d{2}-\d{2})"', url)
        days = (date.fromisoformat(last) - date.fromisoformat(first)).days + 1
        total = min(days * self.rows_per_day, ROW_CAP)
        return json.dumps({"data": [{"playerId": 1}], "total": total})


@pytest.fixture
def con():
    """A throwaway in-memory database with a game list for 2025-26: one regular-season game a day in October, and
    one playoff game. Nothing touches MotherDuck."""
    con = duckdb.connect(":memory:")
    ensure_table(con, GAME_TABLE)
    games = [{"id": i, "gameType": 2, "gameDate": f"2025-10-{i:02d}T00:00:00"} for i in range(1, 32)]
    games.append({"id": 99, "gameType": 3, "gameDate": "2026-04-20T00:00:00"})
    load_response(con, GAME_TABLE, "game-list", 20252026, json.dumps({"data": games}))
    yield con
    con.close()


def test_windows_group_dates_up_to_the_game_limit():
    games = {date(2025, 10, d): 10 for d in range(1, 11)}
    assert skater_games.date_windows(games, max_games=25) == [
        (date(2025, 10, 1), date(2025, 10, 2)), (date(2025, 10, 3), date(2025, 10, 4)),
        (date(2025, 10, 5), date(2025, 10, 6)), (date(2025, 10, 7), date(2025, 10, 8)),
        (date(2025, 10, 9), date(2025, 10, 10))]


def test_a_season_is_fetched_in_windows_per_game_type(con):
    client = FakeStats()
    counts = skater_games.run(20252026, client, con, verbose=False)
    # 31 regular-season games fit in one window; the playoff game is its own window.
    assert counts == {skater_games.SKATER_GAME_TABLE: [2, 2]}
    assert "gameTypeId=2" in client.urls[0] and 'gameDate>="2025-10-01"' in client.urls[0]
    assert "gameTypeId=3" in client.urls[1]


def test_a_window_at_the_row_cap_is_split_until_it_fits(con):
    client = FakeStats(rows_per_day=1000)  # 31 days x 1,000 rows would reach the cap
    counts = skater_games.run(20252026, client, con, verbose=False)
    stored = counts[skater_games.SKATER_GAME_TABLE][1]
    assert stored == 5  # Oct 1-8, 9-16, 17-24, 25-31, and the playoff date
    assert all(json.loads(b)["total"] < ROW_CAP for (b,) in con.execute(
        "SELECT payload::VARCHAR FROM raw.nhl_stats__skater_game").fetchall())


def test_a_single_date_over_the_cap_is_refused(con):
    with pytest.raises(RuntimeError):
        skater_games.fetch_window(FakeStats(rows_per_day=ROW_CAP), 20252026, 2, date(2025, 10, 1), date(2025, 10, 1))


def test_recent_mode_fetches_the_last_dates_before_today(con):
    client = FakeStats()
    skater_games.run_recent(20252026, client, con, days=3, today=date(2025, 10, 15), verbose=False)
    assert [re.findall(r'gameDate>="([^"]+)"', u)[0] for u in client.urls] == ["2025-10-12", "2025-10-13", "2025-10-14"]


def test_recent_mode_loads_a_never_loaded_season_in_full_first(con):
    skater_games.run_season(20252026, FakeStats(), con, recent_days=3, verbose=False)
    assert is_season_done(con, skater_games.JOB, 20252026)
    client = FakeStats()
    skater_games.run_season(20252026, client, con, recent_days=3, verbose=False)
    assert len(client.urls) == 4  # now only the last dates: 3 regular-season dates and the 1 playoff date


def test_rerun_with_unchanged_content_adds_nothing(con):
    skater_games.run(20252026, FakeStats(), con, verbose=False)
    assert skater_games.run(20252026, FakeStats(), con, verbose=False) == {skater_games.SKATER_GAME_TABLE: [2, 0]}


def test_backfill_job_skater_games_logs_and_resumes(con):
    with pytest.raises(KeyboardInterrupt):
        backfill.backfill([20252026], FakeStats(fail_on="gameTypeId=3"), con, job=skater_games)
    assert not is_season_done(con, skater_games.JOB, 20252026)
    loaded, skipped, requests = backfill.backfill([20252026], FakeStats(), con, job=skater_games)
    assert (loaded, skipped, requests) == (1, 0, 2)
    assert is_season_done(con, skater_games.JOB, 20252026)
