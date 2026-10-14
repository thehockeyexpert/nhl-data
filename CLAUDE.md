# NHL data platform

Ingest NHL data with Python, store in MotherDuck, transform with dbt, and eventually query it conversationally.
The owner is new to Python and dbt: explain changes in plain language.

## Hard rules
- PUBLIC repo. Never commit secrets or data files (.json, .csv, .parquet, .duckdb).
- The MotherDuck token lives in the env var `motherduck_token`. Never print, log, or write it.
- Use uv for everything Python (`uv add`, `uv run`). No pip, no manual venvs.
- No MoneyPuck data for now.
- No NHL data files in the public repo: no API responses, extracts or exports, in any format. The repo holds code, docs and our own decisions (seeds) only.
- Nothing from the NHL is printed in logs: ingest output reports counts, timings and status only, never response content.
- The NHL endpoints are unofficial and unlicensed, used for personal use only. Public content is facts and figures only: no NHL logos, photos or video. See `docs/decisions.md` (2026-10-14).

## Layers (schemas in the single MotherDuck database `nhl`)
- `raw`: JSON exactly as received, plus `source_url` and `loaded_at`. Append-only. Written only by `ingest/`.
- `staging`: one dbt model per raw table. Unpack JSON, rename, cast types, dedupe. No business logic.
- `marts`: analysis-ready tables built from staging (`fct_games`, `dim_teams`).
- `reference`: dbt seeds, small hand-written CSVs in `dbt/seeds/` holding our own decisions (labels, overrides, exceptions). Never NHL data.
- `checks`: `check_failures` (every row that breaks a data check), `season_status` (which seasons count as finished) and `season_in_progress_notes` (postponed or pending games; never fails).

## Data tiers
- Tier 1: all-history schedule, results, game-level stats. Small.
- Tier 2: play-by-play and shifts, 2007-08 onward. Heavy; backfilled later from the laptop. Do not start without being asked.
- Open decision, to settle BEFORE starting Tier 2: MotherDuck's free plan caps storage at 10 GB, so Tier 2 raw payloads may need to be stored as compressed files outside MotherDuck instead of in the `raw` schema.

## Folders
- `ingest/`: Python that fetches from the NHL API and loads `raw`.
- `dbt/`: the dbt project (`models/staging`, `models/marts`, `macros`).
- `tests/`: Python tests for the ingest code.
- `docs/`: metric definitions, and `data_coverage.md` (where the data is thin or different by era; read it before answering historical questions).
- `analyst/`: golden questions for checking the conversational query layer.
- `.github/workflows/`: reserved for a future daily run.
- `data/`: local scratch, gitignored.

## Conventions
- Python does fetching and loading only; all cleaning happens in dbt SQL.
- All HTTP goes through `ingest/nhl_api.py`; all raw writes go through `ingest/raw_loader.py`.
- Ingest jobs are safe to rerun and are polite to the NHL API (pacing, retries).
- Naming: snake_case; staging models `stg_<source>__<entity>`; marts `fct_` / `dim_`.
- Seasons use the NHL's 8-digit ID, e.g. `20252026`. The first season being built end to end is `20252026`.
- Every dbt model has a description and at least a uniqueness and not-null test on its key.

## What we have learned about the data
- Sources: the weekly schedule (`api-web.nhle.com/v1/schedule/{date}`) is the main source for games. The stats API game list is an independent cross-check, and the stats API season facts supply the expected counts.
- `game_date` is the North American calendar date the NHL lists the game under, not the UTC date. A late West Coast game has a `start_time_utc` on the following day. Use `game_date` for "games on a date".
- Scores are final scores as the NHL reports them, so a shootout win counts as one goal. `last_period_type` is REG, OT or SO.
- The game list includes scheduled "if necessary" playoff games that were never played (`is_final` false). The weekly schedule leaves them out.
- Game type labels live in `dbt/seeds/game_type_labels.csv`, keyed by season and type. 1 = preseason, 2 = regular, 3 = playoff. Other types are labelled per season; `docs/game_type_evidence.md` records the evidence, the rules applied and what is still unknown. Never label a (season, game type) pair without checking the data and getting the owner's sign-off; unverified pairs stay `unknown type N`.
- Season 20042005 has no season facts and no played games. That is expected, not an error.
- Teams: `dim_teams` has one row per team identity, with the NHL's `franchise_id` and our `lineage_id`. They are equal unless `dbt/seeds/team_lineage_overrides.csv` says otherwise; an override needs an independent source and the owner's approval. Utah is deliberately kept as the NHL's separate franchise.
- Era differences (ties, shootouts, thin preseason, non-NHL opponents, 1917-18) are recorded in `docs/data_coverage.md`. Keep it up to date when something new is found.
- `fct_games` holds types 1, 2 and 3 only. Special events stay in staging.

## Data checks (dbt/tests)
- Each rule is written once in `dbt/models/checks/check_failures.sql`. The files in `dbt/tests/` are thin: one check each, minus documented exceptions.
- Never hardcode a count. Compare against `stg_nhl_stats__seasons` so the same check works for every season.
- Count and completeness checks apply only to finished seasons (`checks.season_status`): the NHL's planned `season_end_date` has passed AND the weekly schedule has no regular-season or playoff game still scheduled.
- A season in progress: checks on recent games use a two-day lag (`game_date <= current_date - 2`), so games that have just ended or are still running do not fail. Postponed, suspended and cancelled games are listed in `checks.season_in_progress_notes`, which never fails the build. Every scheduled regular-season game must already be in the game list.
- Checks depend on the date the build runs, so the same data can pass one day and fail the next (for example a game postponed two days ago with no new date). Rerun before investigating.
- Regular-season games must equal `total_regular_season_games`; played playoff games must equal `total_playoff_games`.
- Every finished season must be balanced (total games x 2 = teams x games per team). In a balanced season every team must have `scheduled_games_per_team` games.
- Level scores are allowed only where `is_ties_in_use` is true.
- The weekly schedule and the game list must agree on finished regular-season and playoff games, teams and scores.
- Never loosen a check to make history pass. A legitimate difference becomes a row in `dbt/seeds/check_exceptions.csv`, shown to the owner with its evidence and approved first. `assert_no_stale_exceptions` fails if an exception stops being needed.
- Do not assert a cause without a source. An exception's `reason`, and anything in `docs/data_coverage.md`, says "unexplained" plus what was observed unless a source confirms the cause.
- Prove every new or changed check can fail, on a throwaway local copy of the data, never on the real tables.

## Commands
- Ingest one season: `uv run python -m ingest.schedule --season 20252026`
- Ingest many seasons, newest first, resumable: `uv run python -m ingest.backfill --from 20242025 --to 19171918`
- Ingest team and franchise lists: `uv run python -m ingest.teams`
- Ingest records lists (players, draft, awards, playoff series) and standings rules: `uv run python -m ingest.records`
- Python tests: `uv run pytest`
- Transform: `uv run dbt build --project-dir dbt --profiles-dir dbt`
