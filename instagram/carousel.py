"""Render a story carousel: a YAML file in carousels/ becomes 3 to 20 slides, each a 1080 x 1350 PNG.

Check the facts only:  uv run python -m instagram.carousel check carousels/mcdavid-hot-start.yml
Render every slide:    uv run python -m instagram.carousel render carousels/mcdavid-hot-start.yml [--mode light|dark]

The layout is the "Story carousels" section of style/style_guide.md, drawn to the coordinates of
style/story_reference.html (kept on the laptop, not in the repo). A carousel has 3 to 20 slides of the types in
SLIDE_TYPES, in any order, any type as often as the story needs (style/story_playbook.md says how to write them).
The only fixed element on every slide is the handle at the bottom right; the NHL data credit goes in the caption.

- Mixed mode is the default: each slide type is light or dark as style.json's story.mixed says (hook, reveal and
  conclusion dark; comparison, trend and turning point light).
  --mode light or --mode dark (or `mode:` in the file) makes every slide the same.
- Before drawing anything, every query under `facts:` is run again; if any answer differs from the value written in
  the file, nothing is drawn and the command shows what changed.
- The slides and caption.txt are saved outside the repo, in posts/<file name>/: the folder in NHL_POSTS_DIR, or
  nhl-data-files/posts in your home folder. Rendering again replaces them.
- --handle (or NHL_POST_HANDLE, or `handle:` in the file): @topshelfstats by default.
- The file format is described in carousels/README.md.
"""

import argparse
import datetime
import math
import os
import re
from pathlib import Path
from types import SimpleNamespace

import matplotlib
import yaml

from instagram import make_post, photos
from instagram.make_post import STYLE, _sized, text_width

matplotlib.rcParams["lines.scale_dashes"] = False  # dash lengths in points, as written

W, H, M = 1080, 1350, 80  # canvas and margins (story_reference.html)
SLIDE_TYPES = ["hook", "reveal", "comparison", "trend", "turning_point", "conclusion", "statement",
               "question", "guess", "leaderboard", "distribution", "shot_map"]
SLIDE_COUNT = (3, 20)  # Instagram allows up to 20 slides; fewer than 3 is not a story
MIXED = STYLE["story"]["mixed"]
CAROUSEL_KEYS = {"accent", "mode", "through", "handle", "caption", "slides", "facts"}
RINK_LINES = {"light": ("#D7263D", "#2F6FEB"), "dark": ("#E0475A", "#5B8DEF")}  # red, blue (story_reference.html)

# The fields each slide takes: (required, optional).
FIELDS = {
    "hook": ({"kicker", "headline"}, {"image"}),
    "reveal": ({"number", "label", "name"}, {"subtitle", "stats"}),
    "comparison": ({"top", "bottom"}, set()),
    "trend": ({"title", "lines", "games"}, {"subtitle", "axis_title", "metric"}),
    "turning_point": ({"title", "stats"}, {"subtitle", "stats_title", "rink"}),
    "conclusion": ({"kicker", "headline"}, {"context", "question", "call"}),
    "statement": ({"headline"}, {"kicker"}),
    "question": ({"question"}, {"call"}),
    "guess": ({"question", "options"}, {"kicker"}),
    "leaderboard": ({"title", "rows"}, {"subtitle", "gap", "bars"}),
    "distribution": ({"title", "sql", "subject"}, {"subtitle", "axis_title", "average_line", "decimals",
                                                   "drop_leading_zero"}),
    "shot_map": ({"title", "from", "to"}, {"subtitle", "player_id", "team_id", "game_types", "count_line"}),
}
SHOT_MAP_FIRST_DAY = datetime.date(2009, 9, 1)  # shot locations start in 2009-10
LEADERBOARD_ROW_KEYS = ({"name", "value"}, {"rank", "team", "subject"})

# Fields written as a list of 1 to N lines of text: {(slide type, field): N}.
LINE_FIELDS = {("statement", "headline"): 3, ("question", "question"): 3, ("guess", "question"): 2}


# ---- Reading and checking a carousel file ----

class CarouselError(SystemExit):
    pass


def load(path):
    """The carousel as a dict, after checking its shape. Raises CarouselError naming every problem found."""
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    problems = validate(data)
    if problems:
        raise CarouselError(f"{path.name}:\n  " + "\n  ".join(problems))
    data["name"] = path.stem
    return data


def validate(data):
    """A list of problems with a carousel's shape; empty when it is fine."""
    if not isinstance(data, dict):
        return ["the file must be a mapping with accent, slides and facts"]
    problems = [f"unknown key '{key}'" for key in data if key not in CAROUSEL_KEYS]
    if data.get("mode", "mixed") not in ("mixed", "light", "dark"):
        problems.append("mode must be mixed, light or dark")
    known = {**STYLE["team_accents"], **STYLE["country_accents"]}
    if data.get("accent") is not None and str(data["accent"]).upper() not in known:
        problems.append(f"unknown accent {data['accent']}")
    if data.get("through") is not None and not isinstance(data["through"], datetime.date):
        problems.append("through must be a date, for example 2026-11-09")
    if "Data: NHL" not in str(data.get("caption") or ""):
        problems.append('caption must credit the data with "Data: NHL"')
    slides = data.get("slides")
    if not isinstance(slides, list) or not slides:
        return problems + ["slides must be a list of story slides"]
    if not SLIDE_COUNT[0] <= len(slides) <= SLIDE_COUNT[1]:
        problems.append(f"a carousel has {SLIDE_COUNT[0]} to {SLIDE_COUNT[1]} slides, not {len(slides)}")
    types = [slide.get("type") if isinstance(slide, dict) else None for slide in slides]
    unknown = [t for t in types if t not in SLIDE_TYPES]
    if unknown:
        problems.append(f"slide types must be {', '.join(SLIDE_TYPES)}, not {', '.join(map(str, unknown))}")
    for slide in slides:
        if not isinstance(slide, dict) or slide.get("type") not in FIELDS:
            continue
        required, optional = FIELDS[slide["type"]]
        missing = required - set(slide)
        extra = set(slide) - required - optional - {"type"}
        problems += [f"{slide['type']}: needs '{key}'" for key in sorted(missing)]
        problems += [f"{slide['type']}: unknown key '{key}'" for key in sorted(extra)]
        for (kind, field), most in LINE_FIELDS.items():
            if slide["type"] != kind or field not in slide:
                continue
            lines = slide[field]
            if not (isinstance(lines, list) and 1 <= len(lines) <= most and all(isinstance(x, str) and x for x in lines)):
                problems.append(f"{kind}: {field} must be a list of 1 to {most} lines of text")
        if slide["type"] == "guess" and "options" in slide:
            options = slide["options"]
            if not (isinstance(options, list) and 3 <= len(options) <= 4
                    and all(isinstance(o, (str, int, float)) and str(o) for o in options)):
                problems.append("guess: options must be a list of 3 or 4 answers")
        if slide["type"] == "shot_map":
            problems += [f"shot_map: {p}" for p in shot_map_problems(slide)]
        if slide["type"] == "distribution":
            problems += [f"distribution: {p}" for p in distribution_problems(slide)]
        if slide["type"] == "leaderboard" and "rows" in slide:
            problems += [f"leaderboard: {p}" for p in leaderboard_problems(slide)]
        if slide["type"] == "trend" and slide.get("metric", "points") not in METRICS:
            problems.append(f"trend: metric must be one of {', '.join(METRICS)}")
        if "image" in slide:
            problems += [f"{slide['type']}: image: {p}" for p in image_problems(slide["image"])]
        rink = slide.get("rink", "illustration") if slide["type"] == "turning_point" else None
        if rink is not None and rink not in ("illustration", "none") and not (
                isinstance(rink, dict) and set(rink) == {"goals_of", "season"}):
            problems.append("turning_point: rink must be illustration, none, or {goals_of: <player_id>, season: <id>}")
    for number, fact in enumerate(data.get("facts") or [], start=1):
        if not isinstance(fact, dict) or not {"claim", "sql", "value"} <= set(fact):
            problems.append(f"fact {number}: needs claim, sql and value")
    if not data.get("facts"):
        problems.append("facts: every number on the slides needs a fact")
    return problems


