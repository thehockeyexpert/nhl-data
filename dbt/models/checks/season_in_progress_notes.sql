-- Games in a season that is not finished yet that need a human eye but are not failures:
-- postponed, suspended or cancelled games, and past games not final yet (still inside the
-- two-day lag the checks allow). Nothing here fails the build.

select
    games.season,
    games.game_id,
    games.game_date,
    games.away_team_abbrev,
    games.home_team_abbrev,
    games.game_state,
    games.game_schedule_state,
    case
        when games.game_schedule_state = 'PPD' then 'postponed'
        when games.game_schedule_state = 'SUSP' then 'suspended'
        when games.game_schedule_state = 'CNCL' then 'cancelled'
        else 'dated before today, not final yet'
    end as note
from {{ ref('stg_nhl_web__schedule_games') }} as games
inner join {{ ref('season_status') }} as season_status on season_status.season = games.season
where not season_status.is_finished
  and games.game_type in (1, 2, 3)
  and (
      games.game_schedule_state in ('PPD', 'SUSP', 'CNCL')
      or (games.game_date < current_date and not games.is_final)
  )
