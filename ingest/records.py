"""Load the NHL's records lists (players, draft, awards, playoff series) and standings rules into raw.

Each source is one request for the whole list, stored as one raw row.
Run it with:  uv run python -m ingest.records
"""

from ingest.nhl_api import NhlApiClient
from ingest.raw_loader import connect, ensure_table, load_response

RECORDS = "https://records.nhl.com/site/api"

# raw table -> URL
SOURCES = {
    "nhl_records__player": f"{RECORDS}/player?limit=-1",
    "nhl_records__draft": f"{RECORDS}/draft?limit=-1",
    "nhl_records__trophy": f"{RECORDS}/trophy",
    "nhl_records__award_details": f"{RECORDS}/award-details?limit=-1",
    "nhl_records__playoff_series": f"{RECORDS}/playoff-series?limit=-1",
    "nhl_web__standings_season": "https://api-web.nhle.com/v1/standings-season",
}


def run(client, con):
    """Fetch and store each list. Returns {table: added}."""
    added = {}
    for table, url in SOURCES.items():
        # These lists do not belong to a season, so the season column stays empty.
        ensure_table(con, table, seasonal=False)
        added[table] = load_response(con, table, url, None, client.fetch(url))
        # Only the table name and the outcome are printed, never response content.
        print(f"  {'new      ' if added[table] else 'unchanged'}  {table}")
    return added


def main():
    con = connect()
    client = NhlApiClient()
    try:
        added = run(client, con)
    finally:
        client.close()
        con.close()
    print(f"  total new rows: {sum(added.values())}")


if __name__ == "__main__":
    main()
