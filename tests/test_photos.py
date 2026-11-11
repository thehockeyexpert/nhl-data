import json

import pytest
from PIL import Image

from instagram import carousel, photos


@pytest.mark.parametrize("licence, ok", [
    ("CC BY 2.0", True), ("CC BY-SA 4.0", True), ("CC BY-SA 3.0 IGO", True), ("Public domain", True),
    ("CC0", True), ("CC BY-NC 2.0", False), ("CC BY-ND 4.0", False), ("CC BY-NC-SA 2.0", False),
    ("GFDL", False), ("Copyrighted", False), ("", False), (None, False),
])
def test_only_cc_by_cc_by_sa_and_public_domain_are_free(licence, ok):
    assert photos.is_free(licence) is ok


def test_the_credit_names_author_licence_and_changes():
    info = {"author": "Jane Smith", "licence": "CC BY-SA 4.0"}
    assert photos.credit_line(info) == "Photo: Jane Smith / Wikimedia Commons, CC BY-SA 4.0"
    assert photos.credit_line(info, ["cropped"]).endswith("CC BY-SA 4.0 (cropped)")
    assert photos.plain('<a href="x">Jane&nbsp;Smith</a>') == "Jane Smith"


def test_resolve_uses_the_saved_credit_and_refuses_a_non_free_licence(tmp_path):
    path = tmp_path / photos.local_name("File:A b.jpg")
    path.write_bytes(b"x")
    photos.credit_file(path).write_text(json.dumps({"author": "J", "licence": "CC BY 2.0"}), encoding="utf-8")
    assert photos.resolve({"commons": "File:A b.jpg"}, tmp_path) == (path, "Photo: J / Wikimedia Commons, CC BY 2.0 (cropped)")
    assert photos.resolve({"commons": "File:A b.jpg", "layout": "cutout"}, tmp_path)[1].endswith("(background removed)")
    photos.credit_file(path).write_text(json.dumps({"author": "J", "licence": "CC BY-NC 2.0"}), encoding="utf-8")
    with pytest.raises(SystemExit):
        photos.resolve({"commons": "File:A b.jpg"}, tmp_path)


def test_an_owner_photo_needs_the_file_and_uses_its_credit(tmp_path):
    with pytest.raises(SystemExit):
        photos.resolve({"file": "mine.jpg", "credit": "Photo: me"}, tmp_path)
    (tmp_path / "mine.jpg").write_bytes(b"x")
    assert photos.resolve({"file": "mine.jpg", "credit": "Photo: me"}, tmp_path)[1] == "Photo: me"


def test_cover_fills_the_area_around_the_focus(tmp_path):
    path = tmp_path / "p.png"
    image = Image.new("RGB", (300, 200), "white")
    image.paste((255, 0, 0), (0, 0, 100, 200))  # the left third is red
    image.save(path)
    left = photos.cover(path, 100, 200, (0.0, 0.5))
    assert left.size == (100, 200) and left.getpixel((50, 100)) == (255, 0, 0)
    assert photos.cover(path, 100, 200, (1.0, 0.5)).getpixel((50, 100)) == (255, 255, 255)


def test_image_field_problems():
    good = {"type": "photo", "commons": "File:X.jpg", "layout": "panel", "side": "left", "focus": [0.4, 0.5]}
    assert carousel.image_problems(good) == []
    assert carousel.image_problems({"type": "photo", "file": "x.jpg", "credit": "Photo: me"}) == []
    problems = carousel.image_problems({"type": "headshot", "commons": "X.jpg", "file": "y.jpg", "layout": "tile",
                                        "side": "top", "focus": [2, 0], "size": 3})
    for expected in ("unknown key 'size'", "type must be photo (headshots and logos are not supported yet)",
                     "give either commons (a Wikimedia Commons file) or file (a photo in assets/nhl/photos/)",
                     "commons must be a Commons file title starting with File:", "layout must be panel or cutout",
                     "side must be left or right", "focus must be two numbers from 0 to 1: [across, down]"):
        assert expected in problems
    assert "a photo from assets/nhl/photos/ needs a credit:" in carousel.image_problems({"type": "photo", "file": "x"})
    assert "a Commons photo's credit comes from Commons: leave credit out" in carousel.image_problems(
        {"type": "photo", "commons": "File:X.jpg", "credit": "c"})


def test_only_the_hook_takes_an_image(monkeypatch):
    from tests.test_carousel import SIX, story

    slides = [dict(s) for s in SIX]
    slides[0]["image"] = {"type": "photo", "commons": "File:X.jpg"}
    assert carousel.validate(story(slides=slides)) == []
    slides[1]["image"] = {"type": "photo", "commons": "File:X.jpg"}
    assert "reveal: unknown key 'image'" in carousel.validate(story(slides=slides))


def test_photo_credits_are_added_to_the_caption_once():
    text = carousel.caption_text("Words. Data: NHL.", ["Photo: A", "Photo: A", "Photo: B"])
    assert text == "Words. Data: NHL.\nPhoto: A\nPhoto: B\n"
    assert carousel.caption_text("Words. Photo: A. Data: NHL.", ["Photo: A"]) == "Words. Photo: A. Data: NHL.\n"
    assert carousel.caption_text("Words. Data: NHL.", []) == "Words. Data: NHL.\n"
