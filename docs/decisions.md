# Decisions

A log of the owner's decisions that change what we load or model, with the date and the expected cost.
The newest decision is first.

## 2026-11-14: raw shifts keep only the season in progress (option A)

**Decision (owner, 2026-11-14).** Approved and merged. **No data deleted yet:** the owner runs the first dry run
and then `--apply`, not before 2026-11-21, once the retained history from the shift backfill has aged out.
Claude does not run `--apply`.

`raw.nhl_stats__shift` keeps only the season in progress. Older seasons' entries are deleted from raw
once checked, and live on in `staging.stg_nhl_stats__shifts` and `marts.fct_shifts`, and as the full gzip charts on
the laptop (`NHL_SHIFTS_DIR`).
- **Why:** raw shifts are 2.06 GB of the database's 4.67 GB active storage (2026-11-14), almost all in the `event`
  JSON column. Expected saving about 2.0 GB once the deleted rows have aged out of history and failsafe (about 14
  days, during which the total is temporarily *higher*). Raw then grows to about 0.13 GB by the end of a season.
- **Lost from MotherDuck:** the original entries of finished seasons. Nothing we model is lost: only staging reads
  raw, and the marts read staging.
- **Safeguards (all on the branch):**
  1. `stg_nhl_stats__shifts` and `fct_shifts` have `full_refresh=false`, so `--full-refresh` cannot rebuild them from
     a raw table that no longer holds old seasons.
  2. `ingest/shifts.py` counts a game as loaded when it is in raw *or* in staging, and sends only games not loaded
     yet (or asked for again), so rerunning an old season adds nothing.
  3. The way back: `uv run python -m ingest.shifts --season <season> --restore` loads the season's games missing
     from staging from the laptop files, with no requests; a normal dbt build adds them back. Tested in
     `tests/test_shifts.py`.
  4. The yearly step: `uv run python -m ingest.prune_shifts --keep <season in progress>` (a dry run unless
     `--apply`), run on the laptop after the daily run moves to the new season. It deletes a season only when every
     game is in staging with the same number of entries as its newest raw load, is in `fct_shifts`, and has its file
     on the laptop; a season that fails is kept and reported.
  5. This entry and the raw-layer exception in `CLAUDE.md`.
- **Cost:** $0; one DELETE a year plus a few checking queries.

## 2026-11-14: daily run moved to 06:23 UTC

**Decision (owner, 2026-11-14).** `.github/workflows/daily.yml` runs at 06:23 UTC instead of 07:00 UTC (cron
`23 6 * * *`). GitHub's docs say scheduled runs can be delayed at busy times, the top of the hour especially; the
07:00 run of 2026-11-13 started at 15:11. Nothing else changed; the cost is unchanged. A game not yet final when the
run starts is picked up the next night, as before (the last 3 days are fetched again).

## 2026-11-13: records lists reloaded on Sundays

**Decision (owner, 2026-11-13).** The daily run reloads the records lists (`ingest.records`: player list, draft,
awards, playoff series, standings rules) whenever it runs the full build: Sundays, or a manual "full" run. Until now
they were loaded only by hand (last on 2026-10-14). 6 requests a week; a list identical to the last adds nothing. $0.

## 2026-11-13: shifts from the HTML reports when the shift chart is empty

**Decision (owner, 2026-11-13).** The rule: when a game's shift chart (stats API) comes back empty, fetch the NHL's
HTML shift reports for that game (home `TH`, visitor `TV`, nhl.com/scores/htmlreports) and store them exactly as
received in `raw.nhl_html__shift_report`; dbt parses the shifts (`stg_nhl_html__shift_reports`) and `fct_shifts`
uses them for games with no chart (`source` = html_report). A report not published yet (404) is asked for again on a
later run; when the NHL fills a chart later, the chart replaces the report rows.
- **Why:** 50 consecutive games of 2026-27 (game numbers 154 to 203, played 2026-10-22 to 29) have an empty shift
  chart, still empty when asked again on 2026-11-13, while their HTML reports are complete. Cause unknown.
- **Player IDs:** the reports carry names and sweater numbers only. Names are matched to the players of that team
  in that game (full name; teammates sharing a full name, such as Vancouver's two Elias Petterssons, by official ice
  time; else a unique last name). Checked on the 50 games: every name matched, and every player's report total equals
  the official time on ice to the second (1,903 player-games).
- **Cost:** 2 requests per game with an empty chart; about 200 KB of HTML per report. $0.
- **"Empty" means no shifts** (added 2026-11-13, after the backfill): a chart holding only goal markers counts as
  empty too, as `fct_shifts` already treated it. Found on 2013020971 (one goal marker, no shifts).

## 2026-11-13: shifts

