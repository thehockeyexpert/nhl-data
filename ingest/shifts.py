"""Load player shifts from the NHL's shift charts into the raw layer (Tier 2, 2010-11 onward).

Run one season with:   uv run python -m ingest.shifts --season 20252026
Many seasons with:     uv run python -m ingest.backfill --job shifts --from 20262027 --to 20102011
Nightly (GitHub):      uv run python -m ingest.shifts --season 20262027 --recent-days 3

The same two steps as the play-by-play (decided by the owner on 2026-11-13, docs/decisions.md):
1. Download: each finished regular-season and playoff game's shift chart from the stats API is saved, exactly as
   received and gzip-compressed, outside the repo: one file per game in <folder>/<season>/<game_id>.json.gz. The
   folder is the environment variable NHL_SHIFTS_DIR, or nhl-data-files/shifts in your home folder.
2. Load: the season's shift rows are gathered on this computer into one Parquet file next to the files, then
   bulk-loaded into raw.nhl_stats__shift in a single statement, one row per entry exactly as received. A response
   already loaded is not added again.

The NHL has shift charts from 2010-11; earlier seasons are skipped with no requests.
Whole season (the laptop): every finished game whose file is not on disk yet is downloaded, so a stopped run can be
restarted; games whose chart came back empty are asked for again, in case the NHL has filled them since.
Nightly (--recent-days N): games of the last NEW_GAME_DAYS days with no shifts loaded yet, plus the last N days'
games fetched again for the NHL's corrections. Older games with an empty chart wait for a whole-season run, so the
nightly run does not ask for a long gap every night (50 games of 2026-10-22 to 29 were empty on 2026-11-13).

The fallback rule (decided by the owner on 2026-11-13): when a game's shift chart is empty, the NHL's HTML shift
reports for that game (home TH and visitor TV, nhl.com/scores/htmlreports) are fetched and stored exactly as received
in raw.nhl_html__shift_report; dbt reads the shifts from them. A report the NHL has not published (404) is skipped and
asked for again on a later run. A game already filled from its reports is not asked for again, unless it is recent.

Raw keeps only the season in progress (option A, proposed 2026-11-14, docs/decisions.md): older seasons' entries are
deleted from raw.nhl_stats__shift by `uv run python -m ingest.prune_shifts`, after checks, and live on in staging and
fct_shifts (which are never rebuilt from raw) and in the files on the laptop. So "already loaded" means in raw OR in
staging, and only games not loaded yet (or asked for again) are gathered and sent.
The way back: `uv run python -m ingest.shifts --season 20152016 --restore` loads, from the files on this computer and
with no requests, the season's games that are missing from staging; the next dbt build adds them back.

The game list comes from raw.nhl_stats__game (load the schedule first).
"""

import argparse
import gzip
import json
import os
import time
from datetime import date, timedelta
from pathlib import Path

import duckdb

from ingest.nhl_api import NhlApiClient
from ingest.play_by_play import REPO_ROOT, download, final_games
from ingest.raw_loader import (
    append_events_file, append_report, connect, ensure_events_table, ensure_log, ensure_report_table, log_season_done,
)
from ingest.schedule import season_id, totals

JOB = "shifts"

SHIFT_URL = "https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={game_id}"
SHIFT_TABLE = "nhl_stats__shift"
# Older seasons' shifts live here once raw keeps only the season in progress (option A).
STAGING_TABLE = "staging.stg_nhl_stats__shifts"
SHIFT_TYPE = 517  # a shift; 505 is a goal marker
FIRST_SEASON = 20102011
# The nightly run asks again for games with no shifts only this many days back.
NEW_GAME_DAYS = 14

# The fallback for empty shift charts: the HTML shift reports, home (TH) and visitor (TV).
REPORT_TABLE = "nhl_html__shift_report"
REPORT_URL = "https://www.nhl.com/scores/htmlreports/{season}/{side}{game_number}.HTM"
REPORT_SIDES = ("TH", "TV")


def report_url(season, game_id, side):
    """The HTML shift report of one side of a game: 2026020154 is game number 020154 of season 20262027."""
    return REPORT_URL.format(season=season, side=side, game_number=str(game_id)[4:])


