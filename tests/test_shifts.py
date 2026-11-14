import gzip
import json
from datetime import date

import duckdb
import pytest

from ingest import backfill, shifts
from ingest.raw_loader import ensure_table, load_response
from ingest.schedule import GAME_TABLE

SHIFT_TABLE = f"raw.{shifts.SHIFT_TABLE}"


class FakeStats:
    """Stands in for the shift charts (three made-up entries per game) and the HTML shift reports."""

    def __init__(self, unpublished=()):
        self.urls = []
        self.html_urls = []
        self.unpublished = set(unpublished)  # report URLs that answer 404

    def fetch_html(self, url):
        self.html_urls.append(url)
        return None if url in self.unpublished else f"<html><body>made-up report {url}</body></html>"

    def fetch(self, url):
        self.urls.append(url)
        game_id = int(url.rsplit("=", 1)[1])
        return json.dumps({"data": [{"id": game_id * 10 + n, "gameId": game_id, "typeCode": 517} for n in range(3)],
                           "total": 3})


def game_list(con, season, games):
    ensure_table(con, GAME_TABLE)
    load_response(con, GAME_TABLE, f"game-list-{season}", season, json.dumps({"data": games}))


@pytest.fixture
def con():
    """A throwaway in-memory database with game lists for 2025-26 and 2009-10. Nothing touches MotherDuck."""
    con = duckdb.connect(":memory:")
    game_list(con, 20252026, [
        {"id": 2025020001, "gameType": 2, "gameStateId": 7, "period": 3, "gameDate": "2025-10-07"},
        {"id": 2025020002, "gameType": 2, "gameStateId": 7, "period": 4, "gameDate": "2025-10-08"},
        {"id": 2025020003, "gameType": 2, "gameStateId": 1, "period": None, "gameDate": "2025-10-09"},  # not played
    ])
    game_list(con, 20092010, [{"id": 2009020001, "gameType": 2, "gameStateId": 7, "period": 3, "gameDate": "2009-10-01"}])
    yield con
    con.close()


def test_files_are_saved_compressed_and_every_shift_is_loaded(con, tmp_path):
    client = FakeStats()
    counts = shifts.run(20252026, client, con, verbose=False, folder=tmp_path)
    assert counts == {shifts.SHIFT_TABLE: [2, 6], shifts.REPORT_TABLE: [0, 0]}
    assert all("shiftcharts?cayenneExp=gameId=" in url for url in client.urls)
    with gzip.open(tmp_path / "20252026" / "2025020001.json.gz", "rt", encoding="utf-8") as file:
        assert len(json.load(file)["data"]) == 3
    rows = con.execute(f"select game_id, count(*), any_value(source_url) from {SHIFT_TABLE} group by 1 order by 1").fetchall()
    assert [(g, n) for g, n, _ in rows] == [(2025020001, 3), (2025020002, 3)]
    assert rows[0][2] == shifts.SHIFT_URL.format(game_id=2025020001)


def test_a_rerun_downloads_and_adds_nothing(con, tmp_path):
    shifts.run(20252026, FakeStats(), con, verbose=False, folder=tmp_path)
    client = FakeStats()
    assert shifts.run(20252026, client, con, verbose=False, folder=tmp_path) == {
        shifts.SHIFT_TABLE: [0, 0], shifts.REPORT_TABLE: [0, 0]}
    assert client.urls == []


def test_seasons_before_shift_charts_make_no_requests(con, tmp_path):
    client = FakeStats()
    assert shifts.run(20092010, client, con, verbose=False, folder=tmp_path) == {
        shifts.SHIFT_TABLE: [0, 0], shifts.REPORT_TABLE: [0, 0]}
    assert client.urls == []


def test_recent_mode_fetches_new_games_and_recent_ones_again(con, tmp_path):
    shifts.run(20252026, FakeStats(), con, verbose=False, folder=tmp_path)
    client = FakeStats()
    shifts.run_recent(20252026, client, con, days=1, today=date(2025, 10, 9), verbose=False, folder=tmp_path)
    assert client.urls == [shifts.SHIFT_URL.format(game_id=2025020002)]


def test_the_folder_must_be_outside_the_repo(monkeypatch):
    monkeypatch.setenv("NHL_SHIFTS_DIR", str(shifts.REPO_ROOT / "data" / "shifts"))
    with pytest.raises(RuntimeError):
        shifts.files_folder()


def test_backfill_knows_the_job():
    assert backfill.JOBS["shifts"] is shifts


