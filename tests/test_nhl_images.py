import json

import pytest

from instagram import nhl_images


class FakeClient:
    """Stands in for the NHL client: a player page naming a headshot, the headshot, and logo SVGs."""

    def __init__(self, headshot="https://assets.nhle.com/mugs/nhl/20252026/COL/8477492.png"):
        self.urls = []
        self.headshot = headshot

    def fetch(self, url):
        self.urls.append(url)
        return json.dumps({"headshot": self.headshot})

    def fetch_bytes(self, url):
        self.urls.append(url)
        if url.endswith(".svg"):
            return b'<svg xmlns="http://www.w3.org/2000/svg" width="30" height="20"><rect width="30" height="20"/></svg>'
        from io import BytesIO
        from PIL import Image
        out = BytesIO()
        Image.new("RGBA", (336, 336)).save(out, format="PNG")
        return out.getvalue()

    def close(self):
        pass


def test_a_headshot_is_saved_once_per_season_and_team(tmp_path):
    client = FakeClient()
    path = nhl_images.headshot_path(8477492, client, tmp_path)
    assert path.name == "20252026_COL_8477492.png"
    assert client.urls == [nhl_images.LANDING_URL.format(player_id=8477492), client.headshot]
    nhl_images.headshot_path(8477492, client, tmp_path)
    assert client.urls[-1] == nhl_images.LANDING_URL.format(player_id=8477492)  # the page again, not the picture
    assert nhl_images.headshot(8477492, client, tmp_path).size == (336, 336)


def test_a_headshot_from_anywhere_but_the_nhl_is_refused(tmp_path):
    with pytest.raises(nhl_images.ImageError, match="No NHL headshot"):
        nhl_images.headshot_path(1, FakeClient(headshot="https://example.com/x.png"), tmp_path)


def test_logos_are_fetched_once_per_team_and_slide_mode_and_drawn_to_height(tmp_path):
    client = FakeClient()
    assert nhl_images.logo_path("edm", "dark", client, tmp_path).name == "EDM_dark.svg"
    assert client.urls == [nhl_images.LOGO_URL.format(team="EDM", variant="dark")]
    nhl_images.logo_path("EDM", "dark", client, tmp_path)
    assert len(client.urls) == 1
    picture = nhl_images.logo("EDM", "dark", 80, client, tmp_path)
    assert picture.size == (120, 80) and picture.mode == "RGBA"


def test_images_are_kept_in_the_git_ignored_assets_folder():
    assert nhl_images.ASSETS.parts[-2:] == ("assets", "nhl")
