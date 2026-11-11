import datetime
from decimal import Decimal

import duckdb
import pytest

from instagram import carousel


def minimal(**overrides):
    data = {"accent": "EDM", "mode": "light", "slides": [{"type": "title", "title": "Hello"}]}
    data.update(overrides)
    return data


def test_a_minimal_carousel_is_valid():
    assert carousel.validate(minimal()) == []


def test_validate_names_every_problem():
    data = minimal(
        mode="sepia",
        accent="XYZ",
        through="yesterday",
        colour="red",
        slides=[
            {"type": "video", "title": "A"},
            {"type": "text"},
            {"type": "chart", "title": "B", "chart": "pie_of_everything"},
            {"type": "end", "title": "C", "season": 20252026},
        ],
        facts=[{"claim": "no query"}],
    )
    problems = carousel.validate(data)
    assert "unknown key 'colour'" in problems
    assert any(p.startswith("mode must be one of") for p in problems)
    assert "unknown accent XYZ" in problems
    assert any(p.startswith("through must be a date") for p in problems)
    assert any(p.startswith("slide 1: type must be") for p in problems)
    assert "slide 2: needs a title" in problems
    assert any(p.startswith("slide 3: chart must be one of") for p in problems)
    assert "slide 4: unknown key 'season'" in problems
    assert "fact 1: needs claim, sql and value" in problems


def test_modes_alternate_and_a_slide_can_choose_its_own():
    slides = [{"type": "text", "title": str(n)} for n in range(1, 6)]
    slides[3]["mode"] = "dark"
    data = minimal(mode="dark-light", slides=slides)
    assert carousel.validate(data) == []
    assert [carousel.slide_mode(data, n) for n in range(1, 6)] == ["dark", "light", "dark", "dark", "dark"]
    data["mode"] = "light-dark"
    assert [carousel.slide_mode(data, n) for n in range(1, 4)] == ["light", "dark", "light"]
    data["mode"] = "light"
    assert [carousel.slide_mode(data, n) for n in (1, 2, 3)] == ["light", "light", "light"]
    slides[0]["mode"] = "sepia"
    assert "slide 1: mode must be light or dark" in carousel.validate(data)


def test_chart_settings_are_the_non_slide_keys():
    slide = {"type": "chart", "chart": "points_leaders", "title": "T", "subtitle": "S", "season": 20262027, "top": 5,
             "mode": "dark"}
    assert carousel.chart_settings(slide) == {"season": 20262027, "top": 5}


def test_normalise_matches_how_values_are_written():
    assert carousel.normalise([(Decimal("48"),)]) == carousel.expected(48)
    assert carousel.normalise([(19, 11.0, 37)]) == carousel.expected([19, 11, 37])
    assert carousel.normalise([("A", 1.92), ("B", 1.88)]) == carousel.expected([["A", 1.92], ["B", 1.88]])
    assert carousel.normalise([(datetime.date(2026, 11, 9),)]) == carousel.expected(datetime.date(2026, 11, 9))
    assert carousel.normalise([(47,)]) != carousel.expected(48)


def test_check_facts_flags_a_changed_answer():
    con = duckdb.connect()
    data = minimal(facts=[
        {"claim": "right", "sql": "select 48", "value": 48},
        {"claim": "wrong", "sql": "select 47", "value": 48},
    ])
    assert [(claim, ok) for claim, ok, _ in carousel.check_facts(con, data)] == [("right", True), ("wrong", False)]


def test_posts_folder_refuses_the_repo(monkeypatch):
    monkeypatch.setenv("NHL_POSTS_DIR", str(carousel.make_post.REPO_ROOT / "posts"))
    with pytest.raises(SystemExit):
        carousel.posts_folder("anything")


def test_the_checked_in_carousels_are_valid():
    for path in (carousel.make_post.REPO_ROOT / "carousels").glob("*.yml"):
        carousel.load(path)  # raises on any problem
