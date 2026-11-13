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
    assert "from=2026-11-11&until=2026-11-12" in sources.urls("oaipmh.arxiv.org")[0]
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
        "https://api.biorxiv.org/details/biorxiv/2026-11-11/2026-11-12/0/json",
        "https://api.biorxiv.org/details/biorxiv/2026-11-11/2026-11-12/3/json",
        "https://api.biorxiv.org/details/medrxiv/2026-11-11/2026-11-12/0/json",
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
    assert query["query"] == ["OPEN_ACCESS:y AND HAS_DOI:y AND FIRST_PDATE:[2026-11-10 TO 2026-11-12]"]
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


def test_crossref_journal_articles_become_candidates_without_full_text(tmp_path):
    code, records, sources = run(tmp_path, "--sources", "crossref", "--since", "2026-11-11")
    assert code == 0
    assert sorted(by_id(records)) == ["doi-10.1007-s44297-026-00091-6", "doi-10.22335-rlct.v18i3.2411", "doi-10.5130-pjx4c836"]
    paper = by_id(records)["doi-10.1007-s44297-026-00091-6"]
    assert {k: v for k, v in paper.items() if k != "abstract"} == {
        "id": "doi-10.1007-s44297-026-00091-6",
        "doi": "10.1007/s44297-026-00091-6",
        "arxiv_id": None,
        "title": "Translating pathogen biology into diagnostic and management strategies for gummy stem blight in cucumber production",
        "authors": paper["authors"],
        "venue": "Crop Health",
        "published": "2026-11-13",
        "status": "peer_reviewed",
        "license": "cc-by",
        "url": "https://doi.org/10.1007/s44297-026-00091-6",
        "source": "crossref",
        "categories": [],
        "fulltext": {"available": False, "kind": None, "url": None},
    }
    assert paper["authors"][:2] == ["Aastha Ranjan", "Alison Lu"]
    assert paper["abstract"].startswith(
        "Abstract Gummy stem blight (GSB) is a major disease of cucurbits caused by Stagonosporopsis spp. and is")
    assert "<" not in paper["abstract"]
    other = by_id(records)["doi-10.22335-rlct.v18i3.2411"]
    assert (other["venue"], other["license"], other["published"]) == ("Revista Logos Ciencia & Tecnología", None, "2026-11-12")
    query = parse_qs(urlsplit(sources.urls("api.crossref.org")[0]).query)
    assert query["filter"][0].startswith("from-created-date:2026-11-11,until-created-date:2026-11-12,type:journal-article,")
    assert (query["sort"], query["order"], query["cursor"]) == (["created"], ["desc"], ["*"])
    assert "mailto" not in query


def test_crossref_list_requests_are_at_least_one_second_apart(tmp_path):
    _, _, sources = run(tmp_path, "--sources", "crossref", "--since", "2026-11-11")
    times = sources.times("api.crossref.org")
    assert len(times) == 2
    assert times[1] - times[0] >= 1.0
    assert f"cursor={CROSSREF_SECOND_CURSOR}" in sources.urls("api.crossref.org")[1]


def first_page_only(name):
    """Serve one Crossref fixture for the first page and the recorded empty page after it."""
    def route(request):
        q = parse_qs(urlsplit(str(request.url)).query)
        return name if q["cursor"] == ["*"] else "crossref/page2.json"
    return route


def test_preprint_and_journal_article_with_the_same_doi_come_out_once_with_journal_metadata(tmp_path):
    # arXiv 2305.05556 was revised on 2026-11-11 to add its Scientific Reports DOI; Crossref has the article.
    code, records, _ = run(
        tmp_path, "--sources", "arxiv,crossref", "--since", "2026-11-11",
        overrides={"oaipmh.arxiv.org": "pairs/arxiv_doi_pair.xml",
                   "api.crossref.org": first_page_only("pairs/crossref_doi_pair.json")})
    assert code == 0
    assert len(records) == 1
    paper = records[0]
    assert paper["id"] == "arxiv-2305.05556"
    assert paper["doi"] == "10.1038/s41598-026-77938-z"
    assert paper["arxiv_id"] == "2305.05556"
    assert (paper["status"], paper["venue"], paper["source"]) == ("peer_reviewed", "Scientific Reports", "crossref")
    assert paper["url"] == "https://doi.org/10.1038/s41598-026-77938-z"
    assert paper["fulltext"] == {"available": True, "kind": "arxiv_html", "url": "https://arxiv.org/html/2305.05556"}
    assert paper["license"] == "cc-by"
    assert "quant-ph" in paper["categories"]


def test_preprint_and_journal_article_with_the_same_title_come_out_once(tmp_path):
    code, records, _ = run(
        tmp_path, "--sources", "arxiv,crossref", "--since", "2026-11-11",
        overrides={"oaipmh.arxiv.org": "pairs/arxiv_title_pair.xml",
                   "api.crossref.org": first_page_only("pairs/crossref_title_pair.json")})
    assert code == 0
    assert [(r["id"], r["doi"], r["status"], r["fulltext"]["kind"]) for r in records] == [
        ("arxiv-2506.15578", "10.1002/qj.70201", "peer_reviewed", "arxiv_html")]


