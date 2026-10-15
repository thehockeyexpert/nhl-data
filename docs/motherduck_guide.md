# NHL database (`nhl`): definitions and pitfalls

This is the text of the MotherDuck guide for the conversational query layer. The owner creates and updates the
guide in MotherDuck by hand (the MCP tools that write guides are blocked); this file is the source. Keep the two in
step: change this file first, then paste it into MotherDuck. Definitions come from `docs/definitions.md`.

---

Read this before answering any question from the `nhl` database. Use the `marts` schema. Table and column
comments in MotherDuck carry more detail.

## Coverage: what is and is not loaded (2026-10-15)
If a question needs data that is not loaded, say so plainly and name what is missing. Never estimate it from
other tables.

**Loaded and modelled (`marts`):**
- Games and results, 1917-18 to today (2004-05 was not played): `fct_games`, `fct_team_games`.
- Standings before every regular-season game, under each era's rules: `fct_team_standings_by_game`.
- Goalie games, regular season and playoffs, all history: `fct_goalie_games` (decisions, shutouts, goals against;
  shots and saves from 1955-56).
- **Skater season totals**, regular season and playoffs, all history: `fct_skater_seasons` (games, goals, assists,
  points, penalty minutes, power-play and short-handed scoring; shots, plus-minus, ice time and faceoffs only in
  later eras). One row per player, season and game type; a player who changed teams has one row, not one per team
  (`bridge_skater_season_teams` lists his teams).
- Players, with birthplace and `is_nhl_player`: `dim_players`. Seasons: `dim_seasons`. Games: `dim_games`.
  Teams, franchises and lineages: `dim_teams`.

**Loaded, in `staging` only (usable, not yet modelled):**
- Draft picks, trophies and award results, playoff series: `staging.stg_nhl_records__draft_picks`,
  `stg_nhl_records__trophies`, `stg_nhl_records__award_results`, `stg_nhl_records__playoff_series_games`.
- Official team season totals: `staging.stg_nhl_stats__team_seasons`.

**Not loaded:**
- **Skater statistics per game** (box scores) and **shots** (play-by-play). Season totals answer "most in a
  season" and career questions; "most in one game", streaks and anything per game cannot be answered yet.
- Skater totals split by team for players who changed teams mid-season.
- Team game statistics (shots, power play, penalties), play-by-play, shifts, fights, game duration.
- Players' seasons in other leagues (junior, college), arena locations and travel.

## Tables
- `marts.fct_games`: one row per game (types 1 preseason, 2 regular season, 3 playoffs). Final scores as the NHL
  reports them: a shootout win counts as one goal.
- `marts.fct_team_games`: one row per team per finished regular-season or playoff game. `result` is W, L, T or OTL
  under that era's rules; `points` is the standings points.
- `marts.fct_goalie_games`: one row per goalie per game. `decision` is the goalie's credited W, L, T or OTL.
- `marts.fct_team_standings_by_game`: each team's standings before each regular-season game (that game excluded).
- `marts.dim_teams`: one row per team identity, with `franchise_id` (the NHL's) and `lineage_id` (ours).
- `marts.fct_skater_seasons`: one row per skater per season and game type. Join to `dim_players` on `player_id`.
- `marts.dim_players`: one row per person. Use `is_nhl_player` (D15): the list also holds people who never played.
- `marts.dim_seasons`, `marts.dim_games`: season facts and rules; game date, type, teams and venue.
- `marts.goalie_records_vs_above_500`: question G01, still a DRAFT.

## Players and scoring
- **"Most goals" (or points) includes goalies' goals** (D15): add `fct_goalie_games.goals` to the skater totals.
- **Where a player is from (D14):** birthplace as the NHL records it. Identify a city by `birth_city`,
  `birth_state_province` and `birth_country` together, so towns that share a name stay separate. Countries are
  three-letter codes (CAN, USA, SWE).
- **Playoffs before 1926-27:** games against non-NHL teams (Vancouver, Seattle, Victoria, Edmonton, Calgary) have
  no credited skater or goalie statistics. Say so when early playoff totals matter.
- **1987-88 playoffs:** the suspended Final game of 1988-05-24 counts in player statistics but is not in the games
  tables, so Edmonton and Boston players have one more game than their team.
- A shootout goal is not a goal in player totals.

## Default scope (D11, decided)
- **Regular season only** (`game_type = 2`) unless the question says playoffs or preseason. If a question
  includes playoffs, report them separately as well as combined. Never include special events (all-star games and
  the like; they are not in `fct_games`).
- Count only finished games (`is_final`). The game list holds "if necessary" playoff games that were never played.
- Seasons are 8-digit IDs: 20252026 is 2025-26. The current season (2026-27) is in progress: say so, or exclude
  it, for "most ever" questions.
- "Since 1990" means 1990-91 onward.

## Teams in history questions
- Group by `lineage_id`, not by team name: a club that moved or was renamed has several team rows.
- Our lineage differs from the NHL for the original Winnipeg Jets (1979-80 to 1995-96): we put them with the
  Coyotes, the NHL puts them with today's Jets. Say so when either club is involved.
- Utah is a separate lineage from the Coyotes.

## Results, ties and overtime (common mistakes)
- Ties exist only up to 2003-04 (`is_tie`). There was no 2004-05 season (lockout).
- **`last_period_type = 'OT'` does not mean the game was decided in overtime.** Before 2005-06, 3,086
  regular-season games went to overtime and still ended tied. For "decided in overtime or a shootout", add
  `NOT is_tie`.
- Shootouts start in 2005-06 (`last_period_type = 'SO'`).
- An OTL result exists only in seasons that gave a point for an overtime loss; otherwise an overtime loss is L.
- Goalie decisions: from 1999-00 to 2003-04 a goalie's overtime loss is recorded as L, while the team gets an OTL.

## Definitions
- **Strong opponent (D01).** Headline: the opponent's points % before the game is strictly above the league median
  that day, and the opponent has played at least 10 games (`is_top_half_before`). Second column: above .500 by
  points % before the game (`is_above_500_before`).
- **G01: always lead with the top-half headline (`top_half_*`), even when the question says ".500"; give the
  literal above-.500 version (`above_500_*`) second.**
- **A goalie's record (D04):** the goalie's credited decisions, whoever started.
- **Best record (D23):** win percentage W / (W + L + T + OTL) is the headline, with points percentage
  (2W + T + OTL) / (2 x decisions) beside it.
- **Minimums (D05):** G01 needs at least 50 qualifying decisions; report the 100-decision version too and say
  which is shown.
- **Standings points (D02):** 2 for a win, 1 for a tie, 1 for an overtime or shootout loss where that season's
  rules give it.

## Era limits
- Goalie shots against and saves start in 1955-56.
- Preseason is complete only from 2005-06.
- 1917-18 and 2019-20 are unbalanced seasons (a withdrawn team; a season stopped by the pandemic).
- Some preseason and early playoff opponents are not NHL teams (`dim_teams.is_nhl_team` false).

## How to answer
- Say the reading you used when a question is ambiguous, and the minimum applied to any rate.
- **Write records as W-L-T-OTL with the labels**, for example "74 W, 31 L, 0 T, 14 OTL". Never give three bare
  numbers: it is unclear which category is missing.
- When combining rankings with UNION ALL, add a final ORDER BY: the order is otherwise not guaranteed.
- Give facts and figures only. The data comes from the NHL's unofficial endpoints, for personal use.
