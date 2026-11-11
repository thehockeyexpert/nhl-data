"""The chart library for carousel slides (instagram/carousel.py).

Each chart reads MotherDuck and draws into the space between a slide's header and its footer. A chart slide in a
carousel names the chart and gives its settings, for example:

    - type: chart
      chart: points_leaders
      season: 20262027
      top: 5

Every chart also gets the carousel's `through` date, when it has one: only games up to that date count, so the chart
shows the same numbers as the text written for it.

The accent rule (style/style_guide.md): exactly one thing per chart gets the accent; everything else is ink.

Charts:
- points_leaders: a season's regular-season points leaders, goalies included (D15). Settings: season, top (5),
  highlight (a player_id; the leader if left out).
- points_histogram: one player's regular-season games by points scored: 0, 1, 2, 3, 4 and 5 or more. Settings:
  player_id, season (all seasons if left out), highlight (a bucket from 0 to 5; the tallest if left out).
- goals_per_game: a line of goals per game, season by season, regular season. Settings: player_id (the league if
  left out: all goals per game played, shootouts left out), from_season, to_season. The latest point gets the accent.
- birthplaces_donut: where players were born, by country (`birth_country`, D24), as shares of a donut. Settings:
  season (the players who played a regular-season game that season; every NHL player if left out), top (5 countries,
  the rest grouped as Other), highlight (a country code; the carousel's accent if it is a country, else the biggest).
  Uses the NHL's birth country only, not GeoNames coordinates, so no GeoNames credit is needed.
"""

import math

from matplotlib.patches import FancyBboxPatch, Wedge
from matplotlib.ticker import MaxNLocator

from instagram.make_post import (
    FOOTER_PX,
    PAD_SIDE,
    ROW_GAP_PX,
    ROW_TEXT_PX,
    TRACK_PX,
    STYLE,
    _sized,
    bar_rows,
    points_leaders as leaders_query,
    season_label,
)

COUNTRY_NAMES = {
    "AUT": "Austria", "BLR": "Belarus", "CAN": "Canada", "CHE": "Switzerland", "CZE": "Czechia", "DEU": "Germany",
    "DNK": "Denmark", "FIN": "Finland", "FRA": "France", "GBR": "Great Britain", "LVA": "Latvia", "NOR": "Norway",
    "RUS": "Russia", "SVK": "Slovakia", "SVN": "Slovenia", "SWE": "Sweden", "UKR": "Ukraine", "USA": "United States",
}

CHARTS = {}


def chart(function):
    """Register a chart under its function name."""
    CHARTS[function.__name__] = function
    return function


def _width():
    return STYLE["canvas"]["width_px"]


def _text(c, x, y, text, role, size_px, colour, **kwargs):
    c.ax.text(x, y, text, fontproperties=_sized(c.font[role], size_px), color=colour, va="baseline", **kwargs)


def _px_to_pt(pixels):
    return pixels * 72 / 100


# ---- points_leaders ----

@chart
def points_leaders(c, con, top_y, bottom_y, through, season, top=5, highlight=None):
    rows, _ = leaders_query(con, season, top, through=through, with_ids=True)
    index = 0
    if highlight is not None:
        ids = [player_id for player_id, _, _ in rows]
        if highlight not in ids:
            raise SystemExit(f"points_leaders: player {highlight} is not in the top {top} of {season}")
        index = ids.index(highlight)
    # bar_rows stacks its rows up from the bottom it is given; give it a bottom that centres them in the free space.
    block = len(rows) * (ROW_TEXT_PX * 1.55 + 6 + TRACK_PX) + (len(rows) - 1) * ROW_GAP_PX
    free_top, free_bottom = top_y + 30, bottom_y - FOOTER_PX - 25
    bottom = free_bottom - max(0, (free_bottom - free_top - block) / 2) + FOOTER_PX + 25
    bar_rows(c.ax, c.colours, c.font, [(name, points) for _, name, points in rows], bottom, highlight=index)


# ---- points_histogram ----

def histogram_counts(con, player_id, season=None, through=None):
    """[games with 0 points, 1, 2, 3, 4, 5 or more], regular season."""
    rows = con.execute(
        """
        select least(points, 5) as bucket, count(*) as games
        from marts.fct_skater_games
        where player_id = $player and game_type = 2
            and ($season is null or season = $season)
            and ($through is null or game_date <= $through)
        group by all
        """,
        {"player": player_id, "season": season, "through": through},
    ).fetchall()
    counts = [0] * 6
    for bucket, games in rows:
        counts[bucket] = games
    if not sum(counts):
        raise SystemExit(f"points_histogram: no regular-season games for player {player_id}")
    return counts


