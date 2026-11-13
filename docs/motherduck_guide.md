# NHL database (`nhl`): definitions and pitfalls

This is the text of the MotherDuck guide for the conversational query layer, and the master copy. Change this file
first, then publish it: `uv run python -m analyst.publish_guide` (add `--dry-run` to see what it would do). Guides
cannot be created in the MotherDuck web UI, and the MCP tools that write guides are blocked. The Claude.ai Project
reads this guide from MotherDuck (`analyst/claude_project_instructions.md`), so there is nothing to paste. Keep the
published text under 16,000 characters (the script warns above 14,000 and refuses above 16,000), so it can still be
pasted as a fallback. Definitions come from `docs/definitions.md`.

---

Read this before answering any question from the `nhl` database. Use the `marts` schema; table and column comments
in MotherDuck carry more detail. If a question needs data that is not loaded, say so and name what is missing; never
estimate it from other tables.

## Tables (`marts`; regular season and playoffs, all history, unless stated)
- `fct_games`: one row per game; `game_type` 1 preseason, 2 regular season, 3 playoffs. Final scores as the NHL
  reports them: a shootout win counts as one goal. 2004-05 was not played.
- `fct_team_games`: one row per team per finished game. `result` W, L, T or OTL under that era's rules; `points`.
- `fct_team_standings_by_game`: each team's standings before each regular-season game (that game excluded).
- `fct_team_seasons`: the NHL's official regular-season team totals. Refreshed Sundays, like draft, awards and
  series, so the current season can lag a week.
- `fct_goalie_games`: one row per goalie per game. `decision` is the goalie's credited W, L, T or OTL.
- `fct_skater_seasons`: one row per skater, season and game type; a traded player has one row
  (`bridge_skater_season_teams` lists the teams). `fct_skater_games`: one row per skater per game, with `team_id`
  and `opponent_team_id` for that game: for "most in one game", streaks and one team's share of a traded player.
- `fct_shots`: one row per shot on goal, missed shot, blocked shot and goal, with period, time, strength
  (`situation_code`), shooter, goalie, blocker, assists, shot type, coordinates. Goals only before 1997-98; shots on
  goal from 1997-98; missed and blocked shots, coordinates and strength from 2009-10. `is_goal`, `is_on_goal`,
  `is_shootout` (leave shootout attempts out of goal and shot totals). Join `dim_players` on `shooting_player_id`,
  `goalie_in_net_id`, `assist1_player_id` (primary) or `assist2_player_id`. Which end a team attacks:
  `home_team_defending_side`.
- `fct_penalties`: one row per penalty. `committed_by_player_id`, `drawn_by_player_id` (from 1997-98),
  `served_by_player_id`, `penalized_team_id`, `penalty_desc_key` (hooking, fighting...), `penalty_type_code` (MIN,
  MAJ, MIS, GAM, MAT, BEN, PS), `penalty_minutes`. `is_fight`: one per player per fight, labelled only from 1947-48.
- `fct_hits`: one row per hit, from 2009-10. `hitting_player_id` threw it, `hittee_player_id` took it. Counted by
  arena scorers, so counts differ between arenas.
- From 2009-10: `fct_faceoffs` (`winning_player_id`, `losing_player_id`, teams, zone: faceoff wins and losses),
  `fct_giveaways` and `fct_takeaways` (`player_id`, `team_id`; arena-counted, goalies included), `fct_stoppages`
  (`stoppage_reason`: icing, offside...).
- `fct_team_game_stats`: one row per team per game: power play (`power_play_goals`, `power_play_opportunities`),
  penalty kill (`times_short_handed`, `power_play_goals_against`), `short_handed_goals`, penalties, shots. PP% = sum
  of goals / sum of opportunities; PK% = 1 - goals against / times short-handed. Opportunities from 1977-78, shots
  1959-60, PP time 1997-98. Its goals leave out the shootout goal: use `goals_for` for scores.
- `fct_skater_shootouts`: shootout attempts, goals, game-deciding goals per skater per regular season, from 2005-06.
  Minimums: 5 attempts for a season, 25 for a career (sum, then divide).
