# NHL data platform

Ingest NHL data with Python, store in MotherDuck, transform with dbt, and eventually query it conversationally.
The owner is new to Python and dbt: explain changes in plain language.

## Hard rules
- PUBLIC repo. Never commit secrets or data files (.json, .csv, .parquet, .duckdb).
- The MotherDuck token lives in the env var `motherduck_token`. Never print, log, or write it.
- Use uv for everything Python (`uv add`, `uv run`). No pip, no manual venvs.
- No MoneyPuck data for now.

## Layers (schemas in the single MotherDuck database `nhl`)
- `raw`: JSON exactly as received, plus `source_url` and `loaded_at`. Append-only. Written only by `ingest/`.
- `staging`: one dbt model per raw table. Unpack JSON, rename, cast types, dedupe. No business logic.
- `marts`: analysis-ready tables built from staging.

## Data tiers
- Tier 1: all-history schedule, results, game-level stats. Small.
- Tier 2: play-by-play and shifts, 2007-08 onward. Heavy; backfilled later from the laptop. Do not start without being asked.
- Open decision, to settle BEFORE starting Tier 2: MotherDuck's free plan caps storage at 10 GB, so Tier 2 raw payloads may need to be stored as compressed files outside MotherDuck instead of in the `raw` schema.

## Folders
- `ingest/`: Python that fetches from the NHL API and loads `raw`.
- `dbt/`: the dbt project (`models/staging`, `models/marts`, `macros`).
- `tests/`: Python tests for the ingest code.
- `docs/`: metric definitions.
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

## Commands
- Ingest: `uv run python -m ingest.schedule --season 20252026`
- Transform: `uv run dbt build --project-dir dbt --profiles-dir dbt`
