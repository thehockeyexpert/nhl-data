{#
    Turns the NHL's numeric game type into a readable label.
    Only combinations we have verified against the data get a name.
    Everything else is labelled 'unknown type N' until someone has looked at it.

    Verified so far:
      1, 2, 3            preseason, regular season, playoffs
      9 in 20252026      the Olympic men's tournament (national teams, Milan venues, February 2026)
#}
{% macro game_type_label(season, game_type) -%}
    case
        when {{ game_type }} = 1 then 'preseason'
        when {{ game_type }} = 2 then 'regular'
        when {{ game_type }} = 3 then 'playoff'
        when {{ game_type }} = 9 and {{ season }} = 20252026 then 'olympics'
        else 'unknown type ' || {{ game_type }}::varchar
    end
{%- endmacro %}
