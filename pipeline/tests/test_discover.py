"""The discover command at its seam: recorded source responses in, work/candidates.jsonl out.

Fixtures in tests/fixtures/discover/ are real responses recorded on 2026-11-13 UTC, trimmed to a
handful of records. Files under pairs/ hold real records of one paper seen twice (arXiv and its
journal version, a bioRxiv preprint and its journal version, a medRxiv preprint in Europe PMC).
"""
import json
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx

from paperboy_pipeline import ids, schemas
from paperboy_pipeline.cli import build_parser
from paperboy_pipeline.commands import discover

FIXTURES = Path(__file__).parent / "fixtures" / "discover"
TODAY = date(2026, 11, 13)
FIRST_ARXIV_TOKEN = "verb%3DListRecords%26metadataPrefix%3DarXivRaw%26from%3D2026-11-11%26skip%3D1300"
EPMC_SECOND_CURSOR = "AoJwwKSw4aEDKDU2ODk1ODYz"
CROSSREF_SECOND_CURSOR = "MTc5NDUzOTYyOTAwMCwxMC42Mjk1MSUyRnNvbHVzaWJlcnNhbWEudjNpNC4zNzE4"


class FakeClock:
    def __init__(self):
        self.now = 1000.0
        self.sleeps = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def default_route(request: httpx.Request) -> str | None:
    """Pick the fixture file a request should get, from the request itself."""
    url = urlsplit(str(request.url))
    q = {k: v[0] for k, v in parse_qs(url.query).items()}
    if url.hostname == "oaipmh.arxiv.org":
        return "arxiv/page2.xml" if q.get("resumptionToken") == FIRST_ARXIV_TOKEN else "arxiv/page1.xml"
    if url.hostname == "api.biorxiv.org":
        server, cursor = url.path.split("/")[2], url.path.split("/")[5]
        if server == "biorxiv":
            return {"0": "biorxiv/page0.json", "3": "biorxiv/page1.json"}[cursor]
        return "medrxiv/page0.json"
    if url.hostname == "www.ebi.ac.uk":
        return {"*": "europepmc/page1.json", EPMC_SECOND_CURSOR: "europepmc/page2.json"}.get(
            q["cursorMark"], "europepmc/page3.json")
    if url.hostname == "api.crossref.org":
        return "crossref/page1.json" if q["cursor"] == "*" else "crossref/page2.json"
    return None


class Sources:
    """A mock transport that serves fixtures and records every request with the fake clock's time."""

    def __init__(self, clock, overrides=None, statuses=None):
        self.clock = clock
        self.overrides = overrides or {}
        self.statuses = statuses or {}
        self.requests = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append((self.clock(), request))
        host = request.url.host
        if host in self.statuses and self.statuses[host]:
            status, headers = self.statuses[host].pop(0)
            return httpx.Response(status, headers=headers)
        name = self.overrides.get(host) or default_route(request)
        if callable(name):
            name = name(request)
        if name is None:
            return httpx.Response(404)
        return httpx.Response(200, content=(FIXTURES / name).read_bytes())

    def times(self, host):
        return [t for t, r in self.requests if r.url.host == host]

    def urls(self, host):
        return [str(r.url) for t, r in self.requests if r.url.host == host]


def run(tmp_path, *argv, overrides=None, statuses=None, content=None, today=TODAY):
    work = tmp_path / "work"
    content = content or tmp_path / "content"
    clock = FakeClock()
    sources = Sources(clock, overrides, statuses)
    args = build_parser().parse_args(["discover", "--work", str(work), "--content", str(content), *argv])
    code = discover.run(args, transport=httpx.MockTransport(sources.handle), clock=clock, sleep=clock.sleep, today=today)
    path = work / "candidates.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    return code, records, sources


def by_id(records):
    return {r["id"]: r for r in records}


def test_arxiv_new_papers_become_candidates(tmp_path):
    code, records, _ = run(tmp_path, "--sources", "arxiv", "--since", "2026-11-11")
    assert code == 0
    assert sorted(by_id(records)) == [
        "arxiv-2611.11868", "arxiv-2611.13070", "arxiv-2611.13192", "arxiv-2611.13440", "arxiv-2611.13622"]
    assert by_id(records)["arxiv-2611.13622"] == {
        "id": "arxiv-2611.13622",
        "doi": None,
        "arxiv_id": "2611.13622",
        "title": "Stochastic evolution of interacting directed strings",
        "authors": ["S. S. Manna", "Deepak Dhar"],
        "abstract": by_id(records)["arxiv-2611.13622"]["abstract"],
        "venue": "arXiv",
        "published": "2026-11-10",
        "status": "preprint",
        "license": "cc-by",
        "url": "https://arxiv.org/abs/2611.13622",
        "source": "arxiv",
        "categories": ["cond-mat.stat-mech"],
        "fulltext": {"available": True, "kind": "arxiv_html", "url": "https://arxiv.org/html/2611.13622"},
    }
    abstract = by_id(records)["arxiv-2611.13622"]["abstract"]
    assert abstract.startswith("We study the stochastic dynamics of a system of $N$ polymer rings")
    assert "$y/\\sqrt{t}$" in abstract