def bar_value(value):
    """The number behind a written value, for the bar's length: 48, "48", ".934", "1,268" or "52.3%"."""
    try:
        return float(str(value).replace(",", "").rstrip("%"))
    except ValueError:
        return None


def leaderboard_problems(slide):
    """Problems with a leaderboard's rows (the Studio Edition leaderboard: up to five rows, one subject)."""
    rows = slide["rows"]
    if not (isinstance(rows, list) and rows and all(isinstance(row, dict) for row in rows)):
        return ["rows must be a list of {name, value} rows"]
    problems = []
    required, optional = LEADERBOARD_ROW_KEYS
    for number, row in enumerate(rows, start=1):
        problems += [f"row {number}: needs '{key}'" for key in sorted(required - set(row))]
        problems += [f"row {number}: unknown key '{key}'" for key in sorted(set(row) - required - optional)]
        amount = bar_value(row["value"]) if "value" in row else 0
        if slide.get("bars", True) and (amount is None or amount < 0):
            problems.append(f"row {number}: bars need a number of 0 or more as the value (or bars: false)")
    subjects = [number for number, row in enumerate(rows, start=1) if row.get("subject")]
    if len(subjects) != 1:
        problems.append("exactly one row must be the subject (subject: true)")
    if slide.get("gap"):
        if len(rows) != 4:
            problems.append("gap: true takes four rows: the top three, then the subject with its real rank")
        elif subjects != [4] or "rank" not in rows[3]:
            problems.append("gap: true needs the fourth row to be the subject, with its rank")
    elif len(rows) > 5:
        problems.append("at most five rows")
    return problems


def shot_map_problems(slide):
    problems = []
    if ("player_id" in slide) == ("team_id" in slide):
        problems.append("give either player_id or team_id")
    start, end = slide.get("from"), slide.get("to")
    if not (isinstance(start, datetime.date) and isinstance(end, datetime.date)):
        problems.append("from and to must be dates, for example 2026-10-07 and 2026-11-09")
    elif start > end:
        problems.append("from must be on or before to")
    elif start < SHOT_MAP_FIRST_DAY:
        problems.append("shot locations start in 2009-10: from must be 2009-09-01 or later")
    game_types = slide.get("game_types", [2])
    if not (isinstance(game_types, list) and game_types and set(game_types) <= {2, 3}):
        problems.append("game_types must be a list of 2 (regular season) and/or 3 (playoffs)")
    if not isinstance(slide.get("count_line", True), bool):
        problems.append("count_line must be true or false")
    return problems


def distribution_problems(slide):
    problems = []
    if "sql" in slide and not (isinstance(slide["sql"], str) and slide["sql"].strip()):
        problems.append("sql must be a query returning one row per player or team: id, name, value")
    average = slide.get("average_line", False)
    if not (isinstance(average, bool) or (isinstance(average, dict) and set(average) == {"value", "label"}
                                          and isinstance(average["value"], (int, float)))):
        problems.append("average_line must be true, false, or {value: <number>, label: <text>}")
    if not isinstance(slide.get("decimals", 0), int) or not 0 <= slide.get("decimals", 0) <= 4:
        problems.append("decimals must be a whole number from 0 to 4")
    return problems


IMAGE_KEYS = {"type", "commons", "file", "credit", "layout", "side", "focus"}


def image_problems(image):
    """Problems with a slide's image: field (style/style_guide.md, "NHL logos and headshots")."""
    if not isinstance(image, dict):
        return ["must be a mapping, for example {type: photo, commons: 'File:...jpg'}"]
    problems = [f"unknown key '{key}'" for key in sorted(set(image) - IMAGE_KEYS)]
    if image.get("type") != "photo":
        problems.append("type must be photo (headshots and logos are not supported yet)")
    if bool(image.get("commons")) == bool(image.get("file")):
        problems.append("give either commons (a Wikimedia Commons file) or file (a photo in assets/nhl/photos/)")
    if image.get("commons") and not str(image["commons"]).startswith("File:"):
        problems.append("commons must be a Commons file title starting with File:")
    if image.get("commons") and "credit" in image:
        problems.append("a Commons photo's credit comes from Commons: leave credit out")
    if image.get("file") and not image.get("credit"):
        problems.append("a photo from assets/nhl/photos/ needs a credit:")
    if image.get("layout", "panel") not in photos.LAYOUTS:
        problems.append("layout must be panel or cutout")
    if image.get("side", "left") not in ("left", "right"):
        problems.append("side must be left or right")
    focus = image.get("focus", [0.5, 0.4])
    if not (isinstance(focus, list) and len(focus) == 2
            and all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in focus)):
        problems.append("focus must be two numbers from 0 to 1: [across, down]")
    return problems


def slide_mode(carousel, slide_type, override=None):
    """light or dark for a slide: --mode, else the file's mode; mixed follows style.json."""
    mode = override or carousel.get("mode", "mixed")
    return MIXED[slide_type] if mode == "mixed" else mode