**Decision (owner, 2026-11-13).** Load the NHL's shift charts (stats API `shiftcharts`, one request per game), regular
season and playoffs, 2010-11 onward (earlier games return nothing). The same split as the play-by-play: each game's
full chart saved gzip-compressed on the laptop (`NHL_SHIFTS_DIR`, default `~/nhl-data-files/shifts`), outside the
repo; one row per entry, exactly as received, bulk-loaded into `raw.nhl_stats__shift`. Modelled as `marts.fct_shifts`
(incremental). Nightly: games of the last 14 days with no shifts yet, plus the last 3 days' games fetched again;
older empty charts are asked for again only by a whole-season run on the laptop.
- **Estimate, shown to the owner before the load:** 20,889 games, about 16.5 million shifts, about 6 hours at the
  API's pace. About 2.3 GB in MotherDuck (about 2 GB raw, 0.3 GB modelled; measured on 30 games, within about 10%),
  taking the database from about 1.3 GB to about 3.6 GB of the 10 GB included; about 310 MB of files on the laptop.
  Nightly 6 to 16 requests, about 0.2 to 0.3 CU-hours a month. $0 a month inside the free plan.

## 2026-11-13: team game statistics

**Decision (owner, 2026-11-13).** Load the NHL stats API's per-game team reports (summary, power play, penalty kill,
penalties; `isGame=true`), regular season and playoffs, all history, one raw table per report
(`raw.nhl_stats__team_game_*`), and nightly for the last 3 game dates. Modelled as `marts.fct_team_game_stats`, one
row per team per game, for power-play and penalty-kill questions (T06).
- **Estimate:** about 880 requests once (15 minutes), about 300 MB of JSON before compression; 8 requests a night.
  $0 a month (inside the free plan's storage and compute).
- **Loaded:** 110 seasons, 872 requests in 15.1 minutes. Per-game power-play goals and opportunities summed by team
  match the NHL's season power-play report exactly (2025-26, 2010-11, 1985-86, regular season and playoffs).

## 2026-11-13: play events (faceoffs, giveaways, takeaways, stoppages) and overtime rules

**Decision (owner, 2026-11-13).** Load the play-by-play's faceoffs, giveaways, takeaways, stoppages and period start
and end markers into a raw table of their own, `raw.nhl_web__pbp_play`, one row per event exactly as received, from
the files already on the laptop (no downloads), and nightly from then on with the existing play-by-play job. The NHL
records these from 2009-10. A table of its own because staging keeps each game's newest load per table: adding them
to `nhl_web__pbp_event` for games already loaded would hide those games' hits and penalties.
- **Estimate, before the load:** about 3.1 million rows, about 1 GB of JSON text before compression, roughly 0.2 to
  0.4 GB in MotherDuck on 1.3 GB; about 2,000 rows a night. Expected $0; the owner checks the Billing page.
- **Loaded:** 3.18 million rows in about a minute from 22,195 files; 13 recent games fetched to complete the laptop's
  2026-27 files (the usual laptop sync).

**Decision (owner, 2026-11-13).** Seed `overtime_rules`: overtime by era for the regular season and the playoffs. The
eras before 1928-29 and the start of the 10-minute full-period overtime rest on what the play-by-play shows
(marked observed); later rules on NHL.com first. 4-on-4 overtime started in 1999-2000 (NHL.com; the owner).
Sources: NHL.com before Wikipedia (owner, 2026-11-13).

## 2026-11-13: league levels for "leagues before the NHL"

**Decision (owner, 2026-11-13).** The seed `dbt/seeds/league_levels.csv` (`reference.league_levels`) gives every
league code on the player pages that appears before an NHL debut a level; only junior, college, minor pro and major
pro count (definition 9). The owner approved the six judgement calls:
1. Renamed leagues count once (OHA Junior, OMJHL and OHL; Sweden and SHL...), and NCAA Division I with all its
   conferences is one league (`league_group`).
2. Senior amateur and semi-pro leagues do not count, the strong pre-1960s ones included.
3. European third tiers and below do not count; second tiers count as minor pro.
4. Under-18 club leagues are youth (not counted); under-19 and under-20 leagues are junior.
5. Canadian junior B and C count as junior.
6. The US national development team is not a league; its USHL and NAHL games count under those leagues.
Codes that meant different leagues in different eras have one row per era. Eight codes are unknown (not counted).
No cost.

## 2026-11-11: logos, headshots and photos in posts

**Decision (owner, 2026-11-11).** This changes the "Public content" point of the 2026-10-14 decision. Posts may use,
each credited in the caption (rules and placement in `style/style_guide.md`, "NHL logos and headshots"):
- **NHL team logos:** the NHL's own SVGs (`assets.nhle.com/logos/nhl/svg/{TEAM}_light.svg` and `_dark.svg`), never
  recoloured, stretched or given effects.
- **Player headshots:** the cut-out PNG in the `headshot` field of the NHL API's player page, current season.
- **Wikimedia Commons photos** under CC BY, CC BY-SA or public domain only, with the photographer and licence in the
  caption.
- **Photos the owner saves** in `assets/nhl/photos/`, named in the carousel YAML with a `credit:` field, also in the
  caption.
- Caption credit: "Data: NHL.", or "Data, logos and headshots: NHL." when an NHL logo or headshot is used.

Still not allowed: automatic downloads from Getty, Imagn, team websites or image searches; AI-generated pictures of
real players; committing any NHL image to the public repo (`assets/` is git-ignored). Video is not covered by this
decision, so NHL video stays out.

Notes for the record (Claude, 2026-11-11):
- The NHL terms quoted in the 2026-10-14 entry still apply to NHL logos and headshots: use "only for non-commercial,
  informational, personal use", "without modification or alteration".
- Commons licences: CC BY and CC BY-SA require the author, the licence and a note of any changes (a crop or a removed
  background is a change); CC BY-SA also requires a changed photo to be shared under the same licence. A licence
  covers the photo's copyright only, not logos on the jerseys or the player's own rights.

## 2026-11-11: player pages, files on the laptop

**Decision (owner, 2026-11-11).** Load B of the question inbox:
the NHL's player page (`api-web.nhle.com/v1/player/{id}/landing`) for everyone in the player list (23,575 people,
about 6.5 hours at our pace, no cost), to answer questions about players' paths before the NHL (junior, college,
minor and major pro leagues) and senior international tournaments.
- **Full pages** stay as gzip files on the owner's laptop (`NHL_PLAYER_DIR`, default
  `~/nhl-data-files/player_pages/<player_id>.json.gz`), exactly as received, as for play-by-play. About 30 KB each.
