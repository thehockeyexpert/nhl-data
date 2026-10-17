-- Every row that breaks a data check, before the known exceptions are taken out.
-- The tests in dbt/tests read from here, so each rule is written once.
-- Expected counts always come from the NHL's season facts, never from a hardcoded number.
-- Rules for a season in progress use a two-day lag (game_date <= current_date - 2), so games that
-- have just ended, or late games still running after midnight Eastern, do not fail a check.
-- Stored as a table, not a view, so the checks read it once instead of each recomputing it from the
-- raw JSON. Rebuild it before running the checks: it holds the failures as of its last build.

{{ config(materialized='table') }}

with seasons as (

    select * from {{ ref('stg_nhl_stats__seasons') }}

),

season_status as (

    select * from {{ ref('season_status') }}

),

finished_seasons as (

    -- Count and completeness rules only apply once a season is over (see season_status).
    select seasons.*
    from seasons
    inner join season_status on season_status.season = seasons.season
    where season_status.is_finished

),

in_progress_seasons as (

    select seasons.*
    from seasons
    inner join season_status on season_status.season = seasons.season
    where not season_status.is_finished
      and seasons.season in (select distinct season from {{ ref('stg_nhl_stats__games') }})

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
        'the game list has games for this season but the NHL has no season facts for it' as detail,
        null::integer as team_id
    from loaded_seasons
    left join seasons on seasons.season = loaded_seasons.season
    where seasons.season is null

),

regular_season_game_count as (

    select
        'regular_season_game_count' as check_name,
        finished_seasons.season,
        null::bigint as game_id,
        'expected ' || finished_seasons.total_regular_season_games || ', actual ' || count(games.game_id) as detail,
        null::integer as team_id
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
        'expected ' || finished_seasons.total_playoff_games || ', actual ' || count(games.game_id) as detail,
        null::integer as team_id
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
            || fewest_games || ' to ' || most_games || ' games' as detail,
            null::integer as team_id
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
            || ', actual ' || per_team.games as detail,
            null::integer as team_id
    from per_team
    inner join season_shape on season_shape.season = per_team.season
    where season_shape.is_balanced
      and per_team.games != season_shape.scheduled_games_per_team

),

regular_season_results_complete as (

    -- Finished seasons: every regular-season game is final, with both scores, and level only if ties
    -- were allowed. A season in progress: final games must not be level when ties are not allowed.
    select
        'regular_season_results_complete' as check_name,
        games.season,
        games.game_id,
        case
            when not games.is_final then 'not final'
            when games.home_score is null or games.away_score is null then 'missing score'
            else 'tie in a season without ties'
        end as detail,
        null::integer as team_id
    from games
    inner join seasons on seasons.season = games.season
    inner join season_status on season_status.season = games.season
    where games.game_type_label = 'regular'
      and (
          (
              season_status.is_finished
              and (
                  not games.is_final
                  or games.home_score is null
                  or games.away_score is null
                  or (games.home_score = games.away_score and not seasons.is_ties_in_use)
              )
          )
          or (
              not season_status.is_finished
              and games.is_final
              and games.home_score = games.away_score
              and not seasons.is_ties_in_use
          )
      )

),

regular_season_teams_are_nhl as (

    select
        'regular_season_teams_are_nhl' as check_name,
        games.season,
        games.game_id,
        'a team in this regular-season game is not in the NHL team list: '
            || games.away_team_abbrev || ' at ' || games.home_team_abbrev as detail,
            null::integer as team_id
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
      and (season in (select season from finished_seasons) or game_date <= current_date - 2)

),

list_games as (

    select game_id, season, home_team_id, away_team_id, home_score, away_score
    from {{ ref('stg_nhl_stats__games') }}
    where game_type in (2, 3)
      and is_final
      and (season in (select season from finished_seasons) or game_date <= current_date - 2)

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
        end as detail,
        null::integer as team_id
    from schedule_games
    full outer join list_games on list_games.game_id = schedule_games.game_id
    where schedule_games.game_id is null
       or list_games.game_id is null
       or schedule_games.home_team_id != list_games.home_team_id
       or schedule_games.away_team_id != list_games.away_team_id
       or schedule_games.home_score != list_games.home_score
       or schedule_games.away_score != list_games.away_score

),

