"""Make a 1080 x 1350 PNG for Instagram from the MotherDuck data, following style/style_guide.md and style/style.json.

Run it with:  uv run python -m instagram.make_post points-leaders --season 20262027 --top 5 --mode light --accent EDM

- --mode light|dark picks the Fresh Ice palette.
- --accent is the post's subject: a team code (EDM) or a country code (CAN) from style.json. Without it the default
  accent is used. As in the team mockups, the accent marks the leader (its bar and its number) and the label; bars use
  the accent shaded to 3:1 and text to 4.5:1 against the background (the contrast rule in the style guide).
- --handle is written on the right of the footer: @topshelfstats unless --handle or NHL_POST_HANDLE says otherwise.

Images are saved outside the repo: the folder in the environment variable NHL_POSTS_DIR, or nhl-data-files/posts in
your home folder. The fonts (Barlow and Barlow Condensed, free under the SIL Open Font License) are downloaded from
Google Fonts' GitHub repository the first time, into nhl-data-files/fonts.
"""

import argparse
import colorsys
import json
import os
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")  # draw to files only, no window
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from ingest.nhl_api import NhlApiClient  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
STYLE = json.loads((REPO_ROOT / "style" / "style.json").read_text(encoding="utf-8"))
FILES_ROOT = Path.home() / "nhl-data-files"

FONTS_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl"
FONT_FILES = {
    "title": "barlowcondensed/BarlowCondensed-Bold.ttf",       # title and label
    "footer": "barlowcondensed/BarlowCondensed-SemiBold.ttf",  # footer line
    "name": "barlow/Barlow-SemiBold.ttf",                      # names
    "number": "barlow/Barlow-Bold.ttf",                        # numbers
    "body": "barlow/Barlow-Regular.ttf",                       # subtitle
    # Story carousels (instagram/carousel.py)
    "hero": "barlowcondensed/BarlowCondensed-ExtraBold.ttf",   # the huge numbers
    "medium": "barlow/Barlow-Medium.ttf",                      # subtitles and context lines
    "semi": "barlowsemicondensed/BarlowSemiCondensed-SemiBold.ttf",  # short lines and chart labels
}

# Sizes in pixels, scaled from the team mockups (a 340 px wide card) to 1080 px: about 3.18 times.
PAD_TOP, PAD_SIDE, PAD_BOTTOM = 57, 51, 38
LABEL_PX, TITLE_PX, SUBTITLE_PX = 35, 83, 38
ROW_TEXT_PX, TRACK_PX, TRACK_RADIUS_PX, ROW_GAP_PX = 38, 29, 6, 29
FOOTER_PX = 32
LABEL_TRACKING = 0.1  # letter spacing of the label, in em


# ---- Colours and the contrast rule ----

def _rgb(hex_colour):
    return [int(hex_colour[i:i + 2], 16) for i in (1, 3, 5)]


def _hex(rgb):
    return "#" + "".join(f"{round(v):02X}" for v in rgb)


def luminance(hex_colour):
    """WCAG relative luminance."""
    channels = []
    for value in _rgb(hex_colour):
        value /= 255
        channels.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(a, b):
    """WCAG contrast ratio between two colours, from 1 to 21."""
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def readable(accent, background, minimum):
    """The accent, mixed toward black (light background) or white (dark background) in 4% steps until its contrast
    with the background reaches the minimum. Mixing toward black or white keeps the hue."""
    if contrast(accent, background) >= minimum:
        return accent
    target = [0, 0, 0] if luminance(background) > 0.5 else [255, 255, 255]
    base = _rgb(accent)
    for step in range(1, 26):
        mixed = _hex([v + (t - v) * step * 0.04 for v, t in zip(base, target)])
        if contrast(mixed, background) >= minimum:
            return mixed
    return _hex(target)


def palette(mode, accent_code):
    """The Fresh Ice colours for the mode, with the subject's accent made readable for bars and for text."""
    colours = dict(STYLE["palettes"][f"fresh_ice_{mode}"])
    if accent_code is None:
        accent = colours["default_accent"]
    else:
        code = accent_code.upper()
        known = {**STYLE["team_accents"], **STYLE["country_accents"]}
        if code not in known:
            raise SystemExit(f"Unknown --accent {accent_code}: use one of {', '.join(sorted(known))}")
        accent = known[code]["accent"]
    colours["accent"] = colours["accent_shape"] = colours["accent_text"] = one_shade(accent)
    return colours


