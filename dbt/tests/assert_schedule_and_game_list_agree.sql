-- The two NHL sources must list the same finished regular-season and playoff games,
-- with the same teams and scores. Returns every game where they disagree.

with schedule_games as (

    select game_id, home_team_id, away_team_id, home_score, away_score
    from {{ ref('stg_nhl_web__schedule_games') }}
    where game_type in (2, 3) and is_final

),

list_games as (

    select game_id, home_team_id, away_team_id, home_score, away_score
    from {{ ref('stg_nhl_stats__games') }}
    where game_type in (2, 3) and is_final

)

select
    coalesce(schedule_games.game_id, list_games.game_id) as game_id,
    case
        when list_games.game_id is null then 'only in weekly schedule'
        when schedule_games.game_id is null then 'only in game list'
        else 'teams or scores differ'
    end as problem
from schedule_games
full outer join list_games on list_games.game_id = schedule_games.game_id
where schedule_games.game_id is null
   or list_games.game_id is null
   or schedule_games.home_team_id != list_games.home_team_id
   or schedule_games.away_team_id != list_games.away_team_id
   or schedule_games.home_score != list_games.home_score
   or schedule_games.away_score != list_games.away_score