past_games_final as (

    -- A game dated at least two days ago must be final, unless the NHL marks it postponed,
    -- suspended or cancelled. Those are listed in checks.season_in_progress_notes instead.
    select
        'past_games_final' as check_name,
        season,
        game_id,
        'dated ' || game_date || ', state ' || game_state || ', schedule state ' || game_schedule_state as detail,
        null::integer as team_id
    from {{ ref('stg_nhl_web__schedule_games') }}
    where game_type in (1, 2, 3)
      and season in (select season from loaded_seasons)
      and game_date <= current_date - 2
      and not is_final
      and game_schedule_state not in ('PPD', 'SUSP', 'CNCL')

),

scheduled_list_games as (

    select season, home_team_id, away_team_id
    from {{ ref('stg_nhl_stats__games') }}
    where game_type = 2
      and season in (select season from in_progress_seasons)

),

scheduled_game_count as (

    -- A season in progress: the game list must already hold the full regular-season schedule,
    -- in total and for every team.
    select
        'scheduled_game_count' as check_name,
        in_progress_seasons.season,
        null::bigint as game_id,
        'scheduled ' || count(scheduled_list_games.season) || ' regular-season games, expected '
            || in_progress_seasons.total_regular_season_games as detail,
            null::integer as team_id
    from in_progress_seasons
    left join scheduled_list_games on scheduled_list_games.season = in_progress_seasons.season
    group by in_progress_seasons.season, in_progress_seasons.total_regular_season_games
    having count(scheduled_list_games.season) != in_progress_seasons.total_regular_season_games

    union all

    select
        'scheduled_game_count' as check_name,
        team_schedule.season,
        null::bigint as game_id,
        'team ' || team_schedule.team_id || ': scheduled ' || team_schedule.games
            || ', expected ' || in_progress_seasons.scheduled_games_per_team as detail,
            null::integer as team_id
    from (
        select season, team_id, count(*) as games
        from (
            select season, home_team_id as team_id from scheduled_list_games
            union all
            select season, away_team_id from scheduled_list_games
        )
        group by season, team_id
    ) as team_schedule
    inner join in_progress_seasons on in_progress_seasons.season = team_schedule.season
    where team_schedule.games != in_progress_seasons.scheduled_games_per_team

),

players as (

    select player_id from {{ ref('stg_nhl_records__players') }}

),

award_player_exists as (

    select
        'award_player_exists' as check_name,
        awards.season,
        null::bigint as game_id,
        'award result ' || awards.award_result_id || ' (trophy ' || awards.trophy_id
            || ') names player ' || awards.player_id || ', who is not in the player list' as detail,
            null::integer as team_id
    from {{ ref('stg_nhl_records__award_results') }} as awards
    where awards.player_id is not null
      and awards.player_id not in (select player_id from players)

),

draft_player_exists as (

    -- The season column holds the season that ends in the draft's year (the 2015 draft is 20142015).
    select
        'draft_player_exists' as check_name,
        (picks.draft_year - 1) * 10000 + picks.draft_year as season,
        null::bigint as game_id,
        'draft pick ' || picks.draft_pick_id || ' (' || picks.draft_year || ', overall '
            || picks.overall_pick || ') names player ' || picks.player_id
            || ', who is not in the player list' as detail,
            null::integer as team_id
    from {{ ref('stg_nhl_records__draft_picks') }} as picks
    where picks.player_id is not null
      and picks.player_id not in (select player_id from players)

),

playoff_series_game_exists as (

    select
        'playoff_series_game_exists' as check_name,
        series_games.season,
        series_games.game_id,
        'series game is not a playoff game in the game list' as detail,
        null::integer as team_id
    from {{ ref('stg_nhl_records__playoff_series_games') }} as series_games
    left join {{ ref('stg_nhl_stats__games') }} as list_games
        on list_games.game_id = series_games.game_id
        and list_games.game_type = 3
    where list_games.game_id is null

),

