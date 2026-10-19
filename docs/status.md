# Project status

Last updated: 2026-10-15

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
- **Exceptions.** 97 rows in `dbt/seeds/check_exceptions.csv`, each approved by the owner. Exceptions can now name a
  single team (`team_id`). From 2022-23, an era rule in `goalie_saves_add_up` allows saves that are exactly 1 too
  high, watched by `checks.goalie_saves_plus_one_by_season` with a 2% limit.
- **Daily run started (2026-10-15).** `.github/workflows/daily.yml`, 11:00 UTC daily, full build on Sundays.
  - First manual run passed: schedule 32 requests, 22 new rows; goalies 2 requests, 1 new row. All checks pass.
  - 20 of the 21 changed schedule weeks differed only in `ticketsLink` / `ticketsLinkFr`. The loader now ignores
    those two fields when deciding whether a response changed (`compare_hash`); the response is still stored as
    received.
  - Actions on Node.js 24 (`actions/checkout@v7.0.1`, `astral-sh/setup-uv@v10.2.0`), runner `ubuntu-24.04`.
- **Conversational query layer connected (2026-10-15).** MotherDuck's remote MCP server, signed in with the owner's
  own account (OAuth).
  - `.claude/settings.json` blocks the 18 tools that write, delete, run or share. `query` is read-only on
    MotherDuck's side: a `CREATE SCHEMA` through it was refused ("Query is not read-only").
  - Read scaling tokens (server-side read-only) are a Business-plan feature, so they were not used.
  - `persist_docs` copies model and column descriptions into MotherDuck as comments, so the MCP tools see them.
  - The text for a MotherDuck guide is in `docs/motherduck_guide.md`; the owner creates the guide by hand.
- **Skater season totals, all history (2026-10-15).** `ingest.skaters` (216 requests, 31.6 MB raw, 220 responses);
  nightly in the daily run (2 requests).
  - `fct_skater_seasons`: 69,635 rows, 7,947 skaters, regular season and playoffs. 4,110 rows are players who
    changed teams (totals not split by team; `bridge_skater_season_teams` lists the teams).
  - New dimensions: `dim_players` (23,575 people, 8,826 NHL players under D15), `dim_seasons`, `dim_games`.
  - New checks: `skater_team_resolves`, `skater_games_within_team`, `skater_goals_add_up`, each proven to fail on a
    local copy or on real data. Exceptions: early playoffs against non-NHL teams, the 1917-18 forfeits, and the
    suspended 1988 Final game (`docs/data_coverage.md`, "Skater stats").
- **Birth city spellings (2026-10-15).** `dbt/seeds/birth_city_spellings.csv` (22 rows, approved) merges spellings
  of the same place into `dim_players.birth_city_standard` (38 NHL players change city); checked by
  `birth_city_spellings_valid`. Former names stay separate (D14). Compared with QuantHockey's city totals in
  `docs/data_coverage.md`, "Birthplaces"; "New York" and "New York City" are deliberately left separate.
- **Records data modelled (2026-10-17).** `fct_draft_picks` (13,152 picks), `dim_trophies`, `fct_award_results`,
  `bridge_playoff_series_games`, `fct_playoff_series` (NHL playoff games only; the 2004 World Cup games in the NHL's
  list are left out; the 1919 Final has no winner) and `fct_team_seasons` (official totals). Tagged `records`:
  rebuilt weekly and after `ingest.records`, not nightly.
  - New checks: `draft_pick_unique`, `playoff_series_score_matches`, `stanley_cup_winner_matches_final`,
    `team_season_goals_match_games` (official goals equal our games minus shootout goals, every team-season from
    2005-06). 5 approved exceptions: the 1919 and 1927 Finals, the 1917-18 forfeits.
  - Golden questions: P08 (draft), A01 (awards), F02 (series), SE01 (team seasons), each with a reference answer.
