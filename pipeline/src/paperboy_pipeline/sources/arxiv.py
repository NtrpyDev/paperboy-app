"""arXiv through OAI-PMH (https://oaipmh.arxiv.org/oai), metadata format arXivRaw.

OAI-PMH is the only arXiv interface that states each paper's license, and arXivRaw carries the
date of every version. `from` selects records by datestamp (the last change), so a revision of
an old paper shows up too. A record counts as new when its first version is at most
NEW_GRACE_DAYS older than `since` (announcement trails submission by a few days). Older records
are kept as context only: they can lend their full text to a journal record of the same paper
but never become a candidate on their own.
"""
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from email.utils import parsedate_to_datetime

from .. import ids
from .http import Http, SourceError
from .text import license_from_url, squash

BASE = "https://oaipmh.arxiv.org/oai"
NEW_GRACE_DAYS = 7
OAI = "{http://www.openarchives.org/OAI/2.0/}"
RAW = "{http://arxiv.org/OAI/arXivRaw/}"


def fetch(since: date, limit: int | None, http: Http) -> list[dict]:
    params = {"verb": "ListRecords", "metadataPrefix": "arXivRaw", "from": since.isoformat()}
    oldest_new = since - timedelta(days=NEW_GRACE_DAYS)
    records, new_count = [], 0
    while True:
        root = _parse(http.get(BASE, params=params).content)
        error = root.find(f"{OAI}error")
        if error is not None:
            if error.get("code") == "noRecordsMatch":
                return records
            raise SourceError(f"arXiv OAI-PMH error {error.get('code')}: {squash(error.text)}")
        for element in root.iter(f"{OAI}record"):
            record = _record(element, oldest_new)
            if record is None:
                continue
            records.append(record)
            new_count += record["_new"]
            if limit is not None and new_count >= limit:
                return records
        token = root.find(f"{OAI}ListRecords/{OAI}resumptionToken")
        if token is None or not (token.text or "").strip():
            return records
        params = {"verb": "ListRecords", "resumptionToken": token.text.strip()}


def _parse(content: bytes) -> ET.Element:
    try:
        return ET.fromstring(content)
    except ET.ParseError as error:
        raise SourceError(f"arXiv OAI-PMH answer is not XML: {error}") from error


def _record(element: ET.Element, oldest_new: date) -> dict | None:
    header = element.find(f"{OAI}header")
    if header is not None and header.get("status") == "deleted":
        return None
    meta = element.find(f"{OAI}metadata/{RAW}arXivRaw")
    if meta is None:
        return None
    arxiv_id = squash(meta.findtext(f"{RAW}id"))
    title = squash(meta.findtext(f"{RAW}title"))
    versions = meta.findall(f"{RAW}version")
    if not arxiv_id or not title or not versions:
        return None
    first = parsedate_to_datetime(versions[0].findtext(f"{RAW}date")).date()
    dois = squash(meta.findtext(f"{RAW}doi")).split()
    return {
        "id": ids.paper_id(arxiv_id=arxiv_id),
        "doi": dois[0] if dois else None,
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": split_authors(meta.findtext(f"{RAW}authors")),
        "abstract": squash(meta.findtext(f"{RAW}abstract")),
        "venue": "arXiv",
        "published": first.isoformat(),
        "status": "preprint",
        "license": license_from_url(meta.findtext(f"{RAW}license")),
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "source": "arxiv",
        "categories": squash(meta.findtext(f"{RAW}categories")).split(),
        "fulltext": {"available": True, "kind": "arxiv_html", "url": f"https://arxiv.org/html/{arxiv_id}"},
        "_new": first >= oldest_new,
        "_aliases": dois[1:],
    }


def split_authors(text: str | None) -> list[str]:
    """Names from arXiv's author line ("A, B and C"), with parenthesized affiliations removed."""
    text = squash(text)
    names, current, depth, i = [], [], 0, 0
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(depth - 1, 0)
            i += 1
            continue
        if depth == 0:
            if ch == ",":
                names.append("".join(current))
                current, i = [], i + 1
                continue
            if text.startswith(" and ", i):
                names.append("".join(current))
                current, i = [], i + 5
                continue
            current.append(ch)
        i += 1
    names.append("".join(current))
    return [squash(name) for name in names if squash(name)]
