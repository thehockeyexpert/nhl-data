-- The lookup table of our expected-goals model (docs/definitions.md, D33): the share of unblocked shots that became
-- goals, by distance band, angle band, shot type, rebound and strength, from every unblocked shot of 2010-11 to the
-- last finished season (checks.season_status), regular season and playoffs. Bands are set in int_shot_geometry.
-- Two eras, each with its own rates at every level (owner's decision 2026-11-13): 2010-11 to 2021-22, and 2022-23 on,
-- when rebounds start being recorded differently. A shot uses the rates of its own season's era.
-- Six levels, from finest to coarsest; a shot takes the rate of the finest level whose cell holds at least 200 shots
-- (fct_shot_xg). A column left empty means "any" at that level.
--   1 distance, angle, shot type, rebound, strength
--   2 distance, angle, rebound, strength
--   3 distance, rebound, strength
--   4 distance, strength
--   5 strength
--   6 all shots of the era

{{ config(materialized='table', tags=['advanced', 'xg']) }}

with fit_shots as (

    select *
    from {{ ref('int_shot_geometry') }}
    where is_unblocked
      and season >= 20102011
      and season <= (select max(season) from {{ ref('season_status') }} where is_finished)

),

cells as (

    select
        grouping(distance_band, angle_band, shot_type_or_unknown, is_rebound, strength) as grouping_bits,
        xg_era,
        distance_band,
        angle_band,
        shot_type_or_unknown as shot_type,
        is_rebound,
        strength,
        count(*) as shots,
        count(*) filter (where is_goal) as goals,
        min(season) as first_season,
        max(season) as last_season
    from fit_shots
    group by grouping sets (
        (xg_era, distance_band, angle_band, shot_type_or_unknown, is_rebound, strength),
        (xg_era, distance_band, angle_band, is_rebound, strength),
        (xg_era, distance_band, is_rebound, strength),
        (xg_era, distance_band, strength),
        (xg_era, strength),
        (xg_era)
    )

)

select
    -- grouping() sets a bit for each column left out: 0 = level 1, 4 = level 2, 12 = level 3, 14 = level 4, 30 = level
    -- 5, 31 = level 6.
    case grouping_bits when 0 then 1 when 4 then 2 when 12 then 3 when 14 then 4 when 30 then 5 when 31 then 6 end
        as level,
    xg_era,
    concat_ws('|', xg_era, level, coalesce(distance_band, '*'), coalesce(angle_band, '*'), coalesce(shot_type, '*'),
        coalesce(is_rebound::varchar, '*'), coalesce(strength, '*')) as cell_key,
    distance_band,
    angle_band,
    shot_type,
    is_rebound,
    strength,
    shots,
    goals,
    goals / shots as goal_rate,
    shots >= 200 or level = 6 as is_usable,
    first_season,
    last_season
from cells
