-- One row per unblocked shot attempt (goal, shot on goal, missed shot) from 2010-11, regular season and playoffs,
-- shootouts left out, with its expected-goals value (xG): the historical goal rate of shots like it, from
-- dim_xg_goal_rates (docs/definitions.md, D33). Blocked attempts count as 0 xG and are not listed.
-- A shot takes the rate of the finest lookup level whose cell holds at least 200 shots: level 1 (distance, angle,
-- shot type, rebound, strength) down to level 6 (all shots). xg_level says which.
-- The rates come from 2010-11 to the last finished season, so the season in progress is scored with them too. Each
-- shot uses the rates of its season's era (xg_era: 2010-11 to 2021-22, or 2022-23 on; owner's decision 2026-11-13).
--
-- Incremental: each night only games with new rows in int_shot_geometry are scored. Every shot is scored again when
-- the goal rates change, which is normally once a year, when a season finishes and joins the fit: xg_rates_version is
-- a fingerprint of every usable rate, and a row scored with other rates than today's makes the whole table rebuild.

{{ config(materialized='incremental', unique_key='game_id', incremental_strategy='delete+insert',
          tags=['advanced', 'xg']) }}

with rates as (

    select * from {{ ref('dim_xg_goal_rates') }}
    where is_usable

),

rates_version as (

    select md5(string_agg(cell_key || '=' || goal_rate::varchar, ',' order by cell_key)) as xg_rates_version
    from rates

),

shots as (

    select * from {{ ref('int_shot_geometry') }}
    where is_unblocked and season >= 20102011
    {% if is_incremental() %}
      and (
          -- Rates changed since the last build (a season finished): score every shot again.
          exists (
              select 1 from {{ this }}
              where xg_rates_version is distinct from (select xg_rates_version from rates_version)
          )
          -- Otherwise only games with new rows.
          or game_id in (
              select game_id from {{ ref('int_shot_geometry') }}
              where loaded_at > (select max(loaded_at) from {{ this }})
          )
      )
    {% endif %}

),

matched as (

    select
        shots.*,
        rates.goal_rate as xg,
        rates.level as xg_level,
        rates.cell_key as xg_cell_key
    from shots
    inner join rates
        on rates.xg_era = shots.xg_era
       and (rates.distance_band is null or rates.distance_band = shots.distance_band)
       and (rates.angle_band is null or rates.angle_band = shots.angle_band)
       and (rates.shot_type is null or rates.shot_type = shots.shot_type_or_unknown)
       and (rates.is_rebound is null or rates.is_rebound = shots.is_rebound)
       and (rates.strength is null or rates.strength = shots.strength)
    -- Each shot matches one cell per level; keep the finest usable one.
    qualify row_number() over (partition by shots.shot_key order by rates.level) = 1

)

select
    shot_key,
    game_id,
    season,
    game_type,
    game_date,
    period_number,
    time_in_period_seconds,
    event_type,
    is_goal,
    shooting_team_id,
    defending_team_id,
    is_home_shooter,
    shooting_player_id,
    goalie_in_net_id,
    shot_type,
    situation_code,
    strength,
    situation_code = '1551' as is_5v5,
    x_norm,
    y_norm,
    distance_ft,
    angle_deg,
    is_rebound,
    distance_band,
    angle_band,
    xg_era,
    xg,
    xg_level,
    xg_cell_key,
    (select xg_rates_version from rates_version) as xg_rates_version,
    loaded_at
from matched