# ---- Facts ----

def normalise(rows):
    """A query's rows in the shape a fact's value is written: one value for one row of one column, a list for one
    row, a list of lists otherwise. Numbers and dates become text, so 1268, 1268.0 and Decimal('1268') agree."""
    def text(value):
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return str(value)

    rows = [[text(value) for value in row] for row in rows]
    if len(rows) == 1:
        return rows[0][0] if len(rows[0]) == 1 else rows[0]
    return rows


def expected(value):
    if isinstance(value, list):
        return [expected(item) for item in value]
    return normalise([[value]])


def check_facts(con, carousel):
    """[(claim, ok, got)] for every fact, after running its query again."""
    results = []
    for fact in carousel.get("facts") or []:
        got = normalise(con.execute(fact["sql"]).fetchall())
        results.append((fact["claim"], got == expected(fact["value"]), got))
    return results


# ---- Data for the trend slide ----

METRICS = ("points", "goals", "assists")


def running_totals(con, player_id, games, season=None, metric="points", through=None):
    """The player's running total of `metric` over his first `games` regular-season games: of the season, or of his
    career when no season is given."""
    if metric not in METRICS:
        raise CarouselError(f"trend: metric must be one of {', '.join(METRICS)}")
    rows = con.execute(
        f"""
        select {metric} from marts.fct_skater_games
        where player_id = $player and game_type = 2 and ($season is null or season = $season)
            and ($through is null or game_date <= $through)
        order by game_date, game_id
        limit $games
        """,
        {"player": player_id, "season": season, "games": games, "through": through},
    ).fetchall()
    if len(rows) < games:
        where = f"in {season}" if season else "in his career"
        raise CarouselError(f"trend: player {player_id} has only {len(rows)} games {where}, not {games}")
    totals, running = [], 0
    for (value,) in rows:
        running += value
        totals.append(running)
    return totals


def goal_locations(con, player_id, season):
    """(points, own_half): the player's regular-season goals of the season (shootouts left out) as (across, depth) in
    feet on a half rink, attacking downwards, and the number scored from his own half (not drawable on a half rink).

    The attacking end comes from home_team_defending_side, which the NHL gives per period: a home team defending the
    left attacks towards +x. Depth is feet from the centre line (the goal line is at 89); across is 0 to 85 feet from
    the shooter's right-hand boards, so the shooter's left is on the right of the drawing, as seen from centre ice.
    """
    rows = con.execute(
        """
        select x_coord, y_coord,
            case when (is_home_shooter and home_team_defending_side = 'left')
                   or (not is_home_shooter and home_team_defending_side = 'right') then 1 else -1 end as dir
        from marts.fct_shots
        where shooting_player_id = $player and season = $season and game_type = 2 and is_goal and not is_shootout
            and home_team_defending_side in ('left', 'right')
        """,
        {"player": player_id, "season": season},
    ).fetchall()
    if not rows:
        raise CarouselError(f"turning_point: no goals with locations for player {player_id} in {season}")
    points = [(42.5 + d * y, d * x) for x, y, d in rows if d * x > 0]
    return points, len(rows) - len(points)


def shot_locations(con, start, end, player_id=None, team_id=None, game_types=(2,)):
    """(shots, (own_half_attempts, own_half_goals)): the unblocked shot attempts (goals, shots on goal, missed shots;
    shootouts left out) of a player or team between two dates, as (across, depth, is_goal) in feet on a half rink
    attacking downwards, and how many attempts and goals came from the shooter's own half (not drawable on a half
    rink; most are empty-net shots).

    Locations come from marts.int_shot_geometry, where every shot is normalised to attack the net at x = +89
    (docs/data_coverage.md, "Advanced stats": the NHL's rink side from 2019-20, inferred from the shots before).
    Depth is feet from the centre line (the goal line is at 89); across is 0 to 85 feet, 42.5 + y."""
    rows = con.execute(
        """
        select x_norm, y_norm, is_goal
        from marts.int_shot_geometry
        where is_unblocked and x_norm is not null and y_norm is not null
            and game_date between $start and $end
            and list_contains($types, game_type)
            and ($player is null or shooting_player_id = $player)
            and ($team is null or shooting_team_id = $team)
        """,
        {"start": start, "end": end, "types": list(game_types), "player": player_id, "team": team_id},
    ).fetchall()
    if not rows:
        who = f"player {player_id}" if player_id is not None else f"team {team_id}"
        raise CarouselError(f"shot_map: no shots with locations for {who} from {start} to {end}")
    shots = [(42.5 + y, x, bool(goal)) for x, y, goal in rows if x >= 0]
    own_half = [bool(goal) for x, _, goal in rows if x < 0]
    return shots, (len(own_half), sum(own_half))


def distribution_rows(con, sql, subject):
    """[(id, name, value)] from a distribution slide's query, sorted by value; the subject must be among them."""
    rows = con.execute(sql).fetchall()
    if not rows or len(rows[0]) != 3:
        raise CarouselError("distribution: the sql must return three columns: id, name, value")
    rows = sorted(((str(i), str(n), float(v)) for i, n, v in rows if v is not None), key=lambda r: r[2])
    if str(subject) not in {i for i, _, _ in rows}:
        raise CarouselError(f"distribution: the subject {subject} is not among the {len(rows)} rows the sql returns")
    return rows


def beeswarm(xs, radius, first=None, subject_radius=None):
    """A vertical offset for each dot so dots on a horizontal value axis never overlap: each dot, in order of x, takes
    the free offset closest to the centre line (0, +d, -d, +2d ...). The dot at index `first` (the subject) is
    placed before all others, so it sits on the centre line, with room for its larger radius. The caller shrinks
    the radius until the swarm fits its height."""
    order = ([first] if first is not None else []) + [i for i in range(len(xs)) if i != first]
    placed, offsets = [], [0] * len(xs)
    for i in order:
        x = xs[i]
        r = subject_radius if i == first and subject_radius else radius
        step, k = radius, 0
        while True:
            offset = 0 if k == 0 else (k + 1) // 2 * step * (1 if k % 2 else -1)
            if all((px - x) ** 2 + (py - offset) ** 2 >= (r + pr + 1) ** 2 for px, py, pr in placed):
                break
            k += 1
        placed.append((x, offset, r))
        offsets[i] = offset
    return offsets


def number_text(value, decimals=0, drop_leading_zero=False):
    text = f"{value:,.{decimals}f}"
    if drop_leading_zero and text.startswith(("0.", "-0.")):
        text = text.replace("0.", ".", 1)
    return text


