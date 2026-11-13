"""A polite HTTP client for fetching full text.

It identifies itself with the project's User-Agent and nothing personal, waits between
requests to the same host, retries 429 and 5xx answers with backoff (honoring Retry-After),
and turns a 403 or a bot challenge page into Unavailable instead of trying to get around it.
"""
import email.utils
import json
import time
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

import httpx

USER_AGENT = "paperboy-pipeline/0.1 (+https://github.com/NtrpyDev/paperboy-app)"

# Seconds between requests to one host. Page hosts use the Crawl-delay their robots.txt sets
# for every user agent (read 2026-11-13): https://arxiv.org/robots.txt (15),
# https://www.biorxiv.org/robots.txt and https://www.medrxiv.org/robots.txt (7),
# https://www.ebi.ac.uk/robots.txt (10). api.biorxiv.org has no robots.txt (404) and its API
# page states no rate limit, so it gets a cautious 1 second.
MIN_INTERVAL = {
    "arxiv.org": 15.0,
    "www.biorxiv.org": 7.0,
    "www.medrxiv.org": 7.0,
    "www.ebi.ac.uk": 10.0,
    "api.biorxiv.org": 1.0,
}
DEFAULT_INTERVAL = 3.0

MAX_ATTEMPTS = 4
BACKOFF_BASE = 5.0
MAX_RETRY_AFTER = 300.0

CHALLENGE_MARKERS = (
    "<title>just a moment...</title>",
    "<title>attention required! | cloudflare</title>",
    "challenges.cloudflare.com",
    "cf-chl-",
    "_cf_chl_opt",
    "enable javascript and cookies to continue",
)


class Unavailable(Exception):
    """No lawful full text can be had from this source. The message says why."""


class FetchError(Exception):
    """A real failure: network trouble, a server that kept failing, or a page we cannot parse."""


def _is_challenge(response: httpx.Response) -> bool:
    if response.headers.get("cf-mitigated", "").lower() == "challenge":
        return True
    if "html" not in response.headers.get("content-type", ""):
        return False
    head = response.text[:20000].lower()
    return any(marker in head for marker in CHALLENGE_MARKERS)


def _retry_after(response: httpx.Response, now: float) -> float | None:
    value = response.headers.get("retry-after")
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        return max(0.0, email.utils.parsedate_to_datetime(value).timestamp() - now)
    except (TypeError, ValueError):
        return None


class PoliteClient:
    def __init__(
        self,
        *,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
        stamp_dir: Path | None = None,
    ):
        self._client = httpx.Client(
            transport=transport,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=60.0,
        )
        self._sleep = sleep
        self._clock = clock
        self._stamp_dir = stamp_dir

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # The last request time per host is kept in a small file in the work folder, so the
    # wait holds across separate fetch commands run one after another.
    def _stamp_path(self, host: str) -> Path | None:
        return self._stamp_dir / host if self._stamp_dir else None

    def _wait_for_turn(self, host: str) -> None:
        interval = MIN_INTERVAL.get(host, DEFAULT_INTERVAL)
        path = self._stamp_path(host)
        last = None
        if path and path.exists():
            try:
                last = json.loads(path.read_text())["last_request"]
            except (ValueError, KeyError):
                last = None
        if last is not None:
            wait = last + interval - self._clock()
            if wait > 0:
                self._sleep(wait)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"last_request": self._clock()}))

    def get(self, url: str, *, accept: str | None = None) -> httpx.Response:
        """GET a URL. Returns the response for 2xx and 404; raises Unavailable or FetchError otherwise."""
        host = urlsplit(url).hostname or ""
        headers = {"Accept": accept} if accept else {}
        for attempt in range(1, MAX_ATTEMPTS + 1):
            self._wait_for_turn(host)
            try:
                response = self._client.get(url, headers=headers)
            except httpx.TransportError as error:
                if attempt == MAX_ATTEMPTS:
                    raise FetchError(f"GET {url} failed: {error}") from error
                self._sleep(BACKOFF_BASE * 2 ** (attempt - 1))
                continue
            if _is_challenge(response):
                raise Unavailable(
                    f"{host} answered with a bot challenge page (HTTP {response.status_code}); not bypassed"
                )
            status = response.status_code
            if status == 403:
                raise Unavailable(f"{host} refused the request (HTTP 403); not bypassed")
            if status == 429 or status >= 500:
                if attempt == MAX_ATTEMPTS:
                    raise FetchError(f"GET {url} kept failing: HTTP {status} after {attempt} attempts")
                delay = _retry_after(response, self._clock())
                if delay is None:
                    delay = BACKOFF_BASE * 2 ** (attempt - 1)
                if delay > MAX_RETRY_AFTER:
                    raise FetchError(f"GET {url}: HTTP {status} with Retry-After of {delay:.0f} s, too long to wait")
                self._sleep(delay)
                continue
            if status == 404 or 200 <= status < 300:
                return response
            raise FetchError(f"GET {url}: unexpected HTTP {status}")
        raise AssertionError("unreachable")
