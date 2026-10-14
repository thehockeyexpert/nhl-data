-- Monitoring: from 2022-23, how many goalie rows have saves + goals against exactly one more than shots against.
-- Observed, unexplained: such rows appear from 2022-23 only, at about 0.5% to 0.9% of goalie rows per season.
-- The era rule in check_failures allows them; goalie_saves_plus_one_rate fails if the share becomes unusual.

select
    season,
    count(*) as goalie_rows_with_shots,
    count(*) filter (
        where coalesce(saves, 0) + coalesce(goals_against, 0) - shots_against = 1
    ) as plus_one_rows,
    count(*) filter (
        where coalesce(saves, 0) + coalesce(goals_against, 0) - shots_against = 1
    ) / count(*)::double as plus_one_share
from {{ ref('fct_goalie_games') }}
where season >= 20222023
  and shots_against is not null
group by season