# ---- Drawing primitives ----

def colours(mode, accent_code):
    """The palette for one slide, with the hairline and panel colours of the story reference."""
    pal = make_post.palette(mode, accent_code)
    return SimpleNamespace(
        mode=mode, dark=mode == "dark", bg=pal["background"], ink=pal["ink"], mut=pal["muted_text"],
        hair_alpha=STYLE["layout"]["hairline"][f"opacity_{mode}"], panel=STYLE["story"]["comparison_panel"][mode],
        accent=pal["accent"], track=pal["bar_track"],
    )


def _px(pixels):
    """Line width or marker size in points for a size in pixels (drawn at 100 dots per inch)."""
    return pixels * 0.72


class Canvas:
    """One slide: y grows downwards and every position is in pixels, as in story_reference.html."""

    FONTS = {"C600": "footer", "C700": "title", "C800": "hero", "B500": "medium", "S600": "semi"}

    def __init__(self, c, font, height=H):
        self.c, self.font, self.height = c, font, height
        self.fig, self.ax = make_post.new_canvas({"background": c.bg})
        if height != H:  # a taller frame, such as a 1080 x 1920 Reel
            self.fig.set_size_inches(W / 100, height / 100)
            self.ax.set_ylim(height, 0)

    def text(self, x, y, size, face, colour, text, anchor="start", spacing=0.0, alpha=1.0):
        """Text with its baseline at y, like SVG <text>: anchor start, middle or end; spacing in pixels."""
        font = self.font[self.FONTS[face]]
        text = str(text)
        if not spacing:
            ha = {"start": "left", "middle": "center", "end": "right"}[anchor]
            self.ax.text(x, y, text, fontproperties=_sized(font, size), color=colour, va="baseline", ha=ha,
                         alpha=alpha)
            return
        total = text_width(self.fig, text, font, size) + spacing * (len(text) - 1)
        start = x - total if anchor == "end" else x - total / 2 if anchor == "middle" else x
        for i, char in enumerate(text):
            offset = text_width(self.fig, text[:i], font, size) if i else 0
            self.ax.text(start + offset + i * spacing, y, char, fontproperties=_sized(font, size), color=colour,
                         va="baseline", alpha=alpha)

    def width(self, text, size, face, spacing=0.0):
        text = str(text)
        return text_width(self.fig, text, self.font[self.FONTS[face]], size) + spacing * (len(text) - 1)

    def line(self, xs, ys, colour, width_px, alpha=1.0, dashes=None, cap="butt", join="miter"):
        kwargs = {"dashes": [_px(d) for d in dashes]} if dashes else {}
        self.ax.plot(xs, ys, color=colour, linewidth=_px(width_px), alpha=alpha, solid_capstyle=cap,
                     dash_capstyle=cap, solid_joinstyle=join, **kwargs)

    def hairline(self, x1, x2, y, alpha_scale=1.0):
        self.line([x1, x2], [y, y], self.c.ink, 2, alpha=self.c.hair_alpha * alpha_scale)

    def rect(self, x, y, w, h, colour):
        from matplotlib.patches import Rectangle

        self.ax.add_patch(Rectangle((x, y), w, h, facecolor=colour, linewidth=0))

    def circle(self, x, y, r, fill, alpha=1.0, stroke=None, stroke_px=0):
        from matplotlib.patches import Circle

        self.ax.add_patch(Circle((x, y), r, facecolor=fill, alpha=alpha, edgecolor=stroke or "none",
                                 linewidth=_px(stroke_px)))

    def polygon(self, points, fill, alpha=1.0):
        from matplotlib.patches import Polygon

        self.ax.add_patch(Polygon(points, closed=True, facecolor=fill, alpha=alpha, linewidth=0))

    def picture(self, pixels, x, y, w, h):
        """A picture (PIL image, RGB or RGBA) drawn at x, y with exactly w x h pixels, behind any text."""
        import numpy

        self.ax.imshow(numpy.asarray(pixels), extent=(x, x + w, y + h, y), origin="upper", aspect="auto",
                       interpolation="antialiased", zorder=0.5)
        self.ax.set_xlim(0, W)
        self.ax.set_ylim(self.height, 0)

    def handle(self, handle, on_photo=False):
        """The handle, bottom right. Over a photo it sits on a small band of the background colour, to stay readable."""
        frame = STYLE["story"]["frame"]["handle"]
        if on_photo:
            width = self.width(handle.upper(), frame["size"], "C600", 1.5)
            self.rect(frame["x_right"] - width - 14, frame["y"] - frame["size"] - 10, width + 28,
                      frame["size"] + 24, self.c.bg)
        self.text(frame["x_right"], frame["y"], frame["size"], "C600", self.c.mut, handle.upper(), anchor="end",
                  spacing=1.5)

    def save(self, path):
        self.fig.savefig(path, dpi=100, facecolor=self.c.bg)
        make_post.plt.close(self.fig)


def arc(cx, cy, r, start_deg, end_deg, steps=48):
    """Points on a circle (y grows downwards, so 90 degrees points down)."""
    angles = [math.radians(start_deg + (end_deg - start_deg) * i / steps) for i in range(steps + 1)]
    return [cx + r * math.cos(a) for a in angles], [cy + r * math.sin(a) for a in angles]


def rink_half(cv, x, y, w, alpha, plain=False):
    """A half rink to real proportions (85 x 100 ft), centre line at the top, as in story_reference.html. plain=True
    draws every line in ink (the shot map), so the accent on the goals is the only colour on the slide."""
    s = w / 85
    red, blue = (cv.c.ink, cv.c.ink) if plain else RINK_LINES[cv.c.mode]
    ink = cv.c.ink

    def px(a, b):
        return x + a * s, y + b * s

    # boards: down the left side, the two rounded corners, up the right side
    left_x, left_y = arc(*px(28, 72), 28 * s, 180, 90)
    right_x, right_y = arc(*px(57, 72), 28 * s, 90, 0)
    xs = [x, x] + left_x + right_x + [x + 85 * s]
    ys = [y, y + 72 * s] + left_y + right_y + [y]
    cv.line(xs, ys, ink, 4, alpha=alpha, join="round")
    cv.line([x, x + 85 * s], [y, y], red, 6, alpha=alpha)                        # centre line
    cv.line([x, x + 85 * s], [y + 25 * s, y + 25 * s], blue, 6, alpha=alpha)     # blue line
    cv.line([x + 5.8 * s, x + 79.2 * s], [y + 89 * s, y + 89 * s], red, 3, alpha=alpha)  # goal line
    cv.line(*arc(*px(42.5, 0), 15 * s, 180, 0), blue, 3, alpha=alpha)           # centre circle (our half)
    for fx in (20.5, 64.5):                                                      # end-zone faceoff circles
        cv.line(*arc(*px(fx, 69), 15 * s, 0, 360), red, 3, alpha=alpha)
        cv.circle(*px(fx, 69), 1 * s, red, alpha=alpha)
    crease_x, crease_y = arc(*px(42.5, 89), 6 * s, 180, 360)
    cv.polygon(list(zip(crease_x, crease_y)), blue, alpha=alpha * 0.2)
    cv.line(crease_x, crease_y, blue, 3, alpha=alpha)


