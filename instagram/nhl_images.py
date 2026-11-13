"""NHL team logos and player headshots for posts (style/style_guide.md, "NHL logos and headshots"; allowed by the
owner on 2026-11-11, credited "Data, logos and headshots: NHL." in the caption).

- Headshots: the cut-out PNG the NHL API gives for a player (the `headshot` field of
  api-web.nhle.com/v1/player/{id}/landing), the current season's photo. 336 x 336 pixels, so slides show them at most
  480 px tall to stay sharp.
- Logos: the NHL's own SVGs, assets.nhle.com/logos/nhl/svg/{TEAM}_light.svg on light slides and _dark.svg on dark
  slides, turned into pictures with resvg (never recoloured, stretched or cropped).

Everything is downloaded through ingest/nhl_api.py (polite pacing and retries) into assets/nhl/headshots/ and
assets/nhl/logos/, which are git-ignored: the repo is public and NHL images are never committed. A logo is fetched
once; a headshot's player page is read on each render so the photo stays the current season's.
"""

import io
import json
from pathlib import Path

from instagram import make_post

ASSETS = make_post.REPO_ROOT / "assets" / "nhl"
LANDING_URL = "https://api-web.nhle.com/v1/player/{player_id}/landing"
LOGO_URL = "https://assets.nhle.com/logos/nhl/svg/{team}_{variant}.svg"
IMAGE_HOST = "https://assets.nhle.com/"
CREDIT = "Data, logos and headshots: NHL."
HEADSHOT_MAX_PX = 480  # the 336 px originals, enlarged at most about 1.4 times


class ImageError(SystemExit):
    pass


def _client():
    from ingest.nhl_api import NhlApiClient

    return NhlApiClient()


def headshot_path(player_id, client=None, folder=None):
    """The player's current headshot, downloaded into assets/nhl/headshots/ if not there yet. The file name keeps
    the season and team from the NHL's URL (e.g. 20252026_COL_8477492.png), so a new season's photo is a new file."""
    folder = Path(folder or ASSETS / "headshots")
    own = client is None
    client = client or _client()
    try:
        landing = json.loads(client.fetch(LANDING_URL.format(player_id=int(player_id))))
        url = landing.get("headshot") or ""
        if not url.startswith(IMAGE_HOST):
            raise ImageError(f"No NHL headshot for player {player_id}")
        parts = url.removeprefix(IMAGE_HOST).split("/")  # mugs/nhl/<season>/<team>/<id>.png
        name = "_".join(parts[-3:]) if len(parts) >= 3 else f"{player_id}.png"
        path = folder / name
        if not path.exists():
            folder.mkdir(parents=True, exist_ok=True)
            path.write_bytes(client.fetch_bytes(url))
        return path
    finally:
        if own:
            client.close()


def headshot(player_id, client=None, folder=None):
    """The headshot as a PIL image with its transparent background (RGBA)."""
    from PIL import Image

    return Image.open(headshot_path(player_id, client, folder)).convert("RGBA")


def logo_path(team, mode, client=None, folder=None):
    """The team's logo SVG for a light or dark slide, downloaded into assets/nhl/logos/ once."""
    variant = "dark" if mode == "dark" else "light"
    team = str(team).upper()
    folder = Path(folder or ASSETS / "logos")
    path = folder / f"{team}_{variant}.svg"
    if not path.exists():
        own = client is None
        client = client or _client()
        try:
            body = client.fetch_bytes(LOGO_URL.format(team=team, variant=variant))
        finally:
            if own:
                client.close()
        if b"<svg" not in body[:2000]:
            raise ImageError(f"No NHL logo for {team}")
        folder.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    return path


def logo(team, mode, height, client=None, folder=None):
    """The logo as a PIL image (RGBA) exactly `height` pixels tall, its width in proportion."""
    import resvg_py
    from PIL import Image

    svg = logo_path(team, mode, client, folder).read_text(encoding="utf-8")
    return Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg, height=int(height))))).convert("RGBA")
