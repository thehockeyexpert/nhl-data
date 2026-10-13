"""Load one season of NHL schedule and results into the raw layer.

Run it with:  uv run python -m ingest.schedule --season 20252026
"""

import argparse
import json
from datetime import date

from ingest.nhl_api import NhlApiClient
from ingest.raw_loader import connect, ensure_log, ensure_table, load_response, log_season_done

JOB = "schedule"

WEB_API = "https://api-web.nhle.com/v1"
STATS_API = "https://api.nhle.com/stats/rest/en"

SEASON_TABLE = "nhl_stats__season"
GAME_TABLE = "nhl_stats__game"
SCHEDULE_TABLE = "nhl_web__schedule"

# The longest season on record spans about 55 weeks. This stops a runaway loop if the API ever misbehaves.
MAX_WEEKS = 80


def season_id(text):
    """Check that a season looks like 20252026 (two consecutive years)."""
    if not (text.isdigit() and len(text) == 8 and int(text[4:]) == int(text[:4]) + 1):
        raise argparse.ArgumentTypeError(f"{text!r} is not a season ID like 20252026")
    return int(text)


def game_date_range(game_list_body):
    """First and last game date in a season's game list, or None if it lists no games.

    The game list is used rather than the season facts because the facts leave out
    preseason dates for most seasons, and one season (20042005) has no facts at all.
    """
    dates = [game["gameDate"][:10] for game in json.loads(game_list_body)["data"]]
    if not dates:
        return None
    return date.fromisoformat(min(dates)), date.fromisoformat(max(dates))


def run(season, client, con, verbose=True):
    """Fetch and store everything for one season. Returns {table: [fetched, added]}."""
    counts = {SEASON_TABLE: [0, 0], GAME_TABLE: [0, 0], SCHEDULE_TABLE: [0, 0]}
    for table in counts:
        ensure_table(con, table)

    def say(text):
        if verbose:
            print(text)

    def fetch_and_load(table, url):
        body = client.fetch(url)
        added = load_response(con, table, url, season, body)
        counts[table][0] += 1
        counts[table][1] += added
        say(f"  {'new      ' if added else 'unchanged'}  {url}")
        return body

    say("Season facts")
    season_body = fetch_and_load(SEASON_TABLE, f"{STATS_API}/season?cayenneExp=id={season}")
    if not json.loads(season_body)["data"]:
        # Not an error: the NHL has no facts for a season that was never played.
        say(f"  note: the NHL has no season facts for {season}")

    say("Game list")
    game_list_body = fetch_and_load(GAME_TABLE, f"{STATS_API}/game?cayenneExp=season={season}")
    date_range = game_date_range(game_list_body)
    if date_range is None:
        say(f"  note: the NHL lists no games for {season}")
        return counts

    # Walk the weekly schedule from the first game date to the last, following the
    # "next week" date that each response gives us. The API skips weeks without games.
    first_day, last_day = date_range
    say(f"Weekly schedule, {first_day} to {last_day}")
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


def totals(counts):
    """(requests made, new rows stored) across all tables."""
    return sum(fetched for fetched, _ in counts.values()), sum(added for _, added in counts.values())


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
    finally:
        client.close()
        con.close()

    print()
    print(f"Season {args.season} summary")
    for table, (fetched, added) in counts.items():
        print(f"  raw.{table:<20} fetched {fetched:>3}   new rows {added:>3}")
    print(f"  total new rows: {totals(counts)[1]}")


if __name__ == "__main__":
    main()
