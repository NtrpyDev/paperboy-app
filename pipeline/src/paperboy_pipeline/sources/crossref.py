"""Crossref journal articles through the REST API (https://api.crossref.org/works).

Filter: created on or after `since`, type journal-article, has an abstract; newest created
first, paged with a deep-paging cursor. No mailto is sent, so requests use the public pool,
which allows one list request per second (spacing lives in sources.http). Crossref records carry
no full text pointer here.
"""
from datetime import date

import httpx

from .. import ids
from .http import Http, SourceError
from .text import license_from_url, squash, strip_markup

BASE = "https://api.crossref.org/works"
PAGE = 1000
FIELDS = "DOI,type,title,author,abstract,container-title,created,published-online,published-print,issued,license,URL"
# License entries by content version, most relevant first: the version of record, then the rest.
VERSION_ORDER = {"vor": 0, "unspecified": 1, "am": 2, "tdm": 3}


def fetch(since: date, limit: int | None, http: Http) -> list[dict]:
    records, cursor = [], "*"
    while True:
        params = {
            "filter": f"from-created-date:{since.isoformat()},type:journal-article,has-abstract:true",
            "sort": "created",
            "order": "desc",
            "rows": min(PAGE, limit) if limit else PAGE,
            "select": FIELDS,
            "cursor": cursor,
        }
        message = _json(http.get(BASE, params=params)).get("message") or {}
        items = message.get("items") or []
        for item in items:
            record = _record(item)
            if record is None:
                continue
            records.append(record)
            if limit is not None and len(records) >= limit:
                return records
        cursor = message.get("next-cursor")
        if not items or not cursor:
            return records


def _json(response: httpx.Response) -> dict:
    try:
        return response.json()
    except ValueError as error:
        raise SourceError(f"{response.request.url}: answer is not JSON") from error


def _record(item: dict) -> dict | None:
    doi = squash(item.get("DOI"))
    title = strip_markup((item.get("title") or [""])[0])
    abstract = strip_markup(item.get("abstract"))
    published = _published(item)
    if not doi or not title or not abstract or not published:
        return None
    return {
        "id": ids.paper_id(doi=doi),
        "doi": doi,
        "arxiv_id": None,
        "title": title,
        "authors": _authors(item),
        "abstract": abstract,
        "venue": strip_markup((item.get("container-title") or [""])[0]),
        "published": published,
        "status": "peer_reviewed",
        "license": _license(item.get("license") or []),
        "url": f"https://doi.org/{doi}",
        "source": "crossref",
        "categories": [],
        "fulltext": {"available": False, "kind": None, "url": None},
        "_new": True,
        "_aliases": [],
    }


def _published(item: dict) -> str | None:
    """The earliest complete date among online, print, issued, and created.

    Created is included so a print date set in the future never makes the paper look newer than
    its registration.
    """
    dates = []
    for field in ("published-online", "published-print", "issued", "created"):
        for parts in (item.get(field) or {}).get("date-parts") or []:
            if parts and len(parts) == 3 and all(isinstance(p, int) for p in parts):
                dates.append(date(*parts).isoformat())
    return min(dates) if dates else None


def _authors(item: dict) -> list[str]:
    names = []
    for author in item.get("author") or []:
        name = squash(f"{author.get('given') or ''} {author.get('family') or ''}") or squash(author.get("name"))
        if name:
            names.append(name)
    return names


def _license(entries: list[dict]) -> str | None:
    if not entries:
        return None
    ordered = sorted(entries, key=lambda e: VERSION_ORDER.get(e.get("content-version"), len(VERSION_ORDER)))
    ids_found = [license_from_url(e.get("URL")) for e in ordered]
    return next((i for i in ids_found if i not in (None, "other")), "other")
