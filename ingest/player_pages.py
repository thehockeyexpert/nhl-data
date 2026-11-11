"""Load every player's season-by-season record in every league (the NHL's player pages) into the raw layer.

Run with:        uv run python -m ingest.player_pages
A trial first:   uv run python -m ingest.player_pages --limit 50

Two steps, like play-by-play (docs/decisions.md, 2026-11-11):
1. Download: the player page of everyone in the NHL's player list (raw.nhl_records__player) is saved, exactly as
   received and gzip-compressed, outside the repo: one file per player, <folder>/<player_id>.json.gz. The folder is
   the environment variable NHL_PLAYER_DIR, or nhl-data-files/player_pages in your home folder. A player with no page
   (HTTP 404) gets an empty <player_id>.missing file, so a rerun doesn't ask again.
2. Load: each page's season totals (one entry per season, league and team: junior, college, minor and major pro,
   international tournaments, NHL) are gathered on this computer into one Parquet file, then bulk-loaded into
   raw.nhl_web__player_season_total in a single statement. The rest of each page stays in the files.

Every file already on disk is skipped, so a stopped run is restarted with the same command. --refresh fetches every
page again (careers change; nothing runs this nightly).
"""

import argparse
import gzip
import os
import time
from pathlib import Path

import duckdb

from ingest.nhl_api import NhlApiClient, NhlApiError
from ingest.raw_loader import append_player_rows_file, connect, ensure_table

PAGE_URL = "https://api-web.nhle.com/v1/player/{player_id}/landing"
PLAYER_LIST_TABLE = "nhl_records__player"
SEASON_TOTAL_TABLE = "nhl_web__player_season_total"

REPO_ROOT = Path(__file__).resolve().parent.parent


def files_folder():
    """Where the compressed player pages live. Never inside the repo: it is public and holds no NHL data."""
    folder = Path(os.environ.get("NHL_PLAYER_DIR") or Path.home() / "nhl-data-files" / "player_pages").resolve()
    if folder == REPO_ROOT or REPO_ROOT in folder.parents:
        raise RuntimeError(f"The player pages folder must be outside the repo, not {folder}")
    return folder


def player_ids(con):
    """Every player ID in the newest player list, in order."""
    ensure_table(con, PLAYER_LIST_TABLE, seasonal=False)
    rows = con.execute(
        f"""
        with latest as (select payload from raw.{PLAYER_LIST_TABLE} order by loaded_at desc limit 1),
        players as (select unnest(json_extract(payload, '$.data[*]')) as player from latest)
        select distinct (player ->> 'id')::bigint from players order by 1
        """
    ).fetchall()
    return [player_id for (player_id,) in rows]


def download(client, ids, folder, verbose=True, refresh=False, clock=time.monotonic):
    """Save each player's page not on disk yet (all of them with refresh). Returns (requests, missing pages)."""
    folder.mkdir(parents=True, exist_ok=True)
    requests = missing = 0
    started = clock()
    for position, player_id in enumerate(ids, start=1):
        path = folder / f"{player_id}.json.gz"
        marker = folder / f"{player_id}.missing"
        if not refresh and (path.exists() or marker.exists()):
            continue
        requests += 1
        try:
            body = client.fetch(PAGE_URL.format(player_id=player_id))
        except NhlApiError as error:
            if "HTTP 404" not in str(error):
                raise
            marker.touch()
            missing += 1
            continue
        # Written under a temporary name first, so a stopped run never leaves a cut-off file behind.
        partial = path.with_suffix(".partial")
        with gzip.open(partial, "wt", encoding="utf-8") as file:
            file.write(body)
        partial.replace(path)
        marker.unlink(missing_ok=True)
        if verbose and requests % 500 == 0:
            # Counts only, never response content.
            minutes = (clock() - started) / 60
            print(f"  {requests} downloaded ({missing} without a page), player {position:,} of {len(ids):,}, "
                  f"{minutes:.0f} min", flush=True)
    return requests, missing


def gather_season_totals(ids, folder):
    """Write these players' season-total entries to one local Parquet file and return its path (this computer only)."""
    files = [str(folder / f"{player_id}.json.gz") for player_id in ids if (folder / f"{player_id}.json.gz").exists()]
    parquet = folder / f"{SEASON_TOTAL_TABLE}.parquet"
    local = duckdb.connect(":memory:")
    try:
        local.execute(
            f"""
            copy (
                with responses as (
                    select
                        regexp_extract(filename, '(\\d+)\\.json\\.gz$', 1)::bigint as player_id,
                        json as response
                    from read_json_objects(?, format = 'auto', compression = 'gzip', filename = true)
                ),
                entries as (
                    select player_id, sha256(response::varchar) as payload_hash,
                        unnest(json_extract(response, '$.seasonTotals[*]')) as entry
                    from responses
                )
                select
                    replace('{PAGE_URL}', '{{player_id}}', player_id::varchar) as source_url,
                    player_id,
                    payload_hash,
                    entry
                from entries
            ) to '{str(parquet).replace("'", "''")}' (format parquet, compression zstd)
            """,
            [files],
        )
    finally:
        local.close()
    return parquet, len(files)


def run(client, con, verbose=True, folder=None, limit=None, refresh=False):
    """Download the pages, then load their season totals. Returns (requests, missing pages, pages, rows added)."""
    folder = folder or files_folder()
    ids = player_ids(con)[:limit] if limit else player_ids(con)
    if verbose:
        print(f"  {len(ids):,} players in the list", flush=True)
    requests, missing = download(client, ids, folder, verbose, refresh)
    parquet, pages = gather_season_totals(ids, folder)
    added = append_player_rows_file(con, SEASON_TOTAL_TABLE, parquet) if pages else 0
    return requests, missing, pages, added


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, help="only the first N players of the list (a trial run)")
    parser.add_argument("--refresh", action="store_true", help="fetch every page again, even if it is on disk")
    args = parser.parse_args()

    started = time.monotonic()
    con = connect()
    client = NhlApiClient()
    try:
        requests, missing, pages, added = run(client, con, limit=args.limit, refresh=args.refresh)
        print(f"  requests {requests:,}, pages {pages:,}, without a page {missing:,}, "
              f"new rows {added:,}, {(time.monotonic() - started) / 60:.0f} min")
    finally:
        client.close()
        con.close()


if __name__ == "__main__":
    main()