- **Only the season totals** (one entry per season, league and team) go to MotherDuck:
  `raw.nhl_web__player_season_total`, one row per entry exactly as received, with the page's URL and hash.
  Expected: a few hundred thousand rows, well within the current plan.
- Not in the daily run: careers change slowly, so the pages are refreshed by hand (`--refresh`) when needed.

## 2026-11-11: daily run moved to 07:00 UTC

**Decision (owner, 2026-11-11).** `.github/workflows/daily.yml` runs at 07:00 UTC instead of 11:00 UTC (cron
`0 7 * * *`). Nothing else in the workflow changed, and the cost is unchanged (the same run, four hours earlier). A
late game not yet final at 07:00 is picked up the next night: the per-game skater and play-by-play loads fetch the
last 3 days again, and the data checks wait two days for recent games.

## 2026-11-10: play-by-play shots, files on the laptop

**Decision (owner, 2026-11-10).** Tier 2 starts with `fct_shots`. This settles the Tier 2 storage question in
`CLAUDE.md`:
- **Raw play-by-play** stays as gzip files on the owner's laptop, outside the repo (`NHL_PBP_DIR`, default
  `~/nhl-data-files/play_by_play/<season>/<game_id>.json.gz`), exactly as received. `ingest/play_by_play.py` refuses a
  folder inside the repo.
- **Only the shot events** (shots on goal, missed, blocked, goals) are bulk-loaded into `raw.nhl_web__pbp_shot`, one
  row per event exactly as received: one insert statement per load. `stg_nhl_web__pbp_shots` and `fct_shots` are
  incremental.
- **Nightly** (`daily.yml`): finished games not loaded yet, plus the last 3 days' games fetched again for the NHL's
  corrections. The runner keeps the files in its temporary folder, deleted after the job; the log prints counts only.
  The owner reruns the season script on the laptop now and then to keep the local archive complete.
- **Loaded so far:** 2025-26 (trial) and 2026-27 (285 games, 290 s, from the laptop before the first nightly run).
- **Older seasons (owner, 2026-11-10, after the trial):** load every season back to 2007-08 from the laptop with
  `ingest.backfill --job play_by_play`, newest first. 2024-25 loaded the same evening; the run stopped partway
  through 2023-24 when the laptop restarted and was resumed on 2026-11-11 (`docs/status.md`).

**Trial, 2025-26 (measured 2026-11-10, from the laptop).** MotherDuck query history is not available on the free plan
("Query History is not available on your plan"), so compute comes from the run's own timings and dbt's log.

| | Measured | Worst case (1 CU-second minimum per statement) |
|---|---|---|
| Download: 1,394 requests | 23 min 16 s | no MotherDuck compute |
| Local files | 16.2 MB gzip (183 MB as JSON), about 11.6 KB per game | |
| Gathering shots on the laptop | 9.5 s, 6.4 MB Parquet, 163,818 rows | no MotherDuck compute |
| Load into MotherDuck: 11 statements, one insert | under 4 s from the end of gathering to the end of the run | about 13 CU-s |
| First dbt build of the two models and 9 tests | 70 statements, 6.8 s | about 73 CU-s |
| Build with no new data (as on a quiet night) | 75 statements, 4.4 s (models 35 of them) | about 76 CU-s |
| **Ingest, start to end** | **1,414 s** | |
| **MotherDuck compute: load and both builds** | | **about 162 CU-s (0.045 CU-hours)** |

