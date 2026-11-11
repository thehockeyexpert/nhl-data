"""Render a race Reel: running career totals drawn game by game as a 1080 x 1920 MP4.

A race is a YAML file in reels/ (see reels/README.md). Its facts are re-checked against MotherDuck before anything is
drawn, as for carousels. The video is saved outside the repo, in posts/<name>/race.mp4, with a cover image (the last
frame) and the caption. It has no sound: music is added in Instagram.

    uv run python -m instagram.race render reels/<name>.yml
    uv run python -m instagram.race check reels/<name>.yml
"""

import argparse
import math
import os
from pathlib import Path
from types import SimpleNamespace

import yaml
from matplotlib import animation

from instagram import make_post
from instagram.carousel import (
    METRICS, STYLE, Canvas, CarouselError, W, M, _sized, check_facts, colours, posts_folder, running_totals,
)

H = 1920  # a Reel is 9:16
TOP = (H - 1350) // 2  # the layout sits in the middle 1080 x 1350, the part the feed and profile grid show
FPS = 30
KEYS = {"accent", "mode", "handle", "kicker", "title", "subtitle", "metric", "games", "axis_title", "lines",
        "seconds", "caption", "facts"}
REQUIRED = {"title", "games", "lines", "caption", "facts"}


def validate(data):
    """Every problem with a race file, as a list of sentences (empty when it is valid)."""
    if not isinstance(data, dict):
        return ["the file must be a mapping with title, games, lines, caption and facts"]
    problems = [f"unknown key '{k}'" for k in sorted(set(data) - KEYS)]
    problems += [f"needs '{k}'" for k in sorted(REQUIRED - set(data))]
    if data.get("mode", "dark") not in ("light", "dark"):
        problems.append("mode must be light or dark")
    known = {**STYLE["team_accents"], **STYLE["country_accents"]}
    if data.get("accent") is not None and str(data["accent"]).upper() not in known:
        problems.append(f"unknown accent {data['accent']}")
    if data.get("metric", "points") not in METRICS:
        problems.append(f"metric must be one of {', '.join(METRICS)}")
    lines = data.get("lines")
    if "lines" in data and (not isinstance(lines, list) or not 1 <= len(lines) <= 3
                            or not all(isinstance(x, dict) and {"player_id", "name"} <= set(x) for x in lines)):
        problems.append("lines must be one to three entries, each with player_id and name")
    if "games" in data and (not isinstance(data["games"], int) or data["games"] < 2):
        problems.append("games must be a whole number of at least 2")
    if "Data: NHL" not in str(data.get("caption", "")):
        problems.append('caption must credit the data with "Data: NHL"')
    if "facts" in data and not data["facts"]:
        problems.append("facts: every number on screen needs a query")
    return problems


def load(path):
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    problems = validate(data)
    if problems:
        raise CarouselError(f"{path.name}:\n  " + "\n  ".join(problems))
    data["name"] = path.stem
    return data


def schedule(games, seconds):
    """Games shown in each frame: a one-second still start, the race (eased in and out), then a three-second hold."""
    race = max(2, round(seconds * FPS))
    eased = [0.5 - 0.5 * math.cos(math.pi * i / (race - 1)) for i in range(race)]
    return [0] * FPS + [max(1, round(e * games)) for e in eased] + [games] * (3 * FPS)


