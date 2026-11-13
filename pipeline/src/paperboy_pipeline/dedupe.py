"""Collapse records of the same paper, from several sources or versions, into one candidate.

Two records are the same paper when they share a DOI (including DOIs a source names as the same
paper), an arXiv id (version dropped), or a title key (ids.title_key). Sameness is transitive.
The title key only links titles of at least MIN_TITLE_CHARS letters and digits, so short titles
that many journals reuse ("Editorial", "Preface") do not merge unrelated papers.

From each group one record is kept:

- The base record is a journal record when there is one (status peer_reviewed, Europe PMC
  before Crossref, see SOURCE_RANK), else the preprint from the highest ranked server in
  PREPRINT_RANK.
- Its full text pointer is kept when it has one; otherwise the first group member with a full
  text lends its pointer, and its license, since the license belongs to that text.
- A missing DOI, arXiv id, abstract, or author list is filled from the other members, and
  categories are combined.
- The paper id is rebuilt with ids.paper_id, so an arXiv id wins when any member has one.

A group with no newly released member (see paperboy_pipeline.sources) is dropped.
"""
import re
from dataclasses import dataclass

from . import ids

MIN_TITLE_CHARS = 20

SOURCE_RANK = {"europepmc": 0, "crossref": 1, "arxiv": 2, "biorxiv": 3, "medrxiv": 4}
PREPRINT_RANK = {"arxiv": 0, "biorxiv": 1, "medrxiv": 2, "europepmc": 3, "crossref": 4}


@dataclass
class Paper:
    record: dict
    members: list[dict]


def keys(record: dict) -> set[str]:
    found = set()
    if len(re.sub(r"[^a-z0-9]", "", record["title"].lower())) >= MIN_TITLE_CHARS:
        found.add(f"title:{ids.title_key(record['title'])}")
    for doi in [record.get("doi"), *record.get("_aliases", [])]:
        if doi:
            found.add(f"doi:{ids.normalize_doi(doi)}")
    if record.get("arxiv_id"):
        found.add(f"arxiv:{ids.paper_id(arxiv_id=record['arxiv_id'])}")
    return found


def merge(records: list[dict]) -> list[Paper]:
    parent = list(range(len(records)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owner: dict[str, int] = {}
    for i, record in enumerate(records):
        for key in keys(record):
            if key in owner:
                parent[root(i)] = root(owner[key])
            else:
                owner[key] = i

    groups: dict[int, list[dict]] = {}
    for i, record in enumerate(records):
        groups.setdefault(root(i), []).append(record)
    return [Paper(_combine(members), members) for members in groups.values() if any(m["_new"] for m in members)]


def _order(record: dict) -> tuple:
    if record["status"] == "peer_reviewed":
        return (0, SOURCE_RANK[record["source"]], not record["_new"])
    return (1, PREPRINT_RANK[record["source"]], not record["_new"])


def _combine(members: list[dict]) -> dict:
    ordered = sorted(members, key=_order)
    base = dict(ordered[0])
    donor = next((m for m in ordered if m["fulltext"]["available"]), None)
    if donor is not None and donor is not ordered[0]:
        base["fulltext"] = dict(donor["fulltext"])
        base["license"] = donor["license"]
    for field in ("doi", "arxiv_id", "abstract", "authors"):
        if not base.get(field):
            base[field] = next((m[field] for m in ordered if m.get(field)), base.get(field))
    categories = []
    for member in ordered:
        categories += [c for c in member.get("categories", []) if c not in categories]
    base["categories"] = categories
    base["_aliases"] = sorted({a for m in ordered for a in m.get("_aliases", [])} | {m["doi"] for m in ordered if m.get("doi")})
    base["_new"] = True
    base["id"] = ids.paper_id(arxiv_id=base.get("arxiv_id"), doi=base.get("doi"))
    return base