def test_journal_doi_named_by_biorxiv_links_a_preprint_to_its_differently_titled_article(tmp_path):
    code, records, _ = run(
        tmp_path, "--sources", "biorxiv,crossref", "--since", "2026-11-11",
        overrides={"api.biorxiv.org": "pairs/biorxiv_published.json",
                   "api.crossref.org": first_page_only("pairs/crossref_published.json")})
    assert code == 0
    assert len(records) == 1
    paper = records[0]
    assert (paper["id"], paper["venue"], paper["status"]) == ("doi-10.3390-genes17111413", "Genes", "peer_reviewed")
    assert paper["title"] == "Integrating CTCF and Histone Modification Profiles Identifies Distinct Chromatin Signatures in Human Cancer Cell Lines"
    assert paper["fulltext"]["kind"] == "biorxiv"
    assert paper["fulltext"]["url"].startswith("https://www.biorxiv.org/content/")


def test_preprint_listed_by_medrxiv_and_europepmc_comes_out_once_from_medrxiv(tmp_path):
    code, records, _ = run(
        tmp_path, "--sources", "medrxiv,europepmc", "--since", "2026-10-01",
        overrides={"api.biorxiv.org": "pairs/medrxiv_same_doi.json",
                   "www.ebi.ac.uk": "pairs/europepmc_same_doi.json"})
    assert code == 0
    assert [(r["id"], r["source"], r["status"], r["fulltext"]["kind"]) for r in records] == [
        ("doi-10.64898-2026.10.02.26364570", "medrxiv", "preprint", "biorxiv")]


def test_every_source_together_writes_valid_unique_candidates_newest_first(tmp_path, capsys):
    code, records, _ = run(tmp_path, "--since", "2026-11-11")
    assert code == 0
    assert len(records) == 17
    assert len({r["id"] for r in records}) == 17
    for record in records:
        assert schemas.errors("candidate", record) == [], record["id"]
    dates = [r["published"] for r in records]
    assert dates == sorted(dates, reverse=True)
    assert capsys.readouterr().out.splitlines() == [
        "arxiv: 5 found, 5 written",
        "biorxiv: 3 found, 3 written",
        "medrxiv: 2 found, 2 written",
        "europepmc: 4 found, 4 written",
        "crossref: 3 found, 3 written",
    ]


def write_state(content, seen=(), cursors=None):
    (content / "state" / "seen").mkdir(parents=True)
    lines = []
    for entry in seen:
        lines.append(json.dumps({"chunk": 1, "added_at": "2026-11-12T10:00:00Z", **entry}))
    (content / "state" / "seen" / "2026-11.jsonl").write_text("".join(line + "\n" for line in lines))
    if cursors is not None:
        (content / "state" / "cursors.json").write_text(json.dumps({"v": 1, "cursors": cursors}))
    for line in lines:
        assert schemas.errors("seen", json.loads(line)) == []


def test_papers_already_in_the_feed_are_skipped_by_id_doi_or_title(tmp_path):
    content = tmp_path / "content"
    write_state(content, seen=[
        {"id": "arxiv-2611.13622", "doi": None, "arxiv_id": "2611.13622",
         "title_key": ids.title_key("Stochastic evolution of interacting directed strings")},
        {"id": "doi-10.64898-other", "doi": "10.64898/2026.11.09.764949", "arxiv_id": None, "title_key": "0" * 20},
        {"id": "doi-10.1-other", "doi": "10.1/other", "arxiv_id": None,
         "title_key": ids.title_key("A mixed review of research on the competencies of built environment professionals "
                                    "in infrastructure delivery within emerging economies")},
    ])
    code, records, _ = run(tmp_path, "--since", "2026-11-11", content=content)
    assert code == 0
    written = set(by_id(records))
    assert len(records) == 14
    assert not written & {"arxiv-2611.13622", "doi-10.64898-2026.11.09.764949", "doi-10.5130-pjx4c836"}


def test_journal_article_of_a_preprint_already_in_the_feed_is_skipped(tmp_path):
    content = tmp_path / "content"
    crossref_title = json.loads((FIXTURES / "pairs/crossref_title_pair.json").read_text())["message"]["items"][0]["title"][0]
    write_state(content, seen=[
        {"id": "arxiv-2506.15578", "doi": None, "arxiv_id": "2506.15578", "title_key": ids.title_key(crossref_title)},
    ])
    code, records, _ = run(
        tmp_path, "--sources", "crossref", "--since", "2026-11-11", content=content,
        overrides={"api.crossref.org": first_page_only("pairs/crossref_title_pair.json")})
    assert code == 0
    assert records == []


def test_each_source_starts_the_day_after_its_cursor_and_ends_yesterday(tmp_path):
    content = tmp_path / "content"
    write_state(content, cursors={"arxiv": "2026-11-05", "crossref": "2026-11-09"})
    _, _, sources = run(tmp_path, content=content)
    assert "from=2026-11-06&until=2026-11-12" in sources.urls("oaipmh.arxiv.org")[0]
    assert "from-created-date%3A2026-11-10%2Cuntil-created-date%3A2026-11-12" in sources.urls("api.crossref.org")[0]
    # No cursor: the last two finished days.
    assert sources.urls("api.biorxiv.org")[0] == "https://api.biorxiv.org/details/biorxiv/2026-11-11/2026-11-12/0/json"


