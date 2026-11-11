import gzip
import json

import duckdb
import pytest

from ingest import player_pages
from ingest.nhl_api import NhlApiError


class FakeWeb:
    """Stands in for the player pages: player 3 has none (HTTP 404), player 9 breaks the connection."""

    def __init__(self):
        self.urls = []

    def fetch(self, url):
        self.urls.append(url)
        player_id = int(url.split("/")[-2])
        if player_id == 3:
            raise NhlApiError(f"HTTP 404 for {url}")
        if player_id == 9:
            raise NhlApiError(f"Gave up on {url} after 4 attempts (ReadTimeout)")
        return json.dumps({"playerId": player_id, "seasonTotals": [
            {"season": 20202021, "leagueAbbrev": "OHL", "gamesPlayed": 60},
            {"season": 20212022, "leagueAbbrev": "NHL", "gamesPlayed": 82},
        ]})


@pytest.fixture
def con():
    con = duckdb.connect(":memory:")
    player_pages.ensure_table(con, player_pages.PLAYER_LIST_TABLE, seasonal=False)
    payload = json.dumps({"data": [{"id": 2}, {"id": 1}, {"id": 3}, {"id": 1}]})
    con.execute(f"insert into raw.{player_pages.PLAYER_LIST_TABLE} values ('u', now(), null, ?, 'h', null)", [payload])
    yield con
    con.close()


def test_player_ids_come_from_the_newest_list_once_each(con):
    assert player_pages.player_ids(con) == [1, 2, 3]


def test_pages_are_saved_compressed_and_a_missing_page_is_marked(con, tmp_path):
    client = FakeWeb()
    assert player_pages.download(client, [1, 2, 3], tmp_path, verbose=False) == (3, 1)
    assert json.loads(gzip.open(tmp_path / "1.json.gz").read())["playerId"] == 1
    assert (tmp_path / "3.missing").exists() and not (tmp_path / "3.json.gz").exists()
    # A rerun asks for nothing: pages on disk and marked missing pages are skipped.
    again = FakeWeb()
    assert player_pages.download(again, [1, 2, 3], tmp_path, verbose=False) == (0, 0)
    assert again.urls == []


def test_any_other_error_stops_the_run(tmp_path):
    with pytest.raises(NhlApiError):
        player_pages.download(FakeWeb(), [1, 9], tmp_path, verbose=False)
    assert (tmp_path / "1.json.gz").exists()  # kept: the rerun starts after it


def test_run_loads_one_row_per_season_entry_and_reruns_add_nothing(con, tmp_path):
    assert player_pages.run(FakeWeb(), con, verbose=False, folder=tmp_path) == (3, 1, 2, 4)
    rows = con.execute(f"select player_id, entry ->> 'leagueAbbrev', source_url from raw.{player_pages.SEASON_TOTAL_TABLE}"
                       " order by 1, 2").fetchall()
    assert rows[0] == (1, "NHL", player_pages.PAGE_URL.format(player_id=1))
    assert [r[:2] for r in rows] == [(1, "NHL"), (1, "OHL"), (2, "NHL"), (2, "OHL")]
    assert player_pages.run(FakeWeb(), con, verbose=False, folder=tmp_path) == (0, 0, 2, 0)


def test_the_folder_is_never_inside_the_repo(monkeypatch):
    monkeypatch.setenv("NHL_PLAYER_DIR", str(player_pages.REPO_ROOT / "data"))
    with pytest.raises(RuntimeError):
        player_pages.files_folder()
