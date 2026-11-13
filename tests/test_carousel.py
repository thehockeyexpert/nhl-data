import datetime
from decimal import Decimal

import duckdb
import pytest

from instagram import carousel

SIX = [
    {"type": "hook", "kicker": "K", "headline": ["A", "B", "C"]},
    {"type": "reveal", "number": 48, "label": ["POINTS IN", "19 GAMES"], "name": "N"},
    {"type": "comparison", "top": {"kicker": "K", "number": 48}, "bottom": {"kicker": "K", "number": 40}},
    {"type": "trend", "title": "T", "games": 3, "lines": [{"player_id": 1, "season": 20262027, "name": "A"}]},
    {"type": "turning_point", "title": "T", "stats": [{"value": "1", "label": ["A", "B"]}]},
    {"type": "conclusion", "kicker": "K", "headline": ["A", "B"]},
]


def story(**overrides):
    data = {"accent": "EDM", "caption": "Words. Data: NHL.", "slides": [dict(s) for s in SIX],
            "facts": [{"claim": "c", "sql": "select 1", "value": 1}]}
    data.update(overrides)
    return data


def test_a_six_slide_story_is_valid():
    assert carousel.validate(story()) == []


def test_slides_come_in_any_order_and_may_repeat():
    assert carousel.validate(story(slides=[dict(s) for s in SIX if s["type"] != "trend"])) == []
    swapped = [dict(s) for s in SIX]
    swapped[0], swapped[1] = swapped[1], swapped[0]
    assert carousel.validate(story(slides=swapped)) == []
    doubled = [dict(s) for s in SIX] + [dict(SIX[2]), dict(SIX[3])]
    assert carousel.validate(story(slides=doubled)) == []


def test_a_carousel_has_3_to_20_slides():
    assert carousel.validate(story(slides=[dict(s) for s in SIX[:3]])) == []
    assert carousel.validate(story(slides=[dict(SIX[2]) for _ in range(20)])) == []
    assert "a carousel has 3 to 20 slides, not 2" in carousel.validate(story(slides=[dict(s) for s in SIX[:2]]))
    assert "a carousel has 3 to 20 slides, not 21" in carousel.validate(story(slides=[dict(SIX[2]) for _ in range(21)]))


def test_repeated_slide_types_get_one_file_each(monkeypatch, tmp_path):
    """Files are named by position (01.png, 02.png ...), so a repeated type never overwrites another slide."""
    from matplotlib.font_manager import FontProperties

    monkeypatch.setattr(carousel.make_post, "fonts", lambda: {role: FontProperties() for role in
                                                              ("footer", "title", "hero", "medium", "semi")})
    monkeypatch.setenv("NHL_POSTS_DIR", str(tmp_path))
    slides = [{"type": "comparison", "top": {"kicker": "K", "number": n}, "bottom": {"kicker": "K", "number": 1}}
              for n in (10, 20, 30)]
    data = story(slides=slides)
    assert carousel.validate(data) == []
    paths = carousel.render(None, {**data, "name": "repeats"}, "@handle")
    assert [p.name for p in paths] == ["01.png", "02.png", "03.png", "caption.txt"]
    assert len({p.read_bytes() for p in paths[:3]}) == 3  # three different slides, none overwritten


def test_a_statement_has_1_to_3_headline_lines_and_an_optional_kicker():
    for lines in (["One."], ["One", "two."], ["One", "two", "three."]):
        assert carousel.validate(story(slides=SIX[:2] + [{"type": "statement", "headline": lines}])) == []
    assert carousel.validate(story(slides=SIX[:2] + [{"type": "statement", "kicker": "K", "headline": ["A"]}])) == []
    for bad in ([], ["1", "2", "3", "4"], "not a list", [""]):
        problems = carousel.validate(story(slides=SIX[:2] + [{"type": "statement", "headline": bad}]))
        assert "statement: headline must be a list of 1 to 3 lines of text" in problems
    assert "statement: needs 'headline'" in carousel.validate(story(slides=SIX[:2] + [{"type": "statement"}]))
    assert carousel.slide_mode(story(), "statement") == "dark"


