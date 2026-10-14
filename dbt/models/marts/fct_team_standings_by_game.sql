-- Standings as of each regular-season game (docs/definitions.md, D01 and D02):
-- for every team and game, the totals from that team's EARLIER games of the same regular season.
-- The game itself is excluded. Games are ordered by date, then start time, then game ID.
-- Also the league median points % on that date, for the D01 headline definition ("top half").

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

),

team_totals_by_date as (

    -- Each team's totals at the end of each date it played (its last game that day).
    select season, team_id, game_date, games_played, points
    from (
        select
            season,
            team_id,
            game_date,
            count(*) over through_game as games_played,
            sum(points) over through_game as points,
            row_number() over (
                partition by season, team_id, game_date
                order by start_time_utc desc nulls first, game_id desc
            ) as last_game_of_day
        from team_games
        window through_game as (
            partition by season, team_id
            order by game_date, start_time_utc nulls last, game_id
            rows between unbounded preceding and current row
        )
    )
    where last_game_of_day = 1

),

league_on_date as (

    -- Every team of the season on every game date, with its totals from games before that date.
    select
        game_dates.season,
        game_dates.game_date,
        season_teams.team_id,
        totals.games_played,
        totals.points
    from (select distinct season, game_date from team_games) as game_dates
    inner join (select distinct season, team_id from team_games) as season_teams
        on season_teams.season = game_dates.season
    asof left join team_totals_by_date as totals
        on totals.season = game_dates.season
        and totals.team_id = season_teams.team_id
        and totals.game_date < game_dates.game_date

),

league_median as (

    -- The median over teams that have played at least one game before that date.
    select
        season,
        game_date,
        median(points / (2.0 * games_played)) filter (where games_played > 0) as league_median_pct_before,
        count(*) filter (where games_played > 0) as teams_with_games_before
    from league_on_date
    group by season, game_date

)

select
    running.*,
    case when running.games_played_before > 0
        then running.points_before / (2.0 * running.games_played_before) end as points_pct_before,
    -- D01, second column: above .500 by points % before the game. A team's first game counts as not above .500.
    coalesce(running.points_before / nullif(2.0 * running.games_played_before, 0) > 0.5, false) as is_above_500_before,
    league_median.league_median_pct_before,
    league_median.teams_with_games_before,
    -- D01, headline: top half of the league before the game. The team's points % is strictly above the league
    -- median that day, and it has played at least 10 games that season. Ties at the median do not count.
    coalesce(
        running.games_played_before >= 10
        and running.points_before / (2.0 * running.games_played_before) > league_median.league_median_pct_before,
        false
    ) as is_top_half_before
from running
left join league_median
    on league_median.season = running.season
    and league_median.game_date = running.game_date