playoff_games_in_series as (

    select
        'playoff_games_in_series' as check_name,
        games.season,
        games.game_id,
        'finished playoff game has no playoff series row' as detail,
        null::integer as team_id
    from games
    where games.game_type_label = 'playoff'
      and games.is_final
      and games.game_id not in (select game_id from {{ ref('stg_nhl_records__playoff_series_games') }})

),

standings_rules_match_season_facts as (

    select
        'standings_rules_match_season_facts' as check_name,
        seasons.season,
        null::bigint as game_id,
        case
            when rules.season is null then 'no standings rules for a season with season facts'
            else 'ties in use: standings rules ' || rules.is_ties_in_use
                || ', season facts ' || seasons.is_ties_in_use
        end as detail,
        null::integer as team_id
    from seasons
    left join {{ ref('stg_nhl_web__standings_rules') }} as rules on rules.season = seasons.season
    where rules.season is null
       or rules.is_ties_in_use != seasons.is_ties_in_use

),

-- Goalie and standings rules. Goalie rules apply only to seasons whose goalie games are loaded.

goalie_seasons as (

    select distinct season from {{ ref('stg_nhl_stats__goalie_games') }}

),

goalie_games as (

    select * from {{ ref('fct_goalie_games') }}

),

checked_team_games as (

    -- Finished regular-season and playoff team-games in goalie seasons, with the two-day lag for a season in progress.
    select team_games.*
    from {{ ref('fct_team_games') }} as team_games
    where team_games.season in (select season from goalie_seasons)
      and (team_games.season in (select season from finished_seasons) or team_games.game_date <= current_date - 2)

),

goalie_sides as (

    select
        game_id,
        team_id,
        count(*) as goalies,
        count(decision) as decisions,
        any_value(decision) as decision
    from goalie_games
    group by game_id, team_id

),

goalie_games_covered as (

    select
        'goalie_games_covered' as check_name,
        checked_team_games.season,
        checked_team_games.game_id,
        'no goalie rows for this team in a finished game' as detail,
        checked_team_games.team_id
    from checked_team_games
    left join goalie_sides
        on goalie_sides.game_id = checked_team_games.game_id
        and goalie_sides.team_id = checked_team_games.team_id
    where goalie_sides.game_id is null

    union all

    select
        'goalie_games_covered' as check_name,
        goalie_games.season,
        goalie_games.game_id,
        'goalie row for a game that is not in fct_games' as detail,
        null::integer as team_id
    from goalie_games
    where goalie_games.team_id is null

),

goalie_decision_matches_result as (

    -- Each team in a finished game has exactly one credited decision, and it matches the result:
    -- W for the winner, T for both teams in a tie, L or OTL for the loser (OTL only after OT or a shootout).
    select
        'goalie_decision_matches_result' as check_name,
        checked_team_games.season,
        checked_team_games.game_id,
        case
            when goalie_sides.decisions != 1 then goalie_sides.decisions || ' credited decisions'
            else 'decision ' || goalie_sides.decision || ' for a team that scored '
                || checked_team_games.goals_for || '-' || checked_team_games.goals_against
                || ' (' || coalesce(checked_team_games.last_period_type, '?') || ')'
        end as detail,
        checked_team_games.team_id
    from checked_team_games
    inner join goalie_sides
        on goalie_sides.game_id = checked_team_games.game_id
        and goalie_sides.team_id = checked_team_games.team_id
    where goalie_sides.decisions != 1
       or (checked_team_games.goals_for > checked_team_games.goals_against and goalie_sides.decision != 'W')
       or (checked_team_games.goals_for = checked_team_games.goals_against and goalie_sides.decision != 'T')
       or (checked_team_games.goals_for < checked_team_games.goals_against and goalie_sides.decision not in ('L', 'OTL'))
       or (goalie_sides.decision = 'OTL' and coalesce(checked_team_games.last_period_type, '') not in ('OT', 'SO'))

),

official_team_seasons as (

    select * from {{ ref('stg_nhl_stats__team_seasons') }}
    where season in (select season from finished_seasons)

),