def test_a_question_slide_has_1_to_3_lines_and_an_optional_call():
    for lines in (["Who wins?"], ["Draisaitl or McDavid:", "who'd you take?"], ["A", "B", "C"]):
        assert carousel.validate(story(slides=SIX[:2] + [{"type": "question", "question": lines}])) == []
    assert carousel.validate(story(slides=SIX[:2] + [{"type": "question", "question": ["Q?"], "call": "C"}])) == []
    for bad in ([], ["1", "2", "3", "4"], "not a list"):
        problems = carousel.validate(story(slides=SIX[:2] + [{"type": "question", "question": bad}]))
        assert "question: question must be a list of 1 to 3 lines of text" in problems
    assert "question: unknown key 'kicker'" in carousel.validate(
        story(slides=SIX[:2] + [{"type": "question", "question": ["Q?"], "kicker": "K"}]))
    assert carousel.slide_mode(story(), "question") == "dark"


def test_a_guess_has_a_1_or_2_line_question_and_3_or_4_options():
    good = {"type": "guess", "kicker": "GUESS FIRST", "question": ["How many?"], "options": [41, 48, 55]}
    assert carousel.validate(story(slides=SIX[:2] + [good])) == []
    assert carousel.validate(story(slides=SIX[:2] + [{**good, "options": ["A", "B", "C", "D"]}])) == []
    for bad in ([1, 2], [1, 2, 3, 4, 5], "48", [1, "", 3]):
        problems = carousel.validate(story(slides=SIX[:2] + [{**good, "options": bad}]))
        assert "guess: options must be a list of 3 or 4 answers" in problems
    problems = carousel.validate(story(slides=SIX[:2] + [{**good, "question": ["1", "2", "3"]}]))
    assert "guess: question must be a list of 1 to 2 lines of text" in problems
    assert "guess: unknown key 'answer'" in carousel.validate(story(slides=SIX[:2] + [{**good, "answer": 48}]))
    assert carousel.slide_mode(story(), "guess") == "dark"


def board(**overrides):
    slide = {"type": "leaderboard", "title": "T", "rows": [
        {"name": "A", "team": "EDM", "value": 48, "subject": True}, {"name": "B", "value": "36"},
        {"name": "C", "value": "31"}]}
    slide.update(overrides)
    return carousel.validate(story(slides=SIX[:2] + [slide]))


def test_a_leaderboard_has_up_to_five_rows_and_one_subject():
    assert board() == []
    five = [{"name": n, "value": v} for n, v in zip("ABCDE", (5, 4, 3, 2, 1))]
    five[4]["subject"] = True
    assert board(rows=five) == []
    six = [{"name": n, "value": 1} for n in "ABCDEF"]
    six[0]["subject"] = True
    assert "leaderboard: at most five rows" in board(rows=six)
    assert "leaderboard: exactly one row must be the subject (subject: true)" in board(
        rows=[{"name": "A", "value": 1}, {"name": "B", "value": 2}, {"name": "C", "value": 3}])
    assert "leaderboard: row 2: needs 'value'" in board(rows=[{"name": "A", "value": 1, "subject": True}, {"name": "B"}])
    assert "leaderboard: row 1: unknown key 'colour'" in board(
        rows=[{"name": "A", "value": 1, "subject": True, "colour": "red"}])
    assert carousel.slide_mode(story(), "leaderboard") == "light"


def test_leaderboard_bars_need_numbers_and_start_at_zero():
    assert carousel.bar_value(".934") == 0.934 and carousel.bar_value("1,268") == 1268
    assert carousel.bar_value("52.3%") == 52.3 and carousel.bar_value("n/a") is None
    rows = [{"name": "A", "value": "+12", "subject": True}, {"name": "B", "value": -3}, {"name": "C", "value": 1}]
    assert "leaderboard: row 2: bars need a number of 0 or more as the value (or bars: false)" in board(rows=rows)
    assert "leaderboard: row 1: bars need a number of 0 or more as the value (or bars: false)" in board(
        rows=[{"name": "A", "value": "n/a", "subject": True}, {"name": "B", "value": 1}])
    assert board(rows=rows, bars=False) == []


def test_a_leaderboard_gap_shows_the_top_three_then_the_subject_at_its_rank():
    top3 = [{"rank": r, "name": n, "value": v} for r, n, v in ((1, "A", 30), (2, "B", 28), (3, "C", 27))]
    assert board(gap=True, rows=top3 + [{"rank": "T14", "name": "S", "value": 19, "subject": True}]) == []
    assert any("needs the fourth row to be the subject" in p for p in board(
        gap=True, rows=top3 + [{"name": "S", "value": 19, "subject": True}]))
    assert any("takes four rows" in p for p in board(gap=True))