class EmptyFor(FakeStats):
    """Shift charts as FakeStats, except an empty chart for the given games."""

    def __init__(self, empty):
        super().__init__()
        self.empty = empty

    def fetch(self, url):
        body = super().fetch(url)
        return json.dumps({"data": [], "total": 0}) if int(url.rsplit("=", 1)[1]) in self.empty else body


def test_a_whole_season_run_asks_again_for_empty_charts_only(con, tmp_path):
    shifts.run(20252026, EmptyFor({2025020001}), con, verbose=False, folder=tmp_path)
    client = FakeStats()
    assert shifts.run(20252026, client, con, verbose=False, folder=tmp_path)[shifts.SHIFT_TABLE] == [1, 3]
    assert client.urls == [shifts.SHIFT_URL.format(game_id=2025020001)]


def test_nightly_asks_again_for_empty_charts_only_while_recent(con, tmp_path):
    shifts.run(20252026, EmptyFor({2025020001}), con, verbose=False, folder=tmp_path)
    client = FakeStats()
    shifts.run_recent(20252026, client, con, days=1, today=date(2025, 10, 9), verbose=False, folder=tmp_path)
    assert shifts.SHIFT_URL.format(game_id=2025020001) in client.urls  # 2 days old: asked again
    client = FakeStats()
    shifts.run_recent(20252026, client, con, days=1, today=date(2025, 11, 30), verbose=False, folder=tmp_path)
    assert shifts.SHIFT_URL.format(game_id=2025020001) not in client.urls  # weeks old: left for a whole-season run


REPORT_TABLE = f"raw.{shifts.REPORT_TABLE}"


def test_report_urls():
    assert shifts.report_url(20262027, 2026020154, "TH") == "https://www.nhl.com/scores/htmlreports/20262027/TH020154.HTM"


def test_an_empty_chart_is_filled_from_both_html_reports(con, tmp_path):
    counts = shifts.run(20252026, EmptyFor({2025020001}), con, verbose=False, folder=tmp_path)
    assert counts[shifts.REPORT_TABLE] == [2, 2]
    rows = con.execute(f"select game_id, source_url, body from {REPORT_TABLE} order by source_url").fetchall()
    assert [(g, u) for g, u, _ in rows] == [
        (2025020001, shifts.report_url(20252026, 2025020001, "TH")),
        (2025020001, shifts.report_url(20252026, 2025020001, "TV"))]
    assert rows[0][2].startswith("<html>")  # stored exactly as received


def test_a_game_filled_from_reports_is_not_asked_for_again(con, tmp_path):
    shifts.run(20252026, EmptyFor({2025020001}), con, verbose=False, folder=tmp_path)
    client = EmptyFor({2025020001})
    assert shifts.run(20252026, client, con, verbose=False, folder=tmp_path)[shifts.REPORT_TABLE] == [0, 0]
    assert client.html_urls == []


def test_an_unpublished_report_is_skipped_and_asked_for_on_the_next_run(con, tmp_path):
    th = shifts.report_url(20252026, 2025020001, "TH")
    client = EmptyFor({2025020001})
    client.unpublished = {th}
    assert shifts.run(20252026, client, con, verbose=False, folder=tmp_path)[shifts.REPORT_TABLE] == [2, 1]
    client = EmptyFor({2025020001})
    assert shifts.run(20252026, client, con, verbose=False, folder=tmp_path)[shifts.REPORT_TABLE] == [2, 1]


class GoalMarkersOnlyFor(FakeStats):
    """Shift charts as FakeStats, except a chart holding one goal marker and no shifts for the given games."""

    def __init__(self, games):
        super().__init__()
        self.games = games

    def fetch(self, url):
        body = super().fetch(url)
        game_id = int(url.rsplit("=", 1)[1])
        marker = {"data": [{"id": game_id * 10, "gameId": game_id, "typeCode": 505}], "total": 1}
        return json.dumps(marker) if game_id in self.games else body


def test_a_chart_with_goal_markers_only_is_filled_from_the_reports(con, tmp_path):
    client = GoalMarkersOnlyFor({2025020001})
    assert shifts.run(20252026, client, con, verbose=False, folder=tmp_path)[shifts.REPORT_TABLE] == [2, 2]
    assert {url.rsplit("/", 1)[1] for url in client.html_urls} == {"TH020001.HTM", "TV020001.HTM"}


def test_games_with_a_chart_never_ask_for_reports(con, tmp_path):
    client = FakeStats()
    shifts.run(20252026, client, con, verbose=False, folder=tmp_path)
    assert client.html_urls == []


# Option A: raw keeps only the season in progress; older seasons live in staging, fct_shifts and the laptop files.

