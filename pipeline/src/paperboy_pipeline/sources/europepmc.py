"""Europe PMC open access records through the REST search (https://europepmc.org/RestfulWebService).

Query: open access, with a DOI (the paper id needs one; very fresh PMC records often have none
yet), first published in the window, newest first, paged with cursorMark. Records marked as
preprints keep status preprint. The full text pointer is the REST fullTextXML address, the
service Europe PMC names for automated retrieval.
"""
from datetime import date

import httpx

from .. import ids
from .http import Http, SourceError
from .text import license_from_name, squash, strip_markup

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
PAGE = 1000


def fetch(since: date, limit: int | None, http: Http) -> list[dict]:
    query = f"OPEN_ACCESS:y AND HAS_DOI:y AND FIRST_PDATE:[{since.isoformat()} TO {http.today().isoformat()}]"
    records, cursor = [], "*"
    while True:
        params = {
            "query": query,
            "sort": "FIRST_PDATE_D desc",
            "resultType": "core",
            "format": "json",
            "pageSize": min(PAGE, limit) if limit else PAGE,
            "cursorMark": cursor,
        }
        data = _json(http.get(f"{BASE}/search", params=params, retry_if=_busy))
        if "errCode" in data:
            raise SourceError(f"Europe PMC error {data.get('errCode')}: {data.get('errMsg')}")
        results = (data.get("resultList") or {}).get("result") or []
        for item in results:
            record = _record(item)
            if record is None:
                continue
            records.append(record)
            if limit is not None and len(records) >= limit:
                return records
        next_cursor = data.get("nextCursorMark")
        if not results or not next_cursor or next_cursor == cursor:
            return records
        cursor = next_cursor


def _json(response: httpx.Response) -> dict:
    try:
        return response.json()
    except ValueError as error:
        raise SourceError(f"{response.request.url}: answer is not JSON") from error


def _busy(response: httpx.Response) -> bool:
    """Europe PMC can answer a busy search with a JSON body holding errCode 503."""
    try:
        code = int(response.json().get("errCode", 0))
    except (ValueError, AttributeError, TypeError):
        return False
    return code == 429 or code >= 500


def _record(item: dict) -> dict | None:
    doi = squash(item.get("doi"))
    title = strip_markup(item.get("title"))
    text_ids = (item.get("fullTextIdList") or {}).get("fullTextId") or []
    if not doi or not title or not text_ids:
        return None
    pub_types = [t.lower() for t in (item.get("pubTypeList") or {}).get("pubType") or []]
    preprint = item.get("source") == "PPR" or "preprint" in pub_types
    venue = (
        squash(((item.get("journalInfo") or {}).get("journal") or {}).get("title"))
        or squash((item.get("bookOrReportDetails") or {}).get("publisher"))
        or "Europe PMC"
    )
    links = (item.get("fullTextUrlList") or {}).get("fullTextUrl") or []
    page = next((l["url"] for l in links if l.get("site") == "Europe_PMC" and l.get("documentStyle") == "html"), None)
    return {
        "id": ids.paper_id(doi=doi),
        "doi": doi,
        "arxiv_id": None,
        "title": title,
        "authors": _authors(item),
        "abstract": strip_markup(item.get("abstractText")),
        "venue": strip_markup(venue),
        "published": squash(item.get("firstPublicationDate")),
        "status": "preprint" if preprint else "peer_reviewed",
        "license": license_from_name(item.get("license")),
        "url": page or f"https://doi.org/{doi}",
        "source": "europepmc",
        "categories": [
            squash(h["descriptorName"])
            for h in (item.get("meshHeadingList") or {}).get("meshHeading") or []
            if squash(h.get("descriptorName"))
        ],
        "fulltext": {"available": True, "kind": "europepmc", "url": f"{BASE}/{text_ids[0]}/fullTextXML"},
        "_new": True,
        "_aliases": [],
    }


def _authors(item: dict) -> list[str]:
    names = []
    for author in (item.get("authorList") or {}).get("author") or []:
        first, last = squash(author.get("firstName")), squash(author.get("lastName"))
        name = f"{first} {last}".strip() if last else squash(author.get("fullName") or author.get("collectiveName"))
        if name:
            names.append(name)
    return names
