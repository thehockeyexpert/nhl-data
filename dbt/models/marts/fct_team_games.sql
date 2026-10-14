-- One row per team per finished regular-season or playoff game, with the result under that era's
-- standings rules (docs/definitions.md, D02): an overtime or shootout loss is OTL only in seasons
-- that award a point for it; before that it is a plain loss.

with games as (

    select * from {{ ref('fct_games') }}
    where game_type in (2, 3) and is_final

),

rules as (

    select season, is_point_for_ot_loss_in_use
    from {{ ref('stg_nhl_web__standings_rules') }}

),

sides as (

    select
        game_id, season, game_type, game_type_label, game_date, start_time_utc, last_period_type,
        home_team_id as team_id, away_team_id as opponent_team_id, true as is_home,
        home_score as goals_for, away_score as goals_against
    from games
    union all
    select
        game_id, season, game_type, game_type_label, game_date, start_time_utc, last_period_type,
        away_team_id, home_team_id, false,
        away_score, home_score
    from games

),

results as (

    select
        sides.*,
        case
            when goals_for > goals_against then 'W'
            when goals_for = goals_against then 'T'
            when coalesce(rules.is_point_for_ot_loss_in_use, false)
                and last_period_type in ('OT', 'SO') then 'OTL'
            else 'L'
        end as result
    from sides
    left join rules on rules.season = sides.season

)

select
    game_id || '-' || team_id as team_game_key,
    *,
    case result when 'W' then 2 when 'T' then 1 when 'OTL' then 1 else 0 end as points
from results
