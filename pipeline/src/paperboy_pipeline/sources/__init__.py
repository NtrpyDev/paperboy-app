"""One adapter per paper source. Each is fetch(since, until, limit, http) -> list of candidate records.

`since` and `until` are the first and last day of the window, both inclusive (UTC). Each adapter
puts the window into its query on the date that source uses to decide newness.

A record has every Candidate field (schema/candidate.schema.json) plus two private fields that
dedupe reads and discover drops before writing:

- `_new`: true when the paper is newly released in the window. A record with `_new` false is
  context only (an older paper that changed): it can lend identifiers or a full text pointer to
  a new record of the same paper but is never written on its own.
- `_aliases`: other DOIs the source says belong to the same paper (for example the journal DOI
  bioRxiv records for a published preprint).

`limit` caps the number of new records an adapter returns; None means everything in the window.
"""
from . import arxiv, biorxiv, crossref, europepmc

ADAPTERS = {
    "arxiv": arxiv.fetch,
    "biorxiv": biorxiv.fetch_biorxiv,
    "medrxiv": biorxiv.fetch_medrxiv,
    "europepmc": europepmc.fetch,
    "crossref": crossref.fetch,
}
