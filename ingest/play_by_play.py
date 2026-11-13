"""Load shot events from play-by-play into the raw layer (Tier 2, 1917-18 onward).

Run one season with:   uv run python -m ingest.play_by_play --season 20252026
Many seasons with:     uv run python -m ingest.backfill --job play_by_play --from 20252026 --to 19171918
Nightly (GitHub):      uv run python -m ingest.play_by_play --season 20262027 --recent-days 3

Two steps, decided by the owner on 2026-11-10 (docs/decisions.md):
1. Download: each finished regular-season and playoff game's play-by-play is saved, exactly as received and
   gzip-compressed, outside the repo: one file per game in <folder>/<season>/<game_id>.json.gz.
   The folder is the environment variable NHL_PBP_DIR, or nhl-data-files/play_by_play in your home folder.
2. Load: the shot events (shots on goal, missed shots, blocked shots, goals) of the season's files are gathered on
   this computer into one Parquet file next to them, then bulk-loaded into raw.nhl_web__pbp_shot in a single
   statement; hits and penalties go the same way into raw.nhl_web__pbp_event (decided 2026-11-11). Everything else
   stays in the files. A response already loaded is not added again.

Whole season (the laptop): every finished game whose file is not on disk yet is downloaded, so a stopped run can be
restarted, and a rerun fills the local archive with games the nightly run loaded.
Nightly (--recent-days N, the daily run on GitHub, whose folder is deleted after the run): only games not yet in
raw.nhl_web__pbp_shot, plus the games of the last N days before today fetched again so the NHL's corrections are
picked up. A corrected game replaces its earlier shots in staging.

The game list comes from raw.nhl_stats__game (load the schedule first).
"""

import argparse
import gzip
import os
import time
from datetime import date, timedelta
from pathlib import Path

import duckdb

from ingest.nhl_api import NhlApiClient
from ingest.raw_loader import (
    append_events_file, connect, ensure_events_table, ensure_log, ensure_table, log_season_done,
)
from ingest.schedule import GAME_TABLE, season_id

JOB = "play_by_play"

PBP_URL = "https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
SHOT_TABLE = "nhl_web__pbp_shot"
SHOT_EVENTS = ("shot-on-goal", "missed-shot", "blocked-shot", "goal")
EVENT_TABLE = "nhl_web__pbp_event"
OTHER_EVENTS = ("hit", "penalty")  # loaded into EVENT_TABLE

# Regular season and playoffs.
GAME_TYPES = (2, 3)

REPO_ROOT = Path(__file__).resolve().parent.parent


def files_folder():
    """Where the compressed play-by-play files live. Never inside the repo: it is public and holds no NHL data."""
    folder = Path(os.environ.get("NHL_PBP_DIR") or Path.home() / "nhl-data-files" / "play_by_play").resolve()
    if folder == REPO_ROOT or REPO_ROOT in folder.parents:
        raise RuntimeError(f"The play-by-play folder must be outside the repo, not {folder}")
    return folder


def final_games(con, season):
    """{game_id: game date} of the season's finished regular-season and playoff games, from the newest game list."""
    ensure_table(con, GAME_TABLE)
    rows = con.execute(
        f"""
        with latest as (
            select payload from raw.{GAME_TABLE} where season = ? order by loaded_at desc limit 1
        ),
        games as (
            select unnest(json_extract(payload, '$.data[*]')) as game from latest
        )
        select (game ->> 'id')::bigint, (game ->> 'gameDate')[1:10]
        from games
        where (game ->> 'gameType')::integer in {GAME_TYPES}
          -- Finished, as in stg_nhl_stats__games: "if necessary" playoff games never played are left out.
          and (game ->> 'gameStateId')::integer in (6, 7)
          and (game ->> 'period') is not null
        order by 1
        """,
        [season],
    ).fetchall()
    return {game_id: date.fromisoformat(day) for game_id, day in rows}


def loaded_games(con, season):
    """The IDs of the season's games that already have shots in the raw layer."""
    table = ensure_events_table(con, SHOT_TABLE)
    rows = con.execute(f"select distinct game_id from {table} where season = ?", [season]).fetchall()
    return {game_id for (game_id,) in rows}