@chart
def points_histogram(c, con, top_y, bottom_y, through, player_id, season=None, highlight=None):
    counts = histogram_counts(con, player_id, season, through)
    if highlight is None:
        highlight = counts.index(max(counts))
    if highlight not in range(6):
        raise SystemExit("points_histogram: highlight must be a bucket from 0 to 5")
    width = _width()
    caption_y = bottom_y - 32 - 40
    label_y = caption_y - 70
    base_y = label_y - 55
    peak_y = top_y + 110
    slot = (width - 2 * PAD_SIDE) / 6
    bar_w = slot * 0.62
    biggest = max(counts)
    c.ax.plot([PAD_SIDE, width - PAD_SIDE], [base_y, base_y], color=c.colours["grid"], linewidth=_px_to_pt(3),
              solid_capstyle="butt")
    for bucket, games in enumerate(counts):
        centre = PAD_SIDE + slot * (bucket + 0.5)
        is_hl = bucket == highlight
        height = (base_y - peak_y) * games / biggest
        if height:
            c.ax.add_patch(FancyBboxPatch((centre - bar_w / 2, base_y - height), bar_w, height, linewidth=0,
                                          facecolor=c.colours["accent_shape"] if is_hl else c.colours["ink"],
                                          boxstyle=f"round,pad=0,rounding_size={min(10, height / 2)}"))
        _text(c, centre, base_y - height - 18, f"{games}", "number", 46,
              c.colours["accent_text"] if is_hl else c.colours["ink"], ha="center")
        _text(c, centre, label_y, "5+" if bucket == 5 else f"{bucket}", "name", 44, c.colours["muted_text"],
              ha="center")
    _text(c, width / 2, caption_y, "Points in the game", "body", 32, c.colours["muted_text"], ha="center")


# ---- goals_per_game ----

def goals_per_game_series(con, player_id=None, from_season=None, to_season=None, through=None):
    """[(season, goals per game)], regular season. A player: goals / games played. The league: all goals scored
    (skaters and goalies, shootouts left out) / games played."""
    filters = """game_type = 2 and ($from is null or season >= $from) and ($to is null or season <= $to)
        and ($through is null or game_date <= $through)"""
    params = {"from": from_season, "to": to_season, "through": through}
    if player_id is not None:
        query = f"""
            select season, sum(goals) / count(*) from marts.fct_skater_games
            where player_id = $player and {filters} group by season order by season
        """
        params["player"] = player_id
    else:
        query = f"""
            with goals as (
                select season, goals, game_id from marts.fct_skater_games where {filters}
                union all
                select season, coalesce(goals, 0), game_id from marts.fct_goalie_games where {filters}
            )
            select season, sum(goals) / count(distinct game_id) from goals group by season order by season
        """
    rows = con.execute(query, params).fetchall()
    if not rows:
        raise SystemExit("goals_per_game: no regular-season games in that range")
    return [(season, float(rate)) for season, rate in rows]


@chart
def goals_per_game(c, con, top_y, bottom_y, through, player_id=None, from_season=None, to_season=None):
    series = goals_per_game_series(con, player_id, from_season, to_season, through)
    width = _width()
    left, right = PAD_SIDE + 70, width - PAD_SIDE - 20
    top, base = top_y + 110, bottom_y - 32 - 110
    values = [rate for _, rate in series]
    ticks = [t for t in MaxNLocator(nbins=4, min_n_ticks=3).tick_values(0, max(values)) if t >= 0]
    y_max = ticks[-1] if ticks[-1] >= max(values) else max(values)

    def y_of(value):
        return base - (base - top) * value / y_max

    def x_of(i):
        return left + (right - left) * (i / (len(series) - 1) if len(series) > 1 else 0.5)

    for tick in ticks:
        c.ax.plot([left, right], [y_of(tick), y_of(tick)], color=c.colours["grid"], linewidth=_px_to_pt(2))
        _text(c, left - 18, y_of(tick) + 12, f"{tick:.2f}".rstrip("0").rstrip(".") if tick else "0", "name", 32,
              c.colours["muted_text"], ha="right")
    shown = sorted({0, len(series) - 1, *range(0, len(series), max(1, math.ceil(len(series) / 5)))})
    if len(shown) > 2 and shown[-1] - shown[-2] < max(1, math.ceil(len(series) / 5)) / 2:
        shown.pop(-2)  # keep the last season's label clear of the one before it
    for i in shown:
        # the first and last labels line up with the ends of the line, so they stay inside the canvas
        align = "left" if i == 0 and len(series) > 1 else "right" if i == len(series) - 1 and i else "center"
        x = x_of(i) - 12 if align == "left" else x_of(i) + 12 if align == "right" else x_of(i)
        _text(c, x, base + 50, season_label(series[i][0]), "name", 30, c.colours["muted_text"], ha=align)
    xs = [x_of(i) for i in range(len(series))]
    ys = [y_of(v) for v in values]
    c.ax.plot(xs, ys, color=c.colours["ink"], linewidth=_px_to_pt(6), solid_joinstyle="round",
              solid_capstyle="round")
    c.ax.plot(xs[:-1], ys[:-1], "o", color=c.colours["ink"], markersize=_px_to_pt(14))
    c.ax.plot(xs[-1], ys[-1], "o", color=c.colours["accent_shape"], markersize=_px_to_pt(28))
    _text(c, xs[-1], ys[-1] - 34, f"{values[-1]:.2f}", "number", 46, c.colours["accent_text"],
          ha="right" if len(series) > 1 else "center")


