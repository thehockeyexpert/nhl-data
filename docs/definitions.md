# Definitions

Status: DRAFT (2026-10-14). These definitions are referenced by id from `analyst/golden_questions.yml`.
Each one must be settled by the owner before the models or answers that depend on it are built.

| id | Definition | Status | Proposed default |
|---|---|---|---|
| D01 | Above .500 | **Decided** | The opponent's points percentage was above .500 in its standings before that game (that game excluded). The opponent's first game of the season counts as not above .500. |
| D02 | Standings points by era | Proposed | Taken from the NHL's `standings-season` flags for each season: 2 for a win, 1 for a tie, and 1 for an overtime or shootout loss where `pointForOTlossInUse` is true. |
| D03 | Team in history questions | **Decided** | Group by `lineage_id`. Answers say when the NHL's `franchise_id` differs, for example for the Winnipeg Jets (1979). |
| D04 | A goalie's record | Open | The goalie's credited decision (W, L, T, OTL) as the NHL reports it, not the team's result. To decide: only games the goalie started, or every game he played? |
| D05 | Minimums for rate leaders | Open | For example, save percentage needs 25 games or 750 shots against, and points per game needs 40 games. The numbers are to be set. |
| D06 | Streaks | Open | Does an overtime or shootout loss, or a tie, end a winning streak? Does a player's point streak skip games he missed? |
| D07 | One-goal game | Open | A final margin of one goal. To decide: include shootout games (scored as a one-goal win) or exclude them? |
| D08 | Back-to-back | Proposed | The team also played on the previous calendar day (`game_date`). |
| D09 | Rookie | Open | The NHL's rookie definition, or a player's first season with any NHL games? |
| D10 | Playoff appearance and drought | Open | A lineage appears in the playoffs if it played any playoff game that season. To decide: how to treat seasons before the NHL had a fixed playoff format. |
| D11 | Default scope | Proposed | Regular season only unless the question says playoffs or preseason. Special events (game types 4 and up) are never included. |
| D12 | "Today" in the daily run | Proposed | The North American date the NHL lists games under (`game_date`). The run computes it in Eastern time. |

Notes:

- The stats API reports skater and goalie rows with a team abbreviation, not a team ID. Abbreviations are reused across eras (for example WPG), so the team is resolved through `gameId` and home or road, joined to `fct_games`.
- Era limits (`docs/data_coverage.md` will be updated when each load lands):
  - Goalie shots against and saves start in 1955-56.
  - Skater shots and plus-minus are present by 1959-60.
  - Skater ice time and faceoffs start in 1997-98.
