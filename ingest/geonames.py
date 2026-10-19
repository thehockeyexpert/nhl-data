"""Load the GeoNames place files used to give player birthplaces coordinates, replacing the previous copy.

Run it with:  uv run python -m ingest.geonames
Refreshed occasionally by .github/workflows/geonames.yml, not by the daily run.

GeoNames (https://www.geonames.org) is licensed CC BY 4.0: anything public built from it must credit GeoNames.
Files: cities500 (every place with at least 500 people), the full Canada file (adds smaller villages, neighbourhoods
and former municipalities) and the country list (two- and three-letter country codes).
"""

import io
import tempfile
import zipfile
from pathlib import Path

from ingest.nhl_api import NhlApiClient
from ingest.raw_loader import connect, replace_text_file

DUMP = "https://download.geonames.org/export/dump"

# raw table -> (URL, file inside the zip, or None for a plain text file)
SOURCES = {
    "geonames__cities500": (f"{DUMP}/cities500.zip", "cities500.txt"),
    "geonames__ca": (f"{DUMP}/CA.zip", "CA.txt"),
    "geonames__country_info": (f"{DUMP}/countryInfo.txt", None),
}


def run(client, con):
    """Fetch and store each file. Returns {table: lines stored, or None if unchanged}."""
    stored = {}
    with tempfile.TemporaryDirectory() as folder:
        for table, (url, member) in SOURCES.items():
            body = client.fetch_bytes(url)
            if member:
                with zipfile.ZipFile(io.BytesIO(body)) as archive:
                    body = archive.read(member)
            path = Path(folder) / f"{table}.txt"
            path.write_bytes(body)
            stored[table] = replace_text_file(con, table, url, path)
            # Counts only, never file content.
            print(f"  {'unchanged' if stored[table] is None else f'replaced  {stored[table]:,} lines'}  {table}")
    return stored


def main():
    con = connect()
    client = NhlApiClient()
    try:
        run(client, con)
    finally:
        client.close()
        con.close()


if __name__ == "__main__":
    main()
