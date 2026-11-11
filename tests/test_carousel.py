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


def test_a_slide_can_be_skipped_but_not_reordered():
    assert carousel.validate(story(slides=[dict(s) for s in SIX if s["type"] != "trend"])) == []
    swapped = [dict(s) for s in SIX]
    swapped[0], swapped[1] = swapped[1], swapped[0]
    assert any("must follow the order" in p for p in carousel.validate(story(slides=swapped)))
    doubled = [dict(s) for s in SIX] + [dict(SIX[-1])]
    assert any("must follow the order" in p for p in carousel.validate(story(slides=doubled)))


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
