# Project status

Last updated: 2026-10-14

## Done

- **Foundations.** Project scaffold, conventions (`CLAUDE.md`), and a `.gitignore` that blocks secrets and data files.
- **Data use.** Decided 2026-10-14 (`docs/decisions.md`): the NHL endpoints are unofficial and unlicensed, and used for
  personal use only. No NHL data files go in the public repo, and nothing from the NHL is printed in logs.
- **Schedule and results, Tier 1 history.** 1917-18 to 2025-26 are loaded in MotherDuck (109 seasons; 2004-05 has no
  games). `fct_games` holds 72,452 games before 2026-27, fingerprint `cae7e79c…`, unchanged since the history load.
- **Game type labels.** Approved for every (season, type) pair except (1948-49, 4), which breaks its rule. Evidence is
  in `docs/game_type_evidence.md`, trimmed to one summary line per pair.
- **Load 1: records and standings rules** (6 requests, 2026-10-14).
  - Players, draft picks, trophies, award results, playoff series games, and the standings rules per season.
  - Known facts checked against outside sources: McDavid's birth and draft, Hart winners, Stanley Cup gaps, the
    first draft, 2024-25 series, and the start seasons of the standings rules. The ROW and regulation-wins start
    seasons are unverified (`docs/data_coverage.md`).
- **Load 2: 2026-27** (32 requests, 2026-10-14). A one-off snapshot: 1,344 regular-season games scheduled, 105 final
  on the day of the load.
- **Checks for a season in progress.** `checks.season_status` decides when a season counts as finished. Recent games
  have a two-day lag. `checks.season_in_progress_notes` lists postponed and pending games and never fails.
- **Load 3: goalie games, all history** (220 requests, 2026-10-14), plus the official team season totals (1 request).
  - `fct_goalie_games` (150,751 rows), `fct_team_games`, and `fct_team_standings_by_game` (standings before every
    regular-season game, under each era's rules).
  - The derived standings match the official season totals for 1,788 of 1,791 team-seasons. The 3 differences are
    pinned to single games and excepted. A spot-check of 4 games against the NHL's standings matched exactly.
  - Career-win sanity check: Brodeur 691 and Roy 551 match our data.
- **Exceptions.** 81 rows in `dbt/seeds/check_exceptions.csv`, each approved by the owner. Exceptions can now name a
  single team (`team_id`). From 2022-23, an era rule in `goalie_saves_add_up` allows saves that are exactly 1 too
  high, watched by `checks.goalie_saves_plus_one_by_season` with a 2% limit.
- **Latest `dbt build` on MotherDuck (2026-10-14):** 141 of 141 pass. No failure is left without an approved exception.

## In progress

- **G01 ("best record against teams above .500"):** `goalie_records_vs_above_500` is built under the revised D01
  (headline: opponent above the league median by points % before the game, with at least 10 games played; second
  column: above .500 by points %), with D04, D05 (50, and 100 reported) and D23.
  - **Verified (2026-10-14).** Recomputed independently from the NHL's official standings for the day before each
    game, it matches game for game: Ken Dryden 1975-76 under the headline (21 qualifying decisions, league median
    equal on all 60 dates), and Dryden 1975-76 and Braden Holtby 2015-16 under the above-.500 column (24 and 45).
  - **Still labelled draft** until the owner has checked it.

## Next

1. **Measure one lighter build, then plan the daily run.**
   - Measure before the MotherDuck Business trial ends on **2026-10-19**: `md_information_schema.query_history`,
     which shows per-query execution time, is a Business-plan feature and disappears with the trial.
   - Then plan the daily run (GitHub Actions) for 2026-27. Until it exists, the 2026-27 snapshot goes stale:
     `past_games_final` will start failing on any build two days after the last schedule load.
2. **Review the golden questions and settle the open definitions.** Approve or reject the proposed rewordings in
   `analyst/golden_questions.yml`, and decide the open entries in `docs/definitions.md` (see "Open decisions").
3. **The conversational query layer,** connecting to MotherDuck with a read-only token, so it can query but never
   change the data.

## Storage (2026-10-14)

- **MotherDuck storage for `nhl`:** active data 33.0 MB. Retained history 264.3 MB, kept under a 7-day snapshot
  retention.
- **Cause:** the history is consistent with dbt re-creating the mart tables on every build (details and sources in
  `docs/decisions.md`).
- **Billing:** MotherDuck's billing docs say all four storage categories, history included, count toward the
  storage bill.
- **Proposed, not applied:** build `fct_goalie_games`, `fct_team_games` and `fct_team_standings_by_game` (and
  possibly `fct_games`) incrementally, so the daily run rewrites only the current season.

## Compute for a nightly run (measured 2026-10-14)

- **A full `dbt build` on MotherDuck** (3 seeds, 6 tables, 18 views, 114 tests) took **61 s** (67 s wall clock
  including start-up). dbt sent **235 SQL statements**, one at a time. The trial runs on a Standard instance.
- **Query history** recorded the first 204 of them, 11.9 s of execution in total, mostly well under 1 s each. It had
  not caught up with the rest by the time of checking. It reports execution time, not compute units.
- **Estimate for Lite**, an estimate and not a measurement:
  - Pulse bills each query for at least 1 CU-second, so a full build is at least about 235 CU-seconds, plus the time
    of the few queries over 1 s. Roughly **250 to 300 CU-seconds, about 0.07 to 0.08 CU-hours**, if Pulse runs these
    queries about as fast as the trial's Standard instance (not verified).
  - A nightly full build: about **2.1 to 2.5 CU-hours a month** of the 10 included, before ingest and any querying.
  - To confirm: the Billing page after the first nights on Lite.
- **Proposed lighter daily build (not applied):**
  1. **Skip seeds:** `--exclude resource_type:seed`. Seeds change only when the owner approves something; a full
     build runs then.
  2. **Skip re-creating views:** views only change when their SQL changes, so the nightly run rebuilds tables only
     (`dbt run --select config.materialized:table`, 6 tables).
  3. **Run the data checks every night** (the `dbt/tests` files on `check_failures`, about 30). Run the 80 or so
     generic key tests on the staging views weekly and after any code change: they scan the raw JSON and are the
     slowest part.
  4. **A full `dbt build`** weekly, and whenever models, seeds or exceptions change.

  Expected: about 40 to 50 queries a night instead of 235. That is about 60 to 100 CU-seconds, or 0.5 to 0.8
  CU-hours a month (estimate). Incremental marts remain a separate, held proposal.

## Open decisions

- **Definitions** still open in `docs/definitions.md`: D05 beyond G01, D06, D07, D09, D10, D13, D14 and D17 to D20.
  Proposed defaults await confirmation: D02, D08, D11, D12, D15, D16, D21 and D22.
- **Golden questions:** the proposed rewordings in `analyst/golden_questions.yml` await approval.
- **Fights and travel** are in scope (`docs/decisions.md`). Before the fight load: an optional wider test for missed
  fights, and the storage decision for play-by-play.
- **Utah** is kept as the NHL's separate franchise (40), with no lineage override.
- **Tier 2 storage:** whether play-by-play payloads go into MotherDuck or into compressed files outside it, to be
  decided before Tier 2 starts.

## Not started

- Team, skater and play-by-play loads; player pages (college and junior seasons); arena coordinates.
- Answers to the golden questions (beyond G01). The conversational layer itself is item 3 under "Next".