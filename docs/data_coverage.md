# Data coverage: where the data is thin or different by era

This file records what we have observed in the NHL's data. It states causes only where a
source has been checked. Anything marked "unexplained" is an observation without a confirmed cause.

Status: written before the full history was loaded. Statements marked "from the game list"
come from the NHL's all-seasons game list. Statements marked "sampled" come from a handful of
weekly schedule responses. Each section will be confirmed against the loaded data.

## Ties

- The NHL's season facts mark ties as possible (`tiesInUse` = 1) in 87 seasons, from 1917-18 to 2003-04, and as not possible from 2005-06 onward.
- From the game list: no season marked as having no ties contains a regular-season game with a level score.
- In `fct_games`, a tied game has `is_tie` true and an empty `winner_team_id`. Any "wins and losses" question about seasons up to 2003-04 has to account for ties.
- Observed 2026-10-15: 3,086 regular-season games have `last_period_type` = OT and `is_tie` true: they went to overtime and still ended level. `last_period_type` = OT therefore does not mean "decided in overtime"; add `NOT is_tie`.

## Shootouts

- Sampled: weekly schedule responses from 2005-06, 2012-13, 2019-20 and 2020-21 contain games with `last_period_type` = SO. Samples from 2003-04 and earlier contain only REG and OT.
- Confirmed after the full load (2026-10-14): the first regular-season game with `last_period_type` = SO is in 2005-06. The last regular-season tie is in 2003-04; there are 5,729 ties in total.
- Scores are the final scores the NHL reports. Observed in 2025-26: a shootout game's scores differ by exactly one.

## Preseason

- From the game list: preseason games (type 1) exist in only 31 seasons. There are none before 1980-81.
- From 1980-81 to 2003-04 at most 14 preseason games are listed in any season, and many seasons have none. From 2005-06 onward each season lists over 100, except 2012-13 and 2020-21, which list none.
- Preseason in `fct_games` should be treated as complete only from 2005-06.
- Observed after the full load (2026-10-14), all unexplained:
  - Two preseason games are in `fct_games` with `is_final` false: 2022010034 (CAR at TBL, 2022-09-28) and 2024010044 (NSH at TBL, 2024-10-07). The weekly schedule marks both `CNCL` (cancelled); the game list gives game state 1.
  - Two preseason games are in the game list but not in the weekly schedule, so they are not in `fct_games`: 2021010083 (2021-10-07, teams 2 at 1, state 1, never played) and 1990010214 (1990-09-09, team 22 at team 5560, 8-4, finished). Team 5560 appears in no other game and has no name in our data.

## The 2004-05 gap

