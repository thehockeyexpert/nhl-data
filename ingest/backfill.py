"""Load many seasons of schedule and results, newest first.

Run it with:  uv run python -m ingest.backfill --from 20242025 --to 19171918

Safe to stop (Ctrl+C) and restart with the same command: seasons that already
finished are skipped without any requests, and a half-finished season is redone
from its start without storing anything twice.
"""

import argparse
import sys
import time

from ingest.nhl_api import NhlApiClient, NhlApiError
from ingest.raw_loader import connect, ensure_log, is_season_done, log_season_done
from ingest.schedule import JOB, run, season_id, totals


def seasons_between(newest, oldest):
    """Every season ID from newest down to oldest, e.g. 20242025, 20232024, ..."""
    if oldest > newest:
        raise ValueError("--from must be the newer season and --to the older one")
    return [year * 10000 + year + 1 for year in range(newest // 10000, oldest // 10000 - 1, -1)]


def season_list(text):
    return [season_id(part.strip()) for part in text.split(",") if part.strip()]


def backfill(seasons, client, con, force=False, clock=time.monotonic):
    """Load each season in order. Returns (seasons loaded, seasons skipped, requests made)."""
    ensure_log(con)
    started = clock()
    loaded = skipped = requests = 0
    for position, season in enumerate(seasons, start=1):
        prefix = f"[{position:>3}/{len(seasons)}] {season}"
        if not force and is_season_done(con, JOB, season):
            skipped += 1
            print(f"{prefix}  already loaded, skipped")
            continue
        print(f"{prefix}  loading...", flush=True)
        counts = run(season, client, con, verbose=False)
        season_requests, season_new_rows = totals(counts)
        log_season_done(con, JOB, season, season_requests, season_new_rows)
        loaded += 1
        requests += season_requests
        minutes = (clock() - started) / 60
        print(
            f"{prefix}  done: {season_requests} requests, {season_new_rows} new rows "
            f"({requests} requests in {minutes:.1f} min so far)",
            flush=True,
        )
    return loaded, skipped, requests


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from", dest="newest", type=season_id, help="newest season, for example 20242025")
    parser.add_argument("--to", dest="oldest", type=season_id, help="oldest season, for example 19171918")
    parser.add_argument("--seasons", type=season_list, help="a comma-separated list instead of a range")
    parser.add_argument("--force", action="store_true", help="reload seasons even if already loaded")
    args = parser.parse_args()

    if args.seasons and not (args.newest or args.oldest):
        seasons = args.seasons
    elif args.newest and args.oldest and not args.seasons:
        seasons = seasons_between(args.newest, args.oldest)
    else:
        parser.error("give either --from and --to, or --seasons")

    con = connect()
    client = NhlApiClient()
    try:
        loaded, skipped, requests = backfill(seasons, client, con, force=args.force)
    except KeyboardInterrupt:
        print("\nStopped. Nothing is lost: run the same command again to carry on where it left off.")
        sys.exit(130)
    except NhlApiError as error:
        print(f"\nStopped because of a problem talking to the NHL: {error}")
        print("Run the same command again to carry on where it left off.")
        sys.exit(1)
    finally:
        client.close()
        con.close()

    print()
    print(f"Finished: {loaded} seasons loaded, {skipped} skipped, {requests} requests.")


if __name__ == "__main__":
    main()
