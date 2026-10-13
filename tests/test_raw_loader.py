import json

import duckdb
import pytest

from ingest import schedule
from ingest.raw_loader import ensure_table, load_response

URL = "https://example.test/schedule/2025-10-07"


@pytest.fixture
def con():
    """A throwaway database that lives in memory. Nothing touches MotherDuck."""
    con = duckdb.connect(":memory:")
    ensure_table(con, "nhl_web__schedule")
    yield con
    con.close()


def row_count(con, table="nhl_web__schedule"):
    return con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]


def test_first_load_adds_a_row_with_the_payload_untouched(con):
    body = '{"games":  [1, 2]}'
    assert load_response(con, "nhl_web__schedule", URL, 20252026, body) is True
    row = con.execute(
        "SELECT source_url, season, payload::VARCHAR, loaded_at IS NOT NULL FROM raw.nhl_web__schedule"
    ).fetchone()
    assert row == (URL, 20252026, body, True)


def test_reloading_the_same_content_adds_nothing(con):
    assert load_response(con, "nhl_web__schedule", URL, 20252026, '{"a": 1}') is True
    assert load_response(con, "nhl_web__schedule", URL, 20252026, '{"a": 1}') is False
    assert row_count(con) == 1


def test_changed_content_adds_a_new_version_and_keeps_the_old(con):
    load_response(con, "nhl_web__schedule", URL, 20252026, '{"score": 1}')
    assert load_response(con, "nhl_web__schedule", URL, 20252026, '{"score": 2}') is True
    assert row_count(con) == 2


def test_same_content_from_a_different_url_is_stored(con):
    load_response(con, "nhl_web__schedule", URL, 20252026, '{"a": 1}')
    assert load_response(con, "nhl_web__schedule", URL + "x", 20252026, '{"a": 1}') is True


def test_rejects_unsafe_table_names(con):
    with pytest.raises(ValueError):
        load_response(con, "x; drop table y", URL, 20252026, "{}")


class FakeClient:
    """Stands in for the NHL API: a three-week season."""

    def __init__(self):
        self.urls = []

    def fetch(self, url):
        self.urls.append(url)
        if "/season?" in url:
            return json.dumps(
                {"data": [{"preseasonStartdate": "2025-09-20T19:00:00", "endDate": "2025-10-05T00:00:00"}]}
            )
        if "/game?" in url:
            return json.dumps({"data": [], "total": 0})
        week = url.rsplit("/", 1)[1]
        following = {"2025-09-20": "2025-09-27", "2025-09-27": "2025-10-04", "2025-10-04": "2025-10-11"}
        return json.dumps({"nextStartDate": following[week], "gameWeek": []})


def test_schedule_job_walks_every_week_and_reruns_add_nothing():
    con = duckdb.connect(":memory:")
    client = FakeClient()

    first = schedule.run(20252026, client, con)
    assert [u.rsplit("/", 1)[1] for u in client.urls[2:]] == ["2025-09-20", "2025-09-27", "2025-10-04"]
    assert first == {"nhl_stats__season": [1, 1], "nhl_stats__game": [1, 1], "nhl_web__schedule": [3, 3]}

    second = schedule.run(20252026, client, con)
    assert second == {"nhl_stats__season": [1, 0], "nhl_stats__game": [1, 0], "nhl_web__schedule": [3, 0]}
    assert row_count(con, "nhl_web__schedule") == 3