- **Storage in MotherDuck:** not measured per table (`storage_info` is per database and updates later). Estimate:
  the raw events, the staging table and `fct_shots` each about the size of the 6.4 MB Parquet file or a few times it,
  so 15 to 40 MB a season.
- **Nightly estimate:** about 11 ingest statements and 35 for the two models, about 50 CU-seconds a night worst
  case, about 0.4 CU-hours a month of the free 10, **$0**. About 50 requests (new games plus 3 days fetched again),
  about 1 minute on GitHub. Each re-fetched game whose response changed adds its shots again (about 117 rows); staging
  keeps the newest.

## 2026-10-19: MotherDuck trial extended to about 2026-11-02

**Fact (from the owner, 2026-10-19).** The Business trial ended on 2026-10-19 and MotherDuck refused connections
until the owner extended it by 14 days, to about **2026-11-02**. The owner still plans to move to the free plan
before then. That day's daily run (11:18 UTC) had already passed; nothing else ran during the outage.

## 2026-10-19: birthplace coordinates from GeoNames

**Decision (owner, 2026-10-19).** `marts.dim_birthplaces` gives each birthplace in `dim_players` a latitude and
longitude from GeoNames (CC BY 4.0), with no paid or per-request geocoding service.
- **Sources:** `cities500` (every place with at least 500 people) and the full Canada file `CA.zip`, plus the
  country list. Not chosen: the US file (71 MB download, 2.2 million rows, about +0.6 points of players).
- **Refresh replaces, not appends:** the GeoNames raw tables are replaced on each refresh so storage stays flat, an
  exception to the append-only raw layer. Refreshed by `.github/workflows/geonames.yml` four times a year and on demand;
  `dim_birthplaces` is rebuilt in the Sunday full build and after a refresh, not nightly.
- **Matching:** exact name, then alternate name, both in the right country (and province or state for CAN and USA);
  then a Canadian administrative area of that name (`admin_area`, for former municipalities such as Scarborough); then
  the name in a successor country (`successor_country`, `seeds/birthplace_successor_countries.csv`). Manual rows
  (`seeds/birthplace_manual_fixes.csv`, about 25, each with a source) take precedence. Coordinates are never guessed.
- **Coverage:** a warning, not a failure, below 95% of players with a birth city (97.40% on 2026-10-19).
- **Cost, measured 2026-10-19:** the load took 12.6 s from the laptop (553,723 lines, about 77 MB of text);
  rebuilding `dim_birthplaces` 1.3 s. Four refreshes a year and one weekly rebuild: well under 0.1 CU-hours a month,
  an estimate. Storage about 77 MB of text, likely less once compressed: under 1% of the free plan's 10 GB. GitHub
  Actions minutes are free for a public repo. **$0 a month.**

## 2026-10-18: per-game skater stats in the daily run

**Decision (owner, 2026-10-18).** The daily run loads the last 3 game dates of per-game skater stats
(`ingest.skater_games --recent-days 3`), and the nightly build adds the incremental models
(`config.materialized:incremental`: `stg_nhl_stats__skater_games`, `fct_skater_games`), which read only raw rows
loaded since the last build. Measured on 2026-10-17: about 47 CU-seconds a night worst case (19 for the ingest, 28
for dbt), about 0.39 CU-hours a month; the whole estimate stays at about 3.3 to 3.7 of the free plan's 10 CU-hours,
$0. A season never loaded in full is loaded in full first, so a new season needs no extra step.

## 2026-10-17: records tables weekly, not nightly

**Decision (owner, 2026-10-17).** The six tables built from the NHL records site and the official team totals
(`fct_draft_picks`, `dim_trophies`, `fct_award_results`, `bridge_playoff_series_games`, `fct_playoff_series`,
`fct_team_seasons`, tagged `records`) are rebuilt in the weekly full build and whenever `ingest.records` runs, not
nightly. Their data changes only when `ingest.records` is run by hand. The nightly build adds `--exclude tag:records`;
after `ingest.records`, run `dbt build --select tag:records+`. Saves about 75 statements a night (about 0.6 CU-hours
a month, worst case).

## 2026-10-15: running-cost budget

**Decision (owner, 2026-10-15).** Total running costs (MotherDuck, GitHub and anything added later) aim for about
**$10 a month** and must **never exceed $30 a month**. Before adding anything that could cost money (a new
service, a paid plan, a heavier schedule, a larger load), estimate its monthly cost and ask the owner first.

