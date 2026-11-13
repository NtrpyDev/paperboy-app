"""The fetch command, tested at its seam: a candidate in the work folder in, fulltext.md and
source.json out. Source responses are real documents recorded once into fixtures/fulltext/
and served through an httpx mock transport; nothing here touches the network."""
import json
import re
from pathlib import Path

import httpx
import pytest

from paperboy_pipeline import schemas
from paperboy_pipeline.cli import build_parser

FIXTURES = Path(__file__).parent / "fixtures" / "fulltext"
USER_AGENT = "paperboy-pipeline/0.1 (+https://github.com/NtrpyDev/paperboy-app)"


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


class FakeWeb:
    """Answers requests from a URL table. A list of responses is served in order, the last repeating."""

    def __init__(self, routes: dict):
        self.routes = routes
        self.requests: list[httpx.Request] = []

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        url = str(request.url)
        if url not in self.routes:
            raise AssertionError(f"unexpected request to {url}")
        entry = self.routes[url]
        if isinstance(entry, list):
            entry = entry.pop(0) if len(entry) > 1 else entry[0]
        status, headers, body = entry
        return httpx.Response(status, headers=headers, content=body)

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handle)

    def urls(self) -> list[str]:
        return [str(r.url) for r in self.requests]


class FakeClock:
    def __init__(self):
        self.now = 1_800_000_000.0
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


HTML = {"content-type": "text/html; charset=utf-8"}
XML = {"content-type": "application/xml"}
JSON = {"content-type": "application/json"}


def candidate(paper_id: str, **fields) -> dict:
    record = {
        "id": paper_id,
        "doi": None,
        "arxiv_id": None,
        "title": "Title from discovery",
        "authors": ["A. Author"],
        "abstract": "Abstract from discovery.",
        "venue": "arXiv",
        "published": "2026-11-11",
        "status": "preprint",
        "license": None,
        "url": "https://example.org/paper",
        "source": "arxiv",
        "categories": [],
        "fulltext": {"available": True, "kind": None, "url": None},
    }
    record.update(fields)
    assert schemas.errors("candidate", record) == []
    return record


def arxiv_candidate(arxiv_id="2611.15301", url=None) -> dict:
    return candidate(
        f"arxiv-{arxiv_id}",
        arxiv_id=arxiv_id,
        url=f"https://arxiv.org/abs/{arxiv_id}",
        fulltext={"available": True, "kind": "arxiv_html", "url": url or f"https://arxiv.org/html/{arxiv_id}"},
    )


def put_candidate(work: Path, record: dict) -> Path:
    folder = work / "papers" / record["id"]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "candidate.json").write_text(json.dumps(record))
    return folder


def run_fetch(work: Path, paper_id: str, web: FakeWeb, clock: FakeClock | None = None) -> int:
    clock = clock or FakeClock()
    args = build_parser().parse_args(["fetch", "--work", str(work), "--id", paper_id])
    return args.run(args, transport=web.transport, sleep=clock.sleep, clock=clock.time)


def read_outputs(folder: Path) -> tuple[str, dict]:
    return (folder / "fulltext.md").read_text(), json.loads((folder / "source.json").read_text())


ARXIV_URL = "https://arxiv.org/html/2611.15301"


def arxiv_web() -> FakeWeb:
    return FakeWeb({ARXIV_URL: (200, HTML, fixture("arxiv-2611.15301.html"))})


# arXiv HTML