def arrow(cv, x1, y1, x2, y2, colour):
    """A dashed arrow, 5 px wide, with a solid head (the reference's marker: 25 px long, tip 7.5 px past the end)."""
    cv.line([x1, x2], [y1, y2], colour, 5, dashes=(14, 10), cap="round")
    length = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    tip = (x2 + ux * 7.5, y2 + uy * 7.5)
    base = (tip[0] - ux * 25, tip[1] - uy * 25)
    cv.polygon([tip, (base[0] - uy * 12.5, base[1] + ux * 12.5), (base[0] + uy * 12.5, base[1] - ux * 12.5)],
               colour)


# ---- The six slides ----

PANEL_W = 470            # a photo panel on the hook: full height, 470 px wide (about 44% of the canvas)
CUTOUT_MAX = (500, 810)  # a cut-out: at most 500 px wide and 60% of the canvas high
CUTOUT_BOTTOM = 1236     # a cut-out stands just above the handle, which it must never cover


def hook(cv, slide, ctx):
    c = cv.c
    image = slide.get("image")
    left, right = M, W - M  # where the kicker and headline may go
    if image is None or image.get("layout", "panel") == "cutout":
        rink_half(cv, 200, 90, 800, 0.16 if c.dark else 0.14)
    if image is not None:
        path, credit = photos.resolve(image)
        ctx.credits.append(credit)
        side = image.get("side", "left")
        if image.get("layout", "panel") == "panel":
            x = 0 if side == "left" else W - PANEL_W
            cv.picture(photos.cover(path, PANEL_W, H, tuple(image.get("focus", [0.5, 0.4]))), x, 0, PANEL_W, H)
            left, right = (PANEL_W + 56, W - M) if side == "left" else (M, W - PANEL_W - 56)
            ctx.handle_on_photo = side == "right"
        else:
            person = photos.cutout(path)
            scale = min(CUTOUT_MAX[0] / person.width, CUTOUT_MAX[1] / person.height)
            w, h = round(person.width * scale), round(person.height * scale)
            x = W - M - w if side == "right" else M
            cv.picture(person.resize((w, h)), x, CUTOUT_BOTTOM - h, w, h)
            left, right = (M + w + 40, W - M) if side == "left" else (M, x - 40)
    # kicker and headline at the reference sizes (40 and 150 px), smaller only when they must fit beside a photo
    room = right - left
    kicker_size = min(40, 40 * room / cv.width(slide["kicker"], 40, "C700", 4))
    lines = slide["headline"]
    size = min(150, 150 * room / max(cv.width(line, 150, "C700") for line in lines))
    gap = 140 * size / 150
    # 32 px above the first line's capitals, as in the reference (780 above a 150 px headline from 920)
    kicker_y = 1200 - (len(lines) - 1) * gap - size * 0.72 - 32
    cv.text(left, kicker_y, kicker_size, "C700", c.accent, slide["kicker"], spacing=4 * kicker_size / 40)
    for i, line in enumerate(lines):
        last = i == len(lines) - 1
        cv.text(left, 1200 - (len(lines) - 1 - i) * gap, size, "C700", c.accent if last else c.ink, line)


def reveal(cv, slide, ctx):
    c = cv.c
    number = str(slide["number"])
    # 600 px as in the reference; a wider number (three digits) shrinks until its two-line label fits beside it
    label_w = max(cv.width(line, 34, "C700", 4) for line in slide["label"][:2])
    room = (W - M) - (M - 14) - 40 - label_w
    size = min(600, 600 * room / cv.width(number, 600, "C800", -18))
    cv.text(M - 14, 720, size, "C800", c.accent, number, spacing=-18 * size / 600)
    label_x = max(M + 600, M - 14 + cv.width(number, size, "C800", -18 * size / 600) + 40)
    for i, line in enumerate(slide["label"][:2]):
        cv.text(label_x, 676 + 40 * i, 34, "C700", c.mut, line, spacing=4)
    cv.text(M, 850, 104, "C700", c.ink, slide["name"])
    if slide.get("subtitle"):
        cv.text(M, 912, 36, "B500", c.mut, slide["subtitle"])
    stats = slide.get("stats") or []
    if stats:
        cv.hairline(M, W - M, 1060)
        for x, stat in zip((M, M + 230, M + 460, M + 740), stats[:4]):
            cv.text(x, 1150, 64, "C700", c.ink, stat["value"])
            cv.text(x, 1190, 22, "C600", c.mut, stat["label"], spacing=2.5)


def comparison(cv, slide, ctx):
    c = cv.c
    cv.rect(0, 0, W, 690, c.panel)
    top, bottom = slide["top"], slide["bottom"]
    cv.text(M, 230, 30, "C700", c.accent, top["kicker"], spacing=4)
    cv.text(M - 10, 610, 400, "C800", c.accent, top["number"], spacing=-12)
    if top.get("line"):
        cv.text(M + 480, 556, 46, "S600", c.ink, top["line"])
    cv.text(M, 800, 30, "C700", c.mut, bottom["kicker"], spacing=4)
    cv.text(M - 10, 1180, 400, "C800", c.ink, bottom["number"], spacing=-12, alpha=0.9)
    if bottom.get("line"):
        cv.text(M + 480, 1126, 46, "S600", c.ink, bottom["line"])


def title_block(cv, slide):
    cv.text(M, 250, 112, "C700", cv.c.ink, slide["title"])
    if slide.get("subtitle"):
        cv.text(M, 318, 36, "B500", cv.c.mut, slide["subtitle"])