class Race:
    """The frame: static title, axes and gridlines drawn once; lines, heads, labels and the game counter updated."""

    def __init__(self, race, series, font, handle):
        self.c = c = colours(race.get("mode", "dark"), race.get("accent"))
        self.cv = cv = Canvas(c, font, height=H)
        self.games = games = race["games"]
        self.series = series
        top_value = max(totals[-1] for _, totals in series)
        step = next(s for s in (5, 10, 20, 50, 100, 200, 250, 500, 1000) if math.ceil(top_value / s) <= 4)
        self.y_max = y_max = step * math.ceil(top_value / step)
        self.x0, self.x1, self.y0, self.y1 = M + 60, W - M - 170, TOP + 1170, TOP + 420

        if race.get("kicker"):
            cv.text(M, TOP + 150, 32, "C700", c.accent, race["kicker"], spacing=4)
        if cv.width(race["title"], 104, "C700") > W - 2 * M:
            raise CarouselError(f"title is too wide for the frame: {race['title']!r}")
        cv.text(M, TOP + 250, 104, "C700", c.ink, race["title"])
        if race.get("subtitle"):
            cv.text(M, TOP + 318, 36, "B500", c.mut, race["subtitle"])
        for value in range(0, y_max + 1, step):
            cv.hairline(self.x0, self.x1 + 150, self.ys(value), alpha_scale=0.8 if value else 2)
            cv.text(self.x0 - 16, self.ys(value) + 9, 26, "C600", c.mut, value, anchor="end")
        x_step = next(s for s in (5, 10, 25, 50, 100, 250, 500) if games / s <= 5)
        ticks = sorted({1, games, *(m for m in range(x_step, games, x_step) if m <= games - 0.4 * x_step)})
        for game in ticks:
            cv.text(self.xs(game), self.y0 + 42, 26, "C600", c.mut, f"{game:,}", anchor="middle")
        cv.text((self.x0 + self.x1) / 2, self.y0 + 80, 22, "C600", c.mut, race.get("axis_title", "GAMES PLAYED"),
                anchor="middle", spacing=2.5)
        cv.text(1000, TOP + 1290, 24, "C600", c.mut, handle.upper(), anchor="end", spacing=1.5)

        # the game counter, top left of the plot, where the lines haven't reached yet
        cv.text(self.x0 + 10, self.y1 + 30, 22, "C600", c.mut, "GAME", spacing=2.5)
        self.counter = cv.ax.text(self.x0 + 6, self.y1 + 130, "", fontproperties=_sized(font["hero"], 110),
                                  color=c.ink, va="baseline", alpha=0.9)

        # the subject in the accent (8 px), the others ink at 85% and 40% (4 px), as on the trend slide
        styles = [(c.accent, 8, 1.0, 1.0), (c.ink, 4, 0.85, 1.0), (c.ink, 4, 0.4, 0.75)]
        self.drawn = []
        for (line, totals), (colour, width_px, alpha, label_alpha) in reversed(list(zip(series, styles))):
            (path,) = cv.ax.plot([], [], color=colour, linewidth=width_px * 0.72, alpha=alpha,
                                 solid_capstyle="round", solid_joinstyle="round")
            (head,) = cv.ax.plot([], [], "o", color=colour, alpha=alpha, markersize=18 * 0.72,
                                 markeredgecolor=c.bg, markeredgewidth=4 * 0.72)
            label = cv.ax.text(0, 0, "", fontproperties=_sized(font["semi"], 30), color=colour if alpha == 1 else c.ink,
                               va="baseline", alpha=label_alpha)
            self.drawn.append((line, totals, path, head, label))

    def xs(self, game):
        return self.x0 + (game - 1) / (self.games - 1) * (self.x1 - self.x0)

    def ys(self, value):
        return self.y0 - value / self.y_max * (self.y0 - self.y1)

    def show(self, n):
        """Draw the race after n games (0: empty axes)."""
        self.counter.set_text(f"{n:,}" if n else "")
        ends = []
        for line, totals, path, head, label in self.drawn:
            if n == 0:
                path.set_data([], [])
                head.set_data([], [])
                label.set_text("")
                continue
            path.set_data([self.xs(g) for g in range(1, n + 1)], [self.ys(v) for v in totals[:n]])
            head.set_data([self.xs(n)], [self.ys(totals[n - 1])])
            label.set_text(f"{line['name']} {totals[n - 1]}")
            ends.append((self.ys(totals[n - 1]), label))
        label_y = 1e9
        for end_y, label in sorted(ends, key=lambda e: -e[0]):  # from the lowest up, pushed apart upwards
            label_y = min(end_y - 4, label_y - 46)
            label.set_position((self.xs(n) + 22, label_y))


def render(con, race, handle):
    """Write race.mp4, cover.png (the last frame) and caption.txt to posts/<name>/; returns the paths."""
    import imageio_ffmpeg

    metric = race.get("metric", "points")
    series = [(line, running_totals(con, line["player_id"], race["games"], None, metric)) for line in race["lines"]]
    frame = Race(race, series, make_post.fonts(), handle)
    folder = posts_folder(race["name"])
    folder.mkdir(parents=True, exist_ok=True)
    video, cover = folder / "race.mp4", folder / "cover.png"
    make_post.plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
    writer = animation.FFMpegWriter(fps=FPS, codec="libx264", bitrate=8000,
                                    extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    with writer.saving(frame.cv.fig, str(video), dpi=100):
        for n in schedule(race["games"], race.get("seconds", 15)):
            frame.show(n)
            writer.grab_frame(facecolor=frame.c.bg)
    frame.cv.save(cover)
    caption = folder / "caption.txt"
    caption.write_text(str(race["caption"]).strip() + "\n", encoding="utf-8")
    return [video, cover, caption]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["check", "render"])
    parser.add_argument("race", help="a YAML file in reels/")
    parser.add_argument("--handle", default=os.environ.get("NHL_POST_HANDLE", "@topshelfstats"))
    args = parser.parse_args()

    race = load(args.race)
    import duckdb

    con = duckdb.connect("md:nhl")
    try:
        results = check_facts(con, race)
        for claim, ok, got in results:
            print(f"{'ok  ' if ok else 'DIFF'}  {claim}" + ("" if ok else f"\n      query now gives: {got}"))
        failed = sum(not ok for _, ok, _ in results)
        print(f"{len(results) - failed} of {len(results)} facts match.")
        if failed:
            raise SystemExit(1)
        if args.action == "render":
            for path in render(con, race, race.get("handle") or args.handle):
                print(f"Saved {path}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
