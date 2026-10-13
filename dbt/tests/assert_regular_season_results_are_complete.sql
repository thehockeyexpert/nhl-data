-- In a finished season every regular-season game must be final and have both scores.
-- Level scores are allowed only in seasons where the NHL had ties.
-- Returns the games that break a rule, with the reason.

select
    games.game_id,
    games.season,
    case
        when not games.is_final then 'not final'
        when games.home_score is null or games.away_score is null then 'missing score'
        else 'tie in a season without ties'
    end as problem
from {{ ref('fct_games') }} as games
inner join {{ ref('stg_nhl_stats__seasons') }} as seasons on seasons.season = games.season
where games.game_type_label = 'regular'
  and seasons.season_end_date < current_date
  and (
      not games.is_final
      or games.home_score is null
      or games.away_score is null
      or (games.home_score = games.away_score and not seasons.is_ties_in_use)
  )
