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
