"""Render an Instagram carousel: a YAML file in carousels/ becomes one 1080 x 1350 PNG per slide.

Check the facts only:  uv run python -m instagram.carousel check carousels/mcdavid-hot-start.yml
Render every slide:    uv run python -m instagram.carousel render carousels/mcdavid-hot-start.yml

- The slides are saved outside the repo, in posts/<carousel name>/01.png, 02.png and so on: the folder in the
  environment variable NHL_POSTS_DIR, or nhl-data-files/posts in your home folder. Old slides in that folder are
  replaced, so a carousel that loses a slide does not keep a stale last image.
- Before drawing anything, `render` runs every query under `facts:` again and stops if any answer differs from the
  value written in the file. So the words on the slides can't drift away from the data.
- --handle is written on the right of the footer: @topshelfstats unless --handle or NHL_POST_HANDLE says otherwise.
- The format of a carousel file is described in carousels/README.md.
"""

import argparse
import datetime
import os
import re
from pathlib import Path
from types import SimpleNamespace

import yaml

from instagram import make_post
from instagram.charts import CHARTS
from instagram.make_post import (
    FOOTER_PX,
    LABEL_PX,
    LABEL_TRACKING,
    PAD_BOTTOM,
    PAD_SIDE,
    PAD_TOP,
    STYLE,
    SUBTITLE_PX,
    TITLE_PX,
    _sized,
    spaced_text,
    text_width,
)

SLIDE_TYPES = {"title", "chart", "text", "end"}
SLIDE_KEYS = {"type", "title", "subtitle", "body", "label", "chart", "mode"}
CAROUSEL_KEYS = {"accent", "mode", "label", "through", "handle", "slides", "facts"}
# light or dark for every slide; dark-light and light-dark alternate, starting with the first one named
MODES = {"light": ("light",), "dark": ("dark",), "dark-light": ("dark", "light"), "light-dark": ("light", "dark")}

COVER_TITLE_PX = 132  # the big title on title and end slides
BODY_PX, BODY_LINE = 46, 1.4  # text slides


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
        return ["the file must be a mapping with accent, mode and slides"]
    problems = [f"unknown key '{key}'" for key in data if key not in CAROUSEL_KEYS]
    if data.get("mode") not in MODES:
        problems.append(f"mode must be one of {', '.join(MODES)}")
    known = {**STYLE["team_accents"], **STYLE["country_accents"]}
    if data.get("accent") is not None and str(data["accent"]).upper() not in known:
        problems.append(f"unknown accent {data['accent']}")
    if data.get("through") is not None and not isinstance(data["through"], datetime.date):
        problems.append("through must be a date, for example 2026-11-09")
    slides = data.get("slides")
    if not isinstance(slides, list) or not slides:
        return problems + ["slides must be a list with at least one slide"]
    for number, slide in enumerate(slides, start=1):
        where = f"slide {number}"
        if not isinstance(slide, dict):
            problems.append(f"{where}: must be a mapping")
            continue
        if slide.get("type") not in SLIDE_TYPES:
            problems.append(f"{where}: type must be one of {', '.join(sorted(SLIDE_TYPES))}")
        if not slide.get("title"):
            problems.append(f"{where}: needs a title")
        if "mode" in slide and slide["mode"] not in ("light", "dark"):
            problems.append(f"{where}: mode must be light or dark")
        if slide.get("type") == "chart":
            if slide.get("chart") not in CHARTS:
                problems.append(f"{where}: chart must be one of {', '.join(sorted(CHARTS))}")
        else:
            extra = [key for key in slide if key not in SLIDE_KEYS - {"chart"}]  # chart settings only on charts
            problems += [f"{where}: unknown key '{key}'" for key in extra]
    for number, fact in enumerate(data.get("facts") or [], start=1):
        if not isinstance(fact, dict) or not {"claim", "sql", "value"} <= set(fact):
            problems.append(f"fact {number}: needs claim, sql and value")
    return problems


