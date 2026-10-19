"""Load each season's standings into the raw layer, for every team's conference and division that season.

Run one season with:   uv run python -m ingest.standings --season 20262027
Many seasons with:     uv run python -m ingest.backfill --job standings --from 20262027 --to 19171918

The standings are taken on the season's first standings day (standingsStart in the NHL's standings-season list).
Every team is already listed that day, and a past date gives the same URL and content on every run, so the nightly
rerun adds nothing. The season's last day would keep moving while the season is in progress.
"""

import argparse
import json
import weakref

from ingest.nhl_api import NhlApiClient
from ingest.raw_loader import connect, ensure_log, ensure_table, load_response, log_season_done
from ingest.schedule import season_id, totals

JOB = "standings"

WEB_API = "https://api-web.nhle.com/v1"
SEASONS_URL = f"{WEB_API}/standings-season"
STANDINGS_TABLE = "nhl_web__standings"

# The season list is fetched once per client, so a backfill does not ask for it again for every season.
_start_dates = weakref.WeakKeyDictionary()


def standings_url(date):
    return f"{WEB_API}/standings/{date}"


def start_dates(client):
    """{season: first standings date} from the NHL's standings-season list. Not stored: ingest.records stores it."""
    if client not in _start_dates:
        seasons = json.loads(client.fetch(SEASONS_URL))["seasons"]
        _start_dates[client] = {season["id"]: season["standingsStart"] for season in seasons}
    return _start_dates[client]


def run(season, client, con, verbose=True):
    """Fetch and store one season's standings. Returns {table: [fetched, added]}."""
    counts = {STANDINGS_TABLE: [0, 0]}
    ensure_table(con, STANDINGS_TABLE)
    date = start_dates(client).get(season)
    if date is None:
        # 20042005 was not played, so the NHL lists no standings for it.
        if verbose:
            print(f"  no standings  {season}")
        return counts
    added = load_response(con, STANDINGS_TABLE, standings_url(date), season, client.fetch(standings_url(date)))
    counts[STANDINGS_TABLE] = [1, int(added)]
    if verbose:
        # Counts only, never response content.
        print(f"  {'new      ' if added else 'unchanged'}  {season}")
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--season", type=season_id, required=True, help="for example 20262027")
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
