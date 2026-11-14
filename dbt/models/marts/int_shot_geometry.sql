-- One row per shot attempt (goal, shot on goal, missed or blocked shot) from 2009-10, regular season and playoffs,
-- shootouts left out: where it was taken relative to the net it attacked, its strength from the shooter's side,
-- and whether it was a rebound. The first step of our expected-goals model (docs/definitions.md, D33); fct_shot_xg
-- uses it. An intermediate table: for analysis use fct_shot_xg.
--
-- Normalised coordinates: every shot attacks the net at x = +89, y = 0 (the NHL rink is 200 ft x 85 ft, centre ice
-- at 0, goal lines at x = +-89). Which net a shot attacked comes from:
--   1. home_team_defending_side when the NHL gives it (2019-20 on): the home team attacks x > 0 when it defends the
--      left side (checked 2026-11-13 on every offensive-zone shot of 2025-26).
--   2. otherwise a vote over the whole game: offensive-zone shots point at the attacked net, defensive-zone shots
--      away from it, and teams change ends every period. Checked 2026-11-13 against rule 1 on 2019-20 to 2026-27: it
--      gives the same net in 99.9% of periods, overtime included. Observed in 2010-11 to 2014-15: regular-season
--      overtime was played at the same ends as the 3rd period (the vote of the overtime's own shots agrees with that
--      in most games, and with switching ends in only 319 of 1,312), so it uses the 3rd period's ends.
-- Blocked shots are kept for the rebound test; their coordinates are where the block happened.
--
-- Strength from the shooter's side, from situation_code (4 digits: away goalie in net 1/0, away skaters, home
-- skaters, home goalie in net 1/0): empty_net when the defending goalie is out; otherwise skaters compared, with an
-- extra attacker for a pulled goalie not counted (the NHL counts 6-on-5 with a pulled goalie as even strength):
-- even, power_play or short_handed. unknown where situation_code is missing (22 unblocked shots).
--
-- Rebound: an unblocked shot whose previous attempt in the same game and period, by either team, was by the same
-- team at most 3 seconds earlier (D33).
--
-- Incremental: each night only games with new rows in fct_shots are rebuilt (every row of a game depends only on that
-- game), replacing all of that game's earlier rows. A change to this file needs one
-- `dbt build --select int_shot_geometry+ --full-refresh`, which is safe: fct_shots keeps every season.

{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert',
          tags=['advanced', 'xg']) }}

with shots as (

    select
        *,
        -- +1 when this shot's zone says the shooter attacked the x > 0 net, -1 for x < 0, 0 when it cannot say.
        case when zone_code = 'O' then sign(x_coord) when zone_code = 'D' then -sign(x_coord) else 0 end
            as attacks_positive_vote
    from {{ ref('fct_shots') }}
    where season >= 20092010  -- shot maps from 2009-10; the xG model uses 2010-11 on
      and game_type in (2, 3)
      and not is_shootout
      and event_type in ('goal', 'shot-on-goal', 'missed-shot', 'blocked-shot')
    {% if is_incremental() %}
      and game_id in (
          select game_id from {{ ref('fct_shots') }} where loaded_at > (select max(loaded_at) from {{ this }})
      )
    {% endif %}

),

-- Ends: is the period one where the home team plays at the same ends as in period 1?
ends as (

    select
        *,
        case
            when game_type = 2 and season < 20152016 and period_number >= 4 then 3  -- overtime kept period 3's ends
            else period_number
        end % 2 = 1 as same_ends_as_period_1
    from shots

),

-- The game vote: does the home team attack x > 0 in period 1?
game_vote as (

    select
        game_id,
        sum(
            attacks_positive_vote
            * case when is_home_shooter then 1 else -1 end
            * case when same_ends_as_period_1 then 1 else -1 end
        ) as home_attacks_positive_in_period_1
    from ends
    group by game_id

),

oriented as (

    select
        ends.*,
        case
            when ends.home_team_defending_side is not null then 'nhl_side'
            when game_vote.home_attacks_positive_in_period_1 <> 0 then 'game_vote'
        end as direction_source,
        -- Does the shooter attack the x > 0 net?
        case
            when ends.home_team_defending_side is not null
                then ends.is_home_shooter = (ends.home_team_defending_side = 'left')
            when game_vote.home_attacks_positive_in_period_1 <> 0
                then ends.is_home_shooter
                    = ((game_vote.home_attacks_positive_in_period_1 > 0) = ends.same_ends_as_period_1)
        end as shooter_attacks_positive
    from ends
    left join game_vote on game_vote.game_id = ends.game_id

),

