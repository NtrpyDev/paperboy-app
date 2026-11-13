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
        return {"*": "europepmc/page1.json", EPMC_SECOND_CURSOR: "europepmc/page2.json"}[q["cursorMark"]]
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


def test_arxiv_requests_are_three_seconds_apart_and_follow_the_resumption_token(tmp_path):
    _, _, sources = run(tmp_path, "--sources", "arxiv", "--since", "2026-11-11")
    times = sources.times("oaipmh.arxiv.org")
    assert len(times) == 2
    assert times[1] - times[0] >= 3.0
    assert "from=2026-11-11" in sources.urls("oaipmh.arxiv.org")[0]
    assert "resumptionToken=" in sources.urls("oaipmh.arxiv.org")[1]


def test_arxiv_author_line_splits_into_names(tmp_path):
    _, records, _ = run(tmp_path, "--sources", "arxiv", "--since", "2026-11-11")
    papers = by_id(records)
    assert papers["arxiv-2611.13440"]["authors"] == ["Joshua Evan Greene", "Shiyu Liang", "John Luecke"]
    assert papers["arxiv-2611.11868"]["authors"] == ["Francisco M. L\\'{o}pez", "Francisco Cruz"]
    assert papers["arxiv-2611.13070"]["authors"][-1] == "for the Alzheimer's Disease Neuroimaging Initiative"


def test_arxiv_keeps_the_journal_doi_and_license_it_states(tmp_path):
    _, records, _ = run(tmp_path, "--sources", "arxiv", "--since", "2026-11-11")
    paper = by_id(records)["arxiv-2611.13192"]
    assert paper["doi"] == "10.1145/3841645.3843276"
    assert paper["license"] == "cc-by-nc-nd"
    assert paper["status"] == "preprint"
    assert by_id(records)["arxiv-2611.13070"]["license"] == "cc-by-nc-sa"


def test_limit_caps_new_papers_per_source_and_stops_paging(tmp_path):
    _, records, sources = run(tmp_path, "--sources", "arxiv", "--since", "2026-11-11", "--limit", "2")
    assert len(records) == 2
    assert len(sources.times("oaipmh.arxiv.org")) == 1


def test_arxiv_no_records_match_means_no_candidates(tmp_path):
    no_records = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
        b"<responseDate>2026-11-13T03:30:22Z</responseDate><request>http://oaipmh.arxiv.org/oai</request>"
        b"<error code='noRecordsMatch'>No records</error></OAI-PMH>"
    )
    (tmp_path / "none.xml").write_bytes(no_records)
    code, records, _ = run(tmp_path, "--sources", "arxiv", overrides={"oaipmh.arxiv.org": str(tmp_path / "none.xml")})
    assert code == 0
    assert records == []


def test_biorxiv_and_medrxiv_first_versions_become_candidates(tmp_path):
    code, records, sources = run(tmp_path, "--sources", "biorxiv,medrxiv", "--since", "2026-11-11")
    assert code == 0
    assert sorted(by_id(records)) == [
        "doi-10.64898-2026.11.08.765212",
        "doi-10.64898-2026.11.09.26367690",
        "doi-10.64898-2026.11.09.26367692",
        "doi-10.64898-2026.11.09.764949",
        "doi-10.64898-2026.11.09.765261",
    ]
    paper = by_id(records)["doi-10.64898-2026.11.09.764949"]
    assert {k: v for k, v in paper.items() if k != "abstract"} == {
        "id": "doi-10.64898-2026.11.09.764949",
        "doi": "10.64898/2026.11.09.764949",
        "arxiv_id": None,
        "title": paper["title"],
        "authors": ["Stine, G. M.", "Gabel, J.", "Watters, N.", "Jazayeri, M."],
        "venue": "bioRxiv",
        "published": "2026-11-11",
        "status": "preprint",
        "license": "cc-by",
        "url": "https://doi.org/10.64898/2026.11.09.764949",
        "source": "biorxiv",
        "categories": ["neuroscience"],
        "fulltext": {
            "available": True,
            "kind": "biorxiv",
            "url": "https://www.biorxiv.org/content/early/2026/11/11/2026.11.09.764949.source.xml",
        },
    }
    assert paper["title"].startswith("OpenDrive: An Open-Source Microdrive")
    assert paper["abstract"].startswith("Neuropixels-NHP probes have ushered in a new era")
    assert by_id(records)["doi-10.64898-2026.11.09.26367690"]["venue"] == "medRxiv"
    assert by_id(records)["doi-10.64898-2026.11.09.26367690"]["fulltext"]["kind"] == "biorxiv"
    assert by_id(records)["doi-10.64898-2026.11.08.765212"]["license"] == "other"
    assert sources.urls("api.biorxiv.org") == [
        "https://api.biorxiv.org/details/biorxiv/2026-11-11/2026-11-13/0/json",
        "https://api.biorxiv.org/details/biorxiv/2026-11-11/2026-11-13/3/json",
        "https://api.biorxiv.org/details/medrxiv/2026-11-11/2026-11-13/0/json",
    ]