# ---- birthplaces_donut ----

def birth_country_counts(con, season=None, through=None):
    """[(country code, players)], biggest first. Players who played a regular-season game in the season, or every
    NHL player (D15) when no season is given. Players with no birth country are left out."""
    if season is None:
        query = """
            select birth_country, count(*) from marts.dim_players
            where is_nhl_player and birth_country is not null group by all order by 2 desc, 1
        """
        params = {}
    else:
        query = """
            with played as (
                select player_id from marts.fct_skater_games
                where season = $season and game_type = 2 and ($through is null or game_date <= $through)
                union
                select player_id from marts.fct_goalie_games
                where season = $season and game_type = 2 and ($through is null or game_date <= $through)
            )
            select players.birth_country, count(*) from played
            inner join marts.dim_players as players using (player_id)
            where players.birth_country is not null group by all order by 2 desc, 1
        """
        params = {"season": season, "through": through}
    rows = con.execute(query, params).fetchall()
    if not rows:
        raise SystemExit("birthplaces_donut: no players found")
    return rows


@chart
def birthplaces_donut(c, con, top_y, bottom_y, through, season=None, top=5, highlight=None):
    rows = birth_country_counts(con, season, through)
    shown, rest = rows[:top], sum(n for _, n in rows[top:])
    total = sum(n for _, n in rows)
    if highlight is None:
        highlight = c.accent_code if c.accent_code in {code for code, _ in shown} else shown[0][0]
    if highlight not in {code for code, _ in shown}:
        raise SystemExit(f"birthplaces_donut: {highlight} is not in the top {top} countries")
    slices = shown + ([("Other", rest)] if rest else [])

    width = _width()
    radius = 230
    centre = (width / 2, top_y + 80 + radius)
    angle = -90.0  # start at the top; y grows downwards, so angles run clockwise on screen
    for code, players in slices:
        sweep = 360 * players / total
        colour = (c.colours["accent_shape"] if code == highlight
                  else c.colours["bar_track"] if code == "Other" else c.colours["ink"])
        c.ax.add_patch(Wedge(centre, radius, angle, angle + sweep, width=radius * 0.36, facecolor=colour,
                             edgecolor=c.colours["background"], linewidth=_px_to_pt(6)))
        angle += sweep
    share = dict(slices)[highlight] / total
    _text(c, centre[0], centre[1] + 22, f"{share:.0%}", "number", 84, c.colours["accent_text"], ha="center")
    _text(c, centre[0], centre[1] + 72, COUNTRY_NAMES.get(highlight, highlight), "name", 32,
          c.colours["muted_text"], ha="center")

    row_px, gap = 40, 22
    y = centre[1] + radius + 90
    for code, players in slices:
        is_hl = code == highlight
        swatch = (c.colours["accent_shape"] if is_hl
                  else c.colours["bar_track"] if code == "Other" else c.colours["ink"])
        c.ax.add_patch(FancyBboxPatch((PAD_SIDE, y - 28), 28, 28, linewidth=0, facecolor=swatch,
                                      boxstyle="round,pad=0,rounding_size=6"))
        _text(c, PAD_SIDE + 50, y, COUNTRY_NAMES.get(code, code), "name", row_px, c.colours["ink"])
        _text(c, width - PAD_SIDE, y, f"{players:,}  ·  {players / total:.0%}", "number", row_px,
              c.colours["accent_text"] if is_hl else c.colours["ink"], ha="right")
        y += row_px + gap