def download(client, season, game_ids, folder, verbose=True, refetch=()):
    """Save each game's play-by-play that is not on disk yet, or is in refetch. Returns the number of requests made."""
    season_folder = folder / str(season)
    season_folder.mkdir(parents=True, exist_ok=True)
    requests = 0
    for position, game_id in enumerate(game_ids, start=1):
        path = season_folder / f"{game_id}.json.gz"
        if path.exists() and game_id not in refetch:
            continue
        body = client.fetch(PBP_URL.format(game_id=game_id))
        requests += 1
        # Written under a temporary name first, so a stopped run never leaves a cut-off file behind.
        partial = path.with_suffix(".partial")
        with gzip.open(partial, "wt", encoding="utf-8") as file:
            file.write(body)
        partial.replace(path)
        if verbose and requests % 100 == 0:
            # Counts only, never response content.
            print(f"  {season}: {requests} downloaded, game {position} of {len(game_ids)}", flush=True)
    return requests


def gather_shots(season, game_ids, folder):
    """Write these games' shot events to one local Parquet file and return its path. Runs on this computer only."""
    return gather_events(season, game_ids, folder, SHOT_TABLE, SHOT_EVENTS)


def gather_events(season, game_ids, folder, table, kinds):
    """Write these games' events of the given kinds to one local Parquet file and return its path (this computer only)."""
    season_folder = folder / str(season)
    files = [str(season_folder / f"{game_id}.json.gz") for game_id in game_ids]
    parquet = season_folder / f"{table}.parquet"
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
                events as (
                    select game_id, sha256(response::varchar) as payload_hash,
                        unnest(json_extract(response, '$.plays[*]')) as event
                    from responses
                )
                select
                    replace('{PBP_URL}', '{{game_id}}', game_id::varchar) as source_url,
                    ?::integer as season,
                    game_id,
                    payload_hash,
                    event
                from events
                where event ->> 'typeDescKey' in {kinds}
            ) to '{str(parquet).replace("'", "''")}' (format parquet, compression zstd)
            """,
            [files, season],
        )
    finally:
        local.close()
    return parquet


def load(client, con, season, game_ids, folder, verbose, refetch=()):
    """Download what is needed of game_ids, then load their shots, hits and penalties.
    Returns {table: [requests, rows added]}; the requests are counted once, under the shot table."""
    requests = download(client, season, game_ids, folder, verbose, refetch)
    added = events = 0
    if game_ids:
        added = append_events_file(con, SHOT_TABLE, gather_shots(season, game_ids, folder))
        events = append_events_file(con, EVENT_TABLE, gather_events(season, game_ids, folder, EVENT_TABLE, OTHER_EVENTS))
    return {SHOT_TABLE: [requests, added], EVENT_TABLE: [0, events]}


def run(season, client, con, verbose=True, folder=None):
    """The whole season: download every finished game not on disk yet and load the season's shots."""
    folder = folder or files_folder()
    return load(client, con, season, sorted(final_games(con, season)), folder, verbose)


def run_recent(season, client, con, days, today=None, verbose=True, folder=None):
    """Games not yet loaded, plus the last `days` days' games fetched again. Today's games are left out."""
    folder = folder or files_folder()
    today = today or date.today()
    games = final_games(con, season)
    loaded = loaded_games(con, season)
    new = {game_id for game_id in games if game_id not in loaded}
    recent = {game_id for game_id, day in games.items() if today - timedelta(days=days) <= day < today}
    if verbose:
        # Counts only, never response content.
        print(f"  {season}: {len(new)} games not loaded yet, {len(recent - new)} recent games to fetch again")
    return load(client, con, season, sorted(new | recent), folder, verbose, refetch=recent)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--season", type=season_id, required=True, help="for example 20252026")
    parser.add_argument("--recent-days", type=int, help="nightly: new games, plus the last N days' games fetched again")
    args = parser.parse_args()

    started = time.monotonic()
    con = connect()
    client = NhlApiClient()
    try:
        if args.recent_days:
            counts = run_recent(args.season, client, con, args.recent_days)
        else:
            ensure_log(con)
            counts = run(args.season, client, con)
        requests, added = counts[SHOT_TABLE]
        events = counts[EVENT_TABLE][1]
        if not args.recent_days:
            log_season_done(con, JOB, args.season, requests, added + events)
        print(f"  requests {requests}, new shot rows {added}, new hit and penalty rows {events}, "
              f"{time.monotonic() - started:.0f} s")
    finally:
        client.close()
        con.close()


if __name__ == "__main__":
    main()
