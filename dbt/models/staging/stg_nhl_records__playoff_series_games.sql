-- One row per playoff game from the NHL records site, with the series it belongs to
-- and the series score after that game.

with latest_response as (

    select *
    from {{ source('raw', 'nhl_records__playoff_series') }}
    qualify row_number() over (partition by source_url order by loaded_at desc) = 1

),

series_games as (

    select unnest(json_extract(payload, '$.data[*]')) as series_game
    from latest_response

)

select
    (series_game ->> 'gameId')::bigint as game_id,
    (series_game ->> 'id')::bigint as series_game_row_id,
    (series_game ->> 'seasonId')::integer as season,
    (series_game ->> 'playoffRound')::integer as playoff_round,
    series_game ->> 'playoffSeriesLetter' as series_letter,
    series_game ->> 'seriesTitle' as series_title,
    (series_game ->> 'gameNumber')::integer as game_number,
    (series_game ->> 'gamesNeededToWin')::integer as games_needed_to_win,
    (series_game ->> 'lengthOfSeries')::integer as length_of_series,
    (series_game ->> 'topSeedWins')::integer as top_seed_wins,
    (series_game ->> 'bottomSeedWins')::integer as bottom_seed_wins
from series_games
