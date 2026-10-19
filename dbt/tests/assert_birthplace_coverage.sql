-- At least 95% of players with a birth city have coordinates. A warning, not a failure (owner, 2026-10-19).
{{ config(severity='warn') }}
{{ unexcepted_failures('birthplace_coverage') }}
