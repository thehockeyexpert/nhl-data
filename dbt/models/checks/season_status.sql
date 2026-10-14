-- One row per season with season facts, saying whether the data checks treat it as finished.
-- A season is finished when the NHL's planned end date has passed AND the weekly schedule has no
-- regular-season or playoff game left that is still scheduled (not final, schedule state OK).
-- The planned end date alone is not enough: a Final can run later than planned.
-- "If necessary" playoff games that were never played are not in the weekly schedule, so they do not count.

with seasons as (

    select * from {{ ref('stg_nhl_stats__seasons') }}

),

open_games as (

    select season, count(*) as open_games
    from {{ ref('stg_nhl_web__schedule_games') }}
    where game_type in (2, 3)
      and not is_final
      and game_schedule_state = 'OK'
    group by season

)

select
    seasons.season,
    seasons.season_end_date,
    coalesce(open_games.open_games, 0) as open_games,
    seasons.season_end_date < current_date
        and coalesce(open_games.open_games, 0) = 0 as is_finished
from seasons
left join open_games on open_games.season = seasons.season