def test_arxiv_html_becomes_markdown_with_front_matter_and_sections_in_order(tmp_path):
    folder = put_candidate(tmp_path, arxiv_candidate())

    assert run_fetch(tmp_path, "arxiv-2611.15301", arxiv_web()) == 0

    md, source = read_outputs(folder)
    assert md.startswith(
        "# The Distant Milky Way Halo from the Southern Hemisphere: Spatially broad and closer stellar"
        " debris associated to the Magellanic Stream\n"
    )
    assert (
        "Authors: Manuel Cavieres, Jesús Torres, Camila Navarrete, Himansh Rathore, Julio Chanamé,"
        " Gurtina Besla, Nicolás Garavito-Camargo, A. Katherina Vivas" in md
    )
    assert "## Abstract\n\nThe Magellanic Stream (MS) is a gaseous structure extending over $150^{\\circ}$ across" in md
    headings = re.findall(r"^(#{2,6}) (.+)$", md, flags=re.M)
    assert headings == [
        ("##", "Abstract"),
        ("##", "I Introduction"),
        ("##", "II Survey data"),
        ("##", "III Halo K-giant selection"),
        ("###", "III.1 Photometric distances"),
        ("##", "IV Spectroscopic follow-up"),
        ("###", "IV.1 Candidate selection for X-shooter follow-up"),
        ("###", "IV.2 X-shooter observations"),
        ("###", "IV.3 Candidate selection for the MagE follow-up"),
        ("###", "IV.4 MagE observations"),
        ("###", "IV.5 Stellar parameters"),
        ("###", "IV.6 Spectro-photometric distances"),
        ("##", "V Results"),
        ("###", "V.1 Metallicities"),
        ("###", "V.2 Velocity gradients"),
        ("###", "V.3 Orbits"),
        ("##", "VI Conclusions"),
        ("##", "Appendix A Supplementary figures and tables"),
        ("##", "Figures"),
        ("##", "Footnotes"),
        ("##", "References"),
    ]
    assert source == {
        "available": True,
        "url": ARXIV_URL,
        "kind": "arxiv_html",
        "license": "cc-by",
        "retrieved_at": source["retrieved_at"],
        "chars": len(md),
        "sections": 17,
    }
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", source["retrieved_at"])


def test_arxiv_equations_stay_latex_with_their_numbers(tmp_path):
    folder = put_candidate(tmp_path, arxiv_candidate())
    run_fetch(tmp_path, "arxiv-2611.15301", arxiv_web())
    md, _ = read_outputs(folder)

    assert (
        "$$\n\\boldsymbol{a}_{\\rm fictitous}(t)=-\\frac{{\\rm d}\\boldsymbol{v}_{\\rm MW}}{{\\rm d}t}. \\tag{5}\n$$"
        in md
    )
    assert "a gradient of $-1.82\\pm 0.66$ km s<sup>-1</sup> kpc<sup>-1</sup>" in md


def test_arxiv_table_numbers_survive_exactly(tmp_path):
    folder = put_candidate(tmp_path, arxiv_candidate())
    run_fetch(tmp_path, "arxiv-2611.15301", arxiv_web())
    md, _ = read_outputs(folder)

    # Table 4 of arXiv:2611.15301, row by row as the paper prints it.
    assert (
        "| Gaia DR3 source ID | Inst. | RA / [deg] | Dec. / [deg] | $d$ / [kpc] |"
        " $v_{\\rm hel}$ / [$\\mathrm{km\\,s^{-1}}$] | $T_{\\rm eff}$ / [K] | $\\log g$ / [dex] |"
        " $\\mathrm{[Fe/H]}$ / [dex] |\n|---|---|---|---|---|---|---|---|---|\n"
        "| 2622351759280470528 | MagE | 335.893366 | $-7.425410$ | $95_{-18}^{+12}$ | $-103.68\\pm 0.46$ |"
        " $4298\\pm 100$ | $0.40\\pm 0.30$ | $-1.59\\pm 0.20$ |\n"
        "| 2441369916261698304 | X-Sh | 359.169473 | $-7.962814$ | $90.2_{-2.0}^{+1.8}$ | $-169.58\\pm 0.04$ |"
        " $3660\\pm 100$ | $-0.35\\pm 0.30$ | $-1.75\\pm 0.20$ |\n"
    ) in md
    assert "**Table 4:** Coordinates and stellar parameters of the five MS candidates" in md


def test_arxiv_figures_are_listed_footnotes_kept_references_counted_and_chrome_dropped(tmp_path):
    folder = put_candidate(tmp_path, arxiv_candidate())
    run_fetch(tmp_path, "arxiv-2611.15301", arxiv_web())
    md, _ = read_outputs(folder)

    figures = re.findall(r"^- \*\*(Figure \d+):\*\* ", md, flags=re.M)
    assert figures == [f"Figure {n}" for n in range(1, 13)]
    assert "- **Figure 11:** As Figure 10, for the three MagE MS candidates. The three radial-velocity outliers are omitted.\n" in md
    assert "on Zenodo[^1]." in md
    assert "[^1]: https://doi.org/10.5281/zenodo.24083695\n" in md
    assert md.count("[^a]: The fit has bad_hessian=True") == 1
    assert "## References\n\nThe reference list (92 entries) is left out.\n" in md
    assert "Stellar Atmospheric Parameters for 754 Spectra" not in md  # the first bibliography entry
    for chrome in ("Skip to main content", "Report issue", "License: CC BY", "cavierescarrera@", "<img", "Refer to caption"):
        assert chrome not in md


