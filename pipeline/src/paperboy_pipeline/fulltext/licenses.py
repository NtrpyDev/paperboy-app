"""Turns the license statements sources give into the lowercase ids the candidate schema uses:
cc0, cc-by, cc-by-sa, cc-by-nc, cc-by-nd, cc-by-nc-sa, cc-by-nc-nd, arxiv-nonexclusive, other."""
import re

_CC_PARTS = {"by", "sa", "nc", "nd"}


def _cc_id(parts: list[str]) -> str | None:
    parts = [p.lower() for p in parts]
    if not parts or parts[0] != "by" or not set(parts) <= _CC_PARTS:
        return None
    rest = parts[1:]
    order = [p for p in ("nc", "nd", "sa") if p in rest]
    if order == ["nd", "sa"] or order == ["nc", "nd", "sa"]:
        return None  # not a real Creative Commons license
    return "cc-" + "-".join(["by", *order])


def from_url(url: str | None) -> str | None:
    """A license URL (Creative Commons or arXiv) to an id, or None when the URL is not one we know."""
    if not url:
        return None
    url = url.strip().lower()
    if "creativecommons.org/publicdomain/zero" in url:
        return "cc0"
    match = re.search(r"creativecommons\.org/licenses/([a-z-]+)", url)
    if match:
        return _cc_id(match.group(1).split("-"))
    if "arxiv.org/licenses/nonexclusive-distrib" in url or "arxiv.org/licenses/assumed-1991-2003" in url:
        return "arxiv-nonexclusive"
    return None


def from_text(text: str | None) -> str | None:
    """A short license label such as "CC BY 4.0", "CC BY-NC-ND 4.0", "CC Zero" or
    "arXiv.org perpetual non-exclusive license" to an id, or None."""
    if not text:
        return None
    text = " ".join(text.split())
    if re.search(r"\bCC[ -]?(0|Zero)\b|Public Domain Dedication", text, flags=re.I):
        return "cc0"
    match = re.search(r"\bCC[ -](BY(?:[ -](?:NC|ND|SA))*)\b", text, flags=re.I)
    if match:
        return _cc_id(re.split(r"[ -]", match.group(1)))
    if re.search(r"arXiv\.org perpetual,? non-?exclusive", text, flags=re.I):
        return "arxiv-nonexclusive"
    return None


# Values the bioRxiv and medRxiv API puts in "license" (https://api.biorxiv.org/). cc_no is
# bioRxiv's "No reuse/adaptation without permission" option; a license the schema has no id
# for, so "other". Values not listed here are also "other": the source states a license we
# cannot name.
_RXIV = {
    "cc_by": "cc-by",
    "cc_by_sa": "cc-by-sa",
    "cc_by_nc": "cc-by-nc",
    "cc_by_nd": "cc-by-nd",
    "cc_by_nc_sa": "cc-by-nc-sa",
    "cc_by_nc_nd": "cc-by-nc-nd",
    "cc0": "cc0",
}


def from_rxiv_api(value: str | None) -> str | None:
    if not value:
        return None
    return _RXIV.get(value.strip().lower(), "other")
