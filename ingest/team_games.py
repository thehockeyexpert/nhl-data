"""Load per-game team stats (power play, penalty kill, penalties, summary) into the raw layer.

Run one season with:   uv run python -m ingest.team_games --season 20252026
Many seasons with:     uv run python -m ingest.backfill --job team_games --from 20262027 --to 19171918
Nightly, recent dates: uv run python -m ingest.team_games --season 20262027 --recent-days 3   (the 3 game dates before today)
                       A season that has never been loaded in full is loaded in full first, so a new season needs no extra step.

The stats API's team reports with isGame=true give one row per team per game. A whole season is at most about
2,700 rows, well under the 10,000-row cap, so a season is one request per report and game type (8 requests).
The nightly run asks only for the last few game dates, so a full season's JSON is not stored again every night.
Each report goes to a raw table of its own.
"""

import argparse
from datetime import date

from ingest.goalies import check_window
from ingest.nhl_api import NhlApiClient
from ingest.raw_loader import connect, ensure_log, ensure_table, is_season_done, load_response, log_season_done
from ingest.schedule import season_id, totals
from ingest.skater_games import games_per_date

JOB = "team_games"

STATS_API = "https://api.nhle.com/stats/rest/en"

# Report name in the stats API -> raw table.
REPORTS = {
    "summary": "nhl_stats__team_game_summary",
    "powerplay": "nhl_stats__team_game_powerplay",
    "penaltykill": "nhl_stats__team_game_penaltykill",
    "penalties": "nhl_stats__team_game_penalties",
}

# Regular season and playoffs.
GAME_TYPES = (2, 3)


def report_url(report, season, game_type, first_day=None, last_day=None):
    """The whole season's rows, or only those from first_day to last_day."""
    dates = ""
    if first_day is not None:
        dates = f' and gameDate>="{first_day.isoformat()}" and gameDate<="{last_day.isoformat()}"'
    return (
        f"{STATS_API}/team/{report}?isAggregate=false&isGame=true&start=0&limit=-1"
        f"&cayenneExp=seasonId={season} and gameTypeId={game_type}{dates}"
    )


def load_windows(season, client, con, windows_by_type, verbose):
    """windows_by_type: {game_type: (first_day, last_day) or None for the whole season}. Returns {table: [fetched, added]}."""
    counts = {table: [0, 0] for table in REPORTS.values()}
    for report, table in REPORTS.items():
        ensure_table(con, table)
        for game_type, window in windows_by_type.items():
            url = report_url(report, season, game_type, *(window or ()))
            body = client.fetch(url)
            check_window(body, url)
            added = load_response(con, table, url, season, body)
            counts[table][0] += 1
            counts[table][1] += added
            if verbose:
                # Counts and dates only, never response content.
                span = f"{window[0]} to {window[1]}" if window else "whole season"
                print(f"  {'new      ' if added else 'unchanged'}  {season} {report} type {game_type} {span}")
    return counts


def run(season, client, con, verbose=True):
    """Fetch and store a whole season, regular season and playoffs. Returns {table: [fetched, added]}."""
    return load_windows(season, client, con, {game_type: None for game_type in GAME_TYPES}, verbose)


def recent_windows(con, season, days, today):
    """{game_type: (first_day, last_day)} covering the season's last `days` game dates before today.

    Today's own games are left out: when the daily run starts they have not been played yet. A game type with no
    game dates yet (the playoffs during the regular season) is left out.
    """
    windows = {}
    for game_type in GAME_TYPES:
        recent = [d for d in sorted(games_per_date(con, season, game_type)) if d < today][-days:]
        if recent:
            windows[game_type] = (recent[0], recent[-1])
    return windows


def run_season(season, client, con, recent_days=None, today=None, verbose=True):
    """The last `recent_days` game dates, or the whole season if it was never loaded in full (or no recent_days)."""
    ensure_log(con)
    if recent_days and is_season_done(con, JOB, season):
        windows = recent_windows(con, season, recent_days, today or date.today())
        return load_windows(season, client, con, windows, verbose)
    if recent_days and verbose:
        print(f"  {season} has not been loaded in full yet: loading the whole season first")
    counts = run(season, client, con, verbose)
    log_season_done(con, JOB, season, *totals(counts))
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--season", type=season_id, required=True, help="for example 20252026")
    parser.add_argument("--recent-days", type=int, help="only the season's last N game dates up to today")
    args = parser.parse_args()

    con = connect()
    client = NhlApiClient()
    try:
        counts = run_season(args.season, client, con, args.recent_days)
        print(f"  requests {totals(counts)[0]}, new rows {totals(counts)[1]}")
    finally:
        client.close()
        con.close()


if __name__ == "__main__":
    main()