- The NHL's season facts have no entry for season 20042005.
- The game list has 1,230 games for it, all of game type 13, dated 2004-10-13 to 2005-04-10. Every one has a 0-0 score, no period recorded and game state 6.
- Sampled: the weekly schedule returns no games for 2005-01-15 and points to September 2005 as the next week with games.
- Cause (sourced): the 2004-05 season was cancelled on 2005-02-16 and its 1,230 games were not played ([Wikipedia: 2004-05 NHL season](https://en.wikipedia.org/wiki/2004%E2%80%9305_NHL_season)).
- In our tables: these rows stay in staging, labelled `cancelled` (approved 2026-10-14), and never reach `fct_games`. The missing season facts are a documented exception in `dbt/seeds/check_exceptions.csv`.

## 1917-18 anomalies

- The season facts say 22 games per team and 34 regular-season games in total. From the game list: there are 36 regular-season games and four teams, three with 22 games and one (Montreal Wanderers) with 6.
- The Wanderers' last two listed games, on 1918-01-02 (against the Canadiens) and 1918-01-05 (against Toronto), both have a 1-0 score.
- Source: the Wanderers withdrew in January 1918 after their arena burned, and two of their games count as wins for the Canadiens and Toronto ([Wikipedia: 1917-18 Montreal Wanderers season](https://en.wikipedia.org/wiki/1917%E2%80%9318_Montreal_Wanderers_season)).
- The NHL's total of 34 is consistent with excluding those two forfeits, but no source confirms that. Documented as exceptions in `dbt/seeds/check_exceptions.csv`.
- The playoff total (7) matches the game list.

## Seasons where teams did not all play the scheduled number of games

- From the game list: besides 1917-18, the only such season is 2019-20, where the facts say 82 games per team and 1,082 games in total, and teams have between 68 and 71 games.
- Cause (sourced): the NHL paused the season on 2020-03-12 after 1,082 of 1,271 scheduled regular-season games ([NHL.com: return-to-play plan](https://nhl.com/news/nhl-announces-return-to-play-plan-317031134)). Documented as an exception.

## Non-NHL opponents

- From the game list: 55 team IDs appear in preseason or playoff games but are not in the NHL's team list. None appear in regular-season games.
- Sampled: the 1918 playoff game on 1918-03-30 lists "Vancouver Millionaires" (VMI, team 7288) at Toronto.
- In `dim_teams` these have `is_nhl_team` false, no franchise and no lineage. Their name and seasons come only from the games they appear in.
- Special events (all-star games, international tournaments) use further team IDs that are not NHL clubs. Those games are not in `fct_games`.

## Shots (play-by-play)

Loaded 2026-11-10 to 2026-11-11: every finished regular-season and playoff game from 2007-08 to today, one
play-by-play response per game from api-web.nhle.com. Only the shot events are in MotherDuck; the full responses are
on the owner's laptop.

- **2,714,604 shot events in 24,827 games**, 2007-08 to 2026-27 (in progress), in `marts.fct_shots`.
- **Goals match the scores.** Leaving out shootouts, each team's goals equal its final score in every game of every
  season (check `shot_goals_match_score`, 2026-11-11).
- **Shooting team.** The event's owner team is the shooter's team (checked against each game's roster in the
  downloaded files) for every shot type, blocked shots included, with 3 exceptions in 2.9 million events: one event
  each in 2012-13 and 2015-16 whose owner team differs from the shooter's roster team, and one in 2013-14 whose shooter
  is not on the game's roster. Unexplained; not investigated.
- **2007-08 and 2008-09 are thin.** Goals and shots on goal look complete (7,491 and 7,840 goals; 70,603 and 73,369
  shots on goal), but missed shots are almost absent (29 and 27 in the whole season) and blocked shots absent (0).
  Shot attempts (Corsi, Fenwick) can only start in 2009-10. Coordinates are missing on 99.6% of events in both
  seasons, so shot and goal locations start in 2009-10.
- **Coordinates from 2009-10:** missing on 115 events in 2009-10, 27 in 2010-11, under 25 a season after that, and
  none from 2020-21. Observed range: x from -99 to 99, y from -42 to 42. Units are not documented by the NHL.
- **Zone** is from the shooter's side: in 2025-26, 8,317 of 8,572 non-shootout goals are in zone O, 131 in D, 124 in N.
- **Shots per season** (regular season and playoffs, shootouts included), for reference:

  | Season | Events | Games | Goals | On goal | Missed | Blocked |
  |---|---|---|---|---|---|---|
  | 2007-08 | 78,123 | 1,315 | 7,491 | 70,603 | 29 | 0 |
  | 2008-09 | 81,236 | 1,317 | 7,840 | 73,369 | 27 | 0 |
  | 2009-10 | 148,018 | 1,319 | 7,767 | 73,163 | 31,018 | 36,070 |
  | 2010-11 | 150,472 | 1,319 | 7,544 | 73,822 | 31,255 | 37,851 |
  | 2011-12 | 147,461 | 1,316 | 7,370 | 71,894 | 30,765 | 37,432 |
  | 2012-13 | 90,068 | 806 | 4,480 | 43,525 | 18,747 | 23,316 |
  | 2013-14 | 149,845 | 1,323 | 7,506 | 73,120 | 31,431 | 37,788 |
  | 2014-15 | 149,467 | 1,319 | 7,377 | 72,659 | 30,887 | 38,544 |
  | 2015-16 | 148,192 | 1,321 | 7,281 | 71,986 | 30,997 | 37,928 |
  | 2016-17 | 149,661 | 1,317 | 7,377 | 73,022 | 31,313 | 37,949 |
  | 2017-18 | 160,727 | 1,355 | 8,187 | 78,950 | 33,416 | 40,174 |
  | 2018-19 | 157,478 | 1,358 | 8,250 | 77,689 | 32,502 | 39,037 |
  | 2019-20 | 139,200 | 1,212 | 7,361 | 69,259 | 28,416 | 34,164 |
  | 2020-21 | 104,316 | 952 | 5,636 | 52,098 | 21,385 | 25,197 |
  | 2021-22 | 160,574 | 1,401 | 8,936 | 80,649 | 32,765 | 38,224 |
  | 2022-23 | 164,416 | 1,400 | 9,027 | 79,059 | 34,625 | 41,705 |
  | 2023-24 | 171,256 | 1,400 | 8,772 | 76,160 | 38,204 | 48,120 |
  | 2024-25 | 167,558 | 1,398 | 8,604 | 70,828 | 41,030 | 47,096 |
  | 2025-26 | 163,818 | 1,394 | 8,836 | 69,507 | 41,811 | 43,664 |

- **Strength (`situation_code`)** is on non-shootout goals only from 2009-10: none of the 2005-06 to 2008-09 goals
  have it (checked 2026-11-13). For power-play goals before then use `fct_skater_seasons` or `fct_skater_games`.
- **Before 2007-08 (loaded 2026-11-11 to 2026-11-12, from 1917-18; checked 2026-11-13):** 876,659 shot events in
  45,648 of the 45,810 finished regular-season and playoff games. Of the 162 games without any, 160 ended 0-0, so
  there is no goal to record. The other two are 1-0 wins over the Montreal Wanderers (1918-01-02 at Montreal,
  1918-01-05 at Toronto) whose play-by-play response holds no events at all (checked 2026-11-13). They are the two
  games the Wanderers' withdrawal turned into wins (see the 1917-18 exception for `regular_season_game_count`); the
  empty play-by-play fits games that were not played, but no source says so. Check `shot_goals_present` (every game
  with a goal outside a shootout has goal rows) lists them as its only exceptions.
  - **Goals match the scores in every game of every season** (check `shot_goals_match_score`). Every goal has a
    scorer, and every scorer's team matches their team in that game in `fct_skater_games` (285,198 goals, no
    exception).
  - **Goals only before 1997-98:** no shots on goal, missed or blocked shots in the play-by-play.
  - **Shots on goal from 1997-98**; missed shots almost absent (46 in 2005-06 and 2006-07) and no blocked shots, as in
    2007-08 and 2008-09. Shot type is on goals from 1997-98 (80% that season, over 99% from 1998-99).
  - **Coordinates:** none before 2005-06; 160 events in 2005-06 and 289 in 2006-07.
  - **Assists:** the share of goals with a first assist is 40-65% in 1917-18 to 1928-29, about 75% from 1929-30 and 85-90%
    from the mid-1930s on; second assists are rare before the 1930s. Whether that reflects the scoring rules of the time
    or gaps in the record is unexplained.
  - **Malformed clock times:** two penalties in 1985-86 have a period time the NHL wrote as `0M:48` and `10:0J`; their
    `time_in_period_seconds` is empty (nothing is guessed).
  - **Shootouts 2005-06 and 2006-07:** the play-by-play and the shootout report agree for 562 of 575 player-seasons;
    2005-06 has 332 goals in the play-by-play and 330 in the report, 2006-07 has 1,222 attempts and 1,215. Unexplained.

## Hits and penalties (play-by-play)

Loaded 2026-11-11 from the same laptop files as the shots (no new downloads), and nightly from then on:
`raw.nhl_web__pbp_event`, `marts.fct_hits` and `marts.fct_penalties`.

- **Hits: 1,033,173 in 22,194 games, 2009-10 to today.** 2007-08 and 2008-09 have no hit events at all (like their
  missed and blocked shots). The play-by-play before 2007-08 has no hits in any season (checked 2026-11-13).
- **Penalties: 207,017, 2007-08 to today** (older seasons below), of which 15,884 are fighting penalties (`is_fight`; every one a 5-minute
  major). A fight is one fighting penalty per player (definition 1, owner 2026-11-11), so one fight between two
  players is two rows. About 250 to 350 penalties a season name no player (bench minors and the like).
- **Team check:** every hit's team is the hitter's team, and every penalty's team the penalised player's team, on the
  game's roster in the downloaded files: 2.1 million events, no exception (checked 2026-11-11).
- **Fights per regular-season game** (fighting penalties / 2): 0.53 in 2007-08, 0.59 in 2008-09, then down to 0.18 in
  2018-19 and 2019-20, about 0.23 to 0.25 since.
- **Before 2007-08 (loaded 2026-11-12, checked 2026-11-13):** 568,173 penalties in 45,721 games, 1917-18 to 2006-07,
  every penalised player's team matching their team in that game in `fct_skater_games` (554,083 with a player, no
  exception). Penalty drawn by (`drawn_by_player_id`) starts in 1997-98.
  - **Fights are identifiable only from 1947-48.** Before that, majors are recorded as a generic "major" (1,852
    of them) with no "fighting" label, so `is_fight` is false for every earlier penalty. Never count fights before
    1947-48 as zero; say the data does not record them. 49,469 fighting penalties from 1947-48 to 2006-07.
  - Penalties naming no player: under 30 a season before 1967-68, about 40 to 400 a season after.

## Play events (faceoffs, giveaways, takeaways, stoppages)

Loaded 2026-11-13 from the laptop's play-by-play files, and nightly from then on: `raw.nhl_web__pbp_play`,
`stg_nhl_web__pbp_plays`, `marts.fct_faceoffs`, `fct_giveaways`, `fct_takeaways`, `fct_stoppages`.

- **From 2009-10 only.** Sampled games before 2009-10 hold goals, penalties and (from 1997-98) shots only.
- **Rows (2026-11-13):** 1,298,104 faceoffs, 427,843 giveaways, 294,988 takeaways, 1,010,513 stoppages and 147,275
  period start and end markers, in every game with play-by-play since 2009-10 except one: game 2009020714, whose
  play-by-play holds only goals and penalties.
- **Teams:** every faceoff winner and loser is on the team the event gives them, and every giveaway and takeaway
  player on theirs (skaters in `fct_skater_games`; 21,609 giveaways and 570 takeaways are by goalies, checked in
  `fct_goalie_games`). Checked 2026-11-13, no exception.
- **Faceoff win % against the official totals** (`fct_skater_seasons.faceoff_win_pct`, regular season 2009-10 to
  2025-26): 9,346 of 9,508 player-seasons agree within 0.05 points; 31 differ by more than 1 point. Unexplained.
- **Giveaways and takeaways** are counted by arena scorers, so counts differ between arenas, as with hits.
- **Stoppage reasons** as the NHL names them: goalie-stopped-after-sog, icing, offside, puck-in-netting...

## Team game statistics

`marts.fct_team_game_stats` (2026-11-13), from the NHL stats API's per-game team reports. Observed when loaded:
- **Power-play opportunities and times short-handed: 1977-78 onward.** Before that the NHL's fields are empty from
  1933-34 and hold a few stray values before (37 opportunities in all against 495 power-play goals), so the mart
  leaves them empty before 1977-78. Power-play goals, short-handed goals and penalties exist from 1917-18.
- **Shots from 1959-60; power-play and short-handed time from 1997-98.**
- **Goals leave out the shootout goal:** the report's goals equal the final score except for the shootout winner, one
  goal fewer (all 2,628 shootout games).
- **No rows for playoff games against PCHA and WCHL teams** (1917-18 to 1925-26, 43 games): the NHL keeps no team
  stats for them.
- **Penalties drawn** equal the opponent's penalties in 99% of games: the opponent's count, not a separate stat.
- Checked: power-play goals against equal the opponent's power-play goals, short-handed goals the opponent's
  short-handed goals against, times short-handed the opponent's opportunities, in every game; season sums match the
  NHL's season report.

## Shifts

`marts.fct_shifts` (2026-11-13), from the NHL's shift charts (stats API), 2010-11 onward; earlier games return
nothing. Observed when loaded:
- **Empty charts:** 50 consecutive games of 2026-27 (game numbers 154 to 203, 2026-10-22 to 29) had an empty chart,
  still empty when asked again on 2026-11-13; cause unknown. Their shifts come from the NHL's HTML shift reports
  (`source` = html_report), which were complete. Report names matched to player IDs (all matched); every player's
  report total equals the official time on ice to the second. The same in the backfill: 57 consecutive games of
  2024-25 (2024021235 to 2024021291) had an empty chart, and one game of 2013-14 (2013020971) had a chart with a
  single goal marker and no shifts. All 58 were filled from the HTML reports; every name matched and all 2,207
  player-games' report totals equal the official time on ice to the second. Cause of the empty charts unknown.
- **Chart totals vs official ice time (2026-27, 248 games):** 8,780 of 8,927 player-games within 1 second; 71 off by
  more than a minute (largest 287 s). Unexplained.
- A team's shifts add up to about 6 x 60 minutes a game (goalie included); shifts average 57 seconds.

## Overtime rules

`reference.overtime_rules` (2026-11-13). The play-by-play shows the early regular-season eras: before 1921-22 no
game ended tied and overtime goals came as late as the 17th minute; 1921-22 to 1926-27 goals to the 20th minute and
ties; 1927-28 goals only to the 10th minute; from 1928-29 up to four overtime goals in one game (the 10-minute period
was played in full). Playoff overtime has always been sudden death, never with two overtime goals in a game, up to
6 overtime periods. Two playoff games are recorded as ties although an overtime goal was scored (1930-03-26 MTL-CHI
2-2, 1934-03-25 CHI-MTL 1-1), both second games of two-game total-goals series; unexplained beyond that. Four tied
playoff games went to overtime with no goal and no recorded overtime length (1919-03-26, 1927-04-07, 1927-04-11,
1951-03-31), so their overtime minutes are unknown.

## Shootout totals (skaters)

Loaded 2026-11-11: the stats API's skater shootout report, one response per regular season from 2005-06 (the first
season with shootouts), 22 requests; the current season refreshes nightly. `marts.fct_skater_shootouts` keeps the
skaters with at least one attempt (the report also lists every other skater, with zeros).

- **Against the play-by-play (2007-08 onward):** 4,823 of 4,928 player-seasons have the same attempts and goals in
  both. Goals differ for 16 player-seasons (mostly 2009-10: 449 goals in the report, 432 in the play-by-play) and the
  report has 90 more attempts in total (10 player-seasons appear only in the report). Unexplained; for shootouts use
  `fct_skater_shootouts` and say which source a number comes from.
- 2005-06 and 2006-07 are now in the play-by-play too; see "Shots" for how they compare.

## Player pages (seasons in every league)

Loaded 2026-11-11 and 2026-11-12: the NHL's player page for everyone in the player list (23,575 people, every one
with a page), full pages as files on the laptop, season totals in `raw.nhl_web__player_season_total` (622,606
entries). `marts.fct_player_league_seasons` holds 622,462 rows for 23,242 people in 1,895 leagues (81,040 NHL rows);
333 people have a page with no season totals. Pages are a snapshot: the 2026-27 rows are as of the load.

- **Exact repeats:** 144 entries appear word for word twice on the same page; each is kept once.
- **NHL skater seasons against `fct_skater_seasons`** (regular season and playoffs): 69,714 of the pages' 69,727
  player-seasons are in our stats, and 69,392 have the same games, goals and points. Of the 322 that differ, 249 are
  2026-27 (the pages were fetched after the stats' nightly load) and 71 are 1910s and 1920s, mostly games played.
  Unexplained. The 13 not in our stats are 1919-20 and 1927-28 playoffs (10) and three 2026-27 seasons. Every
  skater-season with games in our stats is on the pages. For NHL totals use `fct_skater_seasons`.
- **NHL goalie seasons against `fct_goalie_games`:** 6,720 of 6,731 are in our stats; 6,696 have the same games played.
- Every NHL player in `dim_players` (8,838) has at least one NHL row on their page.
- **Repeated keys:** 336 players have more than one entry with the same season, league, game type and sequence that
  differ in team or stats (472 cases, most often J20 Nationell, J18 Nationell, ECHL, AHL, KHL, PCHA). Unexplained.
  All are kept; the key is the player plus a hash of the entry.
- **Game types 6 and 7** appear only for the W-Cup (171 and 1 entries); unverified, not labelled.
- **Fields by era and league:** games, goals, assists, points and penalty minutes are on nearly every entry; plus-minus,
  power-play and shorthanded figures, shots and time on ice only on some (mostly NHL and recent seasons).
- **Save percentage** is a fraction, except 3 entries above 1 (unexplained; kept as received).
- **Canada Cup and World Cup listed twice** (checked 2026-11-13, team Canada): many players have the same tournament
  under two codes a season apart: `CC` one season before `Can-Cup` (1976, 1981, 1984, 1987, 1991; 76 of 82 pairs
  identical) and `WCup`/`W-Cup` for 1996 and 2004 (28 pairs, all identical). Count each tournament once per player.
  Other senior codes for Canada: World Championships `WC-A`, `WEC-A`, `WC`, `WEC`; Olympics `Olympics`, `OG`;
  women's tournaments end in `(W)`.
- **Goalie rows have no points** in international tournaments (points empty, not 0).
- **League names are not consistent across eras** (checked 2026-11-13): older pages use codes such as `CzRep`,
  `Olympics`, `Sweden`; recent ones `Czechia`, `OG`, age groups (`Czechia U16`, `BEAST 16U`), and a country name can
  be a league or a national team (`Latvia`). Counting "leagues" needs a hand-checked list of which codes are leagues
  and at what level.
- **League levels** (`reference.league_levels`, approved 2026-11-13): 1,142 codes appear before NHL debuts; several
  codes mean different leagues in different eras (`USHL`, `WHL`, `WCHL`, `MHL`, `MPHL`, `ECHL`...), so the seed
  has season ranges. 8 codes could not be placed (`Other`, `(none)`, `Independent`, `Ind.`, `NOHA`, `RHL`, `ACH`,
  `OPHL` after 1950).
- **World Junior ages** (checked 2026-11-13 against `reference.world_junior_tournaments`): of 5,173 player
  tournaments with a birth date and at least one game, 8 give an impossible age at the start: Igor Boldin at 12 and 13
  (his birth date is recorded as 1970-01-01) and six players aged 22 to 34 on under-20 teams (Tom Anderson, USA 1989;
  Ivan Kulbakov, Belarus 2016; Mike Green, USA 2003; Niclas Wallin, Switzerland 1998; Sergei Zinovjev and Sergey
  Kalinin, Russia 2003 and 2014). Unexplained; leave them out of age questions. The 2022 tournament is listed under
  2021-22; whether those rows are the cancelled December games or the August replay is not known.
- **Coverage of other leagues** is whatever the NHL lists: a missing league or season is not proof a player never
  played there.

## Skater stats per game

Loaded 2026-10-17: the stats API's skater summary with `isGame=true`, 434 responses (date windows), 1.24 GB raw JSON.

- **2,421,850 rows** (one per skater per game, regular season and playoffs, 1917-18 to 2025-26), 7,923 skaters. That
  equals exactly the sum of games played in the season totals.
- **Per-game rows add up to the season totals** (games, goals, assists, points) for every player-season in every
  finished season (check `skater_games_match_seasons`).
- **The suspended 1988 Final game** (1988-05-24) has 36 skater rows under game ID 1987030999, which is not in our games
  (see "Skater stats"). Its team cannot be taken from the game, so `team_id` is empty for those rows.
- Early-era gaps are the same as the season totals: shots and plus-minus from 1959-60, ice time and faceoffs from
  1997-98. Playoff games against non-NHL teams up to 1925-26 have no rows.

## Records data: drafts, awards, playoff series, official team totals

Observed 2026-10-17 while building `fct_draft_picks`, `fct_award_results`, `fct_playoff_series` and `fct_team_seasons`.

- **Draft:** 13,152 picks, 1963 to 2026. 790 have no NHL player ID; 5,658 drafted players later played an NHL game.
- **Awards:** several winners in one season are normal for some trophies. The Stanley Cup results list every player
  engraved on the Cup (up to 32 a season); the Vezina, Jennings, Rocket Richard and a few others have been shared.
  One 1925-26 Stanley Cup runner-up row uses a team ID that is not in our teams (4814).
- **Playoff series list:** includes the 7 knockout games of the 2004 World Cup of Hockey (game type 7), filed as
  2003-04 series with letters that overlap the NHL first round. `fct_playoff_series` and `bridge_playoff_series_games`
  keep NHL playoff games (type 3) only.
  - `games_needed_to_win` is 0 for 37 series from 1917-18 to 1935-36, consistent with series decided on total goals;
    the winner is then the team with more goals when wins are level.
  - 1919 Final (Seattle v the Canadiens): stopped at 2-2-1 by the flu epidemic and never finished; no Cup awarded
    ([Wikipedia](https://en.wikipedia.org/wiki/1919_Stanley_Cup_Final)). No winner in `fct_playoff_series`.
  - 1927 Final (Ottawa v Boston): Ottawa won 2-0-2 in a series where ties were allowed, although the NHL's list says
    3 wins were needed ([Wikipedia](https://en.wikipedia.org/wiki/1927_Stanley_Cup_Final)).
- **Official team totals:** from 2005-06 the official goals for and against equal our games' totals minus one per
  shootout won (for) or lost (against), for every team-season (check `team_season_goals_match_games`). That is
  consistent with the official totals leaving out the extra goal a shootout win adds to the final score. 1917-18: the
  two Wanderers forfeits recorded as 1-0 are in our games but not in the official goals (Toronto and the Canadiens
  +1 goal for, the Wanderers +2 against).

## Birthplaces

Observed 2026-10-15 in the NHL's player list (`stg_nhl_records__players`).

- **Spellings:** 168 places appear under more than one spelling within the same country and province (capitals,
  accents, punctuation, Saint and St.). In 16 of them a second spelling belongs to NHL players. Those 16, plus
  local and English names of the same city (Göteborg and Gothenburg, Praha and Prague, Moskva and Moscow), are
  merged in `dbt/seeds/birth_city_spellings.csv` (22 rows, 38 NHL players). The other 152 groups affect only people
  with no NHL game and are left as recorded.
- **No birth city:** 278 people, none with an NHL game.
- **Former names and suburbs are separate places** in the NHL's data: Fort William, Port Arthur (now Thunder Bay),
  Berlin (now Kitchener), South Porcupine and Schumacher (now Timmins), Rouyn and Noranda (now Rouyn-Noranda),
  Leningrad (now St. Petersburg), and Scarborough, Etobicoke, North York, Weston, Verdun or Lachine. We keep them
  separate (D14).
- **Compared with QuantHockey's city totals** (regular season, top 50 cities pasted by the owner, 2026-10-15):
  - QuantHockey counts goalies among players and groups by today's municipality. Timmins matches exactly once
    Timmins, South Porcupine, Schumacher and Porcupine are combined (39 players, 12,529 games, 3,057 goals); Thunder
    Bay's 97 players equal Thunder Bay, Fort William and Port Arthur combined.
  - Four cities match exactly on players, games, goals and assists; most others are within a few goals.
  - Not explained without their per-player lists: Toronto (ours 446 players and 19,073 goals, theirs 434 and
    17,558), Montréal (272 and 14,153; 271 and 14,272), Edmonton and Calgary.

## Franchises and lineage

- The NHL's franchise IDs group team identities. Observed: franchise 35 holds the Winnipeg Jets (1979), the Atlanta Thrashers and today's Winnipeg Jets. Franchise 28 holds the Phoenix and Arizona Coyotes, 1996-97 to 2023-24. Franchise 40 holds the Utah Hockey Club and Utah Mammoth, from 2024-25.
- `dim_teams.lineage_id` equals the NHL franchise unless `dbt/seeds/team_lineage_overrides.csv` says otherwise.
- **Our lineage differs from the NHL's attribution for the original Winnipeg Jets (1979-80 to 1995-96, team 33).** The NHL treats the Phoenix Coyotes as a 1996 expansion team and attributes the original Jets' records to today's Winnipeg Jets (franchise 35). Their players, coaches and staff moved to Phoenix in 1996 ([Wikipedia: Arizona Coyotes](https://en.wikipedia.org/wiki/Arizona_Coyotes), [Wikipedia: Winnipeg Jets](https://en.wikipedia.org/wiki/Winnipeg_Jets)), so our `lineage_id` puts team 33 with the Coyotes (28). `franchise_id` keeps the NHL's view. Totals grouped by `lineage_id` will therefore not match the NHL's official franchise records for the Jets or the Coyotes.
- Utah (franchise 40) is kept separate from the Coyotes, as the NHL has it. No override.

## Goalie stats

Status: observed in samples and on a local copy, 2026-10-14. To be confirmed after the full goalie load.

- **Shots:** goalie shots against and saves are recorded from 1955-56. The official team shots per season start
  in 1959-60.
- **Credited decisions:** every finished team-game sampled has exactly one credited goalie decision, and it
  matches the result.
- **OT losses:**
  - Goalie OT losses are recorded from 2005-06.
  - From 1999-00 to 2003-04 a goalie's overtime loss is recorded as L, while the team gets an OTL. Answers about
    goalie records in those seasons must say so.
- **Shutouts:** team shutouts can exceed goalie shutouts. That is consistent with shared shutouts, which are
  credited to neither goalie. Shutouts are also credited in some games won in overtime or a shootout.
- **Saves:** observed, unexplained. From 2022-23 on, about 0.5% to 0.9% of goalie rows per season have saves
  exactly one more than shots against minus goals against. There are none before 2022-23. They are spread over
  all teams and goalies, so they cluster by era, not by team or goalie.
  - An era rule in `goalie_saves_add_up` allows exactly this +1 from 2022-23 (approved 2026-10-14). Any other
    difference still fails.
  - `checks.goalie_saves_plus_one_by_season` shows the share per season. `goalie_saves_plus_one_rate` fails if
    it exceeds 2% in a season with at least 500 goalie rows.
- **Other saves differences:**
  - 1956-57 and 1958-59: shots against recorded as 0 with goals allowed.
  - 1979-80: one playoff game where two goalies are off by +2 and -2.

  All are excepted, observed, unexplained.
- **1917-18:**
  - No goalie rows for the two forfeit games.
  - No goalie rows for the five playoff games against the Vancouver Millionaires (team 7288), 1918-03-20 to
    1918-03-30.
- **Shots on an empty net:** per game, the opponent's team shots usually exceed the goalie's shots against by
  0 to 2. That is consistent with shots on an empty net, which count for the team but against no goalie.

## Skater stats

Status: all seasons loaded, 2026-10-15 (69,635 rows, 7,947 skaters).

- **Source:** the stats API's skater summary, one row per player, season and game type. Goalies are not in it.
- **Players who changed teams:** one row, with the teams listed together ("TOR,BOS"). The totals are not split
  by team. Observed: 6 of 39 rows in 1917-18, 81 of 940 in the 2025-26 regular season.
  - Such a player can have more games than any one team played: in 2025-26 one player has 83 regular-season games
    over three teams.
  - In 15 player-seasons (1924-25 to 2023-24) the same team appears twice in the list. That is consistent with a
    player who left a team and came back the same season; not checked against a source. The bridge table keeps
    each team once.
- **Thin early data:** in 1917-18, ice time, shots, plus-minus and faceoffs are empty for every row. Skater ice
  time and faceoffs start in 1997-98 (sampled, `docs/definitions.md`).
- **Goals against the final scores** (check `skater_goals_add_up`):
  - 1917-18 regular season: 342 credited goals against 344 in the final scores. The difference of 2 matches the
    two Montreal Wanderers forfeits recorded as 1-0 (see "1917-18 anomalies").
  - 1917-18 playoffs: 17 credited goals. They equal the goals in the two games between NHL teams (7-3 and 4-3);
    the five games against the Vancouver Millionaires (18 goals by Toronto) have no credited skater goals.
    Observed, unexplained. The goalie data has no rows for those games either.
  - The same holds in every playoff from 1918-19 to 1925-26 except 1919-20: credited skater goals equal exactly the
    goals in games between NHL teams, and games against non-NHL teams (Seattle, Vancouver, Edmonton, Calgary,
    Victoria) have none. In 1919-20 the only playoff series was against Seattle, and there are no playoff skater rows.
    Observed, unexplained. The opponents are sourced as champions of other leagues for 1922, 1923 and 1924
    ([1922](https://en.wikipedia.org/wiki/1922_Stanley_Cup_Final),
    [1923](https://en.wikipedia.org/wiki/1923_Stanley_Cup_playoffs),
    [1924](https://en.wikipedia.org/wiki/1924_Stanley_Cup_Final)).
  - 1987-88 playoffs: 628 credited goals against 622 in the final scores, and 15 Edmonton and 11 Boston skaters have
    one more game than their team. Source: game 4 of the Final (Boston Garden, 1988-05-24) was suspended at 3-3 after
    a power failure and replayed; its result does not count, but the players' statistics do
    ([Wikipedia](https://en.wikipedia.org/wiki/1988_Stanley_Cup_Final), [CBC](https://www.cbc.ca/1.5579029)). The
    suspended game is not in our games.

## Standings derived from games

`fct_team_standings_by_game` derives the standings before every regular-season game from `fct_games`, under each
season's points rules.

- **Official totals:** at season end they equal the NHL's official totals for 1,788 of 1,791 team-seasons
  (games, W, L, T, OTL and points).
- **The 3 differences:** each is one game that ended in overtime, which the NHL's official record counts as a
  regulation loss for the home team, while our rule counts it as an OT loss. Observed, unexplained.
  - Game 1999021129 (2000-04-07, team 23 lost 4-5 in OT)
  - Game 2002021141 (2003-03-25, team 26 lost 1-2 in OT)
  - Game 2023021166 (2024-03-30, team 30 lost 1-2 in OT)

  The NHL's per-game team report confirms all three. For the 2023-24 game the goalie is also credited with L.
- **Spot-check:** the standings before 4 games on 3 dates (1968-02-03, 1996-01-16, and two games on 2026-01-15)
  matched the NHL's standings for the previous day exactly, for all 8 teams.

## Standings rules by season

The NHL's standings rules come from `api-web.nhle.com/v1/standings-season` (`stg_nhl_web__standings_rules`).
What we checked on 2026-10-14:

- **Point for an overtime loss:** observed from 1999-00 onward, in every season since. Confirmed by
  [Wikipedia: Overtime (ice hockey)](https://en.wikipedia.org/wiki/Overtime_(ice_hockey)), which says that
  "since 1999–00" the team losing in overtime gets one point.
- **Ties:** observed in use through 2003-04, in agreement with the season facts. The same page says the shootout
  ended regular-season ties from 2005-06.
- **Wild card:**
  - Observed in use from 2013-14, matching the realignment approved for that season
    ([NBC Sports, 2013-03-14](https://nhl.nbcsports.com/2013/03/14/its-official-nhl-realignment-approved-for-next-season/)).
  - **Observed gap:** the wild card is marked not in use in 2019-20 and 2020-21, and in use again from 2021-22.
    Unexplained. It is consistent with the special formats of those two seasons, but no source has been checked for it.
- **Regulation wins (tiebreaker):**
  - Observed in use from 2019-20 onward.
  - **Start season unverified.** A fan blog,
    [Blueline Station (2019-11-09)](https://bluelinestation.com/2019/11/09/new-york-rangers-rule-change-worth-watching/),
    says the change to put regulation wins first took effect that season. It is not a league source, and no NHL
    source was found.
- **Regulation plus overtime wins (ROW):**
  - Observed in use from 2010-11 onward.
  - **Start season unverified.** The sources found
    ([Blueline Station](https://bluelinestation.com/2019/11/09/new-york-rangers-rule-change-worth-watching/),
    [hockeyanswered.com](https://hockeyanswered.com/what-is-the-row-stat-in-hockey/)) explain what ROW is and
    that it was the first tiebreaker before 2019-20, but neither gives the season it was introduced.

## Conferences and divisions

Each team's conference and division per season come from the NHL's standings on the season's first standings day
(`api-web.nhle.com/v1/standings/{date}`, `dim_team_season`). Observed on 2026-10-19, 109 seasons, 1,791 team-seasons:

- **No divisions in 38 seasons:** 1917-18 to 1925-26 and 1938-39 to 1966-67. Canadian and American divisions from
  1926-27 to 1937-38; East and West divisions with no conferences from 1967-68 to 1973-74.
- **No conferences in 58 seasons:** every season to 1973-74, and 2020-21. Prince of Wales and Clarence Campbell
  conferences, then Eastern and Western.
- **2020-21:** four divisions with sponsors' names (MassMutual East, Discover Central, Honda West, Scotia North)
  and no conferences.
- These empty values agree with the NHL's own `conferencesInUse` and `divisionsInUse` flags in every season
  (check `team_season_groups_match_rules`).
- **Different abbreviation:** the standings list the Cleveland Barons (1976-77, 1977-78) as `CBN`; the games use
  `CLE`. They are matched to team 49 by the team's full name. Unexplained.

## Birthplace coordinates

`dim_birthplaces` gives each distinct birthplace (country, state or province, standard city) coordinates from
GeoNames (`docs/decisions.md`, 2026-10-19). Observed on 2026-10-19, 4,442 birthplaces of 23,297 players with a birth
city:

| match_method | places | players | share of players |
|---|---|---|---|
| exact | 3,745 | 21,787 | 93.52% |
| alternate_name | 106 | 564 | 2.42% |
| manual | 25 | 167 | 0.72% |
| admin_area | 23 | 152 | 0.65% |
| successor_country | 11 | 21 | 0.09% |
| unmatched | 532 | 606 | 2.60% |

- **Matched: 97.40% of players.**
- **Former places share a successor's coordinates.** Fort William and Port Arthur are placed at Thunder Bay, Noranda
  and Rouyn at Rouyn-Noranda. They stay separate birthplaces (D14); only their map point is shared.
- **Population is today's,** from GeoNames, not the place's size when the player was born.
- **Why places are unmatched (observed):** villages and townships that GeoNames lists only as localities or not at all
  in the files we load (most of the US ones: the US file is not loaded), alternative spellings or short forms in the
  NHL's data, places recorded under a former country, and a few names that may be misspelled (for example
  "Sverdlovskurg"). Unexplained beyond what is observed.
- **Ambiguous names left unmatched on purpose:** "Saint-Jean" (QC) could be several places, and no source confirmed it
  as Saint-Jean-sur-Richelieu.

## Venue names

- Observed: four venue names arrive garbled from the NHL's weekly schedule, for example `Le Colis√©e` for Le Colisée and `Sportovn√≠ hala` for Sportovní hala. 676 games are affected. They are stored as received.

## Where the NHL's data differs from outside sources

Found while sourcing game type labels (2026-10-14). Raw data is unchanged; these are notes, not corrections.
We have not established which side is right.

- **1996 World Cup (1996-97, type 6):** the schedule puts Finland's home pool games on 1996-08-27 and 1996-08-28 at "Tampereen Jaahalli Arena". [Wikipedia](https://en.wikipedia.org/wiki/1996_World_Cup_of_Hockey) puts them at the Helsinki Ice Hall.
- **1938 European tour (1937-38, type 18):** the schedule records game 1 (1938-04-21, Canadiens 5 Red Wings 4) as ending in regulation. [Wikipedia](https://en.wikipedia.org/wiki/1938_Detroit_Red_Wings%E2%80%93Montreal_Canadiens_European_tour) says it went to overtime. That page is also inconsistent about two dates (game 7 on May 7 or 8; series end May 13 or 14). The schedule has May 7 and May 14.
- **1959 European tour (1958-59, type 18):** the schedule has the Rangers winning 4-3 on 1959-04-30; [Wikipedia](https://en.wikipedia.org/wiki/List_of_international_games_played_by_NHL_teams) has 4-2. The schedule puts the games on 1959-05-04 and 1959-05-05 at "Federal Ice Stadium"; the source puts them at the Patinoire de Boulogne-Billancourt, near Paris. The series record (Rangers 11-9-3) matches.
- **Coverage gaps in the sources:** the 1991 Canada Cup page gives venues only for the two final games. For the 1976 to 1987 Canada Cups, the venues were compared as a set, not game by game. The 2016 World Cup page text read did not show the date of Finland v Russia.
- **Not in the NHL's data at all:** the 2004 World Cup's 12 pre-tournament games ([Wikipedia](https://en.wikipedia.org/wiki/2004_World_Cup_of_Hockey)). The 2016 ones are type 8.

## Game types

- Besides preseason (1), regular season (2) and playoffs (3), the game list holds 12 other game types across various seasons.
- A (season, game type) pair gets a readable label only after its teams, dates and venues have been checked and the owner has confirmed it (`dbt/seeds/game_type_labels.csv`). Unverified pairs show as `unknown type N`.

## Playoff games that were never played

- From the game list: from 2019-20 onward the list includes scheduled playoff games with game state 1 (117 in total). The weekly schedule for 2025-26 leaves them out.