# No lawful full text


def test_arxiv_paper_without_html_exits_3_and_writes_only_an_unavailable_record(tmp_path):
    folder = put_candidate(tmp_path, arxiv_candidate("2611.15335"))
    (folder / "fulltext.md").write_text("stale text from an earlier run")
    web = FakeWeb({"https://arxiv.org/html/2611.15335": (404, HTML, fixture("arxiv-2611.15335-no-html.html"))})

    assert run_fetch(tmp_path, "arxiv-2611.15335", web) == 3

    assert not (folder / "fulltext.md").exists()
    source = json.loads((folder / "source.json").read_text())
    assert source["available"] is False
    assert "no HTML rendering" in source["reason"]
    assert web.urls() == ["https://arxiv.org/html/2611.15335"]  # no fallback to the PDF


def test_candidate_without_free_full_text_exits_3_without_any_request(tmp_path):
    record = candidate("doi-10.1000-paywalled", doi="10.1000/paywalled", source="crossref",
                       fulltext={"available": False, "kind": None, "url": None})
    folder = put_candidate(tmp_path, record)
    web = FakeWeb({})

    assert run_fetch(tmp_path, "doi-10.1000-paywalled", web) == 3

    assert web.requests == []
    assert json.loads((folder / "source.json").read_text())["available"] is False
    assert not (folder / "fulltext.md").exists()


@pytest.mark.parametrize("status", [403, 503])
def test_challenge_page_counts_as_unavailable_and_is_not_retried(tmp_path, status):
    folder = put_candidate(tmp_path, arxiv_candidate())
    headers = {**HTML, "cf-mitigated": "challenge", "server": "cloudflare"}
    web = FakeWeb({ARXIV_URL: (status, headers, fixture("cloudflare-challenge.html"))})

    assert run_fetch(tmp_path, "arxiv-2611.15301", web) == 3

    assert len(web.requests) == 1
    source = json.loads((folder / "source.json").read_text())
    assert source["available"] is False
    assert "challenge" in source["reason"]
    assert not (folder / "fulltext.md").exists()


def test_challenge_page_served_with_200_is_still_caught(tmp_path):
    folder = put_candidate(tmp_path, arxiv_candidate())
    web = FakeWeb({ARXIV_URL: (200, HTML, fixture("cloudflare-challenge.html"))})

    assert run_fetch(tmp_path, "arxiv-2611.15301", web) == 3
    assert "challenge" in json.loads((folder / "source.json").read_text())["reason"]


def test_plain_403_counts_as_unavailable(tmp_path):
    folder = put_candidate(tmp_path, arxiv_candidate())
    web = FakeWeb({ARXIV_URL: (403, {"content-type": "text/plain"}, b"Forbidden")})

    assert run_fetch(tmp_path, "arxiv-2611.15301", web) == 3
    assert "403" in json.loads((folder / "source.json").read_text())["reason"]


# HTTP manners


def test_requests_carry_the_project_user_agent_and_nothing_personal(tmp_path):
    put_candidate(tmp_path, arxiv_candidate())
    web = arxiv_web()
    run_fetch(tmp_path, "arxiv-2611.15301", web)

    request = web.requests[0]
    assert request.headers["user-agent"] == USER_AGENT
    assert "from" not in request.headers
    assert "@" not in str(request.url) + "".join(request.headers.values())


def test_429_is_retried_after_the_retry_after_delay(tmp_path):
    put_candidate(tmp_path, arxiv_candidate())
    web = FakeWeb({ARXIV_URL: [
        (429, {"retry-after": "42"}, b""),
        (200, HTML, fixture("arxiv-2611.15301.html")),
    ]})
    clock = FakeClock()

    assert run_fetch(tmp_path, "arxiv-2611.15301", web, clock) == 0

    assert len(web.requests) == 2
    assert 42 in clock.sleeps


