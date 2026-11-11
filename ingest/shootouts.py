"""Load one season's shootout totals per skater into the raw layer.

Run one season with:   uv run python -m ingest.shootouts --season 20252026
Many seasons with:     uv run python -m ingest.backfill --job shootouts --from 20262027 --to 20052006

The stats API's skater shootout report gives one row per player and season: shootout attempts, goals and
game-deciding goals. Shootouts began in 2005-06 and happen only in the regular season, so earlier seasons and
playoffs have nothing to load.
"""

import argparse

from ingest.goalies import check_window
from ingest.nhl_api import NhlApiClient
from ingest.raw_loader import connect, ensure_log, ensure_table, load_response, log_season_done
from ingest.schedule import season_id, totals

JOB = "skater_shootouts"

STATS_API = "https://api.nhle.com/stats/rest/en"
SHOOTOUT_TABLE = "nhl_stats__skater_shootout"

FIRST_SHOOTOUT_SEASON = 20052006


def shootout_url(season):
    return (
        f"{STATS_API}/skater/shootout?isAggregate=false&isGame=false&start=0&limit=-1"
        f"&cayenneExp=seasonId={season} and gameTypeId=2"
    )


def run(season, client, con, verbose=True):
    """Fetch and store one season's shootout totals. Returns {table: [fetched, added]}."""
    counts = {SHOOTOUT_TABLE: [0, 0]}
    if season < FIRST_SHOOTOUT_SEASON:
        if verbose:
            print(f"  skipped  {season}: no shootouts before 2005-06")
        return counts
    ensure_table(con, SHOOTOUT_TABLE)
    url = shootout_url(season)
    body = client.fetch(url)
    check_window(body, url)
    added = load_response(con, SHOOTOUT_TABLE, url, season, body)
    counts[SHOOTOUT_TABLE] = [1, added]
    if verbose:
        # Counts only, never response content.
        print(f"  {'new      ' if added else 'unchanged'}  {season} regular season")
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--season", type=season_id, required=True, help="for example 20252026")
    args = parser.parse_args()

    con = connect()
    client = NhlApiClient()
    try:
        ensure_log(con)
        counts = run(args.season, client, con)
        log_season_done(con, JOB, args.season, *totals(counts))
        print(f"  requests {totals(counts)[0]}, new rows {totals(counts)[1]}")
    finally:
        client.close()
        con.close()


if __name__ == "__main__":
    main()