def trend(cv, slide, ctx):
    """Running totals: the first line is the subject (accent, 8 px); the others ink at 85% and 40% (4 px)."""
    c = cv.c
    a = a_text = c.accent
    title_block(cv, slide)
    games = slide["games"]
    metric = slide.get("metric", "points")
    series = [(line, running_totals(ctx.con, line["player_id"], games, line.get("season"), metric, ctx.through))
              for line in slide["lines"]]
    top_value = max(totals[-1] for _, totals in series)
    step = next(s for s in (5, 10, 20, 50, 100, 200, 250, 500, 1000) if math.ceil(top_value / s) <= 4)
    y_max = step * math.ceil(top_value / step)
    x0, x1, y0, y1 = M + 60, W - M - 170, 1170, 420

    def xs(game):
        return x0 + (game - 1) / (games - 1) * (x1 - x0)

    def ys(value):
        return y0 - value / y_max * (y0 - y1)

    for value in range(0, y_max + 1, step):
        cv.hairline(x0, x1 + 150, ys(value), alpha_scale=0.8 if value else 2)
        cv.text(x0 - 16, ys(value) + 9, 26, "C600", c.mut, value, anchor="end")
    x_step = next(s for s in (5, 10, 25, 50, 100, 250, 500) if games / s <= 5)
    ticks = sorted({1, games, *(m for m in range(x_step, games, x_step) if m <= games - 0.4 * x_step)})
    for game in ticks:
        cv.text(xs(game), y0 + 42, 26, "C600", c.mut, f"{game:,}", anchor="middle")
    cv.text((x0 + x1) / 2, y0 + 80, 22, "C600", c.mut, slide.get("axis_title", "GAME NUMBER"), anchor="middle",
            spacing=2.5)

    others = [(0.85, 1.0), (0.4, 0.75)]  # (line opacity, end-label opacity) for the second and third lines
    styles = [(a, 8, 1.0, a_text, 1.0)] + [(c.ink, 4, op, c.ink, label_op) for op, label_op in others]
    drawn = list(zip(series, styles))
    for (line, totals), (colour, width_px, alpha, _, _) in reversed(drawn):  # the subject is drawn last, on top
        cv.line([xs(g) for g in range(1, games + 1)], [ys(v) for v in totals], colour, width_px, alpha=alpha,
                cap="round", join="round")
    # end labels: two lines each, pushed apart so they never overlap
    ends = sorted(((ys(totals[-1]), line, totals, style) for (line, totals), style in drawn), key=lambda e: e[0])
    label_y = -1e9
    for end_y, line, totals, (colour, _, alpha, label_colour, label_alpha) in ends:
        cv.circle(xs(games), end_y, 9, colour, alpha=alpha, stroke=c.bg, stroke_px=4)
        label_y = max(end_y - 4, label_y + 66)  # the reference's offsets: just above the point, 66 px apart
        cv.text(xs(games) + 22, label_y, 30, "S600", label_colour, f"{line['name']} {totals[-1]}", alpha=label_alpha)
        if line.get("season"):  # a career line needs no season under its name
            cv.text(xs(games) + 22, label_y + 30, 22, "C600", c.mut, make_post.season_label(line["season"]),
                    spacing=1.5)


def turning_point(cv, slide, ctx):
    c = cv.c
    a = a_text = c.accent
    title_block(cv, slide)
    if slide.get("stats_title"):
        cv.text(M, 520, 24, "C700", c.mut, slide["stats_title"], spacing=3)
    for y, stat in zip((660, 820, 980), slide["stats"][:3]):
        cv.text(M, y, 96, "C700", a_text if stat.get("accent") else c.ink, stat["value"])
        for i, line in enumerate(stat["label"][:2]):
            cv.text(M + 150, y - 36 + 32 * i, 24, "C700", c.mut, line, spacing=3)
        cv.hairline(M, M + 400, y + 30)
    rink = slide.get("rink", "illustration")
    rx, ry, rw = 560, 420, 440
    s = rw / 85
    if isinstance(rink, dict):  # real goal locations from the play-by-play: no illustration label needed
        rink_half(cv, rx, ry, rw, 0.45 if c.dark else 0.4)
        points, own_half = goal_locations(ctx.con, rink["goals_of"], rink["season"])
        for across, depth in points:
            cv.circle(rx + across * s, ry + min(depth, 100) * s, 9, a, alpha=0.85, stroke=c.bg, stroke_px=2)
        lines = [f"{len(points)} OF HIS {len(points) + own_half} GOALS, {make_post.season_label(rink['season'])}"]
        if own_half:
            lines.append(f"{own_half} SCORED FROM HIS OWN HALF")
        for i, line in enumerate(lines):
            cv.text(rx + rw / 2, ry + 100 * s + 48 + 32 * i, 22, "C600", c.mut, line, anchor="middle", spacing=2)
    elif rink == "illustration":
        rink_half(cv, rx, ry, rw, 0.45 if c.dark else 0.4)
        for (fx1, fy1), (fx2, fy2) in (((70, 40), (48, 78)), ((14, 60), (38, 80))):
            arrow(cv, rx + fx1 * s, ry + fy1 * s, rx + fx2 * s, ry + fy2 * s, a)
        cv.circle(rx + 42.5 * s, ry + 82 * s, 16, a)
        cv.text(rx + rw / 2, ry + 100 * s + 48, 22, "C600", c.mut, "ILLUSTRATION, NOT TRACKED PASSES",
                anchor="middle", spacing=2)


def conclusion(cv, slide, ctx):
    c = cv.c
    cv.text(M, 330, 40, "C700", c.mut, slide["kicker"], spacing=4)
    lines = slide["headline"]
    for i, line in enumerate(lines[:2]):
        cv.text(M, 520 + 180 * i, 190, "C700", c.accent if i == 1 else c.ink, line)
    for i, line in enumerate((slide.get("context") or [])[:2]):
        cv.text(M, 800 + 52 * i, 40, "B500", c.mut, line)
    if slide.get("question"):
        cv.hairline(M, W - M, 960)
        cv.text(M, 1080, 96, "C700", c.ink, slide["question"])
        cv.text(M, 1160, 34, "S600", c.mut, slide.get("call", "Tell us in the comments."))


def statement(cv, slide, ctx):
    """One big sentence: the take or the verdict. Up to three lines at the hook's 150 px (smaller only when a line
    would not fit between the margins), the last line in the accent, an optional small kicker above in muted text
    (the accent belongs to the last line only). The block is centred a little above the middle of the canvas."""
    c = cv.c
    lines = slide["headline"]
    size = min(150, 150 * (W - 2 * M) / max(cv.width(line, 150, "C700") for line in lines))
    gap = 140 * size / 150
    kicker = slide.get("kicker")
    # From the top of the kicker (or of the first line's capitals) to the last baseline.
    block = (len(lines) - 1) * gap + size * 0.72 + (40 * 0.72 + 32 if kicker else 0)
    last_y = 620 + block / 2
    first_y = last_y - (len(lines) - 1) * gap
    if kicker:
        cv.text(M, first_y - size * 0.72 - 32, 40, "C700", c.mut, kicker, spacing=4)
    for i, line in enumerate(lines):
        cv.text(M, first_y + i * gap, size, "C700", c.accent if i == len(lines) - 1 else c.ink, line)


