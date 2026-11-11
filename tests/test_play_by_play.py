import gzip
import json
from datetime import date

import duckdb
import pytest

from ingest import play_by_play
from ingest.raw_loader import ensure_table, load_response
from ingest.schedule import GAME_TABLE

SHOT_TABLE = f"raw.{play_by_play.SHOT_TABLE}"
EVENT_TABLE = f"raw.{play_by_play.EVENT_TABLE}"
S, E = play_by_play.SHOT_TABLE, play_by_play.EVENT_TABLE


def made_up_game(game_id):
    """A made-up play-by-play response: one of each shot event, a hit, a penalty and two events we don't load."""
    kinds = ["faceoff", "shot-on-goal", "missed-shot", "blocked-shot", "goal", "hit", "penalty", "takeaway"]
    return json.dumps({"id": game_id, "plays": [{"eventId": n, "typeDescKey": kind} for n, kind in enumerate(kinds)]})


class FakeWeb:
    def __init__(self):
        self.urls = []

    def fetch(self, url):
        self.urls.append(url)
        return made_up_game(int(url.split("/")[-2]))


@pytest.fixture
def con():
    """A throwaway in-memory database with a game list for 2025-26. Nothing touches MotherDuck."""
    con = duckdb.connect(":memory:")
    ensure_table(con, GAME_TABLE)
    games = [
        {"id": 2025020001, "gameType": 2, "gameStateId": 7, "period": 3, "gameDate": "2025-10-07"},
        {"id": 2025020002, "gameType": 2, "gameStateId": 7, "period": 4, "gameDate": "2025-10-08"},
        {"id": 2025010001, "gameType": 1, "gameStateId": 7, "period": 3, "gameDate": "2025-09-20"},  # preseason: left out
        {"id": 2025020003, "gameType": 2, "gameStateId": 1, "period": None, "gameDate": "2025-10-09"},  # not played: left out
        {"id": 2025030417, "gameType": 3, "gameStateId": 7, "period": None, "gameDate": "2026-06-20"},  # never played: left out
        {"id": 2025030411, "gameType": 3, "gameStateId": 6, "period": 3, "gameDate": "2026-06-10"},
    ]
    load_response(con, GAME_TABLE, "game-list", 20252026, json.dumps({"data": games}))
    yield con
    con.close()


def test_only_finished_regular_season_and_playoff_games(con):
    assert play_by_play.final_games(con, 20252026) == {
        2025020001: date(2025, 10, 7), 2025020002: date(2025, 10, 8), 2025030411: date(2026, 6, 10)}


def test_files_are_saved_compressed_and_only_shots_hits_and_penalties_are_loaded(con, tmp_path):
    client = FakeWeb()
    counts = play_by_play.run(20252026, client, con, verbose=False, folder=tmp_path)
    assert counts == {S: [3, 12], E: [0, 6]}
    others = con.execute(f"select distinct event ->> 'typeDescKey' from {EVENT_TABLE} order by 1").fetchall()
    assert [kind for (kind,) in others] == ["hit", "penalty"]
    with gzip.open(tmp_path / "20252026" / "2025020001.json.gz", "rt", encoding="utf-8") as file:
        assert file.read() == made_up_game(2025020001)
    kinds = con.execute(f"select distinct event ->> 'typeDescKey' from {SHOT_TABLE} order by 1").fetchall()
    assert [kind for (kind,) in kinds] == ["blocked-shot", "goal", "missed-shot", "shot-on-goal"]
    row = con.execute(f"select source_url, season from {SHOT_TABLE} where game_id = 2025030411 limit 1").fetchone()
    assert row == ("https://api-web.nhle.com/v1/gamecenter/2025030411/play-by-play", 20252026)


def test_a_rerun_makes_no_requests_and_adds_nothing(con, tmp_path):
    play_by_play.run(20252026, FakeWeb(), con, verbose=False, folder=tmp_path)
    client = FakeWeb()
    assert play_by_play.run(20252026, client, con, verbose=False, folder=tmp_path) == {S: [0, 0], E: [0, 0]}
    assert client.urls == []
    assert con.execute(f"select count(*) from {SHOT_TABLE}").fetchone()[0] == 12


def test_a_changed_file_is_loaded_again(con, tmp_path):
    play_by_play.run(20252026, FakeWeb(), con, verbose=False, folder=tmp_path)
    changed = json.dumps({"id": 2025020001, "plays": [{"eventId": 9, "typeDescKey": "goal"}]})
    with gzip.open(tmp_path / "20252026" / "2025020001.json.gz", "wt", encoding="utf-8") as file:
        file.write(changed)
    assert play_by_play.run(20252026, FakeWeb(), con, verbose=False, folder=tmp_path) == {S: [0, 1], E: [0, 0]}


def test_nightly_fetches_new_games_and_refetches_recent_ones(con, tmp_path):
    # The laptop loaded the two October games; the playoff game is new. The nightly run starts with an empty folder.
    play_by_play.load(FakeWeb(), con, 20252026, [2025020001, 2025020002], tmp_path / "laptop", verbose=False)
    client = FakeWeb()
    counts = play_by_play.run_recent(
        20252026, client, con, days=3, today=date(2025, 10, 10), verbose=False, folder=tmp_path / "runner")
    # New: the playoff game. Recent (Oct 7 to 9): both October games, fetched again but unchanged, so nothing added.
    assert sorted(url.split("/")[-2] for url in client.urls) == ["2025020001", "2025020002", "2025030411"]
    assert counts == {S: [3, 4], E: [0, 2]}


def test_nightly_fetches_again_only_the_days_before_today(con, tmp_path):
    games = [2025020001, 2025020002, 2025030411]
    play_by_play.load(FakeWeb(), con, 20252026, games, tmp_path / "laptop", verbose=False)
    client = FakeWeb()
    play_by_play.run_recent(20252026, client, con, days=3, today=date(2025, 10, 8), verbose=False, folder=tmp_path)
    # All three are loaded. Oct 5 to 7 holds 2025020001; 2025020002 is dated today, so it waits for tomorrow.
    assert [url.split("/")[-2] for url in client.urls] == ["2025020001"]


def test_the_folder_must_be_outside_the_repo(monkeypatch):
    monkeypatch.setenv("NHL_PBP_DIR", str(play_by_play.REPO_ROOT / "data" / "play_by_play"))
    with pytest.raises(RuntimeError, match="outside the repo"):
        play_by_play.files_folder()