- **Skater stats per game (2026-10-17; in the daily run from 2026-10-18).** `ingest.skater_games` (425 requests in 12.1 min,
  434 date-window responses, 1.24 GB raw JSON); `stg_nhl_stats__skater_games` and `fct_skater_games` are incremental
  (each build reads only raw rows loaded since the last one).
  - 2,421,850 rows, 108 seasons, 7,923 skaters. Per-game rows add up to the season totals for every player-season
    (`skater_games_match_seasons`); `skater_game_in_games` flags only the suspended 1988 Final game (exception
    approved 2026-10-18; 98 exceptions in all).
  - First incremental build: 65 s for the staging model (one-off). Measured nightly run (ingest of the 3 last game
    dates plus the nightly dbt build): the per-game ingest 17 statements (19 CU-s worst case); the two incremental
    models 0.65 s each. The whole nightly dbt build: 244 recorded statements, 16.1 s execution, 249 CU-s worst case.
  - In the daily run from 2026-10-18 (owner's decision, about +0.39 CU-hours a month): 2026-27 loaded in full once
    (7 requests, 16 s); nightly `ingest.skater_games --season "$SEASON" --recent-days 3`, and
    `config.materialized:incremental` in the nightly selection (48 of 48 pass). In recent mode a season never loaded
    in full is loaded in full first, so a new `CURRENT_SEASON` needs no extra step.
  - Guide version 4 (2026-10-18): coverage lists `fct_skater_games` and the records tables.
- **Conferences and divisions per season (2026-10-19).** `ingest.standings` (110 requests in 1.8 min, standings on each
  season's first standings day); `stg_nhl_web__standings` and `dim_team_season` (1,791 team-seasons, 109 seasons,
  including 32 teams in 2026-27). Divisions are empty in 38 seasons, conferences in 58 (`docs/data_coverage.md`).
  - New checks `team_season_unique`, `team_season_resolves`, `team_season_covered`, `team_season_groups_match_rules`,
    each proven to fail on a throwaway local copy. No exceptions needed.
  - In the daily run: `ingest.standings --season "$SEASON"` (2 requests, nothing stored after the first run), and
    `dim_team_season` in the nightly build (53 of 53 pass on 2026-10-19).
- **Birthplace coordinates (2026-10-19).** `ingest.geonames` (cities500, the Canada file and the country list; 553,723
  lines in 12.6 s, replaced on each refresh); `dim_birthplaces` (4,442 places) and `dim_players.birthplace_key`.
  97.40% of players with a birth city matched; 532 places (606 players) unmatched, 25 manual rows (approved 2026-10-19)
  (`docs/data_coverage.md`, "Birthplace coordinates").
  - New checks `birthplace_coordinates_valid`, `birthplace_manual_fixes_valid` and `birthplace_coverage` (a warning
    below 95%), each proven to fail on a throwaway local copy.
  - Refreshed by `.github/workflows/geonames.yml` (quarterly and on demand); rebuilt in the Sunday full build, not nightly.
- **Latest `dbt build` on MotherDuck (2026-10-18):** 229 of 229 pass; the nightly build 48 of 48 (12 tables, 2 incremental
  models, 34 data checks). No failure is left without an approved exception.

## In progress

- **G01 ("best record against teams above .500"):** `goalie_records_vs_above_500` is built under the revised D01
  (headline: opponent above the league median by points % before the game, with at least 10 games played; second
  column: above .500 by points %), with D04, D05 (50, and 100 reported) and D23.
  - **Verified (2026-10-14).** Recomputed independently from the NHL's official standings for the day before each
    game, it matches game for game: Ken Dryden 1975-76 under the headline (21 qualifying decisions, league median
    equal on all 60 dates), and Dryden 1975-76 and Braden Holtby 2015-16 under the above-.500 column (24 and 45).
  - **Still labelled draft** until the owner has checked it.
- **Golden-question test of the query layer (2026-10-15).** Five questions (H03, T11, X01, SE05, G01), with
  reference answers computed by direct SQL and checked against outside sources where they exist:
  - H03: 21 goals, MTL 14-TSP 7 (1920-01-10) and EDM 12-CHI 9 (1985-12-11); playoffs 18, LAK 10-EDM 8
    (1982-04-07). Matches Hockey Reference and NHL.com.
  - T11: Montréal Canadiens lineage, 805 playoff games through 2025-26. Through 2019-20, 759 games and 434 wins,
    matching the Ice Hockey Wiki.
  - X01: regular season 302 games, Rangers 143-130-19-10 (W-L-T-OTL); playoffs 39 games, Islanders 20-19,
    matching outside sources.
  - SE05: 2025-26, 326 of 1,312 regular-season games decided in OT or a shootout (2013-14 has the highest share,
    25.0%). Counting OT games that ended tied wrongly puts 2003-04 and 2002-03 near the top.
  - G01: the mart matches an independent recomputation for every goalie.
  - **Blind run** (a fresh agent using only the MCP tools, before the guide existed): every figure was right, and it
    excluded OT ties. Two misses, both from definitions not yet in MotherDuck: SE05 included playoffs (348), and G01
    led with the literal above-.500 column instead of the D01 headline. Records were given as three unlabelled
    numbers.
  - **Second blind run, with the guide text** given in the agent's instructions (the guide could not be read through
    MCP, see below): SE05, G01 and a new question, G02 (most shutouts in a season), all correct. SE05 was regular
    season only (326); G01 led with the D01 headline and labelled records W-L-T-OTL; G02 gave George Hainsworth,
    22 in 1928-29. So the guide's content fixes both misses.
  - **The guide in MotherDuck (resolved 2026-10-15).** MCP saw no guides because none existed: Guides cannot be
    created in the MotherDuck web UI, only with SQL (`MD_CREATE_GUIDE`) or the MCP tools, which are blocked here.
    `analyst/publish_guide.py` now publishes `docs/motherduck_guide.md` (text below its `---` line) as a private
    (`user`) Guide, topic `nhl`; version 1 published 2026-10-15 and readable through MCP.
  - **Third blind run, reading the guide from MotherDuck itself** (2026-10-15): a fresh agent with only the MCP
    tools found it (`get_query_guide`, then `list_guides` on topic `nhl`, then `get_guide`) and applied its rules.
    SE05 (2025-26, 326), G01 (top-half headline first: Samsonov .653 at 50, Holtby .600 at 100; then above .500) and
    G02 (Hainsworth, 22 in 1928-29) all match the references. 12 MCP calls in all (3 to find the guide, 3 per
    question).
  - **Cost:** each answer query ran in about 20 ms. Query history is incomplete for MCP queries: it holds 26 MCP
    entries after 12:48 UTC, fewer than the two blind runs alone made, none of their marker queries, and no entry
    for a full dbt build at 12:46. So per-question costs of the blind runs could not be measured. Estimate: at most 3 to 4 CU-seconds per question (worst case, 3 or 4
    calls each).

