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

## Shootouts

- Sampled: weekly schedule responses from 2005-06, 2012-13, 2019-20 and 2020-21 contain games with `last_period_type` = SO. Samples from 2003-04 and earlier contain only REG and OT.
- To confirm after the full load: the first and last season in which SO appears.
- Scores are the final scores the NHL reports. Observed in 2025-26: a shootout game's scores differ by exactly one.

## Preseason

- From the game list: preseason games (type 1) exist in only 31 seasons. There are none before 1980-81.
- From 1980-81 to 2003-04 at most 14 preseason games are listed in any season, and many seasons have none. From 2005-06 onward each season lists over 100, except 2012-13 and 2020-21, which list none.
- Preseason in `fct_games` should be treated as complete only from 2005-06.

## The 2004-05 gap

- The NHL's season facts have no entry for season 20042005.
- The game list has 1,230 games for it, all of game type 13, dated 2004-10-13 to 2005-04-10. Every one has a 0-0 score, no period recorded and game state 6.
- Sampled: the weekly schedule returns no games for 2005-01-15 and points to September 2005 as the next week with games.
- Cause: unexplained here until a source is recorded.
- In our tables: these rows stay in staging, labelled `cancelled` once that label is verified, and never reach `fct_games`. The missing season facts are a documented exception in `dbt/seeds/check_exceptions.csv`.

## 1917-18 anomalies

- The season facts say 22 games per team and 34 regular-season games in total. From the game list: there are 36 regular-season games and four teams, three with 22 games and one (Montreal Wanderers) with 6.
- The Wanderers' last two listed games, on 1918-01-02 and 1918-01-05, both have a 1-0 score.
- Cause: unexplained.
- The playoff total (7) matches the game list.

## Seasons where teams did not all play the scheduled number of games

- From the game list: besides 1917-18, the only such season is 2019-20, where the facts say 82 games per team and 1,082 games in total, and teams have between 68 and 71 games.
- Cause: unexplained here until a source is recorded.

## Non-NHL opponents

- From the game list: 55 team IDs appear in preseason or playoff games but are not in the NHL's team list. None appear in regular-season games.
- Sampled: the 1918 playoff game on 1918-03-30 lists "Vancouver Millionaires" (VMI, team 7288) at Toronto.
- In `dim_teams` these have `is_nhl_team` false, no franchise and no lineage. Their name and seasons come only from the games they appear in.
- Special events (all-star games, international tournaments) use further team IDs that are not NHL clubs. Those games are not in `fct_games`.

## Franchises and lineage

- The NHL's franchise IDs group team identities. Observed: franchise 35 holds the Winnipeg Jets (1979), the Atlanta Thrashers and today's Winnipeg Jets. Franchise 28 holds the Phoenix and Arizona Coyotes, 1996-97 to 2023-24. Franchise 40 holds the Utah Hockey Club and Utah Mammoth, from 2024-25.
- `dim_teams.lineage_id` equals the NHL franchise unless `dbt/seeds/team_lineage_overrides.csv` says otherwise. That file is empty.

## Game types

- Besides preseason (1), regular season (2) and playoffs (3), the game list holds 12 other game types across various seasons.
- A (season, game type) pair gets a readable label only after its teams, dates and venues have been checked and the owner has confirmed it (`dbt/seeds/game_type_labels.csv`). Unverified pairs show as `unknown type N`.

## Playoff games that were never played

- From the game list: from 2019-20 onward the list includes scheduled playoff games with game state 1 (117 in total). The weekly schedule for 2025-26 leaves them out.