def files_folder():
    """Where the compressed shift charts live. Never inside the repo: it is public and holds no NHL data."""
    folder = Path(os.environ.get("NHL_SHIFTS_DIR") or Path.home() / "nhl-data-files" / "shifts").resolve()
    if folder == REPO_ROOT or REPO_ROOT in folder.parents:
        raise RuntimeError(f"The shifts folder must be outside the repo, not {folder}")
    return folder


def season_games(con, season):
    """{game_id: game date} of the season's finished games, or nothing before the NHL kept shift charts."""
    return final_games(con, season) if season >= FIRST_SEASON else {}


def has_staging(con):
    """Whether dbt has built the shift staging table in this database yet."""
    schema, name = STAGING_TABLE.split(".")
    return con.execute(
        "select count(*) from information_schema.tables "
        "where table_catalog = current_database() and table_schema = ? and table_name = ?",
        [schema, name],
    ).fetchone()[0] > 0


def staged_games(con, season):
    """The IDs of the season's games that have shift-chart entries in staging."""
    if not has_staging(con):
        return set()
    rows = con.execute(f"select distinct game_id from {STAGING_TABLE} where season = ?", [season]).fetchall()
    return {game_id for (game_id,) in rows}


def loaded_games(con, season):
    """The IDs of the season's games that already have shifts: in the raw layer, or in staging for a season whose raw
    entries have been deleted (raw keeps only the season in progress, option A)."""
    table = ensure_events_table(con, SHIFT_TABLE)
    rows = con.execute(f"select distinct game_id from {table} where season = ?", [season]).fetchall()
    return {game_id for (game_id,) in rows} | staged_games(con, season)


def gather_shifts(season, game_ids, folder):
    """Write these games' shift rows to one local Parquet file and return its path. Runs on this computer only."""
    season_folder = folder / str(season)
    files = [str(season_folder / f"{game_id}.json.gz") for game_id in game_ids]
    parquet = season_folder / f"{SHIFT_TABLE}.parquet"
    local = duckdb.connect(":memory:")
    try:
        local.execute(
            f"""
            copy (
                with responses as (
                    select
                        regexp_extract(filename, '(\\d+)\\.json\\.gz$', 1)::bigint as game_id,
                        json as response
                    from read_json_objects(?, format = 'auto', compression = 'gzip', filename = true)
                ),
                shifts as (
                    select game_id, sha256(response::varchar) as payload_hash,
                        unnest(json_extract(response, '$.data[*]')) as event
                    from responses
                )
                select
                    replace('{SHIFT_URL}', '{{game_id}}', game_id::varchar) as source_url,
                    ?::integer as season,
                    game_id,
                    payload_hash,
                    event
                from shifts
            ) to '{str(parquet).replace("'", "''")}' (format parquet, compression zstd)
            """,
            [files, season],
        )
    finally:
        local.close()
    return parquet


def empty_charts(season, game_ids, folder):
    """The games among game_ids whose saved shift chart has no shifts (type 517). A chart holding only goal markers
    (type 505) counts as empty, as fct_shifts treats it (2013020971 has one goal marker and nothing else)."""
    season_folder = folder / str(season)
    empty = set()
    for game_id in game_ids:
        with gzip.open(season_folder / f"{game_id}.json.gz", "rt", encoding="utf-8") as file:
            entries = json.load(file).get("data") or []
            if not any(entry.get("typeCode") == SHIFT_TYPE for entry in entries):
                empty.add(game_id)
    return empty


def reported_games(con, season):
    """The games of the season with both HTML shift reports stored."""
    table = ensure_report_table(con, REPORT_TABLE)
    rows = con.execute(
        f"select game_id from {table} where season = ? group by game_id having count(distinct source_url) = ?",
        [season, len(REPORT_SIDES)],
    ).fetchall()
    return {game_id for (game_id,) in rows}


def fill_from_reports(client, con, season, game_ids, folder, verbose, refetch=()):
    """The fallback rule: store the HTML shift reports of the games whose shift chart is empty.
    Games already filled are skipped unless in refetch. Returns [requests, reports added]."""
    stored = reported_games(con, season)
    todo = sorted(g for g in empty_charts(season, game_ids, folder) if g not in stored or g in refetch)
    requests = added = missing = 0
    for game_id in todo:
        for side in REPORT_SIDES:
            url = report_url(season, game_id, side)
            body = client.fetch_html(url)
            requests += 1
            if body is None:
                missing += 1
                continue
            added += append_report(con, REPORT_TABLE, url, season, game_id, body)
    if verbose and todo:
        # Counts only, never report content.
        print(f"  {season}: {len(todo)} games with an empty shift chart; {added} HTML reports added, {missing} not published")
    return [requests, added]