def spread(**overrides):
    slide = {"type": "distribution", "title": "T", "sql": "select 1, 'A', 2.0", "subject": 1}
    slide.update(overrides)
    return carousel.validate(story(slides=SIX[:2] + [slide]))


def test_a_distribution_needs_a_query_and_a_subject():
    assert spread() == []
    assert spread(average_line=True, decimals=3, drop_leading_zero=True) == []
    assert spread(average_line={"value": 0.905, "label": "LEAGUE .905"}) == []
    assert "distribution: needs 'subject'" in carousel.validate(
        story(slides=SIX[:2] + [{"type": "distribution", "title": "T", "sql": "select 1"}]))
    assert any(p.startswith("distribution: average_line must be") for p in spread(average_line="yes"))
    assert any(p.startswith("distribution: decimals") for p in spread(decimals=9))
    assert carousel.slide_mode(story(), "distribution") == "light"


def test_distribution_rows_are_sorted_and_must_include_the_subject():
    con = duckdb.connect()
    sql = "select * from (values (1, 'A', 3.0), (2, 'B', 1.0), (3, 'C', null), (4, 'D', 2.0)) t(id, name, v)"
    assert carousel.distribution_rows(con, sql, 4) == [("2", "B", 1.0), ("4", "D", 2.0), ("1", "A", 3.0)]
    with pytest.raises(carousel.CarouselError, match="not among the 3 rows"):
        carousel.distribution_rows(con, sql, 3)  # its value is empty, so it is not drawn
    with pytest.raises(carousel.CarouselError, match="three columns"):
        carousel.distribution_rows(con, "select 1, 2", 1)


def test_beeswarm_dots_never_overlap():
    xs = [100 + (i % 7) * 3 for i in range(60)]  # many dots crowded on a few x positions
    offsets = carousel.beeswarm(xs, 10)
    points = list(zip(xs, offsets))
    for i, (ax, ay) in enumerate(points):
        for bx, by in points[i + 1:]:
            assert (ax - bx) ** 2 + (ay - by) ** 2 >= 21 ** 2
    assert offsets[0] == 0  # the first dot sits on the centre line
    # the subject (index 30) is placed first, on the centre line, with room for its larger dot
    offsets = carousel.beeswarm(xs, 10, first=30, subject_radius=17)
    assert offsets[30] == 0
    for i, (x, y) in enumerate(zip(xs, offsets)):
        if i != 30:
            assert (x - xs[30]) ** 2 + y ** 2 >= 28 ** 2


def test_number_text():
    assert carousel.number_text(0.9123, 3, True) == ".912"
    assert carousel.number_text(1268, 0) == "1,268"
    assert carousel.number_text(-0.05, 2, True) == "-.05"


def shot_map_slide(**overrides):
    slide = {"type": "shot_map", "title": "T", "player_id": 8478402,
             "from": datetime.date(2025, 10, 7), "to": datetime.date(2026, 4, 16)}
    slide.update(overrides)
    return carousel.validate(story(slides=SIX[:2] + [slide]))


def test_a_shot_map_needs_one_shooter_and_a_date_range_from_2009_10():
    assert shot_map_slide() == []
    assert shot_map_slide(game_types=[2, 3], count_line=False) == []
    both = shot_map_slide(team_id=22)
    assert "shot_map: give either player_id or team_id" in both
    early = shot_map_slide(**{"from": datetime.date(2008, 10, 1)})
    assert any("shot locations start in 2009-10" in p for p in early)
    backwards = shot_map_slide(**{"to": datetime.date(2025, 10, 1)})
    assert "shot_map: from must be on or before to" in backwards
    assert any(p.startswith("shot_map: game_types") for p in shot_map_slide(game_types=[1]))
    assert carousel.slide_mode(story(), "shot_map") == "light"


