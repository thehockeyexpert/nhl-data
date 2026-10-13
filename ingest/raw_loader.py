"""The one place that writes to the raw layer.

Every raw table has the same shape: one row per API response, stored untouched,
together with where it came from and when we loaded it.
"""

import hashlib
import os
import re

import duckdb

DATABASE = "nhl"
RAW_SCHEMA = "raw"
LOG_TABLE = f"{RAW_SCHEMA}.ingest_log"

_TABLE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


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
            payload_hash VARCHAR NOT NULL
        )
        """
    )


def load_response(con, table, source_url, season, body):
    """Store one API response. Returns True if a row was added.

    If the newest row we already hold for this URL has identical content,
    nothing is added. That is what makes reruns safe. If the content changed,
    a new row is added and the old one is kept as history.
    """
    payload_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    latest = con.execute(
        f"""
        SELECT payload_hash FROM {_qualified(table)}
        WHERE source_url = ?
        ORDER BY loaded_at DESC
        LIMIT 1
        """,
        [source_url],
    ).fetchone()
    if latest is not None and latest[0] == payload_hash:
        return False
    con.execute(
        f"INSERT INTO {_qualified(table)} VALUES (?, now(), ?, ?, ?)",
        [source_url, season, body, payload_hash],
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