goalie_team_seasons as (

    select
        season,
        team_id,
        count(*) filter (where decision = 'W') as wins,
        count(*) filter (where decision = 'L') as losses,
        count(*) filter (where decision = 'T') as ties,
        count(*) filter (where decision = 'OTL') as ot_losses,
        count(*) filter (where is_shutout) as shutouts,
        sum(shots_against) as shots_against,
        count(*) filter (where shots_against is null) as rows_without_shots
    from goalie_games
    where game_type = 2
    group by season, team_id

),

goalie_totals_match_official as (

    -- Goalie wins and ties equal the official team totals. Goalie losses plus OT losses equal the team's;
    -- goalie OT losses alone are compared from 2005-06, because 1999-00 to 2003-04 goalie OT losses appear as L.
    select
        'goalie_totals_match_official' as check_name,
        official.season,
        null::bigint as game_id,
        'goalies W-L-T-OTL ' || coalesce(goalies.wins, 0) || '-' || coalesce(goalies.losses, 0) || '-'
            || coalesce(goalies.ties, 0) || '-' || coalesce(goalies.ot_losses, 0) || ', official '
            || official.wins || '-' || official.losses || '-' || coalesce(official.ties, 0) || '-'
            || coalesce(official.ot_losses, 0) as detail,
        official.team_id
    from official_team_seasons as official
    left join goalie_team_seasons as goalies
        on goalies.season = official.season
        and goalies.team_id = official.team_id
    where official.season in (select season from goalie_seasons)
      and (
          coalesce(goalies.wins, 0) != official.wins
          or coalesce(goalies.ties, 0) != coalesce(official.ties, 0)
          or coalesce(goalies.losses, 0) + coalesce(goalies.ot_losses, 0)
              != official.losses + coalesce(official.ot_losses, 0)
          or (official.season >= 20052006 and coalesce(goalies.ot_losses, 0) != coalesce(official.ot_losses, 0))
      )

),

goalie_shutouts_consistent as (

    select
        'goalie_shutouts_consistent' as check_name,
        season,
        game_id,
        'shutout credited to player ' || player_id || ' with ' || goals_against || ' goals against' as detail,
        team_id
    from goalie_games
    where is_shutout and goals_against > 0

    union all

    -- Team shutouts can exceed goalie shutouts (a shutout shared by two goalies is credited to neither).
    select
        'goalie_shutouts_consistent' as check_name,
        official.season,
        null::bigint as game_id,
        'goalie shutouts ' || goalies.shutouts || ' exceed official team shutouts ' || official.team_shutouts as detail,
        official.team_id
    from official_team_seasons as official
    inner join goalie_team_seasons as goalies
        on goalies.season = official.season
        and goalies.team_id = official.team_id
    where goalies.shutouts > official.team_shutouts

),

goalie_saves_add_up as (

    select
        'goalie_saves_add_up' as check_name,
        season,
        game_id,
        'player ' || player_id || ': saves ' || coalesce(saves::varchar, 'empty') || ' + goals against '
            || coalesce(goals_against::varchar, 'empty') || ' != shots against ' || shots_against as detail,
        team_id
    from goalie_games
    where season >= 19551956
      and shots_against is not null
      and coalesce(saves, 0) + coalesce(goals_against, 0) != shots_against
      -- Era rule: from 2022-23, saves + goals against exceeding shots against by exactly 1 is allowed
      -- (observed, unexplained; watched by goalie_saves_plus_one_rate). Any other difference still fails.
      and not (
          season >= 20222023
          and coalesce(saves, 0) + coalesce(goals_against, 0) - shots_against = 1
      )

),

goalie_saves_plus_one_rate as (

    -- The +1 rows allowed above must stay rare: at most 2% of a season's goalie rows,
    -- judged once a season has at least 500 goalie rows with shots.
    select
        'goalie_saves_plus_one_rate' as check_name,
        season,
        null::bigint as game_id,
        plus_one_rows || ' of ' || goalie_rows_with_shots || ' goalie rows ('
            || round(100 * plus_one_share, 2) || '%) have saves + goals against = shots against + 1; the limit is 2%' as detail,
        null::integer as team_id
    from {{ ref('goalie_saves_plus_one_by_season') }}
    where goalie_rows_with_shots >= 500
      and plus_one_share > 0.02

),

