-- One row per game in fct_games (preseason, regular season, playoffs): what the game was, not how it ended.
-- fct_games keeps the same columns plus the result, so existing queries keep working.

select
    game_id,
    season,
    game_type,
    game_type_label,
    game_date,
    start_time_utc,
    home_team_id,
    away_team_id,
    venue_name,
    is_neutral_site
from {{ ref('fct_games') }}