def chart_settings(slide):
    """The chart's own settings: every key of a chart slide that is not a slide key."""
    return {key: value for key, value in slide.items() if key not in SLIDE_KEYS}


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


# ---- Drawing ----

def wrap(fig, text, font, size_px, max_width):
    """Lines of text no wider than max_width pixels, broken between words."""
    lines = []
    for paragraph in str(text).split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if line and text_width(fig, candidate, font, size_px) > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines


def draw_lines(c, x, y, lines, role, size_px, colour, line_height):
    """Draw lines from the baseline y down; returns the baseline after the last line."""
    for line in lines:
        c.ax.text(x, y, line, fontproperties=_sized(c.font[role], size_px), color=colour, va="baseline")
        y += size_px * line_height
    return y - size_px * line_height


def frame(c, label, counter, handle):
    """Label (top left), slide counter (top right), and the footer: "Data: NHL" left, the handle right.
    Returns (baseline of the label, baseline of the footer)."""
    width, height = STYLE["canvas"]["width_px"], STYLE["canvas"]["height_px"]
    label_y = PAD_TOP + LABEL_PX * 0.8
    spaced_text(c.ax, c.fig, PAD_SIDE, label_y, label.upper(), c.font["title"], LABEL_PX, c.colours["accent_text"],
                LABEL_TRACKING)
    small = _sized(c.font["footer"], FOOTER_PX)
    c.ax.text(width - PAD_SIDE, label_y, counter, fontproperties=small, color=c.colours["muted_text"],
              va="baseline", ha="right")
    footer_y = height - PAD_BOTTOM
    c.ax.text(PAD_SIDE, footer_y, "Data: NHL", fontproperties=small, color=c.colours["muted_text"], va="baseline")
    if handle:
        c.ax.text(width - PAD_SIDE, footer_y, handle, fontproperties=small, color=c.colours["muted_text"],
                  va="baseline", ha="right")
    return label_y, footer_y


def heading(c, top_y, title, subtitle):
    """Title (wrapped) and optional subtitle under the label; returns the y below them."""
    content = STYLE["canvas"]["width_px"] - 2 * PAD_SIDE
    y = top_y + 25 + TITLE_PX * 0.85
    y = draw_lines(c, PAD_SIDE, y, wrap(c.fig, title, c.font["title"], TITLE_PX, content), "title", TITLE_PX,
                   c.colours["ink"], 0.95)
    if subtitle:
        y += 25 + SUBTITLE_PX * 0.9
        y = draw_lines(c, PAD_SIDE, y, wrap(c.fig, subtitle, c.font["body"], SUBTITLE_PX, content), "body",
                       SUBTITLE_PX, c.colours["muted_text"], 1.25)
    return y + 20


def cover(c, title, subtitle):
    """Title and end slides: a big title and its subtitle or body, set a little above the middle."""
    width, height = STYLE["canvas"]["width_px"], STYLE["canvas"]["height_px"]
    content = width - 2 * PAD_SIDE
    title_lines = wrap(c.fig, title, c.font["title"], COVER_TITLE_PX, content)
    sub_lines = wrap(c.fig, subtitle, c.font["body"], BODY_PX, content) if subtitle else []
    block = len(title_lines) * COVER_TITLE_PX * 0.95 + (len(sub_lines) * BODY_PX * 1.3 + 40 if sub_lines else 0)
    y = (height - block) / 2 - 40 + COVER_TITLE_PX * 0.8
    y = draw_lines(c, PAD_SIDE, y, title_lines, "title", COVER_TITLE_PX, c.colours["ink"], 0.95)
    if sub_lines:
        draw_lines(c, PAD_SIDE, y + 40 + BODY_PX * 1.1, sub_lines, "body", BODY_PX, c.colours["muted_text"], 1.3)


