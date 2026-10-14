-- Standings as of each regular-season game (docs/definitions.md, D01 and D02):
-- for every team and game, the totals from that team's EARLIER games of the same regular season.
-- The game itself is excluded. Games are ordered by date, then start time, then game ID.

with team_games as (

    select * from {{ ref('fct_team_games') }}
    where game_type = 2

),

running as (

    select
        team_game_key,
        game_id,
        season,
        game_date,
        team_id,
        opponent_team_id,
        result,
        count(*) over earlier as games_played_before,
        count(*) filter (where result = 'W') over earlier as wins_before,
        count(*) filter (where result = 'L') over earlier as losses_before,
        count(*) filter (where result = 'T') over earlier as ties_before,
        count(*) filter (where result = 'OTL') over earlier as ot_losses_before,
        coalesce(sum(points) over earlier, 0) as points_before
    from team_games
    window earlier as (
        partition by season, team_id
        order by game_date, start_time_utc nulls last, game_id
        rows between unbounded preceding and 1 preceding
    )

)

select
    *,
    case when games_played_before > 0 then points_before / (2.0 * games_played_before) end as points_pct_before,
    -- Above .500 before the game (D01). A team's first game of the season counts as not above .500.
    coalesce(points_before / nullif(2.0 * games_played_before, 0) > 0.5, false) as is_above_500_before
from running
