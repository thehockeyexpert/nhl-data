"""Keep only the season in progress in raw.nhl_stats__shift (option A, docs/decisions.md).

Check what would be deleted (the default; changes nothing):  uv run python -m ingest.prune_shifts --keep 20262027
Delete the seasons that pass every check:                    uv run python -m ingest.prune_shifts --keep 20262027 --apply

Run on the laptop, where the full shift charts are saved (NHL_SHIFTS_DIR). Once a year, after a season has finished
and the daily run has moved to the new season. Every season before --keep that is still in raw is checked, and is
deleted only if all three hold:
1. staging has it all: every game in raw has entries in stg_nhl_stats__shifts, and the same number of entries as its
   newest load in raw;
2. fct_shifts has it: every game with shifts (type 517) in staging has rows in fct_shifts;
3. the way back exists: every game in raw has its compressed shift chart on this computer, so
   `uv run python -m ingest.shifts --season <season> --restore` can bring it back.
A season that fails a check is kept and reported. Output is counts only, never shift content.
"""

import argparse
import time

from ingest.raw_loader import connect, delete_seasons, ensure_events_table
from ingest.schedule import season_id
from ingest.shifts import SHIFT_TABLE, SHIFT_TYPE, STAGING_TABLE, files_folder, has_staging

MART_TABLE = "marts.fct_shifts"


def season_checks(con, keep, folder):
    """{season: {games, rows, missing_in_staging, count_mismatch, missing_in_mart, missing_files}} for every season
    before `keep` still in raw. A season may be deleted only when the last four are all 0."""
    raw = ensure_events_table(con, SHIFT_TABLE)
    if not has_staging(con):
        raise RuntimeError(f"{STAGING_TABLE} does not exist: nothing may be deleted from raw")
    games = con.execute(
        f"""
        with newest as (
            select season, game_id, count(*) as entries
            from {raw}
            where season < ?
            group by season, game_id, loaded_at
            qualify loaded_at = max(loaded_at) over (partition by game_id)
        ),
        totals as (select season, count(*) as rows from {raw} where season < ? group by season),
        staged as (select game_id, count(*) as entries from {STAGING_TABLE} where season < ? group by game_id),
        staged_shifts as (select distinct game_id from {STAGING_TABLE} where season < ? and type_code = {SHIFT_TYPE}),
        in_mart as (select distinct game_id from {MART_TABLE} where season < ?)
        select
            newest.season,
            newest.game_id,
            totals.rows,
            staged.game_id is null as missing_in_staging,
            staged.entries is distinct from newest.entries as count_mismatch,
            staged_shifts.game_id is not null and in_mart.game_id is null as missing_in_mart
        from newest
        join totals using (season)
        left join staged using (game_id)
        left join staged_shifts using (game_id)
        left join in_mart using (game_id)
        """,
        [keep] * 5,
    ).fetchall()
    result = {}
    for season, game_id, rows, missing_in_staging, count_mismatch, missing_in_mart in games:
        checks = result.setdefault(season, {"games": 0, "rows": rows, "missing_in_staging": 0, "count_mismatch": 0,
                                            "missing_in_mart": 0, "missing_files": 0})
        checks["games"] += 1
        checks["missing_in_staging"] += missing_in_staging
        checks["count_mismatch"] += count_mismatch and not missing_in_staging
        checks["missing_in_mart"] += missing_in_mart
        checks["missing_files"] += not (folder / str(season) / f"{game_id}.json.gz").exists()
    return result


def passes(checks):
    return not (checks["missing_in_staging"] or checks["count_mismatch"] or checks["missing_in_mart"]
                or checks["missing_files"])


def prune(con, keep, apply=False, folder=None, verbose=True):
    """Check every season before `keep` in raw; with apply, delete those that pass. Returns (seasons, rows deleted)."""
    folder = folder or files_folder()
    checks = season_checks(con, keep, folder)
    ready = sorted(season for season, c in checks.items() if passes(c))
    if verbose:
        for season, c in sorted(checks.items()):
            verdict = "ok" if passes(c) else "KEEP"
            print(f"  {season}: {c['games']} games, {c['rows']} rows; missing in staging {c['missing_in_staging']}, "
                  f"count mismatch {c['count_mismatch']}, missing in fct_shifts {c['missing_in_mart']}, "
                  f"missing files {c['missing_files']}: {verdict}")
    if not apply:
        if verbose:
            print(f"  dry run: {len(ready)} seasons would be deleted; nothing changed (add --apply)")
        return ready, 0
    deleted = delete_seasons(con, SHIFT_TABLE, ready)
    if verbose:
        print(f"  deleted {deleted} rows of {len(ready)} seasons from raw.{SHIFT_TABLE}")
    return ready, deleted


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--keep", type=season_id, required=True, help="the season in progress, for example 20262027")
    parser.add_argument("--apply", action="store_true", help="delete; without it, only report what would be deleted")
    args = parser.parse_args()
    started = time.monotonic()
    con = connect()
    try:
        prune(con, args.keep, apply=args.apply)
    finally:
        con.close()
    print(f"  {time.monotonic() - started:.0f} s")


if __name__ == "__main__":
    main()