def test_server_errors_are_retried_then_reported_as_a_real_error(tmp_path):
    folder = put_candidate(tmp_path, arxiv_candidate())
    web = FakeWeb({ARXIV_URL: [(503, {"content-type": "text/plain"}, b"busy")]})
    clock = FakeClock()

    code = run_fetch(tmp_path, "arxiv-2611.15301", web, clock)

    assert code not in (0, 3)
    assert len(web.requests) == 4
    assert not (folder / "source.json").exists()
    assert not (folder / "fulltext.md").exists()
    assert sum(clock.sleeps) >= 5 + 10 + 20  # backoff doubles between the four attempts


def test_consecutive_fetches_wait_at_least_three_seconds_between_arxiv_requests(tmp_path):
    put_candidate(tmp_path, arxiv_candidate())
    put_candidate(tmp_path, arxiv_candidate("2611.15335"))
    web = FakeWeb({
        ARXIV_URL: (200, HTML, fixture("arxiv-2611.15301.html")),
        "https://arxiv.org/html/2611.15335": (404, HTML, fixture("arxiv-2611.15335-no-html.html")),
    })
    clock = FakeClock()
    request_times = []
    original = web._handle

    def timed(request):
        request_times.append(clock.now)
        return original(request)

    web._handle = timed

    run_fetch(tmp_path, "arxiv-2611.15301", web, clock)
    clock.now += 1.0  # the next command starts a second later
    run_fetch(tmp_path, "arxiv-2611.15335", web, clock)

    assert len(request_times) == 2
    assert request_times[1] - request_times[0] >= 3.0


def test_missing_or_invalid_candidate_is_a_real_error(tmp_path):
    web = FakeWeb({})
    assert run_fetch(tmp_path, "arxiv-2611.15301", web) not in (0, 3)

    folder = tmp_path / "papers" / "arxiv-2611.15301"
    folder.mkdir(parents=True)
    (folder / "candidate.json").write_text(json.dumps({"id": "arxiv-2611.15301"}))
    assert run_fetch(tmp_path, "arxiv-2611.15301", web) not in (0, 3)
    assert web.requests == []


# bioRxiv and medRxiv (JATS XML)

BIORXIV_XML = "https://www.biorxiv.org/content/early/2026/11/01/2026.10.30.763081.source.xml"
BIORXIV_XML_FINAL = "https://www.biorxiv.org/content/biorxiv/early/2026/11/01/2026.10.30.763081.source.xml"
BIORXIV_DOI = "10.64898/2026.10.30.763081"


def biorxiv_candidate(fulltext_url=BIORXIV_XML) -> dict:
    return candidate(
        "doi-10.64898-2026.10.30.763081",
        doi=BIORXIV_DOI,
        venue="bioRxiv",
        source="biorxiv",
        license="cc-by",
        url=f"https://www.biorxiv.org/content/{BIORXIV_DOI}v1",
        fulltext={"available": True, "kind": "biorxiv", "url": fulltext_url},
    )


def biorxiv_web() -> FakeWeb:
    # bioRxiv answers the API's jatsxml link with a 301 to the real file, as it did live.
    return FakeWeb({
        BIORXIV_XML: (301, {"location": BIORXIV_XML_FINAL}, b""),
        BIORXIV_XML_FINAL: (200, XML, fixture("biorxiv-2026.10.30.763081.source.xml")),
        f"https://api.biorxiv.org/details/biorxiv/{BIORXIV_DOI}": (
            200, JSON, fixture("biorxiv-details-2026.10.30.763081.json")),
    })


