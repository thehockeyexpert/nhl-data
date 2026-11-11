"""Find and download free-licence player photos from Wikimedia Commons for posts.

    uv run python -m instagram.photos search "Connor McDavid"          # list candidates, largest first
    uv run python -m instagram.photos download "File:Connor McDavid 2019.jpg"

Only files under CC BY, CC BY-SA or public domain (CC0 counts as public domain) are accepted; anything else is
refused, whatever the search returns (style/style_guide.md, "NHL logos and headshots"; docs/decisions.md,
2026-11-11). The original (largest) file is saved in assets/nhl/photos/, which is git-ignored, with a
<file>.credit.json beside it holding the photographer, licence and source page. Photos are never searched for
anywhere else (no Getty, Imagn, team sites or image searches).
"""

import argparse
import html
import json
import re
import time
from pathlib import Path

import httpx

from instagram import make_post

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "nhl-data (personal project; https://github.com/thehockeyexpert/nhl-data)"
PHOTOS = make_post.REPO_ROOT / "assets" / "nhl" / "photos"
IMAGE_TYPES = ("image/jpeg", "image/png")

_FREE = [re.compile(p, re.I) for p in (
    r"^CC BY(-SA)? \d(\.\d)?",       # CC BY 2.0, CC BY-SA 4.0, CC BY-SA 3.0 IGO ...
    r"^Public domain",
    r"^CC0",
)]
_NOT_FREE = re.compile(r"\b(NC|ND)\b|non-?commercial|no ?deriv", re.I)


class PhotoError(SystemExit):
    pass


def is_free(licence):
    """True for CC BY, CC BY-SA and public domain (including CC0); false for anything else, NC or ND included."""
    licence = (licence or "").strip()
    return bool(licence) and not _NOT_FREE.search(licence) and any(p.search(licence) for p in _FREE)


