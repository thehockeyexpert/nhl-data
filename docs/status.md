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

## Pilot run (2026-10-14): done and reviewed

- Team and franchise lists loaded (3 requests).
- Seven pilot seasons loaded: 20202021, 20192020, 20122013, 20042005, 19941995, 19671968, 19171918. 170 requests in 2.8 minutes, as estimated.
- `dbt build` on MotherDuck: 65 of 67 pass. The two failures are the expected ones; their exceptions were approved on 2026-10-14 (not yet rebuilt on MotherDuck):
  - `regular_season_game_count`, 19171918: expected 34, actual 36.
  - `season_balanced`, 19171918 (teams have 6 to 22 games) and 20192020 (68 to 71 games).
- Every pilot season's regular-season and playoff counts match the NHL's season facts, apart from 1917-18.
- MotherDuck storage for the `nhl` database after the pilot: about 5.2 MiB (8 seasons).

## Next

1. Pilot reviewed (2026-10-14): exceptions approved with sources; labels approved for (1967-68, 4), (2019-20, 4), (2019-20, 12); Jets (1979) lineage override approved.
2. Full history load (2024-25 back to 1917-18, about 3,300 more requests, 60 to 90 minutes), run by the owner in a separate terminal. Seasons already loaded are skipped. In progress, run by the owner.
3. After the load: `dbt build` on MotherDuck, then the game type evidence for every remaining pair, and any new exceptions.

## Open decisions

- **Game type labels.** Approved so far: 1, 2, 3 for all seasons; (20252026, 9) olympics; (19671968, 4) and (20192020, 4) all_star; (20192020, 12) all_star_womens_game. Every other pair stays `unknown type N` until its evidence is reviewed after the full load.
- **Utah.** Kept as the NHL's separate franchise (40). No lineage override.
- **Tier 2 storage.** Whether play-by-play payloads go into MotherDuck or into compressed files outside it, to be decided before Tier 2 starts.

## Not started

- Season 20262027 (in progress) and the daily run.
- Per-game statistics (the rest of Tier 1).
- Tier 2: play-by-play and shifts.
- The conversational query layer and golden questions.
