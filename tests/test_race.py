from instagram import make_post, race

GOOD = {"accent": "TBL", "title": "T", "games": 10, "metric": "goals", "caption": "Words. Data: NHL.",
        "lines": [{"player_id": 1, "name": "A"}], "facts": [{"claim": "c", "sql": "select 1", "value": 1}]}


def test_a_race_is_valid():
    assert race.validate(GOOD) == []


def test_validate_names_every_problem():
    data = dict(GOOD, colour="red", mode="sepia", accent="XYZ", metric="shots", games=1, caption="no credit",
                lines=[{"name": "no id"}], facts=[])
    del data["title"]
    problems = race.validate(data)
    for expected in ("unknown key 'colour'", "needs 'title'", "mode must be light or dark", "unknown accent XYZ",
                     "metric must be one of points, goals, assists", "games must be a whole number of at least 2",
                     'caption must credit the data with "Data: NHL"', "facts: every number on screen needs a query",
                     "lines must be one to three entries, each with player_id and name"):
        assert expected in problems


def test_the_schedule_holds_still_then_races_then_holds_the_end():
    frames = race.schedule(1246, 15)
    assert len(frames) == race.FPS * (1 + 15 + 3)
    assert frames[: race.FPS] == [0] * race.FPS
    assert frames[race.FPS] == 1 and frames[-1] == 1246
    assert frames == sorted(frames)  # the game counter never goes backwards


def test_the_checked_in_races_are_valid():
    for path in (make_post.REPO_ROOT / "reels").glob("*.yml"):
        race.load(path)  # raises on any problem