goalie_shots_within_team as (

    -- Shots on an empty net count for the team but not against a goalie, so goalie shots against can be lower.
    select
        'goalie_shots_within_team' as check_name,
        official.season,
        null::bigint as game_id,
        'goalie shots against ' || goalies.shots_against || ' exceed official team shots against '
            || round(official.shots_against_per_game * official.games_played)::integer as detail,
        official.team_id
    from official_team_seasons as official
    inner join goalie_team_seasons as goalies
        on goalies.season = official.season
        and goalies.team_id = official.team_id
    where official.season >= 19591960
      and official.shots_against_per_game is not null
      and goalies.rows_without_shots = 0
      and goalies.shots_against > round(official.shots_against_per_game * official.games_played)

),

derived_team_seasons as (

    select
        season,
        team_id,
        count(*) as games_played,
        count(*) filter (where result = 'W') as wins,
        count(*) filter (where result = 'L') as losses,
        count(*) filter (where result = 'T') as ties,
        count(*) filter (where result = 'OTL') as ot_losses,
        sum(points) as points
    from {{ ref('fct_team_games') }}
    where game_type = 2
    group by season, team_id

),

standings_match_official as (

    -- Standings derived from fct_games under each era's rules must equal the NHL's official season totals.
    select
        'standings_match_official' as check_name,
        coalesce(official.season, derived.season) as season,
        null::bigint as game_id,
        'derived GP-W-L-T-OTL-PTS ' || coalesce(derived.games_played, 0) || '-' || coalesce(derived.wins, 0) || '-'
            || coalesce(derived.losses, 0) || '-' || coalesce(derived.ties, 0) || '-' || coalesce(derived.ot_losses, 0)
            || '-' || coalesce(derived.points, 0) || ', official ' || coalesce(official.games_played, 0) || '-'
            || coalesce(official.wins, 0) || '-' || coalesce(official.losses, 0) || '-' || coalesce(official.ties, 0)
            || '-' || coalesce(official.ot_losses, 0) || '-' || coalesce(official.points, 0) as detail,
        coalesce(official.team_id, derived.team_id) as team_id
    from official_team_seasons as official
    full outer join (
        select * from derived_team_seasons where season in (select season from finished_seasons)
    ) as derived
        on derived.season = official.season
        and derived.team_id = official.team_id
    where official.season is null
       or derived.season is null
       or derived.games_played != official.games_played
       or derived.wins != official.wins
       or derived.losses != official.losses
       or derived.ties != coalesce(official.ties, 0)
       or derived.ot_losses != coalesce(official.ot_losses, 0)
       or derived.points != official.points

),

skater_seasons as (

    select * from {{ ref('fct_skater_seasons') }}

),

skater_team_resolves as (

    -- Every team abbreviation in the skater totals matches a team that played that season.
    select
        'skater_team_resolves' as check_name,
        season,
        null::bigint as game_id,
        'abbreviation ' || team_abbrev || ' (game type ' || game_type || ') matches no team that season' as detail,
        null::integer as team_id
    from {{ ref('bridge_skater_season_teams') }}
    where team_id is null

),

team_games_per_season as (

    select season, game_type, team_id, count(*) as games
    from {{ ref('fct_team_games') }}
    group by season, game_type, team_id

),

skater_team_games as (

    -- The games the skater's teams played that season and game type: one team's games, or for a player who
    -- changed teams, the total of his teams' games.
    select
        bridge.skater_season_key,
        sum(coalesce(team_games.games, 0)) as team_games
    from {{ ref('bridge_skater_season_teams') }} as bridge
    left join team_games_per_season as team_games
        on team_games.season = bridge.season
        and team_games.game_type = bridge.game_type
        and team_games.team_id = bridge.team_id
    group by bridge.skater_season_key

),

