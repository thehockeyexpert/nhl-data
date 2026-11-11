# Instagram story carousels

Every post is a six-slide story carousel: the "Story carousels" section of `style/style_guide.md`. Each `.yml` file
here is one carousel: the words, the caption and the facts behind them. Text only: no data files, no images.

```
uv run python -m instagram.carousel check  carousels/mcdavid-hot-start.yml               # re-run the facts only
uv run python -m instagram.carousel render carousels/mcdavid-hot-start.yml               # mixed light and dark
uv run python -m instagram.carousel render carousels/mcdavid-hot-start.yml --mode light  # or --mode dark
```

The slides and `caption.txt` are saved outside the repo in `posts/<file name>/` (`NHL_POSTS_DIR`, or
`~/nhl-data-files/posts`). Rendering again replaces them.

## The workflow (`style/new_post_prompt.md`)

1. **You describe a story:** what's surprising, the subject, the accent, the timeframe.
2. **Claude tests it against MotherDuck.** If the story doesn't hold up, Claude says so before drafting and suggests a
   better angle.
3. **Claude drafts the YAML:** the six slides and a caption that credits "Data: NHL". Every number comes from a query
   Claude ran, saved under `facts:` with dates pinned. If a slide has no honest data, Claude proposes skipping it.
4. **You edit the words.** If you change a number, change or add the fact that backs it.
5. **Render.** The facts are re-checked first: if the data no longer gives the same answer, nothing is drawn.
   Commit only the YAML, after reviewing the diff.

## The six slides, always in this order

| Slide | Fields | Notes |
|---|---|---|
| `hook` | `kicker`, `headline` (three lines; the last is in the accent) | Full-bleed dark, faint half-rink behind the words |
| `reveal` | `number`, `label` (two lines), `name`, `subtitle`, `stats` (up to four `{value, label}`) | The hero number in the accent |
| `comparison` | `top` and `bottom`, each `{kicker, number, line}` | Top panel: the subject, in the accent. Bottom: the comparison, in ink |
| `trend` | `title`, `subtitle`, `games`, `axis_title`, `lines` (`{player_id, season, name}`; the first is the subject) | Running points totals, drawn from MotherDuck at render time; labels at the line ends |
| `turning_point` | `title`, `subtitle`, `stats_title`, `stats` (up to three `{value, label: [two lines], accent}`), `rink` | `rink: illustration` draws arrows labelled "ILLUSTRATION, NOT TRACKED PASSES"; `rink: none` leaves it out |
| `conclusion` | `kicker`, `headline` (two lines; the second in the accent), `context` (up to two lines), `question`, `call` | `call` defaults to "Tell us in the comments." |

A slide can be left out only when there is no honest data for it; the order never changes. Kickers and labels are
written exactly as they should appear (uppercase in the file, so "McDAVID" keeps its small c).

Every slide carries only the handle at the bottom right: no label, counter, hairline frame or source line. The NHL
credit goes in `caption:` (required, and it must contain "Data: NHL").

## Writing rules

- Every number on a slide is backed by a fact whose query Claude ran; dates are pinned (`game_date <= '2026-11-09'`).
- No claims that aren't in the data: no tactics, linemates or units the data doesn't record.
- As clean as possible: every piece of text adds something new. A label and a sentence never say the same thing, a
  question isn't repeated as a graphic, and a closing line doesn't restate the stats. When in doubt, cut it.
- Follow `docs/motherduck_guide.md`: regular season unless the story says otherwise, players by `player_id`, the
  guide's minimums for rates. Check the season's schedule length in `dim_seasons` before any pace (2026-27 has 84
  games per team).
- Facts and figures only: no logos or photos. The rink drawing and the typography are the visuals.

## Example

```yaml
accent: EDM
mode: mixed
through: 2026-11-09
slides:
  - type: hook
    kicker: "CONNOR McDAVID · 2026-27"
    headline: ["Nobody has", "started like this", "in 30 years."]
  # ... reveal, comparison, trend, turning_point, conclusion
caption: |
  ... Data: NHL.
facts:
  - claim: "Reveal: 19 games, 48 points"
    sql: select count(*), sum(points) from marts.fct_skater_games where ...
    value: [19, 48]          # one value, a list for one row, or a list of rows
```
