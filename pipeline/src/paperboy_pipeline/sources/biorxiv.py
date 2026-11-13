"""bioRxiv and medRxiv through their shared details API (https://api.biorxiv.org/).

/details/<server>/<from>/<to>/<cursor>/json lists every version posted in the date interval,
30 per call. A paper is new when the listed version is its first; later versions are kept as
context only. DOIs use both the old 10.1101 prefix and the new 10.64898 one, so no prefix is
assumed. The `published` field, when not "NA", is the journal DOI of the same paper.
"""
from datetime import date
from functools import partial

from .. import ids
from .http import Http, SourceError
from .text import license_from_name, squash, strip_markup

BASE = "https://api.biorxiv.org/details"
VENUES = {"biorxiv": "bioRxiv", "medrxiv": "medRxiv"}


def fetch(server: str, since: date, until: date, limit: int | None, http: Http) -> list[dict]:
    records, new_count, cursor = [], 0, 0
    while True:
        url = f"{BASE}/{server}/{since.isoformat()}/{until.isoformat()}/{cursor}/json"
        try:
            data = http.get(url).json()
        except ValueError as error:
            raise SourceError(f"{url}: answer is not JSON") from error
        message = (data.get("messages") or [{}])[0]
        batch = data.get("collection") or []
        if message.get("status") != "ok" or not batch:
            return records
        for item in batch:
            record = _record(server, item)
            if record is None:
                continue
            records.append(record)
            new_count += record["_new"]
            if limit is not None and new_count >= limit:
                return records
        cursor += len(batch)
        if cursor >= int(message.get("total") or 0):
            return records


def _record(server: str, item: dict) -> dict | None:
    doi = squash(item.get("doi"))
    title = strip_markup(item.get("title"))
    if not doi or not title:
        return None
    published = squash(item.get("published"))
    jats = squash(item.get("jatsxml"))
    return {
        "id": ids.paper_id(doi=doi),
        "doi": doi,
        "arxiv_id": None,
        "title": title,
        "authors": [squash(name) for name in (item.get("authors") or "").split(";") if squash(name)],
        "abstract": strip_markup(item.get("abstract")),
        "venue": VENUES[server],
        "published": squash(item.get("date")),
        "status": "preprint",
        "license": license_from_name(item.get("license")),
        "url": f"https://doi.org/{doi}",
        "source": server,
        "categories": [squash(item["category"])] if squash(item.get("category")) else [],
        "fulltext": {"available": True, "kind": "biorxiv", "url": jats or None},
        "_new": squash(str(item.get("version"))) == "1",
        "_aliases": [published] if published and published != "NA" else [],
    }


fetch_biorxiv = partial(fetch, "biorxiv")
fetch_medrxiv = partial(fetch, "medrxiv")
