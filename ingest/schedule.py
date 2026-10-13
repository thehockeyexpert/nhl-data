"""Load one season of NHL schedule and results into the raw layer.

Run it with:  uv run python -m ingest.schedule --season 20252026
"""

import argparse
import json
from datetime import date

from ingest.nhl_api import NhlApiClient
from ingest.raw_loader import connect, ensure_table, load_response

WEB_API = "https://api-web.nhle.com/v1"
STATS_API = "https://api.nhle.com/stats/rest/en"

SEASON_TABLE = "nhl_stats__season"
GAME_TABLE = "nhl_stats__game"
SCHEDULE_TABLE = "nhl_web__schedule"

# A season is about 40 weeks. This stops a runaway loop if the API ever misbehaves.
MAX_WEEKS = 80


def season_id(text):
    """Check that a season looks like 20252026 (two consecutive years)."""
    if not (text.isdigit() and len(text) == 8 and int(text[4:]) == int(text[:4]) + 1):
        raise argparse.ArgumentTypeError(f"{text!r} is not a season ID like 20252026")
    return int(text)


def season_date_range(season_body, season):
    """Read the first and last day of the season from the season facts response."""
    rows = json.loads(season_body)["data"]
    if len(rows) != 1:
        raise RuntimeError(f"Expected one season record for {season}, got {len(rows)}")
    facts = rows[0]
    first = facts.get("preseasonStartdate") or facts["startDate"]
    return date.fromisoformat(first[:10]), date.fromisoformat(facts["endDate"][:10])


def run(season, client, con):
    """Fetch and store everything for one season. Returns {table: [fetched, added]}."""
    counts = {SEASON_TABLE: [0, 0], GAME_TABLE: [0, 0], SCHEDULE_TABLE: [0, 0]}
    for table in counts:
        ensure_table(con, table)

    def fetch_and_load(table, url):
        body = client.fetch(url)
        added = load_response(con, table, url, season, body)
        counts[table][0] += 1
        counts[table][1] += added
        print(f"  {'new      ' if added else 'unchanged'}  {url}")
        return body

    print("Season facts")
    season_body = fetch_and_load(SEASON_TABLE, f"{STATS_API}/season?cayenneExp=id={season}")
    print("Game list")
    fetch_and_load(GAME_TABLE, f"{STATS_API}/game?cayenneExp=season={season}")

    # Walk the weekly schedule from the first day of the season to the last,
    # following the "next week" date that each response gives us.
    first_day, last_day = season_date_range(season_body, season)
    print(f"Weekly schedule, {first_day} to {last_day}")
    week_start = first_day
    for _ in range(MAX_WEEKS):
        body = fetch_and_load(SCHEDULE_TABLE, f"{WEB_API}/schedule/{week_start}")
        next_start = json.loads(body).get("nextStartDate")
        if not next_start:
            break
        next_start = date.fromisoformat(next_start)
        if next_start <= week_start or next_start > last_day:
            break
        week_start = next_start
    else:
        raise RuntimeError(f"Schedule walk did not finish within {MAX_WEEKS} weeks")

    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--season", type=season_id, required=True, help="for example 20252026")
    args = parser.parse_args()

    con = connect()
    client = NhlApiClient()
    try:
        counts = run(args.season, client, con)
    finally:
        client.close()
        con.close()

    print()
    print(f"Season {args.season} summary")
    for table, (fetched, added) in counts.items():
        print(f"  raw.{table:<20} fetched {fetched:>3}   new rows {added:>3}")
    print(f"  total new rows: {sum(added for _, added in counts.values())}")


if __name__ == "__main__":
    main()