def test_shot_locations_read_normalised_shots_and_count_the_own_half():
    con = duckdb.connect()
    con.execute("create schema marts")
    con.execute("""
        create table marts.int_shot_geometry as select * from (values
            (1, 20, 80, 5, true, true, 2, date '2025-10-08'),     -- a goal 9 ft out, 5 ft to one side
            (1, 20, 40, -10, true, false, 2, date '2025-10-08'),  -- a shot from the blue line area
            (1, 20, -30, 0, true, false, 2, date '2025-10-09'),   -- from the shooter's own half
            (1, 20, 70, 0, false, false, 2, date '2025-10-09'),   -- blocked: left out
            (2, 20, 60, 0, true, false, 2, date '2025-10-09'),    -- another player
            (1, 20, 50, 0, true, false, 3, date '2025-10-09'),    -- playoffs: left out by default
            (1, 20, 50, 0, true, false, 2, date '2025-12-01')     -- after the range
        ) t(shooting_player_id, shooting_team_id, x_norm, y_norm, is_unblocked, is_goal, game_type, game_date)""")
    shots, own_half = carousel.shot_locations(con, datetime.date(2025, 10, 7), datetime.date(2025, 10, 31), player_id=1)
    assert sorted(shots) == [(32.5, 40, False), (47.5, 80, True)]
    assert own_half == (1, 0)  # one attempt from his own half, not a goal
    shots, _ = carousel.shot_locations(con, datetime.date(2025, 10, 7), datetime.date(2025, 10, 31), team_id=20,
                                       game_types=(2, 3))
    assert len(shots) == 4
    with pytest.raises(carousel.CarouselError, match="no shots with locations"):
        carousel.shot_locations(con, datetime.date(2024, 1, 1), datetime.date(2024, 1, 2), player_id=1)


def test_validate_names_every_problem():
    slides = [dict(s) for s in SIX]
    del slides[1]["name"]
    slides[2]["title"] = "not a comparison field"
    data = story(mode="sepia", accent="XYZ", through="yesterday", colour="red", caption="no credit", facts=[],
                 slides=slides + [{"type": "chart"}])
    problems = carousel.validate(data)
    assert "unknown key 'colour'" in problems
    assert "mode must be mixed, light or dark" in problems
    assert "unknown accent XYZ" in problems
    assert any(p.startswith("through must be a date") for p in problems)
    assert 'caption must credit the data with "Data: NHL"' in problems
    assert any(p.startswith("slide types must be") for p in problems)
    assert "reveal: needs 'name'" in problems
    assert "comparison: unknown key 'title'" in problems
    assert any(p.startswith("facts:") for p in problems)


def test_mixed_mode_follows_the_style_guide_and_can_be_overridden():
    data = story()
    assert [carousel.slide_mode(data, s["type"]) for s in SIX] == ["dark", "dark", "light", "light", "light", "dark"]
    assert {carousel.slide_mode(data, s["type"], "light") for s in SIX} == {"light"}
    assert {carousel.slide_mode(story(mode="dark"), s["type"]) for s in SIX} == {"dark"}


def test_normalise_matches_how_values_are_written():
    assert carousel.normalise([(Decimal("48"),)]) == carousel.expected(48)
    assert carousel.normalise([(19, 11.0, 37)]) == carousel.expected([19, 11, 37])
    assert carousel.normalise([("A", 1.92), ("B", 1.88)]) == carousel.expected([["A", 1.92], ["B", 1.88]])
    assert carousel.normalise([(datetime.date(2026, 11, 9),)]) == carousel.expected(datetime.date(2026, 11, 9))
    assert carousel.normalise([(47,)]) != carousel.expected(48)


def test_check_facts_flags_a_changed_answer():
    con = duckdb.connect()
    data = story(facts=[
        {"claim": "right", "sql": "select 48", "value": 48},
        {"claim": "wrong", "sql": "select 47", "value": 48},
    ])
    assert [(claim, ok) for claim, ok, _ in carousel.check_facts(con, data)] == [("right", True), ("wrong", False)]


def fake_marts():
    con = duckdb.connect()
    con.execute("create schema marts")
    con.execute("""create table marts.fct_skater_games as select * from (values
        (1, 20252026, 2, date '2025-10-09', 9, 1, 0, 1), (1, 20262027, 2, date '2026-10-03', 12, 2, 1, 1),
        (1, 20262027, 2, date '2026-10-01', 10, 1, 1, 0), (1, 20262027, 2, date '2026-10-02', 11, 0, 0, 0),
        (1, 20262027, 3, date '2026-10-04', 13, 9, 9, 0), (1, 20262027, 2, date '2026-10-09', 14, 5, 2, 3))
        as t(player_id, season, game_type, game_date, game_id, points, goals, assists)""")
    return con


