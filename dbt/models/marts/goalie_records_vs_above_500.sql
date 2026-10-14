-- G01: each goalie's career regular-season record against opponents that were above .500 before the game.
--   D01: opponent's points percentage before that game (that game excluded) above .500.
--   D04: the goalie's credited decisions, whoever started.
--   D05: at least 50 such decisions to qualify (meets_minimum).
--   D23: ranked by win percentage of decisions; points percentage shown as a second column.
-- Caveats for any answer: from 1999-00 to 2003-04 a goalie's overtime loss is recorded as L;
-- standings use each era's points rules (D02).

with decisions as (

    select goalie_games.*
    from {{ ref('fct_goalie_games') }} as goalie_games
    inner join {{ ref('fct_team_standings_by_game') }} as opponent
        on opponent.game_id = goalie_games.game_id
        and opponent.team_id = goalie_games.opponent_team_id
    where goalie_games.game_type = 2
      and goalie_games.decision is not null
      and opponent.is_above_500_before

),

records as (

    select
        player_id,
        arg_max(goalie_name, game_date) as goalie_name,
        min(season) as first_season,
        max(season) as last_season,
        count(*) as decisions,
        count(*) filter (where decision = 'W') as wins,
        count(*) filter (where decision = 'L') as losses,
        count(*) filter (where decision = 'T') as ties,
        count(*) filter (where decision = 'OTL') as ot_losses
    from decisions
    group by player_id

)

select
    *,
    wins / decisions::double as win_pct,
    (2 * wins + ties + ot_losses) / (2.0 * decisions) as points_pct,
    decisions >= 50 as meets_minimum
from records
