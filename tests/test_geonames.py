import io
import zipfile

import duckdb
import pytest

from ingest import geonames


def zipped(name, text):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, text)
    return buffer.getvalue()


class FakeGeoNames:
    """Stands in for download.geonames.org."""

    def __init__(self, places=("1\tToronto\t43.7\t-79.4", "2\tScarborough\t43.8\t-79.2")):
        self.urls = []
        self.text = "\n".join(places) + "\n"

    def fetch_bytes(self, url):
        self.urls.append(url)
        if url.endswith(".zip"):
            member = geonames.SOURCES[next(t for t, (u, _) in geonames.SOURCES.items() if u == url)][1]
            return zipped(member, self.text)
        return ("#ISO\tISO3\nCA\tCAN\n").encode("utf-8")


@pytest.fixture
def con():
    con = duckdb.connect(":memory:")
    yield con
    con.close()


def test_each_file_is_stored_one_row_per_line_untouched(con):
    client = FakeGeoNames()
    assert geonames.run(client, con) == {"geonames__cities500": 2, "geonames__ca": 2, "geonames__country_info": 2}
    assert client.urls == [url for url, _ in geonames.SOURCES.values()]
    assert con.execute("SELECT line_number, line FROM raw.geonames__cities500 ORDER BY 1").fetchall() == [
        (1, "1\tToronto\t43.7\t-79.4"), (2, "2\tScarborough\t43.8\t-79.2")]
    assert con.execute("SELECT line FROM raw.geonames__country_info ORDER BY line_number").fetchall() == [
        ("#ISO\tISO3",), ("CA\tCAN",)]


def test_rerun_with_unchanged_files_changes_nothing(con):
    geonames.run(FakeGeoNames(), con)
    loaded_at = con.execute("SELECT max(loaded_at) FROM raw.geonames__ca").fetchone()
    assert geonames.run(FakeGeoNames(), con) == dict.fromkeys(geonames.SOURCES)
    assert con.execute("SELECT max(loaded_at) FROM raw.geonames__ca").fetchone() == loaded_at


def test_a_changed_file_replaces_the_table_instead_of_adding(con):
    geonames.run(FakeGeoNames(), con)
    stored = geonames.run(FakeGeoNames(places=["3\tThunder Bay\t48.4\t-89.2"]), con)
    assert stored["geonames__ca"] == 1
    assert con.execute("SELECT count(*), any_value(line) FROM raw.geonames__ca").fetchone() == (
        1, "3\tThunder Bay\t48.4\t-89.2")


def test_progress_output_never_contains_file_content(con, capsys):
    geonames.run(FakeGeoNames(), con)
    out = capsys.readouterr().out
    assert "Toronto" not in out and "Scarborough" not in out and "CAN" not in out
