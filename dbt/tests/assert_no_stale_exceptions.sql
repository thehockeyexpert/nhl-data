-- Every documented exception must still match a real failing row.
-- If the data changes and an exception is no longer needed, this fails so the list gets cleaned up.
select exceptions.*
from {{ ref('check_exceptions') }} as exceptions
where not exists (
    select 1
    from {{ ref('check_failures') }} as failures
    where failures.check_name = exceptions.check_name
      and failures.season = exceptions.season
      and (exceptions.game_id is null or exceptions.game_id = failures.game_id)
)
