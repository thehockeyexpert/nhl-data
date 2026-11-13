# Instagram story carousels

Every post is a story carousel of 3 to 20 slides, in the order the story needs: the "Story carousels" section of
`style/style_guide.md` for the design, and `style/story_playbook.md` for how to write it (usually 6 to 10 slides).
Each `.yml` file here is one carousel: the words, the caption and the facts behind them. Text only: no data files,
no images (a photo is named here and kept in the git-ignored `assets/nhl/photos/`; NHL headshots and logos are
downloaded into the git-ignored `assets/nhl/`).

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
3. **Claude drafts the YAML:** the slides the playbook's arc calls for, and a caption that credits "Data: NHL."
   ("Data, logos and headshots: NHL." when an NHL logo or headshot is used). Every number comes from a query Claude
   ran, saved under `facts:` with dates pinned. A slide without honest data is cut.
4. **You edit the words.** If you change a number, change or add the fact that backs it.
5. **Render.** The facts are re-checked first: if the data no longer gives the same answer, nothing is drawn.
   Commit only the YAML, after reviewing the diff.

## Slide types

A carousel has 3 to 20 slides. Any type can come anywhere and repeat; mixed mode makes each type light or dark as
shown. Which slide to use for which question is in `style/story_playbook.md` ("Picking the chart").

| Slide | Fields | Notes |
|---|---|---|
| `hook` (dark) | `kicker`, `headline` (three lines; the last is in the accent); optional `image` | Full-bleed dark, faint half-rink behind the words, or a photo or headshot |
| `reveal` (dark) | `number`, `label` (two lines), `name`, `subtitle`, `stats` (up to four `{value, label}`); optional `image` (a headshot) | The hero number in the accent; with a headshot, at most two stats |
| `comparison` (light) | `top` and `bottom`, each `{kicker, number, line}`, optional `logo` (team code) | Top panel: the subject, in the accent. Bottom: the comparison, in ink |
| `trend` (light) | `title`, `subtitle`, `games`, `axis_title`, `lines` (`{player_id, season, name}`; the first is the subject) | Running points totals, drawn from MotherDuck at render time; labels at the line ends |
| `turning_point` (light) | `title`, `subtitle`, `stats_title`, `stats` (up to three `{value, label: [two lines], accent}`), `rink` | `rink: illustration` draws arrows labelled "ILLUSTRATION, NOT TRACKED PASSES"; `rink: none` leaves it out |
| `conclusion` (dark) | `kicker`, `headline` (two lines; the second in the accent), `context` (up to two lines), `question`, `call` | `call` defaults to "Tell us in the comments." |
| `statement` (dark) | `headline` (1 to 3 lines; the last in the accent); optional `kicker` (muted) | One big sentence: the take or the verdict. Shrinks only to fit the margins |
| `question` (dark) | `question` (1 to 3 lines); optional `call` | The conclusion's question on its own, when the verdict is a separate `statement`. `call` defaults to "Tell us in the comments." |
| `guess` (dark) | `question` (1 or 2 lines), `options` (3 or 4); optional `kicker` (in the accent) | A quiz: options as large rows A to D, no answer shown. The next slide reveals it |
| `leaderboard` (light) | `title`, `subtitle`, `rows` (up to five `{rank, name, team, value, subject}`, exactly one `subject: true`); optional `gap`, `bars`, `logos` | The Studio Edition leaderboard; only the subject's row is in the accent. `gap: true`: four rows, the top three then the subject at its real rank (`rank: T14`). `bars: false` for rates or negative values. `logos: true`: team logos after the names |
| `distribution` (light) | `title`, `subtitle`, `sql` (one row per player or team: `id, name, value`; dates pinned), `subject` (an id); optional `axis_title`, `average_line`, `decimals`, `drop_leading_zero` | A dot strip of every qualifying player or team, drawn from MotherDuck at render time; the subject in the accent and labelled. `average_line: true` (mean of the dots) or `{value, label}` (a league figure backed by a fact) |
| `shot_map` (light) | `title`, `subtitle`, `player_id` or `team_id`, `from`, `to` (dates, 2009-10 on); optional `game_types` (default `[2]`), `count_line` | Real unblocked shot attempts on a half rink, every shot attacking the same net (`marts.int_shot_geometry`); shots in ink, goals in the accent. Real data, so no illustration label. `count_line: false` leaves out the totals line |