- `fct_player_league_seasons`: one row per player, season, league, team and game type in every league on the
  player's NHL page (junior, college, minor and major pro, international, NHL). `league_abbrev` as the NHL writes it
  (OHL, AHL, H-East, WC-A...); `is_before_first_nhl_season`. For NHL totals use the NHL tables. Only what the NHL
  lists: no row does not prove someone never played there.
  **Duplicate seasons:** a traded player's season can appear both per team and as a whole-season row, so summing a
  season's rows can double count (129 junior games in one season). Use the best single row, or sum only when the
  games played add up to no more than a season. **Colleges:** filter on `team_name` (e.g. 'Boston College'); most
  college seasons are filed under conference codes (H-East, ECAC, WCHA), not 'NCAA'. **CHL** (D18) = `league_group`
  'OHL', 'WCJHL/WHL junior' or 'QMJHL' in `reference.league_levels` (earlier names included).
  The Canada Cup and World Cup are often listed twice, a season apart (`CC`/`Can-Cup`, `WCup`/`W-Cup`): count each
  tournament once. Goalie rows in tournaments have no points. For "how many leagues", join
  `reference.league_levels` on `league_abbrev` with `season` between `from_season` and `to_season` (empty = open),
  keep `counts_before_nhl`, and count distinct `league_group`.
- `dim_players`: one row per person; use `is_nhl_player` (D15), as the list holds people who never played.
  Goalies are `position = 'G'`.
- `dim_birthplaces`: `latitude`, `longitude` per birthplace (GeoNames, CC BY 4.0: credit GeoNames when shown); join
  on `birthplace_key`. 'unmatched' has no coordinates: say how many players a map leaves out. Former towns share
  their successor's point (Fort William at Thunder Bay).
- `dim_teams`: one row per team identity, `franchise_id` (the NHL's) and `lineage_id` (ours). `is_nhl_team` false
  for non-NHL preseason and early playoff opponents.
- `dim_team_season`: conference and division per team per regular season. Join on `team_id` and `season`.
- `dim_team_home_cities`: each team's home building and city per era (most home games each season), with the
  building's coordinates for travel. `home_city` is the building's municipality (Inglewood, Uniondale).
- `dim_seasons` (season facts and rules), `dim_games` (date, type, teams, venue). `reference.overtime_rules`:
  overtime length, sudden death or not, skaters and shootout by era (game_type 2 or 3).
- `fct_draft_picks` (1963 on), `fct_award_results` (`is_winner`; finalists also listed; Stanley Cup rows name every
  player engraved), `dim_trophies`, `fct_playoff_series` (`winner_team_id`, `loser_team_id`, `is_final_round`;
  `has_winner` false for the unfinished 1919 Final), `bridge_playoff_series_games`.
- `goalie_records_vs_above_500`: question G01, still a DRAFT.

**Not loaded, never estimate:** shifts, zone starts, expected goals, Game Score. Travel distances are not stored. Compute them (D20) as the
great-circle distance between the arenas of a team's consecutive regular-season games (`fct_games.venue_name` joins
`reference.venues.venue_name` for coordinates), from the home arena (`dim_team_home_cities`) to a season-opening road
game and back home after a season-ending one.

## When stats begin (never count earlier seasons as zero; leave them out of "best ever" rates)
- Strength split of skater scoring (even, power play, short-handed) 1933-34; goalie shots and saves 1955-56; skater
  shots and plus-minus 1959-60; ice time and faceoffs 1997-98.
- Play-by-play: primary and secondary assists all history (`fct_shots`, not in the totals tables); fights 1947-48;
  shots on goal 1997-98; hits, faceoff events, giveaways, takeaways, stoppages, shot attempts and goal strength
  2009-10 (earlier power-play goals: skater totals).
- Preseason is complete only from 2005-06. Ties up to 2003-04 (`is_tie`); shootouts from 2005-06.
- 1917-18 and 2019-20 are unbalanced (a withdrawn team; the pandemic).

## Players and scoring
- **Identify a player by `player_id`**, looked up in `dim_players`; if several NHL players share a name, say so.
- **"Most goals/assists/points" include goalies** (D15): add `fct_goalie_games` goals and assists. "Skaters"
  excludes them.
- **Nationality (D24):** "Canadian", "Swedish" mean born there (`birth_country`, three-letter codes).
- **One team's totals for a traded player (D27):** sum `fct_skater_games` or `fct_goalie_games` by `team_id`.
- **Where from (D14):** group by `birth_city_standard` (merges spellings: Göteborg/Gothenburg) with
  `birth_state_province` and `birth_country`. Former names are separate places (Fort William is not Thunder Bay,
  Berlin not Kitchener, Scarborough not Toronto); sites grouping by today's municipality give different totals.
- **Playoffs before 1926-27:** games against non-NHL teams have no player statistics.
- **1987-88:** the suspended Final game of 1988-05-24 counts in player stats but not in the games tables
  (game 1987030999, empty `team_id` in `fct_skater_games`).
- A shootout goal is not a goal in player totals.

