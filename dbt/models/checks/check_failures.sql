-- Every row that breaks a data check, before the known exceptions are taken out.
-- The tests in dbt/tests read from here, so each rule is written once.
-- Expected counts always come from the NHL's season facts, never from a hardcoded number.

with seasons as (

    select * from {{ ref('stg_nhl_stats__seasons') }}

),

finished_seasons as (

    -- Count and completeness rules only apply once a season is over.
    select * from seasons where season_end_date < current_date

),

loaded_seasons as (

    select distinct season from {{ ref('stg_nhl_stats__games') }}

),

games as (

    select * from {{ ref('fct_games') }}

),

regular_team_games as (

    select season, home_team_id as team_id, home_team_abbrev as team_abbrev
    from games
    where game_type_label = 'regular'
    union all
    select season, away_team_id, away_team_abbrev
    from games
    where game_type_label = 'regular'

),

per_team as (

    select season, team_id, any_value(team_abbrev) as team_abbrev, count(*) as games
    from regular_team_games
    group by season, team_id

),

season_shape as (

    select
        finished_seasons.season,
        finished_seasons.scheduled_games_per_team,
        finished_seasons.total_regular_season_games,
        count(per_team.team_id) as teams,
        min(per_team.games) as fewest_games,
        max(per_team.games) as most_games,
        -- Balanced: every team can have played the scheduled number of games.
        finished_seasons.total_regular_season_games * 2
            = count(per_team.team_id) * finished_seasons.scheduled_games_per_team as is_balanced
    from finished_seasons
    inner join per_team on per_team.season = finished_seasons.season
    group by
        finished_seasons.season,
        finished_seasons.scheduled_games_per_team,
        finished_seasons.total_regular_season_games

),

season_facts_present as (

    select
        'season_facts_present' as check_name,
        loaded_seasons.season,
        null::bigint as game_id,
        'the game list has games for this season but the NHL has no season facts for it' as detail
    from loaded_seasons
    left join seasons on seasons.season = loaded_seasons.season
    where seasons.season is null

),

regular_season_game_count as (

    select
        'regular_season_game_count' as check_name,
        finished_seasons.season,
        null::bigint as game_id,
        'expected ' || finished_seasons.total_regular_season_games || ', actual ' || count(games.game_id) as detail
    from finished_seasons
    left join games on games.season = finished_seasons.season and games.game_type_label = 'regular'
    group by finished_seasons.season, finished_seasons.total_regular_season_games
    having count(games.game_id) != finished_seasons.total_regular_season_games

),

playoff_game_count as (

    select
        'playoff_game_count' as check_name,
        finished_seasons.season,
        null::bigint as game_id,
        'expected ' || finished_seasons.total_playoff_games || ', actual ' || count(games.game_id) as detail
    from finished_seasons
    left join games
        on games.season = finished_seasons.season
        and games.game_type_label = 'playoff'
        and games.is_final
    group by finished_seasons.season, finished_seasons.total_playoff_games
    having count(games.game_id) != finished_seasons.total_playoff_games

),

season_balanced as (

    select
        'season_balanced' as check_name,
        season,
        null::bigint as game_id,
        teams || ' teams, ' || scheduled_games_per_team || ' scheduled per team, '
            || total_regular_season_games || ' games in total, teams have '
            || fewest_games || ' to ' || most_games || ' games' as detail
    from season_shape
    where not is_balanced

),

games_per_team as (

    -- Only meaningful in a balanced season. Unbalanced seasons are reported by season_balanced.
    select
        'games_per_team' as check_name,
        per_team.season,
        null::bigint as game_id,
        per_team.team_abbrev || ': expected ' || season_shape.scheduled_games_per_team
            || ', actual ' || per_team.games as detail
    from per_team
    inner join season_shape on season_shape.season = per_team.season
    where season_shape.is_balanced
      and per_team.games != season_shape.scheduled_games_per_team

),

regular_season_results_complete as (

    select
        'regular_season_results_complete' as check_name,
        games.season,
        games.game_id,
        case
            when not games.is_final then 'not final'
            when games.home_score is null or games.away_score is null then 'missing score'
            else 'tie in a season without ties'
        end as detail
    from games
    inner join finished_seasons on finished_seasons.season = games.season
    where games.game_type_label = 'regular'
      and (
          not games.is_final
          or games.home_score is null
          or games.away_score is null
          or (games.home_score = games.away_score and not finished_seasons.is_ties_in_use)
      )

),

regular_season_teams_are_nhl as (

    select
        'regular_season_teams_are_nhl' as check_name,
        games.season,
        games.game_id,
        'a team in this regular-season game is not in the NHL team list: '
            || games.away_team_abbrev || ' at ' || games.home_team_abbrev as detail
    from games
    left join {{ ref('dim_teams') }} as home_teams on home_teams.team_id = games.home_team_id
    left join {{ ref('dim_teams') }} as away_teams on away_teams.team_id = games.away_team_id
    where games.game_type_label = 'regular'
      and not (coalesce(home_teams.is_nhl_team, false) and coalesce(away_teams.is_nhl_team, false))

),

schedule_games as (

    select game_id, season, home_team_id, away_team_id, home_score, away_score
    from {{ ref('stg_nhl_web__schedule_games') }}
    where game_type in (2, 3)
      and is_final
      and season in (select season from loaded_seasons)

),

list_games as (

    select game_id, season, home_team_id, away_team_id, home_score, away_score
    from {{ ref('stg_nhl_stats__games') }}
    where game_type in (2, 3) and is_final

),

schedule_and_game_list_agree as (

    select
        'schedule_and_game_list_agree' as check_name,
        coalesce(schedule_games.season, list_games.season) as season,
        coalesce(schedule_games.game_id, list_games.game_id) as game_id,
        case
            when list_games.game_id is null then 'only in weekly schedule'
            when schedule_games.game_id is null then 'only in game list'
            else 'teams or scores differ: schedule '
                || schedule_games.away_team_id || ' ' || schedule_games.away_score || ' at '
                || schedule_games.home_team_id || ' ' || schedule_games.home_score || ', game list '
                || list_games.away_team_id || ' ' || list_games.away_score || ' at '
                || list_games.home_team_id || ' ' || list_games.home_score
        end as detail
    from schedule_games
    full outer join list_games on list_games.game_id = schedule_games.game_id
    where schedule_games.game_id is null
       or list_games.game_id is null
       or schedule_games.home_team_id != list_games.home_team_id
       or schedule_games.away_team_id != list_games.away_team_id
       or schedule_games.home_score != list_games.home_score
       or schedule_games.away_score != list_games.away_score

)

select * from season_facts_present
union all
select * from regular_season_game_count
union all
select * from playoff_game_count
union all
select * from season_balanced
union all
select * from games_per_team
union all
select * from regular_season_results_complete
union all
select * from regular_season_teams_are_nhl
union all
select * from schedule_and_game_list_agree