def load(client, con, season, game_ids, folder, verbose, refetch=(), report_refetch=()):
    """Download what is needed of game_ids, load their shifts, then fill empty charts from the HTML reports.
    Only games not loaded yet, or asked for again (refetch), are gathered and sent: a game whose raw entries were
    deleted but which is in staging is not loaded again (option A). Returns {table: [requests, rows added]}."""
    requests = download(client, season, game_ids, folder, verbose, refetch, url=SHIFT_URL)
    loaded = loaded_games(con, season)
    to_send = [game_id for game_id in game_ids if game_id in refetch or game_id not in loaded]
    added = append_events_file(con, SHIFT_TABLE, gather_shifts(season, to_send, folder)) if to_send else 0
    reports = fill_from_reports(client, con, season, game_ids, folder, verbose, report_refetch)
    return {SHIFT_TABLE: [requests, added], REPORT_TABLE: [reports[0], reports[1]]}


def run(season, client, con, verbose=True, folder=None):
    """The whole season: download every finished game not on disk yet and load the season's shifts."""
    games = season_games(con, season)
    if not games:
        return {SHIFT_TABLE: [0, 0], REPORT_TABLE: [0, 0]}
    empty = set(games) - loaded_games(con, season)
    return load(client, con, season, sorted(games), folder or files_folder(), verbose, refetch=empty)


def run_recent(season, client, con, days, today=None, verbose=True, folder=None):
    """Recent games with no shifts loaded yet, plus the last `days` days' games fetched again. Today's games are left out."""
    folder = folder or files_folder()
    today = today or date.today()
    games = season_games(con, season)
    loaded = loaded_games(con, season)
    new = {game_id for game_id, day in games.items()
           if game_id not in loaded and today - timedelta(days=NEW_GAME_DAYS) <= day < today}
    recent = {game_id for game_id, day in games.items() if today - timedelta(days=days) <= day < today}
    if verbose:
        # Counts only, never response content.
        print(f"  {season}: {len(new)} games without shifts yet, {len(recent - new)} recent games to fetch again")
    return load(client, con, season, sorted(new | recent), folder, verbose, refetch=new | recent, report_refetch=recent)


def restore(season, con, verbose=True, folder=None):
    """The way back (option A): load into raw again, from the files on this computer and with no requests, the
    season's games that have a file on disk but no entries in staging. Games still in staging are left alone, so a
    correction fetched later by the nightly run is not replaced by an older file. The next dbt build of
    stg_nhl_stats__shifts and fct_shifts adds them back. Returns {table: [requests, rows added]}."""
    folder = folder or files_folder()
    staged = staged_games(con, season)
    season_folder = folder / str(season)
    to_send = sorted(game_id for game_id in season_games(con, season)
                     if game_id not in staged and (season_folder / f"{game_id}.json.gz").exists())
    added = append_events_file(con, SHIFT_TABLE, gather_shifts(season, to_send, folder)) if to_send else 0
    if verbose:
        # Counts only, never file content.
        print(f"  {season}: {len(to_send)} games restored from files on disk, {added} rows added to raw")
    return {SHIFT_TABLE: [0, added], REPORT_TABLE: [0, 0]}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--season", type=season_id, required=True, help="for example 20252026")
    parser.add_argument("--recent-days", type=int, help="nightly: new games, plus the last N days' games fetched again")
    parser.add_argument("--restore", action="store_true",
                        help="the way back: load the season's games missing from staging from the files on disk, no requests")
    args = parser.parse_args()

    started = time.monotonic()
    con = connect()
    client = NhlApiClient()
    try:
        if args.restore:
            counts = restore(args.season, con)
        elif args.recent_days:
            counts = run_recent(args.season, client, con, args.recent_days)
        else:
            ensure_log(con)
            counts = run(args.season, client, con)
            log_season_done(con, JOB, args.season, *totals(counts))
        requests, added = counts[SHIFT_TABLE]
        report_requests, reports = counts[REPORT_TABLE]
        print(f"  requests {requests + report_requests}, new shift rows {added}, new HTML reports {reports}, "
              f"{time.monotonic() - started:.0f} s")
    finally:
        client.close()
        con.close()


if __name__ == "__main__":
    main()
