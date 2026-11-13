"""Europe PMC records through the REST search (https://europepmc.org/RestfulWebService).

Two queries, each with a DOI (the paper id needs one; very fresh PMC records often have none
yet), first published in the window, newest first, paged with cursorMark:

- open access records from any journal or preprint server;
- records from the followed journals (paperboy_pipeline.journals), open access or not, so a
  paywalled paper still arrives with its PubMed abstract. The ISSNs are ORed and split across
  requests (journals.issn_groups) so each URL stays a sane length.

A paper both queries return is kept once. Records marked as preprints keep status preprint. A
record has full text only when it is open access and Europe PMC lists a full text id; the
pointer is the REST fullTextXML address, the service Europe PMC names for automated retrieval.
A record from a followed journal takes that journal's title as its venue.
"""
from datetime import date

import httpx

from .. import ids, journals
from .http import Http, SourceError
from .text import license_from_name, squash, strip_markup

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
PAGE = 1000


def fetch(since: date, until: date, limit: int | None, http: Http) -> list[dict]:
    window = f"HAS_DOI:y AND FIRST_PDATE:[{since.isoformat()} TO {until.isoformat()}]"
    queries = [f"OPEN_ACCESS:y AND {window}"]
    queries += ["(" + " OR ".join(f'ISSN:"{issn}"' for issn in issns) + f") AND {window}" for issns in journals.issn_groups()]
    records: list[dict] = []
    ids_found: set[str] = set()
    for query in queries:
        if _fetch_query(query, limit, http, records, ids_found):
            break
    return records


def _fetch_query(query: str, limit: int | None, http: Http, records: list[dict], ids_found: set[str]) -> bool:
    """Append this query's records not already found; True when `limit` is reached."""
    cursor = "*"
    while True:
        params = {
            "query": query,
            "sort": "FIRST_PDATE_D desc",
            "resultType": "core",
            "format": "json",
            "pageSize": min(PAGE, limit - len(records)) if limit else PAGE,
            "cursorMark": cursor,
        }
        data = _json(http.get(f"{BASE}/search", params=params, retry_if=_busy))
        if "errCode" in data:
            raise SourceError(f"Europe PMC error {data.get('errCode')}: {data.get('errMsg')}")
        results = (data.get("resultList") or {}).get("result") or []
        for item in results:
            record = _record(item)
            if record is None or record["id"] in ids_found:
                continue
            ids_found.add(record["id"])
            records.append(record)
            if limit is not None and len(records) >= limit:
                return True
        next_cursor = data.get("nextCursorMark")
        if not results or not next_cursor or next_cursor == cursor:
            return False
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
    if not doi or not title:
        return None
    has_text = item.get("isOpenAccess") == "Y" and bool(text_ids)
    pub_types = [t.lower() for t in (item.get("pubTypeList") or {}).get("pubType") or []]
    preprint = item.get("source") == "PPR" or "preprint" in pub_types
    journal = (item.get("journalInfo") or {}).get("journal") or {}
    venue = (
        journals.title_for([journal.get("issn"), journal.get("essn")])
        or squash(journal.get("title"))
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
        "fulltext": (
            {"available": True, "kind": "europepmc", "url": f"{BASE}/{text_ids[0]}/fullTextXML"}
            if has_text else {"available": False, "kind": None, "url": None}
        ),
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