def plain(text):
    """Commons metadata fields are HTML: keep the words only."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text or ""))).strip()


def credit_line(info, changes=()):
    """'Photo: <author> / Wikimedia Commons, <licence>' plus any changes, as CC BY and CC BY-SA require."""
    author = info["author"] or "unknown author"
    line = f"Photo: {author} / Wikimedia Commons, {info['licence']}"
    return line + (f" ({', '.join(changes)})" if changes else "")


def _client():
    return httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True)


def _query(client, **params):
    time.sleep(0.5)  # polite: Commons asks bots to keep requests serial and unhurried
    response = client.get(API, params={"action": "query", "format": "json", "formatversion": 2, **params})
    response.raise_for_status()
    return response.json()


def _candidate(page):
    info = (page.get("imageinfo") or [{}])[0]
    meta = info.get("extmetadata") or {}
    value = lambda key: (meta.get(key) or {}).get("value", "")  # noqa: E731
    return {
        "title": page["title"],
        "width": info.get("width", 0),
        "height": info.get("height", 0),
        "mime": info.get("mime", ""),
        "licence": plain(value("LicenseShortName")),
        "licence_url": value("LicenseUrl"),
        "author": plain(value("Artist")),
        "date": plain(value("DateTimeOriginal"))[:10],
        "description": plain(value("ImageDescription"))[:160],
        "page": info.get("descriptionurl", ""),
        "url": info.get("url", ""),
        "thumb": info.get("thumburl", ""),
    }


def search(name, limit=40, client=None):
    """Free-licence photos on Commons matching the name, largest first."""
    own = client is None
    client = client or _client()
    try:
        data = _query(client, generator="search", gsrsearch=f'"{name}" filetype:bitmap', gsrnamespace=6,
                      gsrlimit=limit, prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=500)
    finally:
        if own:
            client.close()
    pages = (data.get("query") or {}).get("pages", [])
    found = [_candidate(p) for p in pages]
    free = [c for c in found if is_free(c["licence"]) and c["mime"] in IMAGE_TYPES]
    return sorted(free, key=lambda c: c["width"] * c["height"], reverse=True)


def file_info(title, client):
    data = _query(client, titles=title, prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=500)
    pages = (data.get("query") or {}).get("pages", [])
    if not pages or "imageinfo" not in pages[0]:
        raise PhotoError(f"No such file on Wikimedia Commons: {title}")
    return _candidate(pages[0])


def local_name(title):
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", title.removeprefix("File:")).strip("_")
    return stem


def download(title, folder=PHOTOS):
    """Download a Commons file's original into folder, refusing anything not under a free licence.
    Returns (path, info); info is also saved as <path>.credit.json."""
    with _client() as client:
        info = file_info(title, client)
        if not is_free(info["licence"]):
            raise PhotoError(f"{title}: licence {info['licence']!r} is not CC BY, CC BY-SA or public domain")
        if info["mime"] not in IMAGE_TYPES:
            raise PhotoError(f"{title}: {info['mime']} is not a JPEG or PNG")
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / local_name(title)
        if not path.exists():
            time.sleep(0.5)
            response = client.get(info["url"])
            response.raise_for_status()
            path.write_bytes(response.content)
    credit_file(path).write_text(json.dumps(info, indent=2), encoding="utf-8")
    return path, info


def credit_file(path):
    return path.with_name(path.name + ".credit.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="action", required=True)
    find = sub.add_parser("search", help="list free-licence photos of a player, largest first")
    find.add_argument("name")
    find.add_argument("--limit", type=int, default=40, help="how many search results to check (default 40)")
    get = sub.add_parser("download", help="download one Commons file into assets/nhl/photos/")
    get.add_argument("title", help='for example "File:Connor McDavid 2019.jpg"')
    args = parser.parse_args()

    if args.action == "search":
        for c in search(args.name, args.limit):
            print(f"{c['width']}x{c['height']}  {c['licence']:<14}  {c['date'] or '?':<10}  {c['title']}\n"
                  f"    by {c['author'] or '?'}  {c['page']}")
    else:
        path, info = download(args.title)
        print(f"Saved {path}\n{credit_line(info)}\nIn the carousel YAML:\n"
              f"  image: {{type: photo, commons: \"{args.title}\"}}")


if __name__ == "__main__":
    main()


# ---- Using a photo on a slide ----

LAYOUTS = ("panel", "cutout")
CUTOUT_MODEL = "u2net_human_seg"  # a person-segmentation model, downloaded once by rembg (about 170 MB)


def resolve(image, folder=PHOTOS):
    """(path, credit) for a slide's image: a Commons file (downloaded if missing, licence re-checked) or a file the
    owner saved in assets/nhl/photos/ with its own credit. The credit names any change made to the photo."""
    changes = ["cropped"] if image.get("layout", "panel") == "panel" else ["background removed"]
    if image.get("commons"):
        path = folder / local_name(image["commons"])
        credit = credit_file(path)
        if path.exists() and credit.exists():
            info = json.loads(credit.read_text(encoding="utf-8"))
            if not is_free(info["licence"]):
                raise PhotoError(f"{image['commons']}: licence {info['licence']!r} is not allowed")
        else:
            path, info = download(image["commons"], folder)
        return path, credit_line(info, changes)
    path = folder / image["file"]
    if not path.exists():
        raise PhotoError(f"Photo not found: {path} (save it in assets/nhl/photos/)")
    return path, image["credit"]


def cover(path, width, height, focus=(0.5, 0.4)):
    """The photo cropped to width x height pixels, filling the area, centred on focus (fractions across and down)."""
    from PIL import Image

    photo = Image.open(path).convert("RGB")
    scale = max(width / photo.width, height / photo.height)
    size = (round(photo.width * scale), round(photo.height * scale))
    photo = photo.resize(size, Image.LANCZOS)
    left = min(max(round(focus[0] * size[0] - width / 2), 0), size[0] - width)
    top = min(max(round(focus[1] * size[1] - height / 2), 0), size[1] - height)
    return photo.crop((left, top, left + width, top + height))


def cutout(path):
    """The photo with its background removed (RGBA), trimmed to the person. Cached beside the photo."""
    from PIL import Image

    cached = path.with_name(path.stem + ".cutout.png")
    if not cached.exists():
        try:
            from rembg import new_session, remove
        except ImportError:
            raise PhotoError("Background removal needs the photos group: "
                             "uv run --group photos python -m instagram.carousel render ...") from None
        result = remove(Image.open(path).convert("RGB"), session=new_session(CUTOUT_MODEL))
        result.save(cached)
    person = Image.open(cached).convert("RGBA")
    box = person.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
    return person.crop(box) if box else person
