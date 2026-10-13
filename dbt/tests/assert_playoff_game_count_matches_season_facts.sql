-- For every finished season, the number of played playoff games must equal the NHL's own total.

with our_counts as (

    select season, count(*) as games
    from {{ ref('fct_games') }}
    where game_type_label = 'playoff' and is_final
    group by season

)

select
    seasons.season,
    seasons.total_playoff_games as expected_games,
    coalesce(our_counts.games, 0) as actual_games
from {{ ref('stg_nhl_stats__seasons') }} as seasons
left join our_counts on our_counts.season = seasons.season
where seasons.season_end_date < current_date
  and coalesce(our_counts.games, 0) != seasons.total_playoff_games
