"""Load per-game skater stats into the raw layer.

Run one season with:   uv run python -m ingest.skater_games --season 20252026
Many seasons with:     uv run python -m ingest.backfill --job skater_games --from 20252026 --to 19171918
Nightly, recent dates: uv run python -m ingest.skater_games --season 20262027 --recent-days 3   (the 3 game dates before today)

The stats API's skater summary with isGame=true gives one row per player per game. It returns at most 10,000 rows
per request, so a season is fetched in windows of game dates. The windows come from the season's game list in
raw.nhl_stats__game (load the schedule first): each covers at most MAX_GAMES_PER_WINDOW games, about 9,000 rows.
A window that still reaches the row cap is split in half, so no rows are cut off silently.
"""

import argparse
import json
from datetime import date, timedelta

from ingest.goalies import ROW_CAP
from ingest.nhl_api import NhlApiClient
from ingest.raw_loader import connect, ensure_log, ensure_table, load_response, log_season_done
from ingest.schedule import GAME_TABLE, season_id, totals

JOB = "skater_games"

STATS_API = "https://api.nhle.com/stats/rest/en"
SKATER_GAME_TABLE = "nhl_stats__skater_game"

# Regular season and playoffs.
GAME_TYPES = (2, 3)

# At most 40 skaters dress per game, so 225 games stay under 9,000 rows, well below the 10,000-row cap.
MAX_GAMES_PER_WINDOW = 225


def window_url(season, game_type, first_day, last_day):
    return (
        f"{STATS_API}/skater/summary?isAggregate=false&isGame=true&start=0&limit=-1"
        f'&cayenneExp=seasonId={season} and gameTypeId={game_type}'
        f' and gameDate>="{first_day.isoformat()}" and gameDate<="{last_day.isoformat()}"'
    )


def games_per_date(con, season, game_type):
    """{date: number of games} from the newest game list stored for the season."""
    ensure_table(con, GAME_TABLE)
    rows = con.execute(
        f"""
        with latest as (
            select payload from raw.{GAME_TABLE} where season = ? order by loaded_at desc limit 1
        )
        select (game ->> 'gameDate')[1:10] as game_date, count(*)
        from (select unnest(json_extract(payload, '$.data[*]')) as game from latest)
        where (game ->> 'gameType')::integer = ?
        group by 1 order by 1
        """,
        [season, game_type],
    ).fetchall()
    return {date.fromisoformat(day): games for day, games in rows}


def date_windows(games_by_date, max_games=MAX_GAMES_PER_WINDOW):
    """Consecutive (first_day, last_day) windows, each with at most max_games games (a busier single day stands alone)."""
    windows, start, last, count = [], None, None, 0
    for day in sorted(games_by_date):
        games = games_by_date[day]
        if start is not None and count + games > max_games:
            windows.append((start, last))
            start, count = None, 0
        if start is None:
            start = day
        last, count = day, count + games
    if start is not None:
        windows.append((start, last))
    return windows


def fetch_window(client, season, game_type, first_day, last_day):
    """[(url, body)] for one window, split in half while a response reaches the row cap."""
    url = window_url(season, game_type, first_day, last_day)
    body = client.fetch(url)
    if json.loads(body)["total"] < ROW_CAP:
        return [(url, body)]
    if first_day == last_day:
        raise RuntimeError(f"{ROW_CAP} or more skater rows on the single date {first_day} at {url}")
    middle = first_day + timedelta(days=(last_day - first_day).days // 2)
    return (fetch_window(client, season, game_type, first_day, middle)
            + fetch_window(client, season, game_type, middle + timedelta(days=1), last_day))


def load_windows(season, client, con, windows_by_type, verbose):
    counts = {SKATER_GAME_TABLE: [0, 0]}
    ensure_table(con, SKATER_GAME_TABLE)
    for game_type, windows in windows_by_type.items():
        for first_day, last_day in windows:
            for url, body in fetch_window(client, season, game_type, first_day, last_day):
                added = load_response(con, SKATER_GAME_TABLE, url, season, body)
                counts[SKATER_GAME_TABLE][0] += 1
                counts[SKATER_GAME_TABLE][1] += added
                if verbose:
                    # Counts and dates only, never response content.
                    print(f"  {'new      ' if added else 'unchanged'}  {season} type {game_type} {first_day} to {last_day}")
    return counts


def run(season, client, con, verbose=True):
    """Fetch and store a whole season, regular season and playoffs. Returns {table: [fetched, added]}."""
    windows = {t: date_windows(games_per_date(con, season, t)) for t in GAME_TYPES}
    return load_windows(season, client, con, windows, verbose)


def run_recent(season, client, con, days, today=None, verbose=True):
    """Fetch the season's last `days` game dates before today, one date per request.

    Today's own games are left out: when the daily run starts (11:00 UTC) they have not been played yet.
    """
    today = today or date.today()
    windows = {}
    for game_type in GAME_TYPES:
        recent = [d for d in sorted(games_per_date(con, season, game_type)) if d < today][-days:]
        windows[game_type] = [(d, d) for d in recent]
    return load_windows(season, client, con, windows, verbose)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--season", type=season_id, required=True, help="for example 20252026")
    parser.add_argument("--recent-days", type=int, help="only the season's last N game dates up to today")
    args = parser.parse_args()

    con = connect()
    client = NhlApiClient()
    try:
        if args.recent_days:
            counts = run_recent(args.season, client, con, args.recent_days)
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
