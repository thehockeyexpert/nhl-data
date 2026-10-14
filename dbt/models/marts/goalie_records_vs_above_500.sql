-- G01: each goalie's career regular-season record against strong opponents.
--   D01 headline (top_half_*): the opponent's points % before the game is strictly above the league median that
--        day (median over teams with at least one game), and the opponent has played at least 10 games.
--   D01 second column (above_500_*): the opponent's points % before the game is above .500 (first game: not above).
--   D04: the goalie's credited decisions, whoever started.
--   D05: at least 50 qualifying decisions (meets_minimum_50), also reported at 100 (meets_minimum_100).
--   D23: win percentage is the headline measure; points percentage beside it.
-- Caveats for any answer: from 1999-00 to 2003-04 a goalie's overtime loss is recorded as L; ties exist only
-- until 2003-04; standings use each era's points rules (D02); strength is measured before each game.

with decisions as (

    select
        goalie_games.player_id,
        goalie_games.goalie_name,
        goalie_games.game_date,
        goalie_games.season,
        goalie_games.decision,
        opponent.is_top_half_before,
        opponent.is_above_500_before
    from {{ ref('fct_goalie_games') }} as goalie_games
    inner join {{ ref('fct_team_standings_by_game') }} as opponent
        on opponent.game_id = goalie_games.game_id
        and opponent.team_id = goalie_games.opponent_team_id
    where goalie_games.game_type = 2
      and goalie_games.decision is not null
      and (opponent.is_top_half_before or opponent.is_above_500_before)

),

records as (

    select
        player_id,
        arg_max(goalie_name, game_date) as goalie_name,
        min(season) filter (where is_top_half_before) as top_half_first_season,
        max(season) filter (where is_top_half_before) as top_half_last_season,
        count(*) filter (where is_top_half_before) as top_half_decisions,
        count(*) filter (where is_top_half_before and decision = 'W') as top_half_wins,
        count(*) filter (where is_top_half_before and decision = 'L') as top_half_losses,
        count(*) filter (where is_top_half_before and decision = 'T') as top_half_ties,
        count(*) filter (where is_top_half_before and decision = 'OTL') as top_half_ot_losses,
        count(*) filter (where is_above_500_before) as above_500_decisions,
        count(*) filter (where is_above_500_before and decision = 'W') as above_500_wins,
        count(*) filter (where is_above_500_before and decision = 'L') as above_500_losses,
        count(*) filter (where is_above_500_before and decision = 'T') as above_500_ties,
        count(*) filter (where is_above_500_before and decision = 'OTL') as above_500_ot_losses
    from decisions
    group by player_id

)

select
    *,
    top_half_wins / nullif(top_half_decisions, 0)::double as top_half_win_pct,
    (2 * top_half_wins + top_half_ties + top_half_ot_losses) / nullif(2.0 * top_half_decisions, 0) as top_half_points_pct,
    top_half_decisions >= 50 as meets_minimum_50,
    top_half_decisions >= 100 as meets_minimum_100,
    above_500_wins / nullif(above_500_decisions, 0)::double as above_500_win_pct,
    (2 * above_500_wins + above_500_ties + above_500_ot_losses) / nullif(2.0 * above_500_decisions, 0) as above_500_points_pct,
    above_500_decisions >= 50 as above_500_meets_minimum_50
from records
