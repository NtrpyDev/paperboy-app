"""Cleaning helpers the adapters share: markup removal, whitespace, and license ids."""
import html
import re
import warnings

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

_TAG = re.compile(r"</?[A-Za-z][\w:.-]*(\s[^<>]*)?/?>")
# Tags whose edges separate words (paragraphs, headings, sections), in HTML and JATS.
_BLOCKS = re.compile(r"^(jats:)?(p|div|br|li|ul|ol|title|sec|h[1-6]|abstract|list-item|table|tr|td|th)$")


def strip_markup(text: str | None) -> str:
    """Plain text from a string that may hold JATS or HTML tags and entities. LaTeX is left as is.

    Entities are decoded first, so escaped tags such as "&lt;i&gt;" are removed too.
    """
    if not text:
        return ""
    text = html.unescape(text)
    if _TAG.search(text):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", MarkupResemblesLocatorWarning)
            soup = BeautifulSoup(f"<div>{text}</div>", "lxml")
        for tag in soup.find_all(_BLOCKS):
            tag.insert_before(" ")
            tag.insert_after(" ")
        text = soup.get_text("")
    return squash(text)


def squash(text: str | None) -> str:
    """Collapse runs of whitespace to one space and trim."""
    return " ".join((text or "").split())


# Creative Commons URL path -> schema license id.
_CC_PATHS = {
    "by": "cc-by",
    "by-sa": "cc-by-sa",
    "by-nc": "cc-by-nc",
    "by-nd": "cc-by-nd",
    "by-nc-sa": "cc-by-nc-sa",
    "by-nc-nd": "cc-by-nc-nd",
}


def license_from_url(url: str | None) -> str | None:
    """Schema license id for a license URL: Creative Commons, CC0, the arXiv license, else other."""
    if not url:
        return None
    url = url.strip().lower()
    if "creativecommons.org/publicdomain/zero" in url:
        return "cc0"
    match = re.search(r"creativecommons\.org/licenses/([a-z-]+)", url)
    if match and match.group(1) in _CC_PATHS:
        return _CC_PATHS[match.group(1)]
    if "arxiv.org/licenses/nonexclusive-distrib" in url:
        return "arxiv-nonexclusive"
    return "other"


def license_from_name(name: str | None) -> str | None:
    """Schema license id for a short name such as "cc by-nc-nd" (Europe PMC) or "cc_by_nc" (bioRxiv).

    Names outside the Creative Commons set, such as bioRxiv's "cc_no" and "cc0_ng", whose exact
    meaning no primary source states, become "other".
    """
    if not name:
        return None
    key = re.sub(r"[\s_]+", "-", name.strip().lower())
    if key == "cc0":
        return "cc0"
    if key.startswith("cc-") and key[3:] in _CC_PATHS:
        return _CC_PATHS[key[3:]]
    return "other"