Kickers and labels are written exactly as they should appear (uppercase in the file, so "McDAVID" keeps its small c).
Leaderboard rows are written in the file and backed by facts; `trend`, `distribution` and `shot_map` draw their
data at render time from MotherDuck, so their queries must pin dates.

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
- Facts and figures first: the typography, the charts and the rink are the visuals. Photos, headshots and logos are
  optional extras (below), credited in the caption.

## Example

```yaml
accent: EDM
mode: mixed
through: 2026-11-09
slides:
  - type: hook
    kicker: "CONNOR McDAVID · 2026-27"
    headline: ["Nobody has", "started like this", "in 30 years."]
  - type: guess
    kicker: "GUESS FIRST"
    question: ["How many points", "in 19 games?"]
    options: [36, 42, 48, 54]
  - type: reveal
    number: 48
    label: ["POINTS IN", "19 GAMES"]
    name: "Connor McDavid"
  - type: leaderboard
    title: "12 points clear"
    rows:
      - {name: "Connor McDavid", team: EDM, value: 48, subject: true}
      - {name: "Leon Draisaitl", team: EDM, value: 36}
  # ... more proof (trend, distribution, shot_map), the twist, then:
  - type: statement
    headline: ["Nobody is", "close."]
  - type: question
    question: ["Will he reach 150?"]
caption: |
  ... Data: NHL.
facts:
  - claim: "Reveal: 19 games, 48 points"
    sql: select count(*), sum(points) from marts.fct_skater_games where ...
    value: [19, 48]          # one value, a list for one row, or a list of rows
```

## Photos, headshots and logos

Allowed since 2026-11-11 (`docs/decisions.md`; `style/style_guide.md`, "NHL logos and headshots").

- **NHL headshot** on the hook or the reveal: `image: {type: headshot, player_id: 8477492}`. The current season's
  photo from the NHL API, bottom right, 480 px tall (the originals are 336 px, so larger would blur); text stays
  clear of it and the handle sits on a small band.
- **NHL team logos:** `logos: true` on a leaderboard (each row's `team`), or `logo: EDM` on a comparison half. The
  NHL's own SVG for the slide's light or dark mode, never recoloured or stretched.
- Any headshot or logo makes the caption credit **"Data, logos and headshots: NHL."** (checked before rendering).
- **Photos** (one per carousel, on the hook):

```yaml
image: {type: photo, commons: "File:Connor McDavid of the Edmonton Oilers.jpg", layout: panel, side: left, focus: [0.45, 0.45]}
image: {type: photo, file: my-photo.jpg, credit: "Photo: Jane Smith", layout: cutout, side: right}
```

| Key | What it is |
|---|---|
| `commons` | A Wikimedia Commons file title. Downloaded into `assets/nhl/photos/` on the first render, after checking the licence is CC BY, CC BY-SA or public domain; the credit comes from Commons |
| `file` + `credit` | A photo the owner saved in `assets/nhl/photos/`, and its credit for the caption |
| `layout` | `panel` (default): the photo fills a full-height strip, 470 px wide, on one side. `cutout`: the background is removed and the person stands beside the headline, above the handle (needs `--group photos`, below) |
| `side` | `left` (default) or `right`. A panel on the right puts the handle on a small band of the background colour |
| `focus` | Where to centre a panel's crop, as fractions across and down the photo (default `[0.5, 0.4]`) |

The kicker and headline shrink only as much as they must to fit beside the photo. Every photo's credit is added to
`caption.txt` automatically, with the change made ("cropped" or "background removed"), as CC BY and CC BY-SA require.

Finding a photo, and rendering with a cut-out (background removal downloads a free model, about 170 MB, once):

```
uv run python -m instagram.photos search "Connor McDavid"
uv run python -m instagram.photos download "File:Connor McDavid of the Edmonton Oilers.jpg"
uv run --group photos python -m instagram.carousel render carousels/<name>.yml
```