**Estimate today (2026-10-15):** $0 a month.
- MotherDuck free Lite plan after 2026-10-19: the daily run is estimated at 1.4 to 1.7 of the 10 included CU-hours a
  month (`docs/status.md`), and storage is about 33 MB of the 10 GB included. Extra Pulse compute is billed at
  $0.60 per CU-hour ([pricing](https://motherduck.com/docs/about-motherduck/billing/pricing/)), so even 10 CU-hours
  over the allowance would cost about $6.
- GitHub Actions: free for public repositories on standard runners.

## 2026-10-15: the daily run on GitHub Actions

**Decision (owner, 2026-10-15).**
- `.github/workflows/daily.yml` runs every day at **11:00 UTC**: the schedule and goalie ingest for the season in the
  repository variable `CURRENT_SEASON`, then the nightly dbt build. On **Sundays** it runs the full `dbt build`.
- **Token:** a separate MotherDuck access token on the owner's own user, used only by GitHub, stored as the repository
  secret `MOTHERDUCK_TOKEN`. It can be revoked on its own. Its usage is not separated from the owner's on the Billing
  page.
- **Not chosen:** a MotherDuck service account. Shares are read-only
  ([sharing](https://motherduck.com/docs/key-tasks/sharing-data/sharing-overview/)), and the docs do not describe
  giving another user write access to a database the owner holds, so the service account would have to own the data.

## 2026-10-15: the nightly build, and `check_failures` as a table

**Decision (owner, 2026-10-15).**
- **Nightly:** one command, which rebuilds the 7 tables and runs the 24 data checks:
  `uv run dbt build --project-dir dbt --profiles-dir dbt --select config.materialized:table test_type:singular --indirect-selection empty --no-populate-cache`
- **`checks.check_failures` is a table**, not a view. The 24 checks read it once instead of each working it out
  again from the raw JSON. It shows the failures as of its last build, so it must be rebuilt before the checks run;
  the nightly command does this.
- **Weekly, and after any change to models, seeds or exceptions:** a full `dbt build`. It reloads the seeds,
  re-creates the views, and runs the 28 key tests the nightly run leaves out (uniqueness, not-null and relationship
  tests on the 7 tables), plus the generic tests on the staging views.

**Measured 2026-10-15** on the Business trial (Standard instance). Three runs, each in its own time window, read from
`md_information_schema.query_history` and dbt's log:

| | 1. Two commands, `check_failures` a view | 2. Two commands, a table | 3. One `dbt build`, a table (chosen) |
|---|---|---|---|
| Statements dbt sent (its log) | 119 | 131 | 113 |
| Statements in query history | 82 | 89 | 88 |
| Execution time in query history | 28.7 s | 9.5 s | 9.6 s |
| of which the 24 checks | 19.4 s | 0.2 s | 0.2 s |
| Statements over 1 s | 18 | 4 | 4 |
| Worst case per night (every recorded statement at 1 CU-second minimum) | 89 CU-s | 93 CU-s | 92 CU-s |
| Worst case per month (30 nights) | 0.74 CU-h | 0.77 CU-h | 0.77 CU-h |
| Share of the free plan's 10 CU-hours | 7.4% | 7.7% | 7.7% |

**What the measurement shows.**
- **Only 31 statements do real work:** 7 table builds and 24 checks. The rest is dbt bookkeeping: per table, a build
  under a temporary name, two renames, a drop, an index lookup and a transaction; per check, a BEGIN and a ROLLBACK.
- **Query history never records** BEGIN or dbt's catalog and index lookups. It does record ROLLBACK, COMMIT, rename,
  drop and `create schema`, each taking milliseconds. Run 3 saves only statements that query history does not record.
- **Billing of those statements is unknown.** The [pricing page](https://motherduck.com/docs/about-motherduck/billing/pricing/)
  says Pulse is metered "on a per-query basis, with a minimum of 1 Compute Unit (CU) second" and names no
  exemptions. The worst case above counts every recorded statement as billed.
- **The table change cuts execution time, not the worst case.** At the 1 CU-second minimum, 24 tiny checks still
  count 24 CU-seconds.
- **Not verified:** whether Pulse runs these as fast as the trial's Standard instance. Ingest and querying are extra.

**Avoidable bookkeeping, not applied.** Replacing dbt's rename-and-drop table build with a single
`create or replace table` would save about 5 statements per table (about 35 a night). It needs a project override of
dbt-duckdb's table materialization, which is extra code to maintain.

**To confirm after the trial:** the [Billing page](https://motherduck.com/docs/about-motherduck/billing/managing-billing/)
shows compute in CU-hours per user and service account, and the current month's invoice so far. Its docs describe no
daily breakdown, and do not say whether a free-plan account sees usage below the allowance.

## 2026-10-14: MotherDuck plan, Business trial until 2026-10-19, then the free Lite plan

**Fact (from the owner, read on the Plans page).** The account is on a MotherDuck Business trial that ends on
**2026-10-19**. The owner expects to be on the free Lite plan after that.

What MotherDuck's docs say changes on the free Lite plan (read 2026-10-14):

- **Compute** ([Pricing model](https://motherduck.com/docs/about-motherduck/billing/pricing/)):
  - "Pulse only" instances.
  - "The Lite plan includes 10 CU hours on Pulse per month."
  - Pulse is metered "on a per-query basis, with a minimum of 1 Compute Unit (CU) second", with no cooldown. The
    page's example: "2 queries x 10s = 20 CU seconds".
  - "Additional usage is billed at the rates above": $0.60 per hour for Lite Pulse in Tier 1.
  - The page does not say whether a free account is blocked or charged when the allowance is used up.
- **History retention** ([Storage lifecycle](https://motherduck.com/docs/concepts/storage-lifecycle/)): 0 days,
  fixed, on Lite (free). Today it is 7 days on the trial. Retained history from rebuilds should therefore stop
  accumulating after the trial; failsafe retention (7 days for standard databases) still applies.
- **Usage visibility** ([Monitoring usage and costs](https://motherduck.com/docs/about-motherduck/billing/monitoring-usage/)):
  - `md_information_schema.query_history` "records every query run across your organization" and is "available on
    Business plans". It reports execution time, not compute units, and "approximates" billed compute.
  - The Billing page (app.motherduck.com/settings/billing) breaks costs down per user and service account.
  - After the trial, the Billing page is the documented place to see usage.

**Consequence for the daily run:** under per-query metering with a 1 CU-second minimum, the **number of queries**
matters as much as their length. See the measurement and the lighter daily build in `docs/status.md`.

## 2026-10-14: storage finding, retained history from rebuilds (no decision yet)

**Observed.** MotherDuck's `md_information_schema.storage_info` for `nhl` (computed 2026-10-14 18:12):
- active bytes: **33.0 MB (31.5 MiB)**;
- historical bytes: **264.3 MB (252 MiB)**;
- retained-for-clone and failsafe bytes: 0;
- snapshot retention: **7 days**.

`pragma_database_size()` reported 45.5 MiB at the same time. What that figure includes is not documented.

**Cause.** Consistent with dbt re-creating the mart tables and reloading the seeds on every build. MotherDuck's
docs say:
- data moves from active to historical bytes when it is "deleted or updated in the database";
- "create or replace tables" is one of the workloads that "tend to delete a lot of data"
  ([Storage lifecycle](https://motherduck.com/docs/concepts/storage-lifecycle/)).

That dbt's rebuilds are the specific source of our 264 MB is our inference, not measured per table.

**What MotherDuck's docs say about billing and the free plan** (read 2026-10-14):
- [Monitoring usage and costs](https://motherduck.com/docs/about-motherduck/billing/monitoring-usage/): "All four
  categories count toward your storage bill" (active, historical, retained for clone, failsafe). Storage is billed on
  average daily usage.
- [Pricing model](https://motherduck.com/docs/about-motherduck/billing/pricing/): "Users are billed for active data
  plus historical, retained, and failsafe bytes"; "Lite plan includes 10 GB of free storage".
- [Storage lifecycle](https://motherduck.com/docs/concepts/storage-lifecycle/): default historical retention is 7
  days on Business (configurable 0 to 90), 1 day fixed on Lite (paid), and 0 days fixed on Lite (free).
- **Not stated:** what happens when a free account exceeds 10 GB.

**Open points:**
- **Plan.** The database reports a 7-day retention, which the docs give as the Business default, not the free plan's
  0 days. Which plan this account is on has not been checked.
- **Growth.** If historical bytes count toward the allowance, as the billing pages say they count toward the bill,
  every full rebuild adds roughly the size of the rebuilt tables for 7 days.
- **Proposed remedy.** Incremental models for the large marts (see `docs/status.md`), not yet applied.

## 2026-10-14: proceed with the NHL's unofficial endpoints, for personal use

**Decision.** The owner decided to keep collecting data from `api-web.nhle.com`, `api.nhle.com/stats` and
`records.nhl.com`.

- **Unofficial and unlicensed.** These endpoints are not an official, documented or licensed API. No published
  API terms were found for them; they have no `robots.txt`, and the NHL publishes no documentation for them.
  The absence of terms is not taken as permission.
- **Risk accepted.** The owner understands the risk.
- **Use.** The project is for the owner's personal use.
- **Public content.** Anything public contains facts and figures only, with no NHL logos, photos or video.
  **Changed 2026-11-11** (see "2026-11-11: logos, headshots and photos in posts"): NHL team logos, NHL API headshots
  and free-licence photos are now allowed, credited in the caption. Video is still not covered.

What the NHL Terms of Service say ([nhl.com/info/terms-of-service](https://www.nhl.com/info/terms-of-service),
last updated 29 October 2025, read on 2026-10-14):

- **Section 1 (scope).** The terms govern "the digital platforms, websites and online services", including
  "nhl.com, and NHL mobile applications". The API hosts are not named, and it is unclear whether they count as
  "the Services".
- **Section 2 (prohibited conduct).** "Engage in unauthorized spidering, scraping, or harvesting of content or
  information … or use any other unauthorized automated means to compile information."
- **Section 7 (NHL Content).**
  - Use is allowed "only for non-commercial, informational, personal use", "without modification or alteration".
  - "Unless expressly permitted by an authorized person in writing or as permitted by applicable law, you may
    not copy, reproduce, distribute, publish … create derivative works from, transmit, or in any way use or
    exploit any part of the NHL Content."
- **Statistics.** The terms do not mention statistics, scores or game data specifically.

Related: the [NHL Online Transmission Policy](https://www.nhl.com/info/online-transmission-policy) (undated)
says the NHL owns the copyrights in "accounts and descriptions of NHL games", and limits play-by-play in
game reports. That matters for any public use of play-by-play data (fights, Tier 2).

What follows from the decision:
- **Repo:** no NHL data files in the public repo.
- **Logs:** nothing from the NHL printed in logs.

Both rules are in `CLAUDE.md`.

## 2026-10-14: fights and travel stay in scope

**Decision.** The fight questions (P14, P19) and the travel questions (T09, T10) in
`analyst/golden_questions.yml` stay in scope. They are marked `in_scope: true`, `load_status: not_started`,
and their `blocked_on` lists what is missing. Nothing has been loaded for them yet.

### Fights: what it will cost

Fights exist only as penalty events in each game's play-by-play
(`api-web.nhle.com/v1/gamecenter/{id}/play-by-play`), one request per game. Loading every game would take
about 72,000 requests (about 20 hours at one request per second).

**The cheaper route.** The stats API's per-game team penalty report
(`api.nhle.com/stats/rest/en/team/penalties?isGame=true`) says how many major penalties each team took in each
game. It takes one request per season and game type, about 220 for all history. The same rows also answer
the bench-minor question, T07. Play-by-play is then loaded only for games with at least one major.

Read-only test on 2026-10-14 (about 300 requests, nothing saved):

| Season | Games with a major | Sampled flagged games with a fight | Fights in sampled unflagged games | Fighting share of majors (sampled) |
|---|---|---|---|---|
| 1960-61 | 41 of 210 (20%) | 16 of 25 | 0 of 25 games | 52 of 65 |
| 1975-76 | 271 of 720 (38%) | 21 of 25 | 0 of 25 games | 57 of 62 |
| 1990-91 | 509 of 840 (61%) | 23 of 25 | 0 of 25 games | 76 of 84 |
| 2005-06 | 379 of 1,230 (31%) | 23 of 25 | 0 of 25 games | 56 of 59 |
| 2018-19 | 213 of 1,271 (17%) | 24 of 25 | 0 of 25 games | 54 of 56 |

What the test shows:

- **No fights are missed in the sample.** None of the 125 sampled unflagged games had a fighting penalty in
  play-by-play.
- **The counts agree.** In every sampled game, the play-by-play majors equal the stats API majors, and the
  play-by-play penalty minutes equal the stats API penalty minutes (250 of 250 games).
- **Non-fighting majors add some noise, mostly in older seasons.** Flagged games without a fight were 36%
  of the sample in 1960-61 and 4% in 2018-19. The only cost is a wasted request; nothing is counted wrongly,
  because the fights themselves are read from play-by-play.
- **Where labelled fights start: 1947-48 (from a sample).**
  - In 1917-18, 1930-31, 1945-46 and 1946-47, every sampled major is recorded only as "major", with no type.
  - From 1947-48 to 1960-61, 4 flagged games were sampled per season, and every season has majors labelled
    "fighting".
  - All 440 fighting penalties seen in that follow-up sample have type code MAJ.
  - Not proven: whether labelling changed partway through 1946-47 or 1947-48, because only 4 flagged games
    per season were sampled.
- **Limit.** Both sources are the NHL's own records. A fight the NHL never recorded as a fighting major will
  not appear in either one.

How reliable the major flag is (first test, 2026-10-14):

- **Fights missed (unflagged games with a fight): 0 of 125.** That is 25 regular-season games in each of
  1960-61, 1975-76, 1990-91, 2005-06 and 2018-19.
- **How strong that is:** with 0 found, the miss rate is at most about 12% per era and about 2.4% across all
  five, at 95% confidence.
- **Unproven:** playoffs (no playoff games tested), the seasons between the five sampled, and 1947-48 to
  1959-60.

Exact counts (follow-up run, 2026-10-14, 346 requests). Games with at least one major from the per-game team
penalty report:

| Era | Regular-season games flagged | Playoff games flagged | Total flagged | Share of games | Play-by-play size per game (sampled) |
|---|---|---|---|---|---|
| 1960-61 to 1966-67 | 295 of 1,470 | 25 of 124 | 320 | 20% | about 15 KB |
| 1967-68 to 1979-80 | 2,923 of 8,096 | 243 of 562 | 3,166 | 37% | about 16 KB |
| 1980-81 to 1994-95 | 7,291 of 12,844 | 555 of 1,188 | 7,846 | 56% | about 18 KB |
| 1995-96 to 2006-07 | 5,407 of 12,833 | 122 of 937 | 5,529 | 40% | about 30 KB |
| 2007-08 to 2025-26 | 6,348 of 22,842 | 207 of 1,700 | 6,555 | 27% | about 112 KB |
| **1960-61 to 2025-26** | **22,264 of 58,085** | **1,152 of 4,511** | **23,416** | **37.4%** | |

| Step | Requests | Time at 1 per second | Raw size |
|---|---|---|---|
| Team penalties per game (flags), 1960-61 to 2025-26, regular season and playoffs | 130 | about 2 minutes | small |
| Play-by-play for flagged games, 1960-61 to 2025-26 | 23,416 | about 6.5 hours | about 1.1 GB as JSON (each season's sampled average size times its flagged games) |
| Optional: flagged games 1947-48 to 1959-60 | 609 more | about 10 minutes | about 9 MB |
| Player pages, for college seasons (P14 only) | about 8,000 | about 2.5 hours | to measure |

The size is an estimate from 2 to 4 sampled games per season, not a measurement. The size estimate matters
against MotherDuck's 10 GB cap, so it belongs with the Tier 2 storage decision in `CLAUDE.md`. A pilot of
one or two seasons measures it first.

### Travel: what it will cost

The NHL data names each game's venue but gives no coordinates, and it does not show a team's actual flights.

- **No NHL requests.**
- **One hand-made reference table**, `dbt/seeds/venue_coordinates.csv`. It has one row per venue name as the
  NHL writes it, with latitude, longitude, the source for each row, and whether the name is a rename of a
  building already listed. 217 distinct venue names appear in regular-season and playoff games, including 90
  neutral-site venues, so the number of distinct buildings is lower.
- **A decision on D20** (the travel definition) in `docs/definitions.md`.

Candidate sources for the coordinates are in the next section. Building and checking the table is about a day
of careful work, done in reviewable batches.

### Sources for arena coordinates

| Source | What it covers | Licence | Notes |
|---|---|---|---|
| Wikidata (`P625` coordinates; `P115` home venue, with start and end dates) | Current and many demolished arenas; team-to-venue history with dates | CC0 (public domain) | Recommended first source. It can be queried in bulk, and its licence lets us publish the table in a public repo. Each value still needs checking by eye. |
| Wikipedia arena articles (infobox coordinates) | Nearly every NHL arena, including historic ones | CC BY-SA 4.0 for the text | Good for checking by hand and for the rows Wikidata lacks. Coordinates are facts; cite the article per row. |
| OpenStreetMap, via Nominatim | Buildings that exist today | ODbL (attribution, share-alike for databases) | Demolished arenas are mostly missing. Nominatim's usage policy allows at most one request per second. The share-alike terms would apply to our table. |
| GeoNames | Cities, not buildings | CC BY 4.0 | A fallback at city level, within a few kilometres, enough for travel distances. |
| Natural Earth populated places | Major cities | Public domain | A coarser city-level fallback. |

### Venues that changed name or location

What our own data shows (regular season and playoffs, not counting neutral sites):

- **Several lineages have used 5 to 7 venue names.** Florida, Carolina and Tampa Bay have 7 each; Arizona,
  Los Angeles, Philadelphia, Calgary and Montreal have 6.
- **A name change can be a rename or a move, and the data cannot tell which.**
  - Montreal: Jubilee Rink, then Mount Royal Arena, then Montreal Forum, then Centre Molson and Centre Bell.
    By general knowledge, Centre Molson and Centre Bell are the same building renamed, while the Forum was a
    different building. This is to confirm per row against a source.
  - Vancouver: Pacific Coliseum, then General Motors Place and Rogers Arena (by general knowledge, the
    latter two are the same building).
  - So the table needs one row per venue name, plus a building id, so renamed buildings share coordinates.
- **Franchise moves change a lineage's home city.** Examples: Winnipeg to Phoenix, Quebec to Colorado,
  Hartford to Carolina, Atlanta to Calgary. The "home" a team returns to must come from the season, not the
  lineage.
- **Neutral-site games are common in some seasons.**
  - 2019-20 has 130 games at Rogers Place and Scotiabank Arena, the two cities where the season resumed.
  - Others include 1993-94 neutral-site games such as Target Center and O-Rena, early playoff series such as
    Denman Arena in 1922-23, and 1967-68 games at Le Colisée.
  - These games use their own venue, not the home team's arena.
- **Garbled names.** Four venue names arrive garbled from the NHL (see `docs/data_coverage.md`). The table
  should list them exactly as written, so the join still works.