normalised as (

    select
        *,
        case when shooter_attacks_positive then x_coord else -x_coord end as x_norm,
        case when shooter_attacks_positive then y_coord else -y_coord end as y_norm,
        -- situation_code digits from the shooter's side
        case when is_home_shooter then substr(situation_code, 4, 1) else substr(situation_code, 1, 1) end = '1'
            as own_goalie_in,
        case when is_home_shooter then substr(situation_code, 1, 1) else substr(situation_code, 4, 1) end = '1'
            as opponent_goalie_in,
        try_cast(case when is_home_shooter then substr(situation_code, 3, 1) else substr(situation_code, 2, 1) end
            as integer) as own_skaters,
        try_cast(case when is_home_shooter then substr(situation_code, 2, 1) else substr(situation_code, 3, 1) end
            as integer) as opponent_skaters
    from oriented

),

measured as (

    select
        *,
        sqrt(power(89 - x_norm, 2) + power(y_norm, 2)) as distance_ft,
        -- 0 = straight in front, 90 = level with the goal line, above 90 = from behind the net.
        degrees(atan2(abs(y_norm), 89 - x_norm)) as angle_deg,
        case
            when situation_code is null or length(situation_code) <> 4 then 'unknown'
            when not opponent_goalie_in then 'empty_net'
            when own_skaters - case when own_goalie_in then 0 else 1 end = opponent_skaters then 'even'
            when own_skaters - case when own_goalie_in then 0 else 1 end > opponent_skaters then 'power_play'
            else 'short_handed'
        end as strength,
        lag(shooting_team_id) over game_period as previous_shooting_team_id,
        time_in_period_seconds - lag(time_in_period_seconds) over game_period as seconds_since_previous_attempt
    from normalised
    window game_period as (partition by game_id, period_number order by sort_order)

)

select
    shot_key,
    game_id,
    season,
    game_type,
    game_date,
    event_id,
    sort_order,
    period_number,
    time_in_period_seconds,
    event_type,
    event_type <> 'blocked-shot' as is_unblocked,
    is_goal,
    is_on_goal,
    shooting_team_id,
    defending_team_id,
    is_home_shooter,
    shooting_player_id,
    goalie_in_net_id,
    shot_type,
    situation_code,
    strength,
    x_coord,
    y_coord,
    direction_source,
    x_norm,
    y_norm,
    distance_ft,
    angle_deg,
    seconds_since_previous_attempt,
    coalesce(
        event_type <> 'blocked-shot'
            and previous_shooting_team_id = shooting_team_id
            and seconds_since_previous_attempt between 0 and 3,
        false
    ) as is_rebound,
    coalesce(shot_type, 'unknown') as shot_type_or_unknown,
    -- The xG model's eras (D33, decided by the owner 2026-11-13): rebounds are recorded differently from about 2022-23
    -- (docs/data_coverage.md), so each era has its own goal rates.
    case when season >= 20222023 then '2022-23 on' when season >= 20102011 then '2010-11 to 2021-22' end as xg_era,
    -- Bands for the goal-rate lookup (dim_xg_goal_rates). 'unknown' where there are no coordinates.
    case
        when distance_ft is null then 'unknown'
        when distance_ft < 5 then '00-05'
        when distance_ft < 10 then '05-10'
        when distance_ft < 15 then '10-15'
        when distance_ft < 20 then '15-20'
        when distance_ft < 25 then '20-25'
        when distance_ft < 30 then '25-30'
        when distance_ft < 40 then '30-40'
        when distance_ft < 50 then '40-50'
        when distance_ft < 60 then '50-60'
        else '60+'
    end as distance_band,
    case
        when angle_deg is null then 'unknown'
        when angle_deg < 15 then '00-15'
        when angle_deg < 30 then '15-30'
        when angle_deg < 45 then '30-45'
        when angle_deg < 60 then '45-60'
        when angle_deg <= 90 then '60-90'
        else 'behind'
    end as angle_band,
    loaded_at
from measured
