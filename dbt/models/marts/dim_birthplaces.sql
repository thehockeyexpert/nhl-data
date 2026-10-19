-- Rebuilt weekly (Sunday full build) and after each GeoNames refresh, not nightly (decided 2026-10-19).
{{ config(tags=['geonames']) }}

-- One row per distinct birthplace in dim_players (country, state or province, standard city), with coordinates from
-- GeoNames (CC BY 4.0). Matching, first that succeeds:
--   manual             a row in seeds/birthplace_manual_fixes.csv, each with its source
--   exact              the place's name, in the right country (and province or state for CAN and USA)
--   alternate_name     one of GeoNames' alternate names for the place, same rules
--   admin_area         a Canadian administrative area of that name, such as a former municipality (Scarborough)
--   successor_country  the name in a country listed in seeds/birthplace_successor_countries.csv (Minsk under RUS)
--   unmatched          no coordinates
-- Names are compared without accents, case or punctuation. Among several places, the largest population wins.

with birthplaces as (

    select distinct
        birthplace_key,
        birth_city_standard as city,
        birth_state_province as state_province,
        birth_country as country
    from {{ ref('dim_players') }}
    where birthplace_key is not null

),

wanted as (

    -- The GeoNames province or state code to require: Canada through the seed; US states are already GeoNames codes.
    select
        birthplaces.*,
        {{ normalize_place_name('birthplaces.city') }} as city_name,
        case
            when birthplaces.country = 'CAN' then provinces.geonames_admin1_code
            when birthplaces.country = 'USA' then birthplaces.state_province
        end as admin1_code
    from birthplaces
    left join {{ ref('canada_province_codes') }} as provinces
        on birthplaces.country = 'CAN' and provinces.province_code = birthplaces.state_province

),

countries as (

    select country_code, country_iso3 from {{ ref('stg_geonames__country_info') }}

),

all_places as (

    select * from {{ ref('stg_geonames__cities500') }}
    union all
    select * from {{ ref('stg_geonames__ca') }}

),

places as (

    -- The Canada file repeats its cities500 rows; keep one copy of each place.
    select all_places.*, countries.country_iso3
    from all_places
    inner join countries on countries.country_code = all_places.country_code
    where all_places.feature_class in ('P', 'A')   -- populated places, and administrative areas
    qualify row_number() over (partition by all_places.geonames_id order by all_places.population desc) = 1

),

features as (

    -- Every GeoNames feature, of any type, for the places named in manual fixes.
    select *
    from all_places
    qualify row_number() over (partition by geonames_id order by population desc) = 1

),

place_names as (

    select geonames_id, country_iso3, admin1_code, population, feature_class, 'name' as name_type,
           {{ normalize_place_name('place_name') }} as name
    from places
    union
    select geonames_id, country_iso3, admin1_code, population, feature_class, 'name',
           {{ normalize_place_name('ascii_name') }}
    from places
    union
    select geonames_id, country_iso3, admin1_code, population, feature_class, 'alternate_name',
           {{ normalize_place_name('alternate_name') }}
    from places, unnest(places.alternate_names) as names(alternate_name)

),

candidates as (

    select
        wanted.birthplace_key,
        place_names.geonames_id,
        case
            when place_names.feature_class = 'A' then 'admin_area'
            when place_names.name_type = 'name' then 'exact'
            else 'alternate_name'
        end as match_method,
        case
            when place_names.feature_class = 'A' then 3
            when place_names.name_type = 'name' then 1
            else 2
        end as priority,
        place_names.population
    from wanted
    inner join place_names
        on place_names.country_iso3 = wanted.country
       and place_names.name = wanted.city_name
       and (wanted.admin1_code is null or place_names.admin1_code = wanted.admin1_code)
       -- Administrative areas only in Canada, the one country loaded in full.
       and (place_names.feature_class = 'P' or wanted.country = 'CAN')

    union all

    select
        wanted.birthplace_key,
        place_names.geonames_id,
        'successor_country' as match_method,
        4 as priority,
        place_names.population
    from wanted
    inner join {{ ref('birthplace_successor_countries') }} as successors on successors.recorded_country = wanted.country
    inner join place_names
        on place_names.country_iso3 = successors.country
       and place_names.name = wanted.city_name
       and place_names.feature_class = 'P'

),

best as (

    select *
    from candidates
    qualify row_number() over (partition by birthplace_key order by priority, population desc, geonames_id) = 1

),

manual as (

    select * from {{ ref('birthplace_manual_fixes') }}

)

select
    wanted.birthplace_key,
    wanted.city,
    wanted.state_province,
    wanted.country,
    -- A manual row gives either a GeoNames place or, where GeoNames has none, coordinates from its source.
    case when manual.birthplace_key is not null then coalesce(manual_places.latitude, manual.latitude)
         else matched_places.latitude end as latitude,
    case when manual.birthplace_key is not null then coalesce(manual_places.longitude, manual.longitude)
         else matched_places.longitude end as longitude,
    case
        when manual.birthplace_key is not null then 'manual'
        when best.birthplace_key is not null then best.match_method
        else 'unmatched'
    end as match_method,
    case when manual.birthplace_key is not null then manual.geonames_id else best.geonames_id end as geonames_id,
    case when manual.birthplace_key is not null then manual_places.population else best.population end as population
from wanted
left join manual on manual.birthplace_key = wanted.birthplace_key
left join features as manual_places on manual_places.geonames_id = manual.geonames_id
left join best on best.birthplace_key = wanted.birthplace_key
left join places as matched_places on matched_places.geonames_id = best.geonames_id
