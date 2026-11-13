"""Crossref journal articles from the followed journals, through the REST API (https://api.crossref.org/works).

Filter: created from `since` through `until`, type journal-article, and one `issn:` filter per
followed ISSN (paperboy_pipeline.journals). Crossref ORs repeated filters of the same name and
ANDs different ones. The ISSNs are split across requests (journals.issn_groups) so each URL stays
a sane length; each request is newest created first, paged with a deep-paging cursor. No mailto
is sent, so requests use the public pool, which allows one list request per second (spacing
lives in sources.http). A record with no abstract is kept with an empty one, since another
source may supply it; discover drops what is still empty after dedupe. Crossref records carry
no full text pointer here.
"""
from datetime import date

import httpx

from .. import ids, journals
from .http import Http, SourceError
from .text import license_from_url, squash, strip_markup

BASE = "https://api.crossref.org/works"
PAGE = 1000
FIELDS = "DOI,type,title,author,abstract,container-title,ISSN,created,published-online,published-print,issued,license,URL"
# License entries by content version, most relevant first: the version of record, then the rest.
VERSION_ORDER = {"vor": 0, "unspecified": 1, "am": 2, "tdm": 3}


def fetch(since: date, until: date, limit: int | None, http: Http) -> list[dict]:
    records: list[dict] = []
    window = f"from-created-date:{since.isoformat()},until-created-date:{until.isoformat()},type:journal-article"
    for issns in journals.issn_groups():
        if _fetch_group(window + "".join(f",issn:{issn}" for issn in issns), limit, http, records):
            break
    return records


def _fetch_group(filters: str, limit: int | None, http: Http, records: list[dict]) -> bool:
    """Append this filter's records to `records`; True when `limit` is reached."""
    cursor = "*"
    while True:
        params = {
            "filter": filters,
            "sort": "created",
            "order": "desc",
            "rows": min(PAGE, limit - len(records)) if limit else PAGE,
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
                return True
        cursor = message.get("next-cursor")
        if not items or not cursor:
            return False


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
    if not doi or not title or not published:
        return None
    return {
        "id": ids.paper_id(doi=doi),
        "doi": doi,
        "arxiv_id": None,
        "title": title,
        "authors": _authors(item),
        "abstract": abstract,
        "venue": journals.title_for(item.get("ISSN") or []) or strip_markup((item.get("container-title") or [""])[0]),
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
