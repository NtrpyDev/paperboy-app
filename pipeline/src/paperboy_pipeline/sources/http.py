"""The one HTTP client every source adapter shares: spacing per host, retries, no personal details.

arXiv asks for at most one request every three seconds across all its hosts, and Crossref's
public pool allows one list request per second (docs/research/paper-sources-and-licensing.md).
Requests are spaced from the start of the previous request to the same host group.
"""
import time
from collections.abc import Callable
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

import httpx

USER_AGENT = "paperboy-pipeline/0.1 (+https://github.com/NtrpyDev/paperboy-app)"

# Host suffix -> minimum seconds between request starts. Every host under the suffix shares one gap.
SPACING = {"arxiv.org": 3.0, "crossref.org": 1.0}

RETRIES = 4
BACKOFF = 2.0
MAX_WAIT = 120.0


class SourceError(Exception):
    """A source could not be read after retries, or answered with something unusable."""


def make_client(transport: httpx.BaseTransport | None = None) -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=httpx.Timeout(120.0, connect=20.0),
        follow_redirects=True,
        transport=transport,
    )


class Http:
    def __init__(
        self,
        client: httpx.Client,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        spacing: dict[str, float] = SPACING,
        retries: int = RETRIES,
        backoff: float = BACKOFF,
    ):
        self.client = client
        self.clock = clock
        self.sleep = sleep
        self.spacing = spacing
        self.retries = retries
        self.backoff = backoff
        self._last_start: dict[str, float] = {}

    def get(self, url: str, params: dict | None = None, *, retry_if: Callable[[httpx.Response], bool] | None = None) -> httpx.Response:
        """GET with spacing and retries. Retries on 429, 5xx, transport errors, and when retry_if says so.

        Raises SourceError when the last attempt still fails.
        """
        for attempt in range(self.retries + 1):
            self._wait_turn(url)
            try:
                response = self.client.get(url, params=params)
            except httpx.TransportError as error:
                if attempt == self.retries:
                    raise SourceError(f"{url}: {error}") from error
                self.sleep(self._backoff(attempt))
                continue
            retryable = response.status_code == 429 or response.status_code >= 500
            if not retryable and retry_if is not None and response.status_code < 400:
                retryable = retry_if(response)
            if not retryable:
                if response.status_code >= 400:
                    raise SourceError(f"{response.request.url}: HTTP {response.status_code}")
                return response
            if attempt == self.retries:
                raise SourceError(f"{response.request.url}: HTTP {response.status_code} after {self.retries + 1} attempts")
            self.sleep(max(self._backoff(attempt), _retry_after(response)))
        raise AssertionError("unreachable")

    def _backoff(self, attempt: int) -> float:
        return min(self.backoff * 2**attempt, MAX_WAIT)

    def _wait_turn(self, url: str) -> None:
        host = httpx.URL(url).host
        group = next((suffix for suffix in self.spacing if host == suffix or host.endswith("." + suffix)), None)
        if group is None:
            return
        last = self._last_start.get(group)
        if last is not None:
            wait = last + self.spacing[group] - self.clock()
            if wait > 0:
                self.sleep(wait)
        self._last_start[group] = self.clock()


def _retry_after(response: httpx.Response) -> float:
    """Seconds from a Retry-After header (seconds or an HTTP date); 0 when absent or unreadable."""
    value = response.headers.get("Retry-After")
    if not value:
        return 0.0
    try:
        return min(max(float(value), 0.0), MAX_WAIT)
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return 0.0
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return min(max((when - datetime.now(timezone.utc)).total_seconds(), 0.0), MAX_WAIT)