def test_biorxiv_no_posts_found_means_no_candidates(tmp_path):
    code, records, _ = run(tmp_path, "--sources", "biorxiv", overrides={"api.biorxiv.org": "empty/biorxiv.json"})
    assert code == 0
    assert records == []


def test_europepmc_open_access_articles_and_preprints_become_candidates(tmp_path):
    code, records, sources = run(tmp_path, "--sources", "europepmc", "--since", "2026-11-10")
    assert code == 0
    assert sorted(by_id(records)) == [
        "doi-10.1039-d6nr02497a",
        "doi-10.1371-journal.pgph.0007566",
        "doi-10.1371-journal.pone.0362399",
        "doi-10.64898-2026.10.02.26364570",
    ]
    article = by_id(records)["doi-10.1039-d6nr02497a"]
    assert {k: v for k, v in article.items() if k not in ("abstract", "authors", "categories")} == {
        "id": "doi-10.1039-d6nr02497a",
        "doi": "10.1039/d6nr02497a",
        "arxiv_id": None,
        "title": "Sensitive detection of in vivo traumatic brain injury foci using magnetic particle imaging.",
        "venue": "Nanoscale",
        "published": "2026-11-12",
        "status": "peer_reviewed",
        "license": "cc-by",
        "url": "https://europepmc.org/articles/PMC13721992",
        "source": "europepmc",
        "fulltext": {
            "available": True,
            "kind": "europepmc",
            "url": "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13721992/fullTextXML",
        },
    }
    assert article["authors"][:2] == ["Hayden J Good", "Mohammad Tabatabaei"]
    assert article["categories"][:2] == ["Brain", "Animals"]
    assert article["abstract"].startswith("Diagnosing traumatic brain injury (TBI) remains a major clinical challenge")
    preprint = by_id(records)["doi-10.64898-2026.10.02.26364570"]
    assert (preprint["status"], preprint["venue"], preprint["license"]) == ("preprint", "medRxiv", "cc-by-nc")
    assert preprint["fulltext"]["url"] == "https://www.ebi.ac.uk/europepmc/webservices/rest/PPR1334369/fullTextXML"
    query = parse_qs(urlsplit(sources.urls("www.ebi.ac.uk")[0]).query)
    assert query["query"] == ["OPEN_ACCESS:y AND HAS_DOI:y AND FIRST_PDATE:[2026-11-10 TO 2026-11-13]"]
    assert query["sort"] == ["FIRST_PDATE_D desc"]
    # The second page repeats the cursor it was asked with, which marks the end.
    assert len(sources.urls("www.ebi.ac.uk")) == 2


def test_europepmc_service_unavailable_body_is_retried(tmp_path):
    busy = tmp_path / "busy.json"
    busy.write_text('{"errCode":503,"errMsg":"Search service is temporarily unavailable. Please retry later."}')
    answers = [str(busy)]

    def route(request):
        return answers.pop(0) if answers else default_route(request)

    code, records, _ = run(tmp_path, "--sources", "europepmc", "--since", "2026-11-10", overrides={"www.ebi.ac.uk": route})
    assert code == 0
    assert len(records) == 4