def test_missing_state_folder_means_nothing_seen_and_the_last_two_finished_days(tmp_path):
    code, records, sources = run(tmp_path, "--sources", "arxiv", content=tmp_path / "no-such-checkout")
    assert code == 0
    assert len(records) == 5
    assert "from=2026-11-11&until=2026-11-12" in sources.urls("oaipmh.arxiv.org")[0]


def test_until_sets_the_last_day_of_every_window(tmp_path):
    content = tmp_path / "content"
    write_state(content, cursors={"biorxiv": "2026-11-07"})
    _, _, sources = run(tmp_path, "--sources", "biorxiv,medrxiv,europepmc", "--until", "2026-11-09", content=content)
    assert sources.urls("api.biorxiv.org") == [
        "https://api.biorxiv.org/details/biorxiv/2026-11-08/2026-11-09/0/json",
        "https://api.biorxiv.org/details/biorxiv/2026-11-08/2026-11-09/3/json",
        "https://api.biorxiv.org/details/medrxiv/2026-11-08/2026-11-09/0/json",
    ]
    query = parse_qs(urlsplit(sources.urls("www.ebi.ac.uk")[0]).query)
    assert query["query"] == ["OPEN_ACCESS:y AND HAS_DOI:y AND FIRST_PDATE:[2026-11-08 TO 2026-11-09]"]


def test_a_source_already_processed_through_the_last_day_is_skipped(tmp_path, capsys):
    content = tmp_path / "content"
    write_state(content, cursors={"arxiv": "2026-11-12", "biorxiv": "2026-11-11"})
    code, records, sources = run(tmp_path, "--sources", "arxiv,biorxiv", content=content)
    assert code == 0
    assert sources.urls("oaipmh.arxiv.org") == []
    assert sources.urls("api.biorxiv.org")[0] == "https://api.biorxiv.org/details/biorxiv/2026-11-12/2026-11-12/0/json"
    assert {r["source"] for r in records} == {"biorxiv"}
    assert capsys.readouterr().out.splitlines()[0] == "arxiv: skipped, processed through 2026-11-12"


def test_since_after_until_is_refused(tmp_path, capsys):
    code, records, sources = run(tmp_path, "--since", "2026-11-13")
    assert code == 2
    assert sources.requests == []
    assert "--since 2026-11-13 is after --until 2026-11-12" in capsys.readouterr().err


def test_since_overrides_cursors(tmp_path):
    content = tmp_path / "content"
    write_state(content, cursors={"arxiv": "2026-11-05"})
    _, _, sources = run(tmp_path, "--sources", "arxiv", "--since", "2026-11-12", content=content)
    assert "from=2026-11-12&until=2026-11-12" in sources.urls("oaipmh.arxiv.org")[0]


def test_rate_limited_answer_is_retried_after_the_time_the_server_asks(tmp_path):
    code, records, sources = run(
        tmp_path, "--sources", "crossref", "--since", "2026-11-11",
        statuses={"api.crossref.org": [(429, {"Retry-After": "7"})]})
    assert code == 0
    assert len(records) == 3
    times = sources.times("api.crossref.org")
    assert times[1] - times[0] >= 7


def test_a_failing_source_is_reported_and_the_others_are_still_written(tmp_path, capsys):
    code, records, sources = run(
        tmp_path, "--sources", "arxiv,biorxiv", "--since", "2026-11-11",
        statuses={"oaipmh.arxiv.org": [(503, {})] * 5})
    assert code == 1
    assert {r["source"] for r in records} == {"biorxiv"}
    assert len(sources.times("oaipmh.arxiv.org")) == 5
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("arxiv: failed: ")
    assert out[1] == "biorxiv: 3 found, 3 written"


def test_requests_carry_the_pipeline_user_agent_and_no_contact_details(tmp_path):
    _, _, sources = run(tmp_path, "--since", "2026-11-11")
    for _, request in sources.requests:
        assert request.headers["User-Agent"] == "paperboy-pipeline/0.1 (+https://github.com/NtrpyDev/paperboy-app)"
        assert "@" not in str(request.url)
        assert "mailto" not in str(request.url)
        assert "From" not in request.headers


def test_short_generic_titles_do_not_merge_different_papers(tmp_path):
    # The recorded Crossref page with two titles changed to "Editorial", a title many journals reuse.
    page = json.loads((FIXTURES / "crossref/page1.json").read_text())
    for item in page["message"]["items"][:2]:
        item["title"] = ["Editorial"]
    (tmp_path / "editorials.json").write_text(json.dumps(page))
    _, records, _ = run(tmp_path, "--sources", "crossref", "--since", "2026-11-11",
                        overrides={"api.crossref.org": first_page_only(str(tmp_path / "editorials.json"))})
    assert len(records) == 3
