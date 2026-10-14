"""Load per-game goalie stats for one season, and the official team season totals, into the raw layer.

Run one season with:   uv run python -m ingest.goalies --season 20252026
Many seasons with:     uv run python -m ingest.backfill --job goalies --from 20262027 --to 19171918
Team season totals:    uv run python -m ingest.goalies --team-seasons
"""

import argparse
import json

from ingest.nhl_api import NhlApiClient
from ingest.raw_loader import connect, ensure_log, ensure_table, load_response, log_season_done
from ingest.schedule import season_id, totals

JOB = "goalie_games"

STATS_API = "https://api.nhle.com/stats/rest/en"
GOALIE_TABLE = "nhl_stats__goalie_game"
TEAM_SEASON_TABLE = "nhl_stats__team_season"

# Regular season and playoffs. Preseason is not needed for the goalie questions.
GAME_TYPES = (2, 3)

# The stats API returns at most this many rows per request, even with limit=-1.
ROW_CAP = 10_000

TEAM_SEASONS_URL = (
    f"{STATS_API}/team/summary?isAggregate=false&isGame=false&start=0&limit=-1&cayenneExp=gameTypeId=2"
)


class WindowTooLargeError(RuntimeError):
    """A response hit the API's row cap, so rows may be missing."""


def goalie_url(season, game_type):
    return (
        f"{STATS_API}/goalie/summary?isAggregate=false&isGame=true&start=0&limit=-1"
        f"&cayenneExp=seasonId={season} and gameTypeId={game_type}"
    )


def check_window(body, url):
    """Refuse a response that reached the row cap: the window would be cut off silently."""
    total = json.loads(body)["total"]
    if total >= ROW_CAP:
        raise WindowTooLargeError(f"{total} rows at {url}: the window must be split before loading")


def run(season, client, con, verbose=True):
    """Fetch and store one season's goalie games. Returns {table: [fetched, added]}."""
    counts = {GOALIE_TABLE: [0, 0]}
    ensure_table(con, GOALIE_TABLE)
    for game_type in GAME_TYPES:
        url = goalie_url(season, game_type)
        body = client.fetch(url)
        check_window(body, url)
        added = load_response(con, GOALIE_TABLE, url, season, body)
        counts[GOALIE_TABLE][0] += 1
        counts[GOALIE_TABLE][1] += added
        if verbose:
            # Counts only, never response content.
            print(f"  {'new      ' if added else 'unchanged'}  {season} game type {game_type}")
    return counts


def load_team_seasons(client, con):
    """Fetch and store the official regular-season totals for every team-season. Returns True if added."""
    ensure_table(con, TEAM_SEASON_TABLE, seasonal=False)
    body = client.fetch(TEAM_SEASONS_URL)
    check_window(body, TEAM_SEASONS_URL)
    added = load_response(con, TEAM_SEASON_TABLE, TEAM_SEASONS_URL, None, body)
    print(f"  {'new      ' if added else 'unchanged'}  {TEAM_SEASON_TABLE}")
    return added


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--season", type=season_id, help="for example 20252026")
    group.add_argument("--team-seasons", action="store_true", help="load the official team season totals")
    args = parser.parse_args()

    con = connect()
    client = NhlApiClient()
    try:
        if args.team_seasons:
            load_team_seasons(client, con)
        else:
            ensure_log(con)
            counts = run(args.season, client, con)
            log_season_done(con, JOB, args.season, *totals(counts))
            print(f"  requests {totals(counts)[0]}, new rows {totals(counts)[1]}")
    finally:
        client.close()
        con.close()


if __name__ == "__main__":
    main()