skater_games_within_team as (

    -- No skater can play more games than his teams played that season and game type.
    select
        'skater_games_within_team' as check_name,
        skater_seasons.season,
        null::bigint as game_id,
        'player ' || skater_seasons.player_id || ' has ' || skater_seasons.games_played || ' games (game type '
            || skater_seasons.game_type || '), his teams ' || coalesce(teams.team_games, 0) as detail,
        skater_seasons.team_id
    from skater_seasons
    left join skater_team_games as teams on teams.skater_season_key = skater_seasons.skater_season_key
    where skater_seasons.games_played > coalesce(teams.team_games, 0)

),

skater_goals_add_up as (

    -- In a finished season, skater goals plus goalie goals equal the goals in the final scores, minus one per
    -- shootout game: the extra goal a shootout adds to the final score is credited to no player.
    select
        'skater_goals_add_up' as check_name,
        scored.season,
        null::bigint as game_id,
        'game type ' || scored.game_type || ': skater ' || coalesce(skaters.goals, 0) || ' + goalie '
            || coalesce(goalies.goals, 0) || ' goals, final scores ' || scored.goals || ' minus '
            || scored.shootouts || ' shootouts' as detail,
        null::integer as team_id
    from (
        select season, game_type, sum(home_score + away_score) as goals,
               count(*) filter (where last_period_type = 'SO') as shootouts
        from games
        where game_type in (2, 3) and is_final
        group by season, game_type
    ) as scored
    inner join (
        select season, game_type, sum(goals) as goals
        from skater_seasons
        group by season, game_type
    ) as skaters on skaters.season = scored.season and skaters.game_type = scored.game_type
    left join (
        select season, game_type, sum(goals) as goals
        from {{ ref('fct_goalie_games') }}
        group by season, game_type
    ) as goalies on goalies.season = scored.season and goalies.game_type = scored.game_type
    where scored.season in (select season from finished_seasons)
      and coalesce(skaters.goals, 0) + coalesce(goalies.goals, 0) != scored.goals - scored.shootouts

),

birth_places as (

    select distinct birth_country, coalesce(birth_state_province, '') as birth_state_province, birth_city
    from {{ ref('stg_nhl_records__players') }}
    where birth_city is not null

),

birth_city_spellings as (

    select *, coalesce(state_province, '') as province_key from {{ ref('birth_city_spellings') }}

),

birth_city_spellings_valid as (

    -- Each row of the birth city spellings seed maps one spelling the NHL actually uses to another spelling the NHL
    -- actually uses for the same country and province, once. A row whose spelling disappears from the data fails,
    -- so the seed is kept clean.
    select
        'birth_city_spellings_valid' as check_name,
        null::integer as season,
        null::bigint as game_id,
        problem || ': ' || spellings.country || ' ' || spellings.province_key || ' ' || spellings.recorded_city
            || ' -> ' || spellings.city as detail,
        null::integer as team_id
    from (
        select *,
            case
                when count(*) over (partition by country, province_key, recorded_city) > 1 then 'listed more than once'
                when recorded_city = city then 'maps a spelling to itself'
                when not exists (
                    select 1 from birth_places
                    where birth_places.birth_country = birth_city_spellings.country
                      and birth_places.birth_state_province = birth_city_spellings.province_key
                      and birth_places.birth_city = birth_city_spellings.recorded_city
                ) then 'spelling not used by anyone in the player list'
                when not exists (
                    select 1 from birth_places
                    where birth_places.birth_country = birth_city_spellings.country
                      and birth_places.birth_state_province = birth_city_spellings.province_key
                      and birth_places.birth_city = birth_city_spellings.city
                ) then 'target spelling not used by the NHL'
            end as problem
        from birth_city_spellings
    ) as spellings
    where problem is not null

),

draft_pick_unique as (

    -- Each overall pick number is used once per draft.
    select
        'draft_pick_unique' as check_name,
        any_value(season) as season,
        null::bigint as game_id,
        'draft ' || draft_year || ': overall pick ' || overall_pick || ' listed ' || count(*) || ' times' as detail,
        null::integer as team_id
    from {{ ref('fct_draft_picks') }}
    group by draft_year, overall_pick
    having count(*) > 1

),