def test_running_totals_count_the_first_games_in_date_order():
    con = fake_marts()
    assert carousel.running_totals(con, 1, 3, season=20262027) == [1, 1, 3]
    assert carousel.running_totals(con, 1, 3, season=20262027, metric="goals") == [1, 1, 2]
    assert carousel.running_totals(con, 1, 4, metric="goals") == [0, 1, 1, 2]  # career: 2025-26 first
    with pytest.raises(SystemExit):  # the through date leaves only three games that season
        carousel.running_totals(con, 1, 4, season=20262027, through=datetime.date(2026, 10, 5))
    with pytest.raises(SystemExit):
        carousel.running_totals(con, 1, 3, metric="shots")


def test_goal_locations_attack_downwards_from_either_end():
    con = duckdb.connect()
    con.execute("create schema marts")
    con.execute("""create table marts.fct_shots as select * from (values
        (7, 20252026, 2, true, false, true, 'left', 80, 10),     -- home attacks +x: 80 ft deep, 10 ft to his left
        (7, 20252026, 2, true, false, false, 'left', -80, -10),  -- away attacks -x: the same spot
        (7, 20252026, 2, true, false, true, 'right', 60, 5),     -- home attacks -x: a shot from its own half
        (7, 20252026, 2, true, true, true, 'left', 85, 0),       -- shootout: left out
        (7, 20252026, 2, false, false, true, 'left', 85, 0))     -- not a goal: left out
        as t(shooting_player_id, season, game_type, is_goal, is_shootout, is_home_shooter,
             home_team_defending_side, x_coord, y_coord)""")
    points, own_half = carousel.goal_locations(con, 7, 20252026)
    assert points == [(52.5, 80), (52.5, 80)]
    assert own_half == 1


def test_rink_must_be_a_known_kind():
    slides = [dict(s) for s in SIX]
    slides[4]["rink"] = {"goals_of": 1, "season": 20252026}
    assert carousel.validate(story(slides=slides)) == []
    slides[4]["rink"] = "passes"
    assert any(p.startswith("turning_point: rink must be") for p in carousel.validate(story(slides=slides)))


def test_posts_folder_refuses_the_repo(monkeypatch):
    monkeypatch.setenv("NHL_POSTS_DIR", str(carousel.make_post.REPO_ROOT / "posts"))
    with pytest.raises(SystemExit):
        carousel.posts_folder("anything")


def test_the_checked_in_carousels_are_valid():
    for path in (carousel.make_post.REPO_ROOT / "carousels").glob("*.yml"):
        carousel.load(path)  # raises on any problem


def test_mean_sd_matches_duckdb_stddev_samp():
    from instagram.charts import mean_sd

    values = [0.2, 0.5, 0.5, 1.1, 2.53]
    mean, sd = mean_sd(values)
    expected_mean, expected_sd = duckdb.connect().execute(
        "select avg(v), stddev_samp(v) from unnest($v) as t(v)", {"v": values}).fetchone()
    assert mean == pytest.approx(expected_mean)
    assert sd == pytest.approx(expected_sd)


def test_the_accent_is_one_shade_readable_on_every_background():
    from instagram.make_post import STYLE, backgrounds, contrast, palette

    for code in {**STYLE["team_accents"], **STYLE["country_accents"]}:
        dark, light = palette("dark", code), palette("light", code)
        assert dark["accent"] == dark["accent_text"] == light["accent"] == light["accent_shape"]
        assert min(contrast(light["accent"], bg) for bg in backgrounds()) >= 3.0, code
    assert palette("light", "CAN")["accent"] != STYLE["country_accents"]["CAN"]["accent"]  # 2.9:1, so it moves


NHL_CREDIT = "Words. Data, logos and headshots: NHL."