def test_biorxiv_jats_becomes_markdown_with_sections_in_order(tmp_path):
    folder = put_candidate(tmp_path, biorxiv_candidate())

    assert run_fetch(tmp_path, "doi-10.64898-2026.10.30.763081", biorxiv_web()) == 0

    md, source = read_outputs(folder)
    assert md.startswith("# Single-cell perturbation prediction near experimental reproducibility with GENESIS\n")
    assert ("Authors: Riccardo Conci, Davide D’Ascenzo, Sebastiano Cultrera di Montesano, Srivatsan Raghavan,"
            " Peter S. Winter, Eliezer M. Van Allen, Lorin Crawford, William Lotter") in md
    assert "## Abstract\n\nSingle-cell perturbation atlases now measure cellular responses across millions of cells" in md
    headings = re.findall(r"^#{2,6} (.+)$", md, flags=re.M)
    assert headings[:9] == [
        "Abstract",
        "Introduction",
        "GENESIS generates perturbation responses from experimental covariates",
        "Experimental reproducibility provides a reference for model performance",
        "GENESIS performance approaches experimental reproducibility",
        "GENESIS maintains strong performance with reduced training data",
        "Generated profiles recapitulate context-dependent biological programs",
        "Discussion",
        "Methods",
    ]
    assert "### Datasets and data processing\n" in md and "#### Tahoe-100M\n" in md
    assert source == {
        "available": True,
        "url": BIORXIV_XML_FINAL,
        "kind": "biorxiv",
        "license": "cc-by",
        "retrieved_at": source["retrieved_at"],
        "chars": len(md),
        "sections": 78,
    }


def test_biorxiv_numbers_in_text_and_image_only_parts_are_marked(tmp_path):
    folder = put_candidate(tmp_path, biorxiv_candidate())
    run_fetch(tmp_path, "doi-10.64898-2026.10.30.763081", biorxiv_web())
    md, _ = read_outputs(folder)

    assert ("in Pearson *Δ* (GENESIS: 0.430 [95% CI 0.381-0.482]; experimental reproducibility: 0.432"
            " [0.378-0.491]; *p* = 0.56)") in md
    # bioRxiv's XML carries these equations and tables only as images; say so instead of guessing.
    assert "[Equation shown only as an image in the source; not transcribed.]" in md
    assert ("**Supplementary Table 1:** Model performance relative to experimental reproducibility on Tahoe-100M"
            " biological-context generalization (Fig. 2a).") in md
    assert "[The table body is an image in the source and is not transcribed.]" in md
    assert "[^1]: https://github.com/rickconci/GENESIS" in md
    assert "## References\n\nThe reference list (44 entries) is left out.\n" in md
    labels = re.findall(r"^- \*\*(.+?):\*\* ", md, flags=re.M)
    assert labels[:5] == ["Fig. 1", "Fig. 2", "Fig. 3", "Fig. 4", "Extended Data Fig. 1"]
    assert len(labels) == 20


def test_biorxiv_landing_page_candidate_is_looked_up_in_the_api(tmp_path):
    folder = put_candidate(tmp_path, biorxiv_candidate(fulltext_url=None))
    web = biorxiv_web()

    assert run_fetch(tmp_path, "doi-10.64898-2026.10.30.763081", web) == 0

    assert web.urls()[0] == f"https://api.biorxiv.org/details/biorxiv/{BIORXIV_DOI}"
    assert BIORXIV_XML in web.urls()
    assert read_outputs(folder)[1]["license"] == "cc-by"


def test_biorxiv_xml_not_posted_yet_is_unavailable(tmp_path):
    folder = put_candidate(tmp_path, biorxiv_candidate())
    web = FakeWeb({BIORXIV_XML: (404, HTML, b"<html><title>Page not found</title></html>")})

    assert run_fetch(tmp_path, "doi-10.64898-2026.10.30.763081", web) == 3

    source = json.loads((folder / "source.json").read_text())
    assert source["available"] is False and "404" in source["reason"]
    assert not (folder / "fulltext.md").exists()


# Europe PMC (JATS XML)

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
EPMC_TEX = f"{EPMC}/PMC13749077/fullTextXML"
EPMC_MATHML = f"{EPMC}/PMC13707691/fullTextXML"
EPMC_SEARCH = f"{EPMC}/search?query=DOI%3A%2210.1088%2F1361-6501%2Faebb53%22&resultType=lite&format=json"


def europepmc_candidate(pmcid="PMC13749077", doi="10.1088/1361-6501/aebb53", fulltext_url="default") -> dict:
    if fulltext_url == "default":
        fulltext_url = f"https://europepmc.org/articles/{pmcid}"
    return candidate(
        "doi-" + re.sub(r"[^a-z0-9._-]", "-", doi.lower()),
        doi=doi,
        venue="Measurement Science & Technology",
        status="peer_reviewed",
        source="europepmc",
        url=f"https://doi.org/{doi}",
        fulltext={"available": True, "kind": "europepmc", "url": fulltext_url},
    )


