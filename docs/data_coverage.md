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
