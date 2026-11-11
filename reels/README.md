# Reels

One YAML file per Reel. For now a Reel is a **race**: up to three players' running career totals (goals, assists or
points), drawn game by game as a 1080 x 1920 MP4 with no sound (add music in Instagram).

```
uv run python -m instagram.race render reels/<name>.yml   # facts re-checked first
uv run python -m instagram.race check reels/<name>.yml    # facts only
```

The video, a cover image (the last frame) and the caption are saved outside the repo, in `posts/<name>/`.
The layout sits in the middle 1080 x 1350 of the frame, so the feed's 4:5 crop shows all of it.

| Key | Required | What it is |
|---|---|---|
| `title` | yes | Up to about 16 characters at 104 px; a title too wide for the frame stops the render |
| `games` | yes | How many career games the race runs (every player must have played that many) |
| `lines` | yes | One to three `{player_id, name}`; the first is the subject, in the accent |
| `caption` | yes | Must include "Data: NHL" |
| `facts` | yes | `claim`, `sql`, `value` for every number on screen, as in `carousels/` |
| `kicker`, `subtitle`, `axis_title` | no | Text above and below the title, and under the x axis |
| `metric` | no | `goals`, `assists` or `points` (default) |
| `accent`, `mode` | no | The subject's team or country; `dark` (default) or `light` |
| `seconds` | no | Length of the race itself (default 15), plus 1 s still at the start and 3 s held at the end |
