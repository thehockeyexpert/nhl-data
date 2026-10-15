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
| D14 | Where a player is "from" | Open | Birthplace as the NHL records it (birth city, state or province code, country code), not nationality or hometown. A city is identified by city plus state or province plus country, so towns that share a name stay separate. |
| D15 | NHL player | Proposed | Anyone with at least one NHL regular-season or playoff game in the game-level stats. Special events (game types 4 and up) do not count. |
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
