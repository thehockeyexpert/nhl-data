import httpx
import pytest

from ingest.nhl_api import NhlApiClient, NhlApiError


def make_client(responses, **kwargs):
    """A client that answers from a list of canned responses instead of the network."""
    waits = []
    queue = list(responses)

    def handler(request):
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    client = NhlApiClient(
        transport=httpx.MockTransport(handler), sleep=waits.append, clock=lambda: 0.0, **kwargs
    )
    return client, waits


def test_returns_body_exactly_as_received():
    body = '{"data": [1, 2],   "total": 2}'
    client, _ = make_client([httpx.Response(200, text=body)])
    assert client.fetch("https://example.test/a") == body


def test_pauses_between_requests():
    client, waits = make_client([httpx.Response(200, text="{}"), httpx.Response(200, text="{}")])
    client.fetch("https://example.test/a")
    client.fetch("https://example.test/b")
    assert waits == [1.0]


def test_retries_when_server_is_busy_and_obeys_retry_after():
    client, waits = make_client(
        [
            httpx.Response(503),
            httpx.Response(429, headers={"Retry-After": "7"}),
            httpx.Response(200, text="{}"),
        ],
        min_interval=0,
    )
    assert client.fetch("https://example.test/a") == "{}"
    assert waits == [2.0, 7.0]


def test_retries_after_a_timeout():
    client, waits = make_client(
        [httpx.ReadTimeout("slow"), httpx.Response(200, text="{}")], min_interval=0
    )
    assert client.fetch("https://example.test/a") == "{}"
    assert waits == [2.0]


def test_gives_up_after_max_retries():
    client, waits = make_client([httpx.Response(500)] * 5, min_interval=0)
    with pytest.raises(NhlApiError, match="after 5 attempts"):
        client.fetch("https://example.test/a")
    assert waits == [2.0, 4.0, 8.0, 16.0]


def test_does_not_retry_a_bad_request():
    client, waits = make_client([httpx.Response(404)], min_interval=0)
    with pytest.raises(NhlApiError, match="HTTP 404"):
        client.fetch("https://example.test/a")
    assert waits == []


def test_rejects_a_body_that_is_not_json():
    client, _ = make_client([httpx.Response(200, text="<html>oops</html>")])
    with pytest.raises(NhlApiError, match="not valid JSON"):
        client.fetch("https://example.test/a")