## Next

1. **Keep the guide in step.** When it changes: edit `docs/motherduck_guide.md`, run
   `uv run python -m analyst.publish_guide`, and paste the same text into the Claude.ai Project instructions.
2. **Watch the daily run.** After the first nights on the free plan (from 2026-10-19): compare the Billing page with
   the estimate below, and check in `raw.ingest_log` how many responses change each night now that ticket links are
   ignored.
3. **Review the golden questions and settle the open definitions.** Approve or reject the proposed rewordings in
   `analyst/golden_questions.yml`, and decide the open entries in `docs/definitions.md` (see "Open decisions").
4. **Parked, not started: `fct_skater_games`** (one row per skater per game, all history, same keys).
   - Recommended source: the stats API skater summary with `isGame=true`, in date windows under its 10,000-row cap
     (1980-81 and 2025-26 both reach the cap). About 2.3 to 2.5 million rows, 300 to 450 requests, about 1.2 GB
     raw JSON (estimates). Whether the API filters by date is not yet verified. Nightly: one request per game date.
   - Alternative: the box score, one request per game (70,459 games, about 20 hours); about 0.8 GB raw. Sampled
     back to 1917-18.
   - Must be an incremental model (re-reading 1.2 GB of JSON every build could cost an estimated 7 to 20 CU-hours a
     month, more than the free 10). With it: about 0.2 CU-hours once, $0 a month.
