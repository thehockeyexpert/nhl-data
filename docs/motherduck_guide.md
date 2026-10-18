# NHL database (`nhl`): definitions and pitfalls

This is the text of the MotherDuck guide for the conversational query layer, and the master copy. Change this file
first, then publish it: `uv run python -m analyst.publish_guide` (add `--dry-run` to see what it would do). Guides
cannot be created in the MotherDuck web UI, and the MCP tools that write guides are blocked. Also paste the text
below the line into the Claude.ai Project instructions. Definitions come from `docs/definitions.md`.

---

Read this before answering any question from the `nhl` database. Use the `marts` schema. Table and column
comments in MotherDuck carry more detail.

## Coverage: what is and is not loaded (2026-10-18)
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
- **Skater games**, regular season and playoffs, all history: `fct_skater_games`, one row per skater per game, with
  the skater's team in that game. Answers "most in one game", streaks, and totals for one team when a player changed teams.
  Same early-era gaps as the season totals (shots and plus-minus from 1959-60, ice time and faceoffs from 1997-98).
- Players, with birthplace and `is_nhl_player`: `dim_players`. Seasons: `dim_seasons`. Games: `dim_games`.
  Teams, franchises and lineages: `dim_teams`.
- Records, refreshed weekly (Sundays), so the current season can lag by up to a week: draft picks
  (`fct_draft_picks`, 1963 on), trophies and award results (`dim_trophies`, `fct_award_results`), playoff series
  (`fct_playoff_series`, `bridge_playoff_series_games`), official team season totals (`fct_team_seasons`).

**Not loaded:**
- **Shots** and events (play-by-play): shot locations, shot attempts, hits, blocks, giveaways, takeaways.
- Team game statistics (shots, power play, penalties), shifts, fights, game duration.
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
- `marts.fct_skater_games`: one row per skater per game. `team_id` and `opponent_team_id` are the teams in that
  game; join to `fct_games` or `dim_games` on `game_id`. For season or career totals use `fct_skater_seasons`.
- `marts.fct_draft_picks` (`overall_pick`, `round_number`, `team_id`, `player_id`), `marts.fct_award_results`
  (`is_winner` true for winners; finalists and runners-up are also listed, and the Stanley Cup rows name every
  player engraved on the Cup), `marts.dim_trophies`.
- `marts.fct_playoff_series`: one row per NHL playoff series, `winner_team_id` and `loser_team_id`; `has_winner` is
  false for the unfinished 1919 Final. `is_final_round` marks the Stanley Cup Final.
- `marts.fct_team_seasons`: the NHL's official regular-season team totals (wins, points, goals for and against).
- `marts.dim_players`: one row per person. Use `is_nhl_player` (D15): the list also holds people who never played.
- `marts.dim_seasons`, `marts.dim_games`: season facts and rules; game date, type, teams and venue.
- `marts.goalie_records_vs_above_500`: question G01, still a DRAFT.

## Players and scoring
- **Identify a player by `player_id`, never by name alone.** Look the name up in `dim_players` first; if several
  NHL players share it, say so and ask or show each one.
- **"Most goals", "most assists" and "most points" include goalies** (D15): add `fct_goalie_games.goals` and
  `assists` to the skater totals. Questions about skaters only leave goalies out.
- **"Canadian", "Swedish" and the like (D24):** born in that country (`birth_country`), not nationality.
- **Totals for one team when a player changed teams (D27):** sum `fct_skater_games` (or `fct_goalie_games`) by
  `team_id`; `fct_skater_seasons` combines all of a season's teams in one row.
- **Where a player is from (D14):** birthplace as the NHL records it. Group by **`birth_city_standard`**, which
  merges spellings of the same place (Göteborg and Gothenburg, Saint Paul and St. Paul), together with
  `birth_state_province` and `birth_country`, so towns that share a name stay separate. Countries are three-letter
  codes (CAN, USA, SWE).
- **Former names count as separate places:** Fort William and Port Arthur are not Thunder Bay, Berlin is not
  Kitchener, South Porcupine is not Timmins, Leningrad is not St. Petersburg, and suburbs such as Scarborough or
  Verdun are not Toronto or Montréal. Say so in city rankings: sites that group by today's municipality (for
  example QuantHockey) give different totals.
- **Playoffs before 1926-27:** games against non-NHL teams (Vancouver, Seattle, Victoria, Edmonton, Calgary) have
  no credited skater or goalie statistics. Say so when early playoff totals matter.
- **1987-88 playoffs:** the suspended Final game of 1988-05-24 counts in player statistics but is not in the games
  tables, so Edmonton and Boston players have one more game than their team. In `fct_skater_games` its 36 rows
  (game 1987030999) have an empty `team_id`.
- A shootout goal is not a goal in player totals.

## Stat terms (full list in the repo's `docs/definitions.md`, "Stat terms")
- **Strength:** "even strength" follows the NHL and includes 4-on-4 and 3-on-3; it is not 5-on-5. Say which one an
  answer uses.
- **Rates and percentages:** sum the totals first, then divide; never average percentages. State the minimum sample
  used.
- **When stats begin:** strength split (even-strength, power-play, short-handed) from 1933-34; skater shots and
  plus-minus from 1959-60; goalie shots and saves from 1955-56; ice time and faceoffs from 1997-98. Leave earlier
  seasons out of "best ever" rate questions; don't count them as zero.
- **Formulas:** save % = saves / shots against; GAA = goals against x 3,600 / `time_on_ice_seconds`.
- **Faceoff %** is empty for players who took no faceoffs, and there are no raw win and loss counts.
- **Not in the data:** primary and secondary assists, the number of penalties, penalties drawn.
- **Not loaded, never estimate:** shot attempts (Corsi/SAT), unblocked attempts (Fenwick/USAT), missed and blocked
  shots, expected goals and anything built on them, shifts, zone starts, hits, takeaways, giveaways, Game Score.
  Say they are not loaded.
- **Other sites' seasons:** a single year such as "2018" means 2018-19. Convert with
  `start_year * 10000 + start_year + 1`.

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
- For franchise-record questions, also give the `franchise_id` figure where it differs from `lineage_id` (D03).

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
  which is shown. Other rates, regular season, where "team games" is the most games any team played that season:
  skater career 400 games; skater season half the team games; shooting % also shots at least equal to team games
  (season) or 1,000 shots (career); goalie season one third of the team games; goalie career 250 games, with
  career save % only over seasons from 1955-56. Never prorate a shortened season (D29).
- **Streaks (D06):** a player's streak counts consecutive games the player played (missed games skipped), within
  one regular season; a streak carried across seasons may be given as extra. A team winning streak counts wins of
  any kind; a loss, overtime or shootout loss, or tie ends it.
- **Rookie (D09):** the NHL's Calder rule from NHL games: no earlier season over 25 games, not 6 or more games in
  each of two earlier seasons, and from 1990-91 under 26 on September 15. We have no other pro leagues: say so,
  and name WHA arrivals (Gretzky and Mike Rogers in 1979-80 were not rookies for the NHL).
- **Age (D25):** youngest or oldest, exact age on the game date; "age in a season", age on February 1.
- **Active player (D26):** played a game this season or last season.
- **Decades (D28):** "the 1980s" is 1980-81 to 1989-90.
- **One-goal games (D07):** overtime wins count, shootout games do not unless asked. **Winning record (D13):** more
  wins than all losses (overtime and shootout losses included), ties ignored. **Hat trick (D16):** 3 or more goals
  in a game. **Back-to-back (D08):** played the previous calendar day.
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
