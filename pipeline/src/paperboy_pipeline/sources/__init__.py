"""One adapter per paper source. Each is fetch(since, limit, http) -> list of candidate records.

A record has every Candidate field (schema/candidate.schema.json) plus two private fields that
dedupe reads and discover drops before writing:

- `_new`: true when the paper is newly released in the window. A record with `_new` false is
  context only (an older paper that changed): it can lend identifiers or a full text pointer to
  a new record of the same paper but is never written on its own.
- `_aliases`: other DOIs the source says belong to the same paper (for example the journal DOI
  bioRxiv records for a published preprint).

`limit` caps the number of new records an adapter returns; None means everything in the window.
"""
from . import arxiv, biorxiv

ADAPTERS = {
    "arxiv": arxiv.fetch,
    "biorxiv": biorxiv.fetch_biorxiv,
    "medrxiv": biorxiv.fetch_medrxiv,
}
