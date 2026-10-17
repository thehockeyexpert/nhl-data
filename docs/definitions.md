# Definitions

Status: DRAFT (2026-10-14). These definitions are referenced by id from `analyst/golden_questions.yml`.
Each one must be settled by the owner before the models or answers that depend on it are built.

| id | Definition | Status | Proposed default |
|---|---|---|---|
| D01 | Strong opponent ("above .500") | **Decided 2026-10-14 (revised)** | **Headline:** the opponent's points % before the game (that game excluded) is strictly above the league median that day, where the median is taken over teams that have played at least one game, **and** the opponent has played at least 10 games that season. Ties at the median do not count. **Second column:** the literal "above .500", meaning the opponent's points % before the game is above .500 (a team's first game counts as not above .500). **Reasons:** compared read-only on 2026-10-14. Above .500 by points % qualifies 46% to 47% of decisions before 1999 but 67% from 2005-06, because the overtime-loss point lifts average teams above .500. The league median keeps the qualifying share between 46.4% and 48.2% in every era; with the 10-game minimum added, as adopted, it is 39.0% to 43.4% (lowest before 1967-68, when seasons were shorter, so 10 games is a larger part of a season). The 10-game minimum removes early-season opponents whose record rests on a handful of games. **Considered and not adopted:** above .550 by points % (still drifts by era: 35% to 52%) and above .500 by wins only (penalises the tie era: 27% to 28% before 2005-06, 46% after). |
| D02 | Standings points by era | Proposed | Taken from the NHL's `standings-season` flags for each season: 2 for a win, 1 for a tie, and 1 for an overtime or shootout loss where `pointForOTlossInUse` is true. |
| D03 | Team in history questions | **Decided** | Group by `lineage_id`. Answers say when the NHL's `franchise_id` differs, for example for the Winnipeg Jets (1979). |
| D04 | A goalie's record | **Decided 2026-10-14** | The goalie's credited decisions (W, L, T, OTL) as the NHL reports them, whoever started the game. In samples, every finished team-game has exactly one credited decision. Caveat: from 1999-00 to 2003-04 a goalie's overtime loss is recorded as L, while the team gets an OTL. |
| D05 | Minimums for rate leaders | Partly decided | **G01 (decided 2026-10-14):** at least 50 career regular-season decisions against qualifying opponents, with a 100-decision version reported too; answers say which one is shown. Other rate leaders: still open (for example, save percentage needs 25 games or 750 shots against, and points per game needs 40 games). |
| D06 | Streaks | Open | Does an overtime or shootout loss, or a tie, end a winning streak? Does a player's point streak skip games he missed? |
| D07 | One-goal game | Open | A final margin of one goal. To decide: include shootout games (scored as a one-goal win) or exclude them? |
| D08 | Back-to-back | Proposed | The team also played on the previous calendar day (`game_date`). |
| D09 | Rookie | Open | The NHL's rookie definition, or a player's first season with any NHL games? |
| D10 | Playoff appearance and drought | Open | A lineage appears in the playoffs if it played any playoff game that season. To decide: how to treat seasons before the NHL had a fixed playoff format. |
| D11 | Default scope | **Decided 2026-10-15** | Regular season only unless the question says playoffs or preseason. Special events (game types 4 and up) are never included. |
| D12 | "Today" in the daily run | Proposed | The North American date the NHL lists games under (`game_date`). The run computes it in Eastern time. |
| D13 | Winning record (goalie or team) | Open | More wins than losses, where losses include overtime and shootout losses and ties are ignored. The alternative is to count only regulation losses. |
| D14 | Where a player is "from" | **Decided 2026-10-15** | Birthplace as the NHL records it (birth city, state or province code, country code), not nationality or hometown. A city is identified by city plus state or province plus country, so towns that share a name stay separate. Spellings of the same place (accents, Saint and St., English and local names) are merged by `dbt/seeds/birth_city_spellings.csv` into `dim_players.birth_city_standard`; former names of a place (Fort William, Berlin, Leningrad) stay separate places. |
| D15 | NHL player | **Decided 2026-10-15** | Anyone with at least one NHL regular-season or playoff game: a skater season with games played above 0, or a goalie game. Special events (game types 4 and up) do not count. **"Most goals" questions include goalies' goals** (decided 2026-10-15). |
| D16 | Hat trick | Proposed | 3 or more goals by one player in one game, so a 4-goal game is one hat trick. |
| D17 | Fight | Open | A fighting major in the NHL's play-by-play penalty events (`descKey` "fighting"). Play-by-play is one request per game. Fighting penalties are labelled from 1947-48 (sampled); in 1917-18, 1930-31, 1945-46 and 1946-47 every sampled major is recorded only as "major", so earlier fights cannot be told apart. Fights are in scope; see `docs/decisions.md` for the cheaper loading route and its cost. |
| D18 | Other leagues (CHL, NCAA) | Open | From each player's NHL player page (`api-web.nhle.com/v1/player/{id}/landing`, season totals by league), one request per player. "CHL" means the OHL, WHL and QMJHL; to decide whether their seasons before the CHL formed in 1975 count. A college is matched by its team name in those season totals (for example "Boston College"). |
| D19 | Minutes played (team) | Open | 60 per regulation game plus the overtime actually played: the time of the overtime goal, or the full overtime if nobody scored. That covers the 10-minute non-sudden-death overtime before 1942 and long playoff overtimes. Shootouts add nothing. The overtime goal time comes from play-by-play. |
| D20 | Travel distance | Open | The straight-line (great-circle) distance between the venues of a team's consecutive games, from the season's first game to its last, as if the team always flew from one game venue to the next. Needs an outside table of arena coordinates, since the NHL data has venue names only. Neutral-site games use their own venue. Travel is in scope; see `docs/decisions.md` for sources and venue-history issues. |
| D21 | "Since <year>" | Proposed | "Since 1990" means seasons starting in that year or later (1990-91 onward). |
| D22 | Playing time (player) | Proposed | Total time on ice. Skater time on ice exists from 1997-98 and goalie time on ice from 1917-18, so skater questions about playing time cover 1997-98 onward only. |
| D23 | "Best record" (goalie) | **Decided 2026-10-14, confirmed 2026-10-14** | Win percentage of decisions, W / (W + L + T + OTL), is the headline measure, with points percentage, (2W + T + OTL) / (2 x decisions), beside it. Used by G01. Note: ties count as decisions without a win, which lowers win percentage for goalies before 2005-06; points percentage shows that difference. |

Notes:

- The stats API reports skater and goalie rows with a team abbreviation, not a team ID. Abbreviations are reused across eras (for example WPG), so the team is resolved through `gameId` and home or road, joined to `fct_games`.
- Era limits (`docs/data_coverage.md` will be updated when each load lands):
  - Goalie shots against and saves start in 1955-56.
  - Skater shots and plus-minus are present by 1959-60.
  - Skater ice time and faceoffs start in 1997-98.

## Stat terms

The list of terms was inspired by MoneyPuck.com's public data dictionary. The wording is ours, and official meanings
follow the NHL. Terms marked not loaded describe data we don't have yet. For those, Claude must say the stat isn't
available rather than estimate it.

### Conventions that apply to every term

- **Season ID.** Ours is 8 digits: 20182019 is 2018-19. Other sites often use the starting year only (MoneyPuck
  writes 2018 for 2018-19). When comparing, convert with `start_year * 10000 + start_year + 1`.
- **Game situation (strength).** The NHL uses three groups. Even strength means equal numbers of skaters, so it
  includes 4-on-4 and 3-on-3 overtime, not only 5-on-5. Power play means the team has more skaters. Short-handed
  means it has fewer. "5-on-5" is narrower than even strength, and many analytics sites use it as their default.
  Our `even_strength_*` columns follow the NHL meaning. Say which one an answer uses.
- **Individual, on-ice and off-ice.** Individual counts what the player did, such as their own goals. On-ice counts
  what happened for or against the player's team while they were on the ice, whoever did it. Off-ice is the same
  while they were on the bench. All of our loaded player stats are individual, except plus-minus.
- **Rates.** "Per game" divides by games played. "Per 60" divides by ice time in minutes and multiplies by 60. Rates
  need a minimum sample (see D05) and must say which minimum was used.
- **Share percentages.** A share is for / (for + against), so 50% means even. They exist only for on-ice stats.

### Stats we have (loaded)

Columns are in `marts.fct_skater_seasons` (S01 to S13) and `marts.fct_goalie_games` (S14 to S18). S19 is kept free
for a later loaded term.

| ID | Term | Ours | Meaning (NHL) | Notes |
|---|---|---|---|---|
| S01 | Games played | `games_played` | Games in which the player dressed and took part. | Per season and game type. |
| S02 | Goal | `goals` | A goal credited to the player. Shootout goals are not goals. | Add goalies' goals for "most goals" (D15). |
| S03 | Assist | `assists` | Up to two players credited for helping set up a goal. The last passer is the primary assist, the one before is the secondary. | We only have the total, so we can't split primary and secondary. |
| S04 | Point | `points` | Goals + assists. | |
| S05 | Even-strength, power-play and short-handed goals and points | `even_strength_goals`, `even_strength_points`, `power_play_goals`, `power_play_points`, `short_handed_goals`, `short_handed_points` | Goals or points scored at even strength (any equal numbers), on the power play, or while short-handed. | From 1933-34; empty before. The three goal columns always add up to `goals`. The three point columns add up to `points` in every row but one (1987-88, a player with 35 points whose parts sum to 34; observed, unexplained). There is no split for assists. |
| S06 | Game-winning goal | `game_winning_goals` | The goal that put the winning team one ahead of the loser's final total. In a 5-2 win, it's the winner's 3rd goal. | A game decided by a shootout credits no game-winning goal. |
| S07 | Overtime goal | `overtime_goals` | A goal scored in overtime. Since 1983-84 regular-season overtime is sudden death, so it ends the game. | |
| S08 | Plus-minus | `plus_minus` | +1 for each even-strength or short-handed goal the team scores while the player is on the ice, and -1 for each one the team allows. Power-play goals and penalty-shot goals don't count. | From 1959-60; empty before. |
| S09 | Penalty minutes | `penalty_minutes` | Minutes of penalties assessed to the player. | We don't have the number of penalties or penalties drawn. |
| S10 | Shot on goal | `shots` | A shot that scores or would have scored if the goalie hadn't stopped it. Missed shots, shots off the post and blocked shots are not shots on goal. | From 1959-60 (regular season and playoffs); empty before. Goalies' shots against start earlier, in 1955-56 (S15). |
| S11 | Shooting percentage | (computed) | Goals / shots on goal. | Only from 1959-60, when shots exist. Needs a minimum number of shots. |
| S12 | Ice time per game | `time_on_ice_per_game_seconds` | Average time on the ice per game, in seconds. | From 1997-98. Divide by 60 for minutes. |
| S13 | Faceoff win % | `faceoff_win_pct` | Faceoffs won / faceoffs taken. | From 1997-98. Empty for a player who took no faceoffs: about 96% to 98% of centres have a value, but only about 60% to 65% of all skaters. We don't have the raw counts of wins and losses. |
| S14 | Goalie decision | `decision` | The win, loss, tie or overtime loss credited to one goalie per team (D04). | From 1999-00 to 2003-04 a goalie's overtime loss shows as L. |
| S15 | Shots against and saves | `shots_against`, `saves` | Shots on goal the goalie faced, and the ones the goalie stopped. | From 1955-56. |
| S16 | Save percentage | (computed) | Saves / shots against. | From 1955-56. Needs a minimum sample. Always sum first, then divide; never average game-level percentages. |
| S17 | Goals-against average | (computed) | Goals against x 3,600 / seconds played, which is goals allowed per 60 minutes. | Uses `time_on_ice_seconds`. Empty-net and shootout goals are not charged to the goalie. |
| S18 | Shutout | `is_shutout` | A game where the goalie allowed no goals. The NHL credits it only when one goalie played the whole game, and a shared shutout goes to no goalie. | Our flag follows the NHL's credit. |

### Stats we don't have yet (not loaded)

These need play-by-play or shot data (our parked Tier 2 work) or an outside source. If someone asks for one of them,
Claude must say it isn't loaded.

| ID | Term | Meaning (in our words) | Also called |
|---|---|---|---|
| S20 | Shot attempt | Any attempt at the net: on goal, missed, or blocked by an opponent. | Corsi. The NHL calls it SAT. |
| S21 | Unblocked shot attempt | Shots on goal plus missed shots, not counting blocked ones. | Fenwick. The NHL calls it USAT. |
| S22 | Missed shot | An attempt that wasn't blocked but didn't hit the net, including shots off the post. | |
| S23 | Blocked shot | An attempt stopped by an opposing skater before it reached the net. It's credited to the blocker as a block, and to the shooter as a blocked attempt. | |
| S24 | Expected goals (xG) | The chance, from 0 to 1, that an unblocked attempt becomes a goal, based on things like distance, angle, shot type and situation. It's summed over shots. It measures shot quality, not finishing. Blocked attempts count as 0. | xGoals |
| S25 | Goals above expected | Goals - expected goals. Positive means the player finished better than the average shooter. | |
| S26 | Shot danger level | Shots grouped into low, medium and high danger by their xG value. The cut-offs belong to whichever model is used (MoneyPuck uses 8% and 20%), so answers must name the model. | Scoring chances |
| S27 | Rebound shot | An attempt taken very soon after an earlier attempt by the same team (the usual convention is within 3 seconds). | |
| S28 | Created expected goals | xG that credits a shooter for the rebounds their shot was likely to cause, rather than only the player who took the rebound. | Earned-rebound xG |
| S29 | Score- and venue-adjusted | A stat reweighted because teams play differently when leading or trailing, and at home or away. A trailing team tends to outshoot its opponent. | |
| S30 | Flurry-adjusted | xG reduced for quick strings of shots on one play, so that a scramble isn't counted as several separate chances. | |
| S31 | On-ice share (%) | For / (for + against) while the player is on the ice, for goals, shot attempts, unblocked attempts or xG, for example "xGF%". The relative version compares on-ice with off-ice. | CF%, FF%, xGF% |
| S32 | Shift | One stretch on the ice between going on and coming off. | |
| S33 | Zone starts | Where a player's shifts begin: an offensive-zone, defensive-zone or neutral-zone faceoff, or on the fly (changing during play). | |
| S34 | Hit, takeaway, giveaway | Body checks given, pucks won from an opponent, and pucks lost to one. These are judgment calls by each arena's scorers, so they vary by arena. | Real-time stats |
| S35 | Penalties drawn | Penalties called on opponents against this player. | |
| S36 | Game Score | A single number for one game that combines a player's box-score and on-ice stats. It's a composite rating by Dom Luszczyszyn, not an official stat. | |

### How Claude answers with these terms

- Use the NHL's meaning by default. If a question uses an analytics word ("Corsi", "5-on-5"), say which meaning the
  answer uses.
- For any rate or percentage, say the minimum sample used. Compute it from summed totals, never as an average of
  percentages.
- Mark any stat that is empty in early seasons, and leave those seasons out of "best ever" rate questions rather
  than treating them as zero.
- For a term that isn't loaded, say so and name what's missing (play-by-play or shot data). Never estimate it from
  the columns we do have.
