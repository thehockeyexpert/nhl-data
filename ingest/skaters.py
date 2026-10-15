"""Load per-season skater totals for one season into the raw layer.

Run one season with:   uv run python -m ingest.skaters --season 20252026
Many seasons with:     uv run python -m ingest.backfill --job skaters --from 20262027 --to 19171918

The stats API's skater summary gives one row per player and season, regular season and playoffs separately.
A player who played for several teams in a season has one row, with the teams listed together (for example
"TOR,BOS"); the totals are not split by team.
"""

import argparse

from ingest.goalies import check_window
from ingest.nhl_api import NhlApiClient
from ingest.raw_loader import connect, ensure_log, ensure_table, load_response, log_season_done
from ingest.schedule import season_id, totals

JOB = "skater_seasons"

STATS_API = "https://api.nhle.com/stats/rest/en"
SKATER_TABLE = "nhl_stats__skater_season"

# Regular season and playoffs.
GAME_TYPES = (2, 3)


def skater_url(season, game_type):
    return (
        f"{STATS_API}/skater/summary?isAggregate=false&isGame=false&start=0&limit=-1"
        f"&cayenneExp=seasonId={season} and gameTypeId={game_type}"
    )


def run(season, client, con, verbose=True):
    """Fetch and store one season's skater totals. Returns {table: [fetched, added]}."""
    counts = {SKATER_TABLE: [0, 0]}
    ensure_table(con, SKATER_TABLE)
    for game_type in GAME_TYPES:
        url = skater_url(season, game_type)
        body = client.fetch(url)
        check_window(body, url)
        added = load_response(con, SKATER_TABLE, url, season, body)
        counts[SKATER_TABLE][0] += 1
        counts[SKATER_TABLE][1] += added
        if verbose:
            # Counts only, never response content.
            print(f"  {'new      ' if added else 'unchanged'}  {season} game type {game_type}")
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