def question(cv, slide, ctx):
    """The conclusion's question and call on their own, for when the verdict is a separate statement slide: the
    question in 1 to 3 lines at the conclusion's 96 px (smaller only when a line would not fit), the call below it
    at 34 px in muted text, the block centred a little above the middle like the statement."""
    c = cv.c
    lines = slide["question"]
    size = min(96, 96 * (W - 2 * M) / max(cv.width(line, 96, "C700") for line in lines))
    gap = 104 * size / 96
    call = slide.get("call", "Tell us in the comments.")
    # From the top of the first line's capitals to the call's baseline (the conclusion puts it 80 px lower).
    block = size * 0.72 + (len(lines) - 1) * gap + 80
    first_y = 620 - block / 2 + size * 0.72
    for i, line in enumerate(lines):
        cv.text(M, first_y + i * gap, size, "C700", c.ink, line)
    cv.text(M, first_y + (len(lines) - 1) * gap + 80, 34, "S600", c.mut, call)


def guess(cv, slide, ctx):
    """A quiz: an optional kicker (the slide's one accent, e.g. "GUESS FIRST"), the question in 1 or 2 lines at
    96 px, then 3 or 4 options as large rows lettered A to D (letters muted, answers in ink, hairlines between
    rows). The answer is never shown: the next slide reveals it."""
    c = cv.c
    if slide.get("kicker"):
        cv.text(M, 230, 40, "C700", c.accent, slide["kicker"], spacing=4)
    lines = slide["question"]
    size = min(96, 96 * (W - 2 * M) / max(cv.width(line, 96, "C700") for line in lines))
    for i, line in enumerate(lines):
        cv.text(M, 360 + i * 104, size, "C700", c.ink, line)
    options = [str(option) for option in slide["options"]]
    text_x = M + 110
    room = W - M - text_x
    option_size = min(56, min(56 * room / cv.width(option, 56, "S600") for option in options))
    top = 360 + (len(lines) - 1) * 104 + 110  # the hairline above the first row
    step = 150
    cv.hairline(M, W - M, top)
    for i, (letter, option) in enumerate(zip("ABCD", options)):
        baseline = top + 95 + i * step
        cv.text(M, baseline + 4, 72, "C700", c.mut, letter)
        cv.text(text_x, baseline, option_size, "S600", c.ink, option)
        cv.hairline(M, W - M, top + (i + 1) * step)


def leaderboard(cv, slide, ctx):
    """The Studio Edition leaderboard in the story frame: the title block, then up to five rows 128 px apart, each with
    a rank (01 to 05, or as written, e.g. T6), the name and team code, the value right-aligned and a flat 8 px bar
    under the name that starts at zero (scaled to the largest value shown). Only the subject's rank, value and bar
    are in the accent. With gap: true the top three come first, then a gap marker, then the subject's row at its
    real rank."""
    c = cv.c
    title_block(cv, slide)
    rows = slide["rows"]
    show_bars = slide.get("bars", True)
    top_value = max(bar_value(row["value"]) for row in rows) if show_bars else 0
    track_w = W - 2 * M - 64 - 120
    y = 510
    for i, row in enumerate(rows):
        if slide.get("gap") and i == 3:
            cv.text(M + 64, y - 34, 44, "S600", c.mut, "···")
            y += 64
        me = bool(row.get("subject"))
        rank = row.get("rank", i + 1)
        rank = f"{rank:02d}" if isinstance(rank, int) else str(rank)
        cv.text(M, y, 30, "C600", c.accent if me else c.mut, rank)
        cv.text(M + 64, y, 44, "S600", c.ink, row["name"])
        if row.get("team"):
            cv.text(M + 64 + cv.width(row["name"], 44, "S600") + 16, y, 24, "C700", c.mut, row["team"], spacing=2)
        cv.text(W - M, y + 2, 64, "C700", c.accent if me else c.ink, row["value"], anchor="end")
        if show_bars:
            cv.rect(M + 64, y + 24, track_w, 8, c.track)
            if top_value > 0:
                cv.rect(M + 64, y + 24, track_w * bar_value(row["value"]) / top_value, 8, c.accent if me else c.ink)
        last = i == len(rows) - 1
        before_gap = slide.get("gap") and i == 2
        if not last and not before_gap:
            cv.line([M, W - M], [y + 78, y + 78], c.ink, 1.5, alpha=c.hair_alpha * 0.8)
        y += 128


def distribution(cv, slide, ctx):
    """How unusual is it: every row of the slide's query as a grey dot on one value axis (a beeswarm, so dots never
    overlap), the subject's dot in the accent, larger, and labelled with its name and value. An optional dashed
    average line: true for the mean of the dots shown, or {value, label} for a figure from a fact (a league rate)."""
    c = cv.c
    title_block(cv, slide)
    rows = distribution_rows(ctx.con, slide["sql"], slide["subject"])
    decimals, drop = slide.get("decimals", 0), slide.get("drop_leading_zero", False)
    values = [v for _, _, v in rows]
    low, high = min(values), max(values)
    span = (high - low) or 1
    x0, x1, centre = M + 20, W - M - 20, 760

    def xs(value):
        return x0 + (value - low) / span * (x1 - x0)

    subject = str(slide["subject"])
    first = next(i for i, (row_id, _, _) in enumerate(rows) if row_id == subject)
    radius = 11
    while True:  # the swarm may use 230 px above and below the centre line
        offsets = beeswarm([xs(v) for v in values], radius, first, radius + 7)
        if max(map(abs, offsets)) <= 230 or radius <= 3:
            break
        radius -= 1
    me = None
    for (row_id, name, value), offset in zip(rows, offsets):
        if row_id == subject:
            me = (name, value, xs(value), centre + offset)
            continue
        cv.circle(xs(value), centre + offset, radius, c.mut, alpha=0.45)
    # the axis: a baseline with about five round ticks
    axis_y = centre + 280
    cv.hairline(x0, x1, axis_y, alpha_scale=2)
    raw = span / 5
    magnitude = 10 ** math.floor(math.log10(raw))
    step = next(m * magnitude for m in (1, 2, 2.5, 5, 10) if m * magnitude >= raw)
    tick = math.ceil(low / step) * step
    while tick <= high + 1e-9:
        cv.line([xs(tick), xs(tick)], [axis_y, axis_y + 12], c.ink, 2, alpha=c.hair_alpha * 2)
        cv.text(xs(tick), axis_y + 48, 26, "C600", c.mut, number_text(tick, decimals, drop), anchor="middle")
        tick += step
    if slide.get("axis_title"):
        cv.text((x0 + x1) / 2, axis_y + 92, 22, "C600", c.mut, slide["axis_title"], anchor="middle", spacing=2.5)
    average = slide.get("average_line")
    if average:
        value = sum(values) / len(values) if average is True else average["value"]
        label = "AVERAGE" if average is True else average["label"]
        cv.line([xs(value), xs(value)], [centre - 250, axis_y], c.ink, 2, alpha=0.5, dashes=(8, 8))
        cv.text(xs(value), centre - 266, 22, "C600", c.mut, label, anchor="middle", spacing=2)
    # the subject on top: a larger dot with a ring, and its label above the swarm with a thin leader line
    name, value, sx, sy = me
    cv.circle(sx, sy, radius + 7, c.accent, stroke=c.bg, stroke_px=4)
    label_y = centre - 330
    cv.line([sx, sx], [label_y + 18, sy - radius - 10], c.ink, 2, alpha=0.6)
    anchor = "end" if sx > W - 300 else "start" if sx < 300 else "middle"
    cv.text(sx, label_y - 36, 34, "S600", c.ink, name, anchor=anchor)
    cv.text(sx, label_y + 4, 34, "C700", c.accent, number_text(value, decimals, drop), anchor=anchor)