def europepmc_web() -> FakeWeb:
    return FakeWeb({
        EPMC_TEX: (200, XML, fixture("europepmc-PMC13749077.xml")),
        EPMC_MATHML: (200, XML, fixture("europepmc-PMC13707691.xml")),
        EPMC_SEARCH: (200, JSON, fixture("europepmc-search-doi-10.1088-1361-6501-aebb53.json")),
    })


def test_europepmc_jats_becomes_markdown_with_tex_equations(tmp_path):
    record = europepmc_candidate()
    folder = put_candidate(tmp_path, record)

    assert run_fetch(tmp_path, record["id"], europepmc_web()) == 0

    md, source = read_outputs(folder)
    assert md.startswith("# Accuracy of AFM cantilever thermal calibration in fluid of varying viscosities\n")
    assert "Authors: Abideen O Ayangbemi, David R Jacobson" in md
    assert "## Abstract\n\nThermal calibration of atomic force microscopy (AFM) cantilever spring constant, *k*," in md
    headings = re.findall(r"^(#{2,6}) (.+)$", md, flags=re.M)
    assert headings[:4] == [("##", "Abstract"), ("##", "1. Introduction"), ("##", "2. Methods"),
                            ("###", "2.1. Sader-Bellon viscous PSD model")]
    # The publisher's <tex-math>, without its \documentclass wrapper.
    assert "$$\nk = \\frac{{k_\\mathrm{B}}T}{ \\langle {x^2} \\rangle}.\n$$" in md
    assert "$\\frac 1{2}{k_\\mathrm{B}}T$" in md
    assert "\\documentclass" not in md and "\\usepackage" not in md
    assert source == {
        "available": True,
        "url": EPMC_TEX,
        "kind": "europepmc",
        "license": "cc-by",
        "retrieved_at": source["retrieved_at"],
        "chars": len(md),
        "sections": 21,
    }


def test_europepmc_table_numbers_survive_exactly(tmp_path):
    record = europepmc_candidate()
    folder = put_candidate(tmp_path, record)
    run_fetch(tmp_path, record["id"], europepmc_web())
    md, _ = read_outputs(folder)

    # Table 1 of doi:10.1088/1361-6501/aebb53: two header rows merged, a spanning group row.
    assert (
        "| Medium | Local fit / *f*<sub>0</sub> (kHz) | Local fit / *Q* | Local fit / *k* (pN nm<sup>−1</sup>) |"
        " Local fit / δ*k* (%) | Global fit / *f*<sub>0</sub> (kHz) | Global fit / *Q* |"
        " Global fit / *k* (pN nm<sup>−1</sup>) | Global fit / δ*k* (%) |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
        "| *BL-AC40TS (k = 90.0 pN nm<sup>−1</sup>)* |  |  |  |  |  |  |  |  |\n"
        "| Air | 151.9 | 26.5 | 92.1 | +2.4 | 151.9 | 26.5 | 92.1 | +2.4 |\n"
        "| Water | 25.2 | 2.2 | 91.7 | +1.9 | 25.1 | 2.3 | 95.2 | +5.8 |\n"
    ) in md
    assert "| 75% glycerol | 0.9 | 0.4 | 19.6 | −2.1 | 0.7 | 0.7 | 22.8 | +14.1 |" in md
    assert "| BL-AC40TS | Air | 93.8 ± 0.01 | 37.6 ± 1.6 | 93.7 ± 3.5 | (2.65 ±0.10) × 10<sup>−26</sup> |" in md
    assert "δ*k* denotes the percentage bias of the fitted *k* relative to the input *k*" in md  # table note


NUMBER = re.compile(r"[−+-]?\d+(?:[.,]\d+)*")


def _local(el) -> str:
    return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""


@pytest.mark.parametrize("pmcid,xml", [("PMC13749077", "europepmc-PMC13749077.xml"),
                                       ("PMC13707691", "europepmc-PMC13707691.xml")])
