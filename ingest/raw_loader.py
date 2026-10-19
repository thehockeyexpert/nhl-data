"""The one place that writes to the raw layer.

Every raw table has the same shape: one row per API response, stored untouched,
together with where it came from and when we loaded it.
"""

import hashlib
import json
import os
import re

import duckdb

DATABASE = "nhl"
RAW_SCHEMA = "raw"
LOG_TABLE = f"{RAW_SCHEMA}.ingest_log"

_TABLE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")

# Fields that change without the data changing. They are still stored, exactly as received, but a response
# that differs only in these fields does not count as new. The weekly schedule's ticket links change almost
# every day (20 of 21 changed weeks on 2026-10-15) and no dbt model reads them. The standings carry the time they
# were produced, which changed between two loads of the same date minutes apart (2026-10-19).
IGNORED_WHEN_COMPARING = {
    "nhl_web__schedule": frozenset({"ticketsLink", "ticketsLinkFr"}),
    "nhl_web__standings": frozenset({"standingsDateTimeUtc"}),
}


def connect(database=DATABASE):
    """Connect to MotherDuck and make sure the database exists.

    DuckDB reads the motherduck_token environment variable by itself,
    so the token never appears in this code.
    """
    if not os.environ.get("motherduck_token"):
        raise RuntimeError("The environment variable motherduck_token is not set.")
    con = duckdb.connect("md:")
    con.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
    con.execute(f"USE {database}")
    return con


def _qualified(table):
    if not _TABLE_NAME.match(table):
        raise ValueError(f"Not a valid raw table name: {table!r}")
    return f"{RAW_SCHEMA}.{table}"


def ensure_table(con, table, seasonal=True):
    """Create the raw schema and table if they do not exist yet.

    Reference data that does not belong to a season (teams, franchises)
    uses seasonal=False, which lets the season column stay empty.
    """
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA}")
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {_qualified(table)} (
            source_url   VARCHAR NOT NULL,
            loaded_at    TIMESTAMPTZ NOT NULL,
            season       INTEGER{' NOT NULL' if seasonal else ''},
            payload      JSON NOT NULL,
            payload_hash VARCHAR NOT NULL,
            compare_hash VARCHAR
        )
        """
    )
    # Tables created before compare_hash existed get the column; their older rows leave it empty.
    con.execute(f"ALTER TABLE {_qualified(table)} ADD COLUMN IF NOT EXISTS compare_hash VARCHAR")


def _sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _without(value, ignored):
    """A copy of parsed JSON with the ignored field names removed at every level."""
    if isinstance(value, dict):
        return {key: _without(item, ignored) for key, item in value.items() if key not in ignored}
    if isinstance(value, list):
        return [_without(item, ignored) for item in value]
    return value


def compare_hash(table, body):
    """The hash used to decide whether a response changed.

    For most tables it is the hash of the response exactly as received (the same as payload_hash).
    For tables in IGNORED_WHEN_COMPARING it is the hash of the response without those fields,
    written with sorted keys so the same content always gives the same hash.
    """
    ignored = IGNORED_WHEN_COMPARING.get(table)
    if not ignored:
        return _sha256(body)
    cleaned = _without(json.loads(body), ignored)
    return _sha256(json.dumps(cleaned, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def load_response(con, table, source_url, season, body):
    """Store one API response. Returns True if a row was added.

    If the newest row we already hold for this URL has the same content (see compare_hash),
    nothing is added. That is what makes reruns safe. If the content changed,
    a new row is added and the old one is kept as history.
    """
    payload_hash = _sha256(body)
    new_compare_hash = compare_hash(table, body)
    # The stored payload is only fetched for an older row that has no compare_hash yet.
    latest = con.execute(
        f"""
        SELECT payload_hash, compare_hash, CASE WHEN compare_hash IS NULL THEN payload::VARCHAR END
        FROM {_qualified(table)}
        WHERE source_url = ?
        ORDER BY loaded_at DESC
        LIMIT 1
        """,
        [source_url],
    ).fetchone()
    if latest is not None:
        old_payload_hash, old_compare_hash, old_payload = latest
        if old_compare_hash is None:
            old_compare_hash = compare_hash(table, old_payload) if table in IGNORED_WHEN_COMPARING else old_payload_hash
        if old_compare_hash == new_compare_hash:
            return False
    con.execute(
        f"INSERT INTO {_qualified(table)} VALUES (?, now(), ?, ?, ?, ?)",
        [source_url, season, body, payload_hash, new_compare_hash],
    )
    return True


def ensure_log(con):
    """Create the completion log: one row each time a season finishes loading cleanly."""
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA}")
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {LOG_TABLE} (
            job         VARCHAR NOT NULL,
            season      INTEGER NOT NULL,
            finished_at TIMESTAMPTZ NOT NULL,
            requests    INTEGER NOT NULL,
            new_rows    INTEGER NOT NULL
        )
        """
    )


def log_season_done(con, job, season, requests, new_rows):
    con.execute(f"INSERT INTO {LOG_TABLE} VALUES (?, ?, now(), ?, ?)", [job, season, requests, new_rows])


def is_season_done(con, job, season):
    """True if this job has already finished this season at least once."""
    row = con.execute(
        f"SELECT 1 FROM {LOG_TABLE} WHERE job = ? AND season = ? LIMIT 1", [job, season]
    ).fetchone()
    return row is not None


def replace_text_file(con, table, source_url, path):
    """Store a downloaded text file one row per line, untouched, replacing what the table held before.

    Used for the GeoNames files: they are not NHL responses, are large, and only the newest copy is useful, so the
    owner decided on 2026-10-19 that a refresh replaces them instead of adding to them (docs/decisions.md).
    Returns the number of lines stored, or None if the stored copy already has the same content.
    """
    with open(path, "rb") as file:
        file_hash = hashlib.sha256(file.read()).hexdigest()
    qualified = _qualified(table)
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA}")
    exists = con.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_schema = ? AND table_name = ?", [RAW_SCHEMA, table]
    ).fetchone()
    if exists:
        stored = con.execute(f"SELECT any_value(file_hash) FROM {qualified} WHERE source_url = ?", [source_url]).fetchone()
        if stored[0] == file_hash:
            return None
    literal_path = str(path).replace("'", "''")
    # One statement, so the table is never left half-replaced. Lines are split on the newline only; nothing else changes.
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {qualified} AS
        SELECT
            ?::VARCHAR AS source_url,
            now() AS loaded_at,
            generate_subscripts(lines, 1) AS line_number,
            unnest(lines) AS line,
            ?::VARCHAR AS file_hash
        FROM (SELECT string_split(rtrim(content, chr(10)), chr(10)) AS lines FROM read_text('{literal_path}'))
        """,
        [source_url, file_hash],
    )
    return con.execute(f"SELECT count(*) FROM {qualified}").fetchone()[0]
