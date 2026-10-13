# Project status

Last updated: 2026-10-13

## Done

- Project scaffold, conventions (`CLAUDE.md`) and a `.gitignore` that blocks secrets and data files.
- Ingest for one season of schedule and results into the `raw` schema: season facts, game list and weekly schedule, paced at one request per second and safe to rerun.
- Season 20252026 loaded end to end in MotherDuck: 1,312 regular-season games, 82 per team, 82 playoff games, all checks passing.
- dbt project: staging models, `fct_games`, and season-aware data checks that compare against the NHL's own season facts.
- Checks proven to fail on damaged local copies of the data.
- Code for the history load, tested but not yet run against the NHL API or MotherDuck:
  - `ingest/backfill.py` (many seasons, newest first, resumable) and `ingest/teams.py` (team and franchise lists).
  - `dim_teams` with the NHL's `franchise_id` and our `lineage_id`.
  - Reference tables in `dbt/seeds/`: game type labels, lineage overrides (empty), check exceptions.
  - `checks.check_failures`, a view of every failing row, with documented exceptions applied by the tests.
- `docs/data_coverage.md`: where the data is thin or different by era.

## Next: the pilot run

1. Load the team and franchise lists: `uv run python -m ingest.teams` (3 requests).
2. Load the seven pilot seasons (about 170 requests, about 3 minutes):
   `uv run python -m ingest.backfill --seasons 20202021,20192020,20122013,20042005,19941995,19671968,19171918`
3. Build on MotherDuck: `uv run dbt build --project-dir dbt --profiles-dir dbt`. This creates the `reference` and `checks` schemas and `dim_teams`.
4. Review: check failures, game type evidence, proposed exceptions, actual storage used.

After the pilot is reviewed: the full history load (2024-25 back to 1917-18, about 3,470 requests, 60 to 90 minutes), run by the owner in a separate terminal.

Until step 1 has run, `dbt build` on MotherDuck fails because the team tables do not exist yet. Until season 20042005 is loaded, `assert_no_stale_exceptions` fails because its exception has nothing to match.

## Open decisions

- **Game type labels.** Types 4, 6, 7, 8, 10, 12, 13, 14, 18, 19 and 20, and type 9 outside 20252026, have proposed labels only. Each (season, game type) pair needs evidence from the weekly schedule (teams, dates, venues) and the owner's confirmation before it goes into `dbt/seeds/game_type_labels.csv`. Until then they show as `unknown type N`.
- **Winnipeg Jets (1979).** The NHL files this team under franchise 35 with today's Jets. A lineage override to the Coyotes line needs a second, independent source confirming the 1996 move to Phoenix, shown to the owner first.
- **Utah.** Kept as the NHL's separate franchise (40) for now. No lineage override.
- **Exception reasons.** The 2004-05 exception reads "unexplained". Sources are still to be recorded for it and for the expected 1917-18 and 2019-20 exceptions.
- **Tier 2 storage.** Whether play-by-play payloads go into MotherDuck or into compressed files outside it, to be decided before Tier 2 starts.

## Not started

- Season 20262027 (in progress) and the daily run.
- Per-game statistics (the rest of Tier 1).
- Tier 2: play-by-play and shifts.
- The conversational query layer and golden questions.
