-- One row per country in GeoNames' country list, with its two- and three-letter ISO codes. GeoNames, CC BY 4.0.
{{ config(tags=['geonames']) }}

with fields as (

    select string_split(line, chr(9)) as field
    from {{ source('raw', 'geonames__country_info') }}
    where not starts_with(line, '#')   -- the file opens with comment lines

)

select
    field[1] as country_code,
    field[2] as country_iso3,
    field[5] as country_name
from fields
