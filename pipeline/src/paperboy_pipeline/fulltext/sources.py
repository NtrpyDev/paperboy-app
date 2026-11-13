"""Where each kind of full text is fetched from, and how.

- arxiv_html: https://arxiv.org/html/<id>, the LaTeXML rendering. No HTML means unavailable;
  the PDF is never parsed.
- biorxiv (bioRxiv and medRxiv): the JATS XML the bioRxiv API lists as "jatsxml" for the
  newest version. bioRxiv's FAQ says "XML is available for text mining purposes"
  (https://www.biorxiv.org/about/FAQ), and robots.txt allows /content for every agent.
- europepmc: the REST fullTextXML endpoint, which Europe PMC names as a service that "may be
  used for automated downloading" (https://europepmc.org/Copyright).
"""
import re
from dataclasses import dataclass

import httpx

from . import jats, latexml, licenses
from .document import Paper
from .http import FetchError, PoliteClient, Unavailable

EUROPEPMC_REST = "https://www.ebi.ac.uk/europepmc/webservices/rest"
BIORXIV_API = "https://api.biorxiv.org/details"


@dataclass
class Fetched:
    paper: Paper
    url: str
    kind: str
    license: str | None


def fetch(candidate: dict, client: PoliteClient) -> Fetched:
    fulltext = candidate.get("fulltext") or {}
    kind = fulltext.get("kind")
    if not fulltext.get("available") or not kind:
        raise Unavailable("the candidate record says no free full text is available")
    if kind == "arxiv_html":
        return _arxiv(candidate, client)
    if kind == "biorxiv":
        return _rxiv(candidate, client)
    if kind == "europepmc":
        return _europepmc(candidate, client)
    raise FetchError(f"unknown full text kind {kind!r}")


def _parse(convert, content: bytes, url: str):
    try:
        return convert(content)
    except (ValueError, TypeError) as error:
        raise FetchError(f"could not read the document at {url}: {error}") from error


# arXiv


def _arxiv(candidate: dict, client: PoliteClient) -> Fetched:
    url = (candidate["fulltext"].get("url") or "").strip()
    if not url.startswith("https://arxiv.org/html/"):
        arxiv_id = candidate.get("arxiv_id") or candidate["id"].removeprefix("arxiv-")
        url = f"https://arxiv.org/html/{arxiv_id}"
    response = client.get(url, accept="text/html")
    if response.status_code == 404:
        raise Unavailable(f"arXiv has no HTML rendering of this paper (HTTP 404 at {url})")
    paper = _parse(latexml.convert, response.content, url)
    license = licenses.from_text(latexml.license_label(response.content))
    return Fetched(paper, str(response.url), "arxiv_html", license)


# bioRxiv and medRxiv


def _rxiv_server(candidate: dict) -> str:
    if candidate.get("source") in ("biorxiv", "medrxiv"):
        return candidate["source"]
    urls = " ".join(filter(None, [candidate.get("url"), (candidate.get("fulltext") or {}).get("url")]))
    return "medrxiv" if "medrxiv.org" in urls else "biorxiv"


def _rxiv(candidate: dict, client: PoliteClient) -> Fetched:
    server = _rxiv_server(candidate)
    url = (candidate["fulltext"].get("url") or "").strip()
    api_license = None
    if not re.search(r"\.xml(\?|$)", url):
        doi = candidate.get("doi")
        if not doi:
            match = re.search(r"10\.\d{4,9}/[^\s?#]+?(?=v\d+(\.full)?$|$|\.full)", url or candidate.get("url", ""))
            doi = match.group(0) if match else None
        if not doi:
            raise Unavailable(f"no DOI to look the preprint up in the {server} API")
        api_url = f"{BIORXIV_API}/{server}/{doi}"
        response = client.get(api_url, accept="application/json")
        records = []
        if response.status_code == 200:
            try:
                records = response.json().get("collection") or []
            except ValueError as error:
                raise FetchError(f"{api_url} did not return JSON") from error
        if not records:
            raise Unavailable(f"the {server} API has no record for {doi}")
        latest = max(records, key=lambda r: int(r.get("version") or 0))
        url = latest.get("jatsxml") or ""
        api_license = latest.get("license")
        if not url:
            raise Unavailable(f"the {server} API lists no JATS XML for {doi}")
    response = client.get(url, accept="application/xml")
    if response.status_code == 404:
        raise Unavailable(
            f"{server} returned HTTP 404 for the JATS XML at {url}"
            " (its FAQ says HTML and XML can take up to 48 hours to appear after posting)"
        )
    if "html" in response.headers.get("content-type", ""):
        raise FetchError(f"{url} returned an HTML page, not JATS XML")
    paper, license = _parse(jats.convert, response.content, url)
    license = license or licenses.from_rxiv_api(api_license) or candidate.get("license")
    return Fetched(paper, str(response.url), "biorxiv", license)


# Europe PMC


def _europepmc(candidate: dict, client: PoliteClient) -> Fetched:
    given = (candidate["fulltext"].get("url") or "").strip()
    match = re.fullmatch(re.escape(EUROPEPMC_REST) + r"/([A-Za-z]+\d+)/fullTextXML", given)
    if match:  # discover's link, which may name a non-PMC full text id
        return _europepmc_xml(candidate, client, match.group(1))
    places = " ".join(filter(None, [given, candidate.get("url")]))
    match = re.search(r"PMC\d+", places, flags=re.I)
    pmcid = match.group(0).upper() if match else None
    if not pmcid:
        doi = candidate.get("doi")
        if not doi:
            raise Unavailable("no PMCID or DOI to find the article in Europe PMC")
        search = httpx.URL(
            f"{EUROPEPMC_REST}/search",
            params={"query": f'DOI:"{doi}"', "resultType": "lite", "format": "json"},
        )
        response = client.get(str(search), accept="application/json")
        try:
            results = response.json().get("resultList", {}).get("result", []) if response.status_code == 200 else []
        except ValueError as error:
            raise FetchError("Europe PMC search did not return JSON") from error
        hit = next((r for r in results if r.get("pmcid")), None)
        if hit is None:
            raise Unavailable(f"Europe PMC has no PMC full text for DOI {doi}")
        if hit.get("isOpenAccess") != "Y":
            raise Unavailable(f"{hit['pmcid']} is not in the Europe PMC open access subset")
        pmcid = hit["pmcid"]
    return _europepmc_xml(candidate, client, pmcid)


def _europepmc_xml(candidate: dict, client: PoliteClient, pmcid: str) -> Fetched:
    url = f"{EUROPEPMC_REST}/{pmcid}/fullTextXML"
    response = client.get(url, accept="application/xml")
    if response.status_code == 404:
        raise Unavailable(f"Europe PMC has no open access full text for {pmcid} (HTTP 404 at {url})")
    paper, license = _parse(jats.convert, response.content, url)
    return Fetched(paper, str(response.url), "europepmc", license or candidate.get("license"))