from ingest import prune_shifts  # noqa: E402


def build_staging(con):
    """Stand in for dbt: staging and fct_shifts copy the newest load of every game in raw."""
    con.execute("create schema if not exists staging")
    con.execute("create schema if not exists marts")
    con.execute(f"""
        create or replace table staging.stg_nhl_stats__shifts as
        select game_id, season, (event ->> 'typeCode')::integer as type_code
        from {SHIFT_TABLE} qualify loaded_at = max(loaded_at) over (partition by game_id)""")
    con.execute("create or replace table marts.fct_shifts as "
                "select game_id, season from staging.stg_nhl_stats__shifts where type_code = 517")


def test_a_game_in_staging_is_not_loaded_again_after_raw_was_pruned(con, tmp_path):
    shifts.run(20252026, FakeStats(), con, verbose=False, folder=tmp_path)
    build_staging(con)
    con.execute(f"delete from {SHIFT_TABLE}")
    assert shifts.run(20252026, FakeStats(), con, verbose=False, folder=tmp_path)[shifts.SHIFT_TABLE] == [0, 0]
    assert con.execute(f"select count(*) from {SHIFT_TABLE}").fetchone()[0] == 0


def test_restore_loads_games_missing_from_staging_from_the_files_with_no_requests(con, tmp_path):
    shifts.run(20252026, FakeStats(), con, verbose=False, folder=tmp_path)
    build_staging(con)
    con.execute(f"delete from {SHIFT_TABLE}")
    con.execute("delete from staging.stg_nhl_stats__shifts where game_id = 2025020002")  # lost from staging
    assert shifts.restore(20252026, con, verbose=False, folder=tmp_path) == {
        shifts.SHIFT_TABLE: [0, 3], shifts.REPORT_TABLE: [0, 0]}
    assert con.execute(f"select distinct game_id from {SHIFT_TABLE}").fetchall() == [(2025020002,)]


def test_prune_is_a_dry_run_unless_applied(con, tmp_path):
    shifts.run(20252026, FakeStats(), con, verbose=False, folder=tmp_path)
    build_staging(con)
    assert prune_shifts.prune(con, 20262027, folder=tmp_path, verbose=False) == ([20252026], 0)
    assert con.execute(f"select count(*) from {SHIFT_TABLE}").fetchone()[0] == 6
    assert prune_shifts.prune(con, 20262027, apply=True, folder=tmp_path, verbose=False) == ([20252026], 6)
    assert con.execute(f"select count(*) from {SHIFT_TABLE}").fetchone()[0] == 0


def test_prune_keeps_the_season_in_progress(con, tmp_path):
    shifts.run(20252026, FakeStats(), con, verbose=False, folder=tmp_path)
    build_staging(con)
    assert prune_shifts.prune(con, 20252026, apply=True, folder=tmp_path, verbose=False) == ([], 0)
    assert con.execute(f"select count(*) from {SHIFT_TABLE}").fetchone()[0] == 6


@pytest.mark.parametrize("break_it", [
    "delete from staging.stg_nhl_stats__shifts where game_id = 2025020001",              # missing in staging
    "delete from staging.stg_nhl_stats__shifts where game_id = 2025020001 and rowid in "
    "(select min(rowid) from staging.stg_nhl_stats__shifts where game_id = 2025020001)",  # entries differ
    "delete from marts.fct_shifts where game_id = 2025020001",                            # missing in fct_shifts
])
def test_prune_keeps_a_season_that_is_not_complete_downstream(con, tmp_path, break_it):
    shifts.run(20252026, FakeStats(), con, verbose=False, folder=tmp_path)
    build_staging(con)
    con.execute(break_it)
    assert prune_shifts.prune(con, 20262027, apply=True, folder=tmp_path, verbose=False) == ([], 0)
    assert con.execute(f"select count(*) from {SHIFT_TABLE}").fetchone()[0] == 6


def test_prune_keeps_a_season_whose_files_are_not_on_this_computer(con, tmp_path):
    shifts.run(20252026, FakeStats(), con, verbose=False, folder=tmp_path)
    build_staging(con)
    (tmp_path / "20252026" / "2025020002.json.gz").unlink()
    assert prune_shifts.prune(con, 20262027, apply=True, folder=tmp_path, verbose=False) == ([], 0)


def test_prune_refuses_without_staging(con, tmp_path):
    shifts.run(20252026, FakeStats(), con, verbose=False, folder=tmp_path)
    with pytest.raises(RuntimeError):
        prune_shifts.prune(con, 20262027, folder=tmp_path, verbose=False)