def backgrounds():
    """Every background accent colour can sit on: both palettes and both comparison panels."""
    return [STYLE["palettes"][f"fresh_ice_{m}"]["background"] for m in ("light", "dark")] + list(
        STYLE["story"]["comparison_panel"].values())


def one_shade(accent):
    """The single shade of the accent used on light and dark slides alike, so a carousel's accent never changes.
    A colour with the minimum contrast on every background is kept. Otherwise its lightness moves (same hue and
    saturation) to the shade whose lowest contrast across the backgrounds is highest. No colour reaches 4.5:1 on
    both a light and a dark background; the best is about 4:1, and 3:1 is the WCAG minimum for large text."""
    bgs = backgrounds()
    worst = lambda colour: min(contrast(colour, bg) for bg in bgs)  # noqa: E731
    if worst(accent) >= STYLE["accent_rule"]["min_contrast"]:
        return accent
    hue, _, saturation = colorsys.rgb_to_hls(*(v / 255 for v in _rgb(accent)))
    shades = [_hex([v * 255 for v in colorsys.hls_to_rgb(hue, step / 200, saturation)]) for step in range(201)]
    return max(shades, key=worst)


# ---- Fonts ----

def fonts():
    """{role: FontProperties}, downloading the font files once."""
    folder = FILES_ROOT / "fonts"
    folder.mkdir(parents=True, exist_ok=True)
    missing = [f for f in FONT_FILES.values() if not (folder / Path(f).name).exists()]
    if missing:
        client = NhlApiClient()
        try:
            for file in missing:
                (folder / Path(file).name).write_bytes(client.fetch_bytes(f"{FONTS_URL}/{file}"))
        finally:
            client.close()
    return {role: FontProperties(fname=folder / Path(file).name) for role, file in FONT_FILES.items()}


# ---- Data ----

def points_leaders(con, season, top, through=None, with_ids=False):
    """The regular season's points leaders, goalies included (D15), and the last game date counted. With through
    (a date), only games up to that date count. With with_ids, each row is (player_id, name, points)."""
    query = """
        with scoring as (
            select player_id, goals, assists, game_date
            from marts.fct_skater_games where season = $season and game_type = 2
            union all
            select player_id, coalesce(goals, 0), coalesce(assists, 0), game_date
            from marts.fct_goalie_games where season = $season and game_type = 2
        )
        select scoring.player_id, players.full_name, sum(scoring.goals + scoring.assists) as points,
            sum(scoring.goals) as goals, max(max(scoring.game_date)) over () as through
        from scoring
        inner join marts.dim_players as players on players.player_id = scoring.player_id
        where $through is null or scoring.game_date <= $through
        group by scoring.player_id, players.full_name
        order by points desc, goals desc, players.full_name
        limit $top
    """
    rows = con.execute(query, {"season": season, "top": top, "through": through}).fetchall()
    if not rows:
        raise SystemExit(f"No regular-season points found for season {season}")
    if with_ids:
        return [(player_id, name, points) for player_id, name, points, _, _ in rows], rows[0][4]
    return [(name, points) for _, name, points, _, _ in rows], rows[0][4]


def season_label(season):
    return f"{season // 10000}-{season % 100:02d}"


# ---- Drawing ----

def _pt(pixels):
    """Font size in points for a size in pixels (the figure is drawn at 100 dots per inch)."""
    return pixels * 72 / 100