def test_every_number_in_every_europepmc_table_body_survives_in_order(tmp_path, pmcid, xml):
    from lxml import etree

    record = europepmc_candidate(pmcid=pmcid, doi=f"10.9999/{pmcid.lower()}")
    folder = put_candidate(tmp_path, record)
    run_fetch(tmp_path, record["id"], europepmc_web())
    md, _ = read_outputs(folder)

    # Numbers read straight from the XML's table body cells, independent of the converter.
    root = etree.fromstring(fixture(xml), etree.XMLParser(load_dtd=False, no_network=True, recover=True))
    source_tables = [t for t in root.iter() if _local(t) == "table"]
    md_tables = re.findall(r"(?:^\|.*\|\n)+", md, flags=re.M)
    assert len(md_tables) == len(source_tables) > 0
    for source_table, md_table in zip(source_tables, md_tables):
        body_cells = [c for c in source_table.iter() if _local(c) in ("td", "th")
                      and not any(_local(a) == "thead" for a in c.iterancestors())]
        expected = [n for c in body_cells for n in NUMBER.findall(" ".join(c.itertext()))]
        body_rows = md_table.splitlines()[2:]
        found = NUMBER.findall(re.sub(r"\\[A-Za-z]+", " ", "\n".join(body_rows)))
        assert found == expected and len(expected) > 10, (len(found), len(expected))


def test_europepmc_mathml_without_tex_is_converted_to_latex(tmp_path):
    record = europepmc_candidate(pmcid="PMC13707691", doi="10.3390/mi17101204")
    folder = put_candidate(tmp_path, record)

    assert run_fetch(tmp_path, record["id"], europepmc_web()) == 0

    md, source = read_outputs(folder)
    # Equation (1) of doi:10.3390/mi17101204, worked by hand from its MathML.
    assert "$$\n\\cos\\theta_{k}=\\cos\\theta_{\\infty}-\\frac{q}{\\gamma_{lv}x_{k}} \\tag{1}\n$$" in md
    assert "where $\\theta_{k}$ is the apparent contact angle" in md
    assert "| $\\mathrm{SiO}_{2}$ | 10 | 1.994 ± 0.019 | 66.51 ± 0.52 |" in md
    assert "<mml:" not in md and "<math" not in md
    assert source["license"] == "cc-by"
    headings = re.findall(r"^## (.+)$", md, flags=re.M)
    assert headings.count("References") == 1 and headings.count("Footnotes") == 1
    assert "Associated Data" not in headings
    assert "## References\n\nThe reference list (25 entries) is left out.\n" in md


def test_europepmc_candidate_without_pmcid_is_found_by_doi(tmp_path):
    record = europepmc_candidate(fulltext_url=None)
    folder = put_candidate(tmp_path, record)
    web = europepmc_web()

    assert run_fetch(tmp_path, record["id"], web) == 0

    assert web.urls() == [EPMC_SEARCH, EPMC_TEX]
    assert read_outputs(folder)[1]["url"] == EPMC_TEX


def test_europepmc_article_outside_the_open_access_subset_is_unavailable(tmp_path):
    record = europepmc_candidate(pmcid="PMC1", doi="10.9999/closed")
    folder = put_candidate(tmp_path, record)
    web = FakeWeb({f"{EPMC}/PMC1/fullTextXML": (404, {"content-type": "text/plain"}, b"")})

    assert run_fetch(tmp_path, record["id"], web) == 3

    source = json.loads((folder / "source.json").read_text())
    assert source["available"] is False and "PMC1" in source["reason"]
    assert not (folder / "fulltext.md").exists()


def test_a_bar_inside_table_math_stays_an_absolute_value(tmp_path):
    folder = put_candidate(tmp_path, arxiv_candidate())
    run_fetch(tmp_path, "arxiv-2611.15301", arxiv_web())
    md, _ = read_outputs(folder)

    # Table 3 of arXiv:2611.15301 has |B_MS| < 50 degrees; "\|" would be LaTeX for a norm.
    assert "| $\\vert B_{\\rm MS}\\vert <50^{\\circ}$ |" in md
    assert "\\|B_{\\rm MS}" not in md