def shot_map(cv, slide, ctx):
    """Where on the ice: a large half rink (the same drawing as the hook and turning point) with every unblocked shot
    attempt of a player or team in a date range, from the play-by-play. Shots in ink at low opacity (lower the more
    shots there are), goals in the accent on top. Real data, so no illustration label. An optional small count line
    at the bottom left (count_line: false leaves it out when the subtitle already says it)."""
    c = cv.c
    title_block(cv, slide)
    shots, own_half = shot_locations(ctx.con, slide["from"], slide["to"], slide.get("player_id"),
                                     slide.get("team_id"), slide.get("game_types", [2]))
    rw = 720
    rx, ry, s = (W - rw) / 2, 380, rw / 85
    rink_half(cv, rx, ry, rw, 0.3 if c.dark else 0.25, plain=True)
    misses = [(a, d) for a, d, goal in shots if not goal]
    goals = [(a, d) for a, d, goal in shots if goal]
    alpha = max(0.08, min(0.35, 0.35 * math.sqrt(300 / max(len(misses), 1))))
    for across, depth in misses:
        cv.circle(rx + across * s, ry + min(depth, 100) * s, 6, c.ink, alpha=alpha)
    for across, depth in goals:
        cv.circle(rx + across * s, ry + min(depth, 100) * s, 9, c.accent, stroke=c.bg, stroke_px=2)
    if slide.get("count_line", True):
        # bottom left, clear of the handle: the totals, then (if any) the attempts a half rink cannot show
        lines = [f"{len(shots):,} SHOT ATTEMPTS \u00b7 {len(goals):,} GOALS"]
        attempts, scored = own_half
        if attempts:
            lines.append(f"NOT SHOWN: {attempts:,} FROM THE OWN HALF"
                         + (f" ({scored:,} {'GOAL' if scored == 1 else 'GOALS'})" if scored else ""))
        for i, line in enumerate(reversed(lines)):
            cv.text(M, 1290 - 30 * i, 22, "C600", c.mut, line, spacing=2)


DRAW = {"hook": hook, "reveal": reveal, "comparison": comparison, "trend": trend, "turning_point": turning_point,
        "conclusion": conclusion, "statement": statement, "question": question, "guess": guess,
        "leaderboard": leaderboard, "distribution": distribution, "shot_map": shot_map}


# ---- Rendering ----

def posts_folder(name):
    folder = Path(os.environ.get("NHL_POSTS_DIR") or make_post.FILES_ROOT / "posts").resolve() / name
    if folder == make_post.REPO_ROOT or make_post.REPO_ROOT in folder.parents:
        raise SystemExit(f"The posts folder must be outside the repo, not {folder}")
    return folder


def caption_text(caption, credits):
    """The caption with every photo credit added after it, once each, unless the caption already has it."""
    text = str(caption).strip()
    extra = [credit for credit in dict.fromkeys(credits) if credit not in text]
    return text + ("\n" + "\n".join(extra) if extra else "") + "\n"


def render(con, carousel, handle, mode=None):
    """Draw every slide, save them as 01.png, 02.png ... and caption.txt; returns the paths."""
    font = make_post.fonts()
    ctx = SimpleNamespace(con=con, through=carousel.get("through"), credits=[], handle_on_photo=False)
    canvases = []
    for slide in carousel["slides"]:
        cv = Canvas(colours(slide_mode(carousel, slide["type"], mode), carousel.get("accent")), font)
        ctx.handle_on_photo = False
        DRAW[slide["type"]](cv, slide, ctx)
        cv.handle(handle, on_photo=ctx.handle_on_photo)
        canvases.append(cv)
    folder = posts_folder(carousel["name"])
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.png"):
        if re.fullmatch(r"\d{2}\.png", old.name):
            old.unlink()
    paths = []
    for number, cv in enumerate(canvases, start=1):
        path = folder / f"{number:02d}.png"
        cv.save(path)
        paths.append(path)
    caption = folder / "caption.txt"
    caption.write_text(caption_text(carousel["caption"], ctx.credits), encoding="utf-8")
    return paths + [caption]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["check", "render"])
    parser.add_argument("carousel", help="a YAML file in carousels/")
    parser.add_argument("--mode", choices=["light", "dark"], help="every slide light or dark (default: mixed)")
    parser.add_argument("--handle", default=os.environ.get("NHL_POST_HANDLE", "@topshelfstats"))
    args = parser.parse_args()

    carousel = load(args.carousel)
    handle = carousel.get("handle") or args.handle
    import duckdb

    con = duckdb.connect("md:nhl")
    try:
        results = check_facts(con, carousel)
        for claim, ok, got in results:
            print(f"{'ok  ' if ok else 'DIFF'}  {claim}" + ("" if ok else f"\n      query now gives: {got}"))
        failed = sum(not ok for _, ok, _ in results)
        print(f"{len(results) - failed} of {len(results)} facts match.")
        if failed:
            raise SystemExit(1)
        if args.action == "render":
            for path in render(con, carousel, handle, args.mode):
                print(f"Saved {path}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
