"""The one place that makes web requests: the NHL API, and the GeoNames files used for birthplace coordinates.

It is deliberately polite: one request at a time, a pause between requests,
and a patient retry when the server is busy.
"""

import json
import time

import httpx

USER_AGENT = "nhl-data (personal project; https://github.com/thehockeyexpert/nhl-data)"

# Status codes that mean "try again later" rather than "your request is wrong".
RETRY_STATUSES = {429, 500, 502, 503, 504}


class NhlApiError(Exception):
    """Raised when a request cannot be completed."""


class NhlApiClient:
    def __init__(
        self,
        min_interval=1.0,
        timeout=30.0,
        max_retries=4,
        backoff_start=2.0,
        max_wait=60.0,
        transport=None,
        sleep=time.sleep,
        clock=time.monotonic,
    ):
        # transport, sleep and clock exist so the tests can run with no network and no waiting.
        self._http = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            transport=transport,
        )
        self._min_interval = min_interval
        self._max_retries = max_retries
        self._backoff_start = backoff_start
        self._max_wait = max_wait
        self._sleep = sleep
        self._clock = clock
        self._last_request_at = None

    def close(self):
        self._http.close()

    def _pace(self):
        """Wait until at least min_interval seconds have passed since the last request."""
        if self._last_request_at is not None:
            remaining = self._min_interval - (self._clock() - self._last_request_at)
            if remaining > 0:
                self._sleep(remaining)
        self._last_request_at = self._clock()

    def _retry_wait(self, attempt, response):
        """How long to wait before retry number `attempt` (0, 1, 2, ...)."""
        wait = self._backoff_start * (2**attempt)
        if response is not None:
            retry_after = response.headers.get("Retry-After", "")
            if retry_after.isdigit():
                wait = max(wait, float(retry_after))
        return min(wait, self._max_wait)

    def fetch(self, url):
        """Return the response body for `url` as text, exactly as the NHL sent it."""
        return self._checked_json_text(url, self._get(url))

    def fetch_bytes(self, url):
        """Return the response body for `url` as bytes, for files that are not JSON (such as a zip)."""
        return self._get(url).content

    def _get(self, url):
        """The successful response for `url`, after pacing and any retries."""
        for attempt in range(self._max_retries + 1):
            self._pace()
            response = None
            try:
                response = self._http.get(url)
            except httpx.TransportError as error:
                # Timeouts and dropped connections: worth another try.
                problem = type(error).__name__
            else:
                if response.status_code == 200:
                    return response
                if response.status_code not in RETRY_STATUSES:
                    raise NhlApiError(f"HTTP {response.status_code} for {url}")
                problem = f"HTTP {response.status_code}"

            if attempt == self._max_retries:
                raise NhlApiError(f"Gave up on {url} after {attempt + 1} attempts ({problem})")
            wait = self._retry_wait(attempt, response)
            print(f"  {problem}; waiting {wait:.0f}s before retrying {url}")
            self._sleep(wait)

    @staticmethod
    def _checked_json_text(url, response):
        # Make sure we never store an error page or a cut-off download in the raw layer.
        text = response.text
        try:
            json.loads(text)
        except ValueError:
            raise NhlApiError(f"Response from {url} is not valid JSON") from None
        return text
