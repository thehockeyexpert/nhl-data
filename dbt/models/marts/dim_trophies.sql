-- Tagged records: rebuilt in the weekly full build and after ingest.records, not nightly (decided 2026-10-17).
{{ config(tags=['records']) }}

-- One row per NHL trophy or award in the NHL records site's list.

select
    trophy_id,
    trophy_name,
    short_name,
    category_id
from {{ ref('stg_nhl_records__trophies') }}