5. **Parked, not started: `fct_shots`** (play-by-play, Tier 2; needs the owner's go-ahead and the Tier 2 storage
   decision first).
   - 24,542 games from 2007-08 to 2025-26, one request each (about 7 to 10 hours). Sampled sizes: about 35 KB per
     game in 2007-09, 100 to 150 KB from 2009-10; about 2.8 GB raw JSON in all. About 2.6 million shot attempts.
   - Shot coordinates: present in every sampled game from 2009-10 on, absent in the sampled games of 2007-08 and
     2008-09 (one game per season; to confirm).
   - Raw JSON in MotherDuck would mean about 49,000 statements (about 13.6 CU-hours, over the monthly allowance).
     Recommended: raw play-by-play as compressed files on the laptop (about 0.3 to 0.4 GB), shots bulk-loaded into
     MotherDuck (a handful of statements, $0). Nightly: 8 to 15 games, about 2 MB, small enough for `raw`.
6. **Parked, not started: MoneyPuck** for expected goals. Blocked by the hard rule "No MoneyPuck data for now".
   - Terms: free for non-commercial use, credit MoneyPuck.com wherever shown; ask before scraping anything not
     offered for download ([moneypuck.com/data.htm](https://moneypuck.com/data.htm)).
   - About 2.08 million shots, 2007-08 to 2024-25 plus the current season nightly; no blocked shots; CSV in zip.
   - IDs not verified (the data dictionary could not be read automatically): check by hand that its game number and
     player IDs match `fct_games` and `dim_players` before any load.
   - Estimate: 150 to 300 MB as a table, a few statements per load, $0 a month.

## Storage (2026-10-14)

- **MotherDuck storage for `nhl`:** active data 33.0 MB. Retained history 264.3 MB, kept under a 7-day snapshot
  retention.
- **Cause:** the history is consistent with dbt re-creating the mart tables on every build (details and sources in
  `docs/decisions.md`).
- **Billing:** MotherDuck's billing docs say all four storage categories, history included, count toward the
  storage bill.
- **Proposed, not applied:** build `fct_goalie_games`, `fct_team_games` and `fct_team_standings_by_game` (and
  possibly `fct_games`) incrementally, so the daily run rewrites only the current season.

## Compute for a nightly run (measured 2026-10-14 and 2026-10-15)

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
- **Nightly build, chosen 2026-10-15** (`docs/decisions.md`): one `dbt build` that rebuilds the tables (7 when chosen, 12 since the skater load) and runs the
  data checks (24 then, 27 now), with `checks.check_failures` now a table:
  `uv run dbt build --project-dir dbt --profiles-dir dbt --select config.materialized:table test_type:singular --exclude tag:records --indirect-selection empty --no-populate-cache`
- **Weekly, and after any change to models, seeds or exceptions:** a full `dbt build`. It also runs the 28 key tests
  the nightly build leaves out (uniqueness, not-null and relationships on the 7 tables) and the staging tests.
- **Measured 2026-10-15** (three runs in separate time windows, from query history and dbt's log):

  | | 1. Two commands, `check_failures` a view | 2. Two commands, a table | 3. One `dbt build`, a table (chosen) |
  |---|---|---|---|
  | Statements dbt sent | 119 | 131 | 113 |
  | Statements in query history | 82 | 89 | 88 |
  | Execution time | 28.7 s | 9.5 s | 9.6 s |
  | Worst case per night (1 CU-second minimum each) | 89 CU-s | 93 CU-s | 92 CU-s |
  | Worst case per month, of 10 CU-hours | 0.74 (7.4%) | 0.77 (7.7%) | 0.77 (7.7%) |

  BEGIN and catalog lookups never appear in query history; whether the near-instant statements are billed is not
  documented. Ingest is not included. To confirm: the Billing page after the first nights on Lite. Incremental marts
  remain a separate, held proposal.

## Daily run (started 2026-10-15)

- **Workflow:** `.github/workflows/daily.yml`. Every day at 11:00 UTC, and by hand from the Actions tab.
  1. Install the locked packages and run `uv run pytest` (no network, no database).
  2. Ingest the season in the repository variable `CURRENT_SEASON`: `ingest.schedule`, then `ingest.goalies`. The
     goalie load is needed nightly, or `goalie_games_covered` fails for newly finished games.
  3. The nightly dbt build; on Sundays the full `dbt build` instead. A manual run can choose either.
- **Token:** the repository secret `MOTHERDUCK_TOKEN`, a separate token on the owner's own MotherDuck user, used only
  by GitHub (`docs/decisions.md`).
- **Safety in a public repo:** no pull-request trigger, read-only repo access, one run at a time, 20-minute limit.
  Logs are public: they hold counts, status and our request URLs only.
- **GitHub pauses scheduled workflows** in a public repo after 60 days without commits; it emails the owner.
- **Estimated compute** (worst case, every recorded statement at the 1 CU-second minimum):

  | Per night | CU-seconds |
  |---|---|
  | Schedule ingest: 8 setup, 32 lookups, an insert per changed response, 1 log row | about 45 to 75 |
  | Goalie ingest (2 requests) | about 11 |
  | Nightly dbt build | 92 |
  | **Total** | **about 150 to 180** |

  - Per month: 30 nights is about 4,400 to 5,300 CU-seconds. The Sunday full build (about 250 to 300 instead of 92) adds
    about 700 to 900.
  - In all, **about 1.4 to 1.7 CU-hours a month of the free 10**, before querying: about $0 (budget in
    `docs/decisions.md`).
  - `persist_docs` (from 2026-10-15) adds about 53 comment statements per nightly build and about 120 per full build:
    about 0.6 CU-hours a month more, worst case. With it, about 2.0 to 2.3 CU-hours a month.
  - Ignoring ticket links should save about 20 inserts a night, and the loader adds about 4 statements (one
    `ADD COLUMN IF NOT EXISTS` per raw table it prepares).
  - The ingest figures come from the 2026-27 load of 2026-10-14 (73 statements, 1.4 s of execution, all new). The
    first nightly-style run (2026-10-15) found 23 changed responses of 34.
- **Raw growth:** each changed response is stored again in full (game list about 0.35 MB, a schedule week about
  0.09 MB): about 0.5 to 3 MB a night.
- **Possible saving, not applied:** fetch only recent and upcoming weeks instead of the whole season (about 25 fewer
  NHL requests and statements a night). A code change.

## Open decisions

- **Definitions** still open in `docs/definitions.md`: D05 beyond G01, D06, D07, D09, D10, D13 and D17 to D20.
  Proposed defaults await confirmation: D02, D08, D12, D16, D21 and D22.
- **Golden questions:** the proposed rewordings in `analyst/golden_questions.yml` await approval.
- **Fights and travel** are in scope (`docs/decisions.md`). Before the fight load: an optional wider test for missed
  fights, and the storage decision for play-by-play.
- **Utah** is kept as the NHL's separate franchise (40), with no lineage override.
- **Tier 2 storage:** whether play-by-play payloads go into MotherDuck or into compressed files outside it, to be
  decided before Tier 2 starts.

## Not started

- Team, skater and play-by-play loads; player pages (college and junior seasons); arena coordinates.
- Answers to the golden questions (beyond G01). The conversational layer itself is item 3 under "Next".