playoff_series_score_matches as (

    -- The series score counted from our games equals the NHL's own series score, and a series that needs a set number
    -- of wins was won with exactly that number.
    select
        'playoff_series_score_matches' as check_name,
        season,
        null::bigint as game_id,
        'series ' || playoff_series_key || ': our games ' || coalesce(team_a_wins, 0) || '-' || coalesce(team_b_wins, 0)
            || ', NHL ' || coalesce(nhl_winner_wins, 0) || '-' || coalesce(nhl_loser_wins, 0)
            || ', needs ' || coalesce(games_needed_to_win, 0)
            || case when not has_winner then ', no winner' else '' end as detail,
        team_a_id as team_id
    from {{ ref('fct_playoff_series') }}
    where season in (select season from finished_seasons)
      and (team_a_wins is distinct from nhl_winner_wins
           or team_b_wins is distinct from nhl_loser_wins
           or (games_needed_to_win > 0 and team_a_wins != games_needed_to_win)
           or not has_winner)

),

stanley_cup_winner_matches_final as (

    -- The team named on the season's Stanley Cup winner results is the winner of the season's last playoff series.
    select
        'stanley_cup_winner_matches_final' as check_name,
        coalesce(cup.season, final.season) as season,
        null::bigint as game_id,
        'Stanley Cup winner team ' || coalesce(cup.team_ids, 'none') || ', last series won by '
            || coalesce(final.winner_team_id::varchar, 'none') as detail,
        final.winner_team_id as team_id
    from (
        select season, string_agg(distinct team_id::varchar, ',' order by team_id::varchar) as team_ids
        from {{ ref('fct_award_results') }}
        where trophy_id = 1 and is_winner and team_id is not null
        group by season
    ) as cup
    full outer join (
        select season, winner_team_id from {{ ref('fct_playoff_series') }} where is_final_round
    ) as final on final.season = cup.season
    where coalesce(cup.season, final.season) in (select season from finished_seasons)
      and cup.team_ids is distinct from final.winner_team_id::varchar

),

shootout_results as (

    select
        season,
        team_id,
        sum(goals_for) as goals_for,
        sum(goals_against) as goals_against,
        count(*) filter (where last_period_type = 'SO' and result = 'W') as shootout_wins,
        count(*) filter (where last_period_type = 'SO' and result != 'W') as shootout_losses
    from {{ ref('fct_team_games') }}
    where game_type = 2
    group by season, team_id

),

team_season_goals_match_games as (

    -- The NHL's official goals for and against equal our games' totals, minus one for each shootout won (for) or lost
    -- (against): the official totals leave out the extra goal a shootout win adds to the final score.
    select
        'team_season_goals_match_games' as check_name,
        official.season,
        null::bigint as game_id,
        'official GF-GA ' || official.goals_for || '-' || official.goals_against || ', our games minus shootouts '
            || (ours.goals_for - ours.shootout_wins) || '-' || (ours.goals_against - ours.shootout_losses) as detail,
        official.team_id
    from {{ ref('fct_team_seasons') }} as official
    inner join shootout_results as ours on ours.season = official.season and ours.team_id = official.team_id
    where official.season in (select season from finished_seasons)
      and (official.goals_for != ours.goals_for - ours.shootout_wins
           or official.goals_against != ours.goals_against - ours.shootout_losses)

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
union all
select * from past_games_final
union all
select * from scheduled_game_count
union all
select * from award_player_exists
union all
select * from draft_player_exists
union all
select * from playoff_series_game_exists
union all
select * from playoff_games_in_series
union all
select * from standings_rules_match_season_facts
union all
select * from goalie_games_covered
union all
select * from goalie_decision_matches_result
union all
select * from goalie_totals_match_official
union all
select * from goalie_shutouts_consistent
union all
select * from goalie_saves_add_up
union all
select * from goalie_saves_plus_one_rate
union all
select * from goalie_shots_within_team
union all
select * from standings_match_official
union all
select * from skater_team_resolves
union all
select * from skater_games_within_team
union all
select * from skater_goals_add_up
union all
select * from birth_city_spellings_valid
union all
select * from draft_pick_unique
union all
select * from playoff_series_score_matches
union all
select * from stanley_cup_winner_matches_final
union all
select * from team_season_goals_match_games
