"""Paper ids and the keys used to spot the same paper arriving twice."""
import hashlib
import re


def paper_id(*, arxiv_id: str | None = None, doi: str | None = None) -> str:
    """arxiv-<id> when an arXiv id exists (version suffix dropped), else doi-<sanitized doi>."""
    if arxiv_id:
        base = re.sub(r"v\d+$", "", arxiv_id.strip().lower())
        return "arxiv-" + re.sub(r"[^a-z0-9._-]", "-", base)
    if doi:
        return "doi-" + re.sub(r"[^a-z0-9._-]", "-", normalize_doi(doi))
    raise ValueError("a paper needs an arXiv id or a DOI")


def normalize_doi(doi: str) -> str:
    return re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", doi.strip().lower())


def title_key(title: str) -> str:
    """Hash of the title with everything but letters and digits removed."""
    return hashlib.sha1(re.sub(r"[^a-z0-9]", "", title.lower()).encode()).hexdigest()[:20]