def body_text(c, top_y, body):
    """Paragraphs separated by blank lines; a line starting with "- " is a bullet."""
    content = STYLE["canvas"]["width_px"] - 2 * PAD_SIDE
    indent = 40
    y = top_y + 40 + BODY_PX
    for paragraph in str(body).strip().split("\n\n"):
        for line in paragraph.split("\n"):
            if line.startswith("- "):
                c.ax.text(PAD_SIDE, y, "•", fontproperties=_sized(c.font["number"], BODY_PX),
                          color=c.colours["muted_text"], va="baseline")
                lines = wrap(c.fig, line[2:], c.font["body"], BODY_PX, content - indent)
                y = draw_lines(c, PAD_SIDE + indent, y, lines, "body", BODY_PX, c.colours["ink"], BODY_LINE)
                y += BODY_PX * (BODY_LINE + 0.15)
            else:
                lines = wrap(c.fig, line, c.font["body"], BODY_PX, content)
                y = draw_lines(c, PAD_SIDE, y, lines, "body", BODY_PX, c.colours["ink"], BODY_LINE)
                y += BODY_PX * BODY_LINE
        y += BODY_PX * 0.5


def render_slide(con, carousel, slide, number, total, colours, font, handle):
    fig, ax = make_post.new_canvas(colours)
    accent = carousel.get("accent")
    c = SimpleNamespace(fig=fig, ax=ax, colours=colours, font=font,
                        accent_code=str(accent).upper() if accent else None)
    label = slide.get("label") or carousel.get("label") or ""
    label_y, footer_y = frame(c, label, f"{number}/{total}", handle)
    kind = slide["type"]
    if kind in ("title", "end"):
        cover(c, slide["title"], slide.get("subtitle") or slide.get("body"))
    elif kind == "text":
        y = heading(c, label_y, slide["title"], slide.get("subtitle"))
        if slide.get("body"):
            body_text(c, y, slide["body"])
    else:
        y = heading(c, label_y, slide["title"], slide.get("subtitle"))
        settings = chart_settings(slide)
        try:
            CHARTS[slide["chart"]](c, con, y, footer_y, carousel.get("through"), **settings)
        except TypeError as error:
            raise CarouselError(f"slide {number} ({slide['chart']}): {error}") from None
    return fig


def slide_mode(carousel, number):
    """light or dark for slide number (from 1): the slide's own mode, else the carousel's, alternating if it says so."""
    own = carousel["slides"][number - 1].get("mode")
    if own:
        return own
    cycle = MODES[carousel["mode"]]
    return cycle[(number - 1) % len(cycle)]


def posts_folder(name):
    folder = Path(os.environ.get("NHL_POSTS_DIR") or make_post.FILES_ROOT / "posts").resolve() / name
    if folder == make_post.REPO_ROOT or make_post.REPO_ROOT in folder.parents:
        raise SystemExit(f"The posts folder must be outside the repo, not {folder}")
    return folder


def render(con, carousel, handle):
    """Draw every slide and save them; returns the paths."""
    palettes = {mode: make_post.palette(mode, carousel.get("accent")) for mode in ("light", "dark")}
    font = make_post.fonts()
    folder = posts_folder(carousel["name"])
    folder.mkdir(parents=True, exist_ok=True)
    total = len(carousel["slides"])
    figures = [render_slide(con, carousel, slide, number, total, palettes[slide_mode(carousel, number)], font, handle)
               for number, slide in enumerate(carousel["slides"], start=1)]
    for old in folder.glob("*.png"):
        if re.fullmatch(r"\d{2}\.png", old.name):
            old.unlink()
    paths = []
    for number, fig in enumerate(figures, start=1):
        path = folder / f"{number:02d}.png"
        fig.savefig(path, dpi=100, facecolor=fig.get_facecolor())
        make_post.plt.close(fig)
        paths.append(path)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=["check", "render"])
    parser.add_argument("carousel", help="a YAML file in carousels/")
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
            for path in render(con, carousel, handle):
                print(f"Saved {path}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
