{#- Birthplace helpers shared by dim_players and dim_birthplaces. -#}

{% macro birthplace_key(country, state_province, city) -%}
    {#- Readable key, for example CAN|ON|Toronto or SWE||Gävle. Empty when there is no city. -#}
    case when {{ city }} is not null then {{ country }} || '|' || coalesce({{ state_province }}, '') || '|' || {{ city }} end
{%- endmacro %}

{% macro normalize_place_name(name) -%}
    {#- For matching only: no accents, lower case, punctuation as spaces, and St / Ste read as Saint / Sainte,
        so "St-Jean" and "Saint-Jean" or "Gävle" and "Gavle" compare equal. -#}
    trim(regexp_replace(regexp_replace(regexp_replace(regexp_replace(
        lower(strip_accents({{ name }})), '[^a-z0-9]+', ' ', 'g'),
        '\bste\b', 'sainte', 'g'), '\bst\b', 'saint', 'g'), '\s+', ' ', 'g'))
{%- endmacro %}

{% macro geonames_places(raw_table) -%}
    {#- Split a GeoNames place file (one raw row per line, tab-separated, columns listed in the GeoNames readme). -#}
    with fields as (

        select string_split(line, chr(9)) as field
        from {{ source('raw', raw_table) }}

    )

    select
        field[1]::bigint as geonames_id,
        field[2] as place_name,
        field[3] as ascii_name,
        case when field[4] <> '' then string_split(field[4], ',') else [] end as alternate_names,
        field[5]::double as latitude,
        field[6]::double as longitude,
        nullif(field[7], '') as feature_class,
        nullif(field[8], '') as feature_code,
        field[9] as country_code,
        nullif(field[11], '') as admin1_code,
        coalesce(nullif(field[15], '')::bigint, 0) as population
    from fields
{%- endmacro %}
