# Instagram carousels

Each `.yml` file here is one carousel: the words, the chart choices and the facts behind them. Text only: no data
files, no images. The slides are drawn from MotherDuck when you render, following `style/style_guide.md`.

```
uv run python -m instagram.carousel check  carousels/mcdavid-hot-start.yml   # re-run the facts only
uv run python -m instagram.carousel render carousels/mcdavid-hot-start.yml   # facts, then one PNG per slide
```

Slides are saved outside the repo as `posts/<file name>/01.png`, `02.png` and so on, in `NHL_POSTS_DIR` or
`~/nhl-data-files/posts`. Rendering again replaces them.

## The workflow

1. **You describe a story** to Claude Code ("McDavid's start to the season", "where Canada's players come from").
2. **Claude drafts the file.** Every number in the draft comes from a query Claude ran against MotherDuck, and each
   query is written under `facts:` with its answer. No number comes from memory or from another site.
3. **You edit the words.** Change titles, subtitles and bodies as you like. If you change a number, change or add
   the fact that backs it.
4. **Render.** The facts are re-checked first: if the data no longer gives the same answer (a correction from the
   NHL, a game added), nothing is drawn and the command shows what changed.

## The file

```yaml
accent: EDM                  # a team or country code from style/style.json; the subject's colour
mode: dark-light             # light, dark, or alternating: dark-light (slide 1 dark) or light-dark
label: "2026-27 · Connor McDavid"   # the small uppercase line at the top of every slide
through: 2026-11-09          # optional: charts count games up to this date, so they match the text
handle: "@topshelfstats"     # optional: defaults to --handle or NHL_POST_HANDLE
slides:
  - type: title              # big title in the middle, subtitle (or body) under it
    title: 48 points in 19 games
    subtitle: Connor McDavid's start to the 2026-27 season
  - type: chart              # title, optional subtitle, then a chart from the library
    chart: points_leaders
    season: 20262027
    top: 5
    title: 12 points clear
  - type: text               # title, optional subtitle, then body: paragraphs, and "- " for bullets
    title: Tied for sixth, all time
    body: |
      - Mario Lemieux, 57 (1988-89)
  - type: end                # like the title slide, for the last slide
    title: Can he keep it going?
    body: Regular season only, games through 9 November 2026.
facts:
  - claim: McDavid has 48 points in 19 games
    sql: select count(*), sum(points) from marts.fct_skater_games where ...
    value: [19, 48]          # one value, a list for one row, or a list of rows
```

Any slide can set its own `label`, and its own `mode` (light or dark), which wins over the carousel's. Every slide gets the label, the slide counter (1/6) and the footer
("Data: NHL" and the handle).

## The chart library (`instagram/charts.py`)

| Chart | What it shows | Settings |
|---|---|---|
| `points_leaders` | A season's regular-season points leaders, goalies included | `season`, `top` (5), `highlight` (a player_id; the leader by default) |
| `points_histogram` | One player's games by points scored: 0, 1, 2, 3, 4, 5+ | `player_id`, `season` (career if left out), `highlight` (a bucket 0-5; the tallest by default) |
| `goals_per_game` | Goals per game, season by season, as a line | `player_id` (the league if left out), `from_season`, `to_season` |
| `birthplaces_donut` | Players by birth country | `season` (every NHL player if left out), `top` (5), `highlight` (a country code; the accent if it is a country) |

One thing per chart gets the accent; everything else is ink (the style guide's accent rule).

## Rules for drafts

- Every number on a slide is backed by a fact whose query Claude ran; dates in queries are pinned (`game_date <=
  '2026-11-09'`) so the facts stay true while a season goes on.
- Follow `docs/motherduck_guide.md`: regular season unless the story says otherwise, players by `player_id`, the
  guide's minimums for rates (and say which one).
- Facts and figures only: no logos, photos or video. Birthplace maps credit GeoNames.
- The `value` of a fact is a handful of figures for one post, never a table extract.