def test_mathml_letters_set_one_by_one_become_one_word(tmp_path):
    # Equation (2) of doi:10.7554/eLife.102635 as Europe PMC serves it: "linear" is six <mi> elements.
    xml = (
        '<article><front><article-meta><title-group><article-title>T</article-title></title-group>'
        '</article-meta></front><body><sec><title>Results</title><p>The slope'
        '<disp-formula id="equ2"><label>(2)</label><mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML"'
        ' display="block"><mml:mstyle displaystyle="true" scriptlevel="0"><mml:mrow><mml:mstyle displaystyle="true"'
        ' scriptlevel="0"><mml:msup><mml:mi>s</mml:mi><mml:mrow><mml:mrow><mml:mi mathvariant="normal">l</mml:mi>'
        '<mml:mi mathvariant="normal">i</mml:mi><mml:mi mathvariant="normal">n</mml:mi><mml:mi mathvariant="normal">'
        'e</mml:mi><mml:mi mathvariant="normal">a</mml:mi><mml:mi mathvariant="normal">r</mml:mi></mml:mrow></mml:mrow>'
        '</mml:msup><mml:mo>=</mml:mo><mml:msub><mml:mrow><mml:mo fence="true" stretchy="true" symmetric="true"/>'
        '<mml:mfrac><mml:mrow><mml:mi>d</mml:mi><mml:mi>x</mml:mi></mml:mrow><mml:mrow><mml:mi>d</mml:mi><mml:mi>t'
        '</mml:mi></mml:mrow></mml:mfrac><mml:mo>|</mml:mo></mml:mrow><mml:mrow><mml:mi>t</mml:mi></mml:mrow>'
        '</mml:msub></mml:mstyle></mml:mrow></mml:mstyle></mml:math></disp-formula></p>'
        '<p>qualifies as a fitness statistic but often will incorrectly estimate the actual change in relative'
        ' abundance because x(t) is nonlinear (Figure 1A, top panel). Instead, we can transform the relative'
        ' abundance using a function m, which we call an encoding, such that it changes linearly in time.</p>'
        '</sec></body></article>'
    ).encode()
    record = europepmc_candidate(pmcid="PMC13727076", doi="10.7554/elife.102635")
    folder = put_candidate(tmp_path, record)
    web = FakeWeb({f"{EPMC}/PMC13727076/fullTextXML": (200, XML, xml)})

    assert run_fetch(tmp_path, record["id"], web) == 0
    assert "$$\ns^{\\mathrm{linear}}=\\frac{dx}{dt}|_{t} \\tag{2}\n$$" in read_outputs(folder)[0]


@pytest.mark.parametrize("text_id", ["PMC13749077", "PPR1234567"])
def test_europepmc_fulltextxml_link_from_discover_is_fetched_as_given(tmp_path, text_id):
    # discover writes {BASE}/{fullTextId}/fullTextXML, and a full text id is not always a PMCID.
    url = f"{EPMC}/{text_id}/fullTextXML"
    record = europepmc_candidate(fulltext_url=url)
    folder = put_candidate(tmp_path, record)
    web = FakeWeb({url: (200, XML, fixture("europepmc-PMC13749077.xml"))})

    assert run_fetch(tmp_path, record["id"], web) == 0

    assert web.urls() == [url]
    assert read_outputs(folder)[1]["url"] == url


@pytest.mark.parametrize("shape", ["no body", "body with only a supplementary file"])
def test_jats_with_front_matter_only_is_unavailable_not_a_short_full_text(tmp_path, shape):
    # Seen live on 2026-11-13: new bioRxiv XML had no <body> at all, and new medRxiv XML had a
    # <body> holding only a supplementary-material link. Both are built here from the CC BY fixture.
    from lxml import etree

    root = etree.fromstring(fixture("biorxiv-2026.10.30.763081.source.xml"))
    body = root.find("body")
    if shape == "no body":
        root.remove(body)
        root.remove(root.find("back"))
    else:
        for child in list(body):
            body.remove(child)
        etree.SubElement(body, "supplementary-material").append(etree.fromstring("<label>Supplementary Material</label>"))
    folder = put_candidate(tmp_path, biorxiv_candidate())
    web = FakeWeb({BIORXIV_XML: (200, XML, etree.tostring(root))})

    assert run_fetch(tmp_path, "doi-10.64898-2026.10.30.763081", web) == 3

    source = json.loads((folder / "source.json").read_text())
    assert source["available"] is False and "no body text" in source["reason"]
    assert not (folder / "fulltext.md").exists()