## Stat terms (full list: `docs/definitions.md`)
- "Even strength" follows the NHL and includes 4-on-4 and 3-on-3, not only 5-on-5. Say which one is used.
- Rates: sum totals, then divide; never average percentages. State the minimum used.
- Save % = saves / shots against; GAA = goals against x 3,600 / `time_on_ice_seconds`. Faceoff % is empty for
  players with no faceoffs; there are no win and loss counts.
- Corsi/SAT = on goal + missed + blocked; Fenwick/USAT = on goal + missed; from 2009-10, shootouts left out.
- A single year such as "2018" means 2018-19: `start_year * 10000 + start_year + 1`.

## Default scope (D11)
- Regular season only (`game_type = 2`) unless playoffs or preseason are asked; with playoffs, give them separately
  and combined. Special events (all-star games) are not in `fct_games`.
- Finished games only (`is_final`): the game list holds never-played "if necessary" playoff games.
- Seasons are 8-digit IDs (20252026 = 2025-26). 2026-27 is in progress: leave it out of single-season "most ever"
  answers and say so; career totals run to today.
- "Since 1990" means 1990-91 onward. "The 1980s" is 1980-81 to 1989-90 (D28).

## Teams in history questions
- Group by `lineage_id`, not team name. Our lineage puts the original Winnipeg Jets (1979-80 to 1995-96) with the
  Coyotes; the NHL puts them with today's Jets: say so when either is involved. Utah is separate from the Coyotes.
  For franchise records also give the `franchise_id` figure where it differs (D03).
- Divisions are empty in 1917-18 to 1925-26 and 1938-39 to 1966-67, conferences up to 1973-74 and in 2020-21. A
  division name can mean different groups in different eras: group by season and name. 2020-21 had four one-off
  sponsor-named divisions.

## Results, ties and overtime
- **`last_period_type = 'OT'` does not mean decided in overtime:** before 2005-06, 3,086 regular-season games went
  to overtime and ended tied. For "decided in OT or a shootout" add `NOT is_tie`.
- OTL exists only in regular-season games of seasons that gave a point for an overtime loss; otherwise, and in every
  playoff game, it is L. From 1999-00 to 2003-04 a goalie's overtime loss is L while the team gets OTL.
- **Minutes played (D19):** 60 a game plus overtime: up to the first overtime goal in `fct_shots` (`period_number` 4
  on, not shootout; earlier periods at full length); with no goal, the full overtime from `reference.overtime_rules`
  (10 minutes played in full 1928-29 to 1942-43, whatever was scored). Shootouts add nothing.
- Standings points (D02): 2 for a win, 1 for a tie, 1 for an OT or shootout loss where that season's rules give it.

## Definitions
- **Strong opponent (D01):** headline, opponent's points % before the game strictly above the league median that
  day, with at least 10 games played (`is_top_half_before`); second, above .500 (`is_above_500_before`).
- **G01: always lead with the top-half headline (`top_half_*`), even when the question says ".500"; give the
  above-.500 version (`above_500_*`) second.**
- **A goalie's record (D04):** the goalie's credited decisions, whoever started.
- **Best record (D23):** win % W / (W + L + T + OTL) headline, points % (2W + T + OTL) / (2 x decisions) beside it.
- **Minimums (D05), regular season; "team games" = most games any team played that season:** G01 50 qualifying
  decisions (also report 100). Skater career 400 games, season half the team games; shooting % also shots at least
  the team games (season) or 1,000 (career); goalie season a third of the team games, career 250 games, career
  save % from 1955-56 only. Never prorate a shortened season (D29).
- **Streaks (D06):** consecutive games the player played, within one regular season (across seasons as an extra).
  A team winning streak counts any win; a loss of any kind or a tie ends it.
- **Rookie (D09):** the Calder rule on NHL regular-season games: no earlier season over 25 games, not 6+ games in
  each of two earlier seasons, from 1990-91 under 26 on September 15. Other pro leagues are not applied: say so,
  and name WHA arrivals (Gretzky and Mike Rogers in 1979-80 were not NHL rookies).
- **Age (D25):** exact age on the game date; "age in a season" is age on February 1. **Active (D26):** played this
  season or last.
- **One-goal games (D07):** OT wins count, shootout games only if asked. **Winning record (D13):** more wins than
  all losses, ties ignored. **Hat trick (D16):** 3+ goals in a game. **Back-to-back (D08):** played the previous day.

## How to answer
- Say the reading used for an ambiguous question, and the minimum applied to any rate.
- **Write records with labels**, e.g. "74 W, 31 L, 0 T, 14 OTL", never three bare numbers.
- With UNION ALL rankings, add a final ORDER BY.
- Facts and figures only. The data comes from the NHL's unofficial endpoints, for personal use.
