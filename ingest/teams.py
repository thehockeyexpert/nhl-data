"""Load the NHL's team and franchise reference lists into the raw layer.

Run it with:  uv run python -m ingest.teams
"""

from ingest.nhl_api import NhlApiClient
from ingest.raw_loader import connect, ensure_table, load_response

# raw table -> URL
SOURCES = {
    "nhl_stats__team": "https://api.nhle.com/stats/rest/en/team",
    "nhl_records__franchise": "https://records.nhl.com/site/api/franchise",
    "nhl_records__franchise_team_totals": "https://records.nhl.com/site/api/franchise-team-totals",
}


def run(client, con):
    """Fetch and store each reference list. Returns {table: added}."""
    added = {}
    for table, url in SOURCES.items():
        # These lists do not belong to a season, so the season column stays empty.
        ensure_table(con, table, seasonal=False)
        added[table] = load_response(con, table, url, None, client.fetch(url))
        print(f"  {'new      ' if added[table] else 'unchanged'}  {url}")
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