def test_a_headshot_can_go_on_the_hook_or_the_reveal_and_needs_the_nhl_credit():
    hook = {"type": "hook", "kicker": "K", "headline": ["A"], "image": {"type": "headshot", "player_id": 8477492}}
    reveal = dict(SIX[1], image={"type": "headshot", "player_id": 8477492}, stats=[{"value": 1, "label": "A"}] * 2)
    assert carousel.validate(story(caption=NHL_CREDIT, slides=[hook, reveal, SIX[2]])) == []
    problems = carousel.validate(story(slides=[hook, reveal, SIX[2]]))  # caption says only "Data: NHL."
    assert 'caption must credit "Data, logos and headshots: NHL." (the post uses an NHL logo or headshot)' in problems
    three = dict(reveal, stats=[{"value": 1, "label": "A"}] * 3)
    assert "reveal: with a headshot, at most two stats fit beside it" in carousel.validate(
        story(caption=NHL_CREDIT, slides=[hook, three, SIX[2]]))
    photo = dict(SIX[1], image={"type": "photo", "commons": "File:X.jpg"})
    assert "reveal: image: only a headshot can go on the reveal" in carousel.validate(
        story(caption=NHL_CREDIT, slides=[hook, photo, SIX[2]]))
    bad = dict(hook, image={"type": "headshot", "player_id": "McDavid", "side": "left"})
    problems = carousel.validate(story(caption=NHL_CREDIT, slides=[bad, SIX[1], SIX[2]]))
    assert "hook: image: a headshot needs the player's player_id" in problems
    assert "hook: image: unknown key 'side'" in problems


def test_logos_on_the_leaderboard_and_the_comparison_need_team_codes_and_the_credit():
    rows = [{"name": "A", "team": "EDM", "value": 3, "subject": True}, {"name": "B", "team": "col", "value": 2},
            {"name": "C", "team": "TOR", "value": 1}]
    slide = {"type": "leaderboard", "title": "T", "rows": rows, "logos": True}
    assert carousel.validate(story(caption=NHL_CREDIT, slides=SIX[:2] + [slide])) == []
    assert any(p.startswith('caption must credit "Data, logos')
               for p in carousel.validate(story(slides=SIX[:2] + [slide])))
    no_team = dict(slide, rows=rows[:2] + [{"name": "C", "value": 1}])
    assert "leaderboard: row 3: logos: true needs a team code, such as EDM" in carousel.validate(
        story(caption=NHL_CREDIT, slides=SIX[:2] + [no_team]))
    compare = {"type": "comparison", "top": {"kicker": "K", "number": 1, "logo": "EDM"},
               "bottom": {"kicker": "K", "number": 2, "logo": "XYZ", "colour": "red"}}
    problems = carousel.validate(story(caption=NHL_CREDIT, slides=SIX[:2] + [compare]))
    assert "comparison: bottom: logo must be a team code, such as EDM" in problems
    assert "comparison: bottom: unknown key 'colour'" in problems
    assert not carousel.uses_nhl_images(story())


def test_slides_with_headshots_and_logos_draw_without_covering_the_handle(monkeypatch, tmp_path):
    """Draws a hook and reveal with a headshot, a leaderboard with logos and a comparison with logos, using made-up
    pictures (no downloads), and checks every slide is saved."""
    from matplotlib.font_manager import FontProperties
    from PIL import Image

    monkeypatch.setattr(carousel.make_post, "fonts", lambda: {role: FontProperties() for role in
                                                              ("footer", "title", "hero", "medium", "semi")})
    monkeypatch.setattr(carousel.nhl_images, "headshot", lambda player_id: Image.new("RGBA", (336, 336), (9, 9, 9, 255)))
    monkeypatch.setattr(carousel.nhl_images, "logo", lambda team, mode, height: Image.new("RGBA", (height * 3 // 2, height)))
    monkeypatch.setenv("NHL_POSTS_DIR", str(tmp_path))
    rows = [{"name": "A", "team": "EDM", "value": 3, "subject": True}, {"name": "B", "team": "COL", "value": 2},
            {"name": "C", "team": "TOR", "value": 1}]
    slides = [
        {"type": "hook", "kicker": "K", "headline": ["Aaaa", "Bbbb"], "image": {"type": "headshot", "player_id": 1}},
        dict(SIX[1], image={"type": "headshot", "player_id": 1}, subtitle="S", stats=[{"value": 1, "label": "A"}]),
        {"type": "leaderboard", "title": "T", "rows": rows, "logos": True},
        {"type": "comparison", "top": {"kicker": "K", "number": 1, "logo": "EDM"},
         "bottom": {"kicker": "K", "number": 2, "logo": "COL"}},
    ]
    data = story(caption=NHL_CREDIT, slides=slides)
    assert carousel.validate(data) == []
    paths = carousel.render(None, {**data, "name": "images"}, "@handle")
    assert [p.name for p in paths] == ["01.png", "02.png", "03.png", "04.png", "caption.txt"]