def new_canvas(colours):
    width, height = STYLE["canvas"]["width_px"], STYLE["canvas"]["height_px"]
    fig = plt.figure(figsize=(width / 100, height / 100), dpi=100, facecolor=colours["background"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)  # y grows downwards, like a web page
    ax.axis("off")
    return fig, ax


def _sized(font, size_px):
    sized = font.copy()
    sized.set_size(_pt(size_px))
    return sized


def text_width(fig, text, font, size_px):
    """Width in pixels of text drawn in this font and size."""
    renderer = fig.canvas.get_renderer()
    width, _, _ = renderer.get_text_width_height_descent(text, _sized(font, size_px), ismath=False)
    return width


def spaced_text(ax, fig, x, y, text, font, size_px, colour, tracking_em):
    """Text with letter spacing (matplotlib has none): each character is placed after the width of the text before
    it, plus the spacing, so the font's own kerning is kept."""
    spacing = tracking_em * size_px
    for i, char in enumerate(text):
        offset = text_width(fig, text[:i], font, size_px) if i else 0
        ax.text(x + offset + i * spacing, y, char, fontproperties=_sized(font, size_px), color=colour, va="baseline")


def header_and_footer(ax, fig, colours, font, label, title, subtitle, handle):
    """Label, title, optional subtitle at the top; "Data: NHL" and the handle at the bottom. Returns the y below them."""
    width, height = STYLE["canvas"]["width_px"], STYLE["canvas"]["height_px"]
    y = PAD_TOP + LABEL_PX * 0.8
    spaced_text(ax, fig, PAD_SIDE, y, label.upper(), font["title"], LABEL_PX, colours["accent_text"], LABEL_TRACKING)
    y += 25 + TITLE_PX * 0.85
    ax.text(PAD_SIDE, y, title, fontproperties=_sized(font["title"], TITLE_PX), color=colours["ink"], va="baseline")
    if subtitle:
        y += 25 + SUBTITLE_PX * 0.9
        ax.text(PAD_SIDE, y, subtitle, fontproperties=_sized(font["body"], SUBTITLE_PX), color=colours["muted_text"],
                va="baseline")
    footer_y = height - PAD_BOTTOM
    footer = _sized(font["footer"], FOOTER_PX)
    ax.text(PAD_SIDE, footer_y, "Data: NHL", fontproperties=footer, color=colours["muted_text"], va="baseline")
    if handle:
        ax.text(width - PAD_SIDE, footer_y, handle, fontproperties=footer, color=colours["muted_text"], va="baseline",
                ha="right")
    return footer_y


def bar_rows(ax, colours, font, rows, bottom, highlight=0):
    """Leaderboard rows sitting just above the footer: name and value, then a bar on a track. The highlighted row's
    bar and number (the leader unless told otherwise) get the accent; every other bar, every name and the other
    numbers are ink."""
    width = STYLE["canvas"]["width_px"]
    content = width - 2 * PAD_SIDE
    row_height = ROW_TEXT_PX * 1.55 + 6 + TRACK_PX
    top = bottom - FOOTER_PX - 25 - len(rows) * row_height - (len(rows) - 1) * ROW_GAP_PX
    biggest = max(value for _, value in rows) or 1
    for i, (name, value) in enumerate(rows):
        y = top + i * (row_height + ROW_GAP_PX)
        baseline = y + ROW_TEXT_PX * 1.2
        ax.text(PAD_SIDE, baseline, name, fontproperties=_sized(font["name"], ROW_TEXT_PX), color=colours["ink"],
                va="baseline")
        ax.text(width - PAD_SIDE, baseline, f"{value}", fontproperties=_sized(font["number"], ROW_TEXT_PX),
                color=colours["accent_text"] if i == highlight else colours["ink"], va="baseline", ha="right")
        track_y = y + ROW_TEXT_PX * 1.55 + 6
        bar_colour = colours["accent_shape"] if i == highlight else colours["ink"]
        for bar_width, colour in ((content, colours["bar_track"]), (content * value / biggest, bar_colour)):
            ax.add_patch(FancyBboxPatch((PAD_SIDE, track_y), bar_width, TRACK_PX, linewidth=0, facecolor=colour,
                                        boxstyle=f"round,pad=0,rounding_size={TRACK_RADIUS_PX}"))


def save(fig, name):
    folder = Path(os.environ.get("NHL_POSTS_DIR") or FILES_ROOT / "posts").resolve()
    if folder == REPO_ROOT or REPO_ROOT in folder.parents:
        raise SystemExit(f"The posts folder must be outside the repo, not {folder}")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.png"
    fig.savefig(path, dpi=100, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


# ---- Posts ----

def post_points_leaders(con, args, colours, font):
    rows, through = points_leaders(con, args.season, args.top)
    fig, ax = new_canvas(colours)
    subtitle = f"Top {args.top} · games through {through.day} {through:%B %Y}"
    bottom = header_and_footer(ax, fig, colours, font, f"{season_label(args.season)} · Regular season",
                               "Points leaders", subtitle, args.handle)
    bar_rows(ax, colours, font, rows, bottom)
    return save(fig, f"points-leaders-{args.season}-top{args.top}-{args.mode}-{(args.accent or 'default').upper()}")


POSTS = {"points-leaders": post_points_leaders}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("post", choices=sorted(POSTS))
    parser.add_argument("--season", type=int, required=True, help="for example 20262027")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--mode", choices=["light", "dark"], required=True)
    parser.add_argument("--accent", help="team code (EDM) or country code (CAN)")
    parser.add_argument("--handle", default=os.environ.get("NHL_POST_HANDLE", "@topshelfstats"))
    args = parser.parse_args()

    colours = palette(args.mode, args.accent)
    font = fonts()
    con = duckdb.connect("md:nhl")
    try:
        path = POSTS[args.post](con, args, colours, font)
    finally:
        con.close()
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
