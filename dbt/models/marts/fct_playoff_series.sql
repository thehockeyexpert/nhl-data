-- Tagged records: rebuilt in the weekly full build and after ingest.records, not nightly (decided 2026-10-17).
{{ config(tags=['records']) }}

-- One row per playoff series, with its two teams and winner taken from our games (fct_games).
-- The NHL's series list gives the round, letter, title, wins needed and the series score after each game, but not the
-- teams, so the teams come from the games (team_a_id, team_b_id). The winner is the team with more wins. With level wins,
-- the team with more goals wins only where games_needed_to_win is 0 (37 early series, 1917-18 to 1935-36, consistent
-- with series decided on total goals); otherwise the series has no winner, as in the 1919 Final stopped by the flu
-- epidemic. Series against non-NHL teams have a non-NHL team (dim_teams.is_nhl_team).

with series_games as (

    -- NHL playoff games only (game type 3); see bridge_playoff_series_games for the World Cup games left out.
    select * from {{ ref('stg_nhl_records__playoff_series_games') }}
    where game_id // 10000 % 100 = 3

),

series as (

    select
        season || '-' || playoff_round || '-' || series_letter as playoff_series_key,
        season,
        playoff_round,
        series_letter,
        any_value(series_title) as series_title,
        max(games_needed_to_win) as games_needed_to_win,
        max(length_of_series) as length_of_series,
        -- The NHL's series score after the last game.
        greatest(arg_max(top_seed_wins, game_number), arg_max(bottom_seed_wins, game_number)) as nhl_winner_wins,
        least(arg_max(top_seed_wins, game_number), arg_max(bottom_seed_wins, game_number)) as nhl_loser_wins
    from series_games
    group by all

),

team_games as (

    -- Both teams' side of every finished game in a series.
    select
        bridge.playoff_series_key,
        sides.team_id,
        sides.goals_for,
        sides.goals_against
    from {{ ref('bridge_playoff_series_games') }} as bridge
    inner join {{ ref('fct_games') }} as games on games.game_id = bridge.game_id
    cross join lateral (
        select games.home_team_id as team_id, games.home_score as goals_for, games.away_score as goals_against
        union all
        select games.away_team_id, games.away_score, games.home_score
    ) as sides
    where games.is_final

),

team_totals as (

    select
        playoff_series_key,
        team_id,
        count(*) as games,
        count(*) filter (where goals_for > goals_against) as wins,
        count(*) filter (where goals_for = goals_against) as ties,
        sum(goals_for) as goals_for
    from team_games
    group by all

),

ranked as (

    select
        *,
        row_number() over (partition by playoff_series_key order by wins desc, goals_for desc, team_id) as rank_in_series,
        count(*) over (partition by playoff_series_key) as teams
    from team_totals

),

joined as (

    select
        series.*,
        first.team_id as team_a_id,
        second.team_id as team_b_id,
        first.games as games_played,
        first.wins as team_a_wins,
        second.wins as team_b_wins,
        first.ties as ties,
        first.goals_for as team_a_goals,
        second.goals_for as team_b_goals,
        -- The leading team wins unless wins are level in a series that needs a set number of wins, or wins and goals
        -- are both level.
        not (first.wins = second.wins and (series.games_needed_to_win > 0 or first.goals_for = second.goals_for))
            as has_winner
    from series
    left join ranked as first on first.playoff_series_key = series.playoff_series_key and first.rank_in_series = 1
    left join ranked as second on second.playoff_series_key = series.playoff_series_key and second.rank_in_series = 2

)

select
    playoff_series_key,
    season,
    playoff_round,
    series_letter,
    series_title,
    games_needed_to_win,
    length_of_series,
    team_a_id,
    team_b_id,
    case when has_winner then team_a_id end as winner_team_id,
    case when has_winner then team_b_id end as loser_team_id,
    has_winner,
    games_played,
    team_a_wins,
    team_b_wins,
    ties,
    team_a_goals,
    team_b_goals,
    nhl_winner_wins,
    nhl_loser_wins,
    playoff_round = max(playoff_round) over (partition by season) as is_final_round
from joined
