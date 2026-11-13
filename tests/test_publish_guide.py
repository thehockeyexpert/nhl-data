import pytest

from analyst import publish_guide


def test_only_the_text_below_the_separator_is_published(tmp_path):
    path = tmp_path / "guide.md"
    path.write_text("# Repo note\n\nNot for MotherDuck.\n\n---\n\n# Guide\n\nUse 'OT' carefully.\n", encoding="utf-8")
    assert publish_guide.guide_text(path) == "# Guide\n\nUse 'OT' carefully.\n"


def test_a_file_without_a_separator_is_refused(tmp_path):
    path = tmp_path / "guide.md"
    path.write_text("# Guide\n", encoding="utf-8")
    with pytest.raises(ValueError):
        publish_guide.guide_text(path)


def test_the_real_guide_has_a_body():
    text = publish_guide.guide_text()
    assert text.startswith("Read this before answering")
    assert "Repo note" not in text and "the owner creates and updates" not in text


def test_a_guide_over_the_limit_is_refused():
    with pytest.raises(ValueError):
        publish_guide.size_check("x" * (publish_guide.SIZE_LIMIT + 1))


def test_a_guide_near_the_limit_gets_a_warning():
    assert publish_guide.size_check("x" * (publish_guide.SIZE_WARNING + 1)).startswith("Warning")
    assert publish_guide.size_check("x" * publish_guide.SIZE_WARNING) is None


def test_the_real_guide_fits_the_limit():
    assert len(publish_guide.guide_text()) <= publish_guide.SIZE_LIMIT
