"""The peer-reviewed journals the feed follows, from pipeline/journals.json.

Each entry is {"title", "issn": [...], "field_hint"}. The Crossref and Europe PMC adapters ask
only for these journals (Europe PMC also keeps its open access query) and name a matching
record's venue with the entry's title, so batch can recognize a followed journal by venue.
The ISSNs were looked up from Crossref's journals endpoint, never written from memory.
"""
import json
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "journals.json"
PATH = DEFAULT_PATH

# ISSNs per request. A journal's ISSNs stay in one request. 40 keeps a Crossref or Europe PMC
# URL near 1,500 characters.
MAX_ISSNS = 40


def load() -> list[dict]:
    return json.loads(Path(PATH).read_text())


def titles() -> set[str]:
    return {journal["title"] for journal in load()}


def title_for(issns) -> str | None:
    """The followed journal's title when any of these ISSNs belongs to it."""
    wanted = {issn.upper() for issn in issns if issn}
    for journal in load():
        if wanted & {issn.upper() for issn in journal["issn"]}:
            return journal["title"]
    return None


def issn_groups(limit: int = MAX_ISSNS) -> list[list[str]]:
    """The followed ISSNs split into lists of at most `limit`, never splitting one journal."""
    groups: list[list[str]] = []
    for journal in load():
        if not groups or len(groups[-1]) + len(journal["issn"]) > limit:
            groups.append([])
        groups[-1].extend(journal["issn"])
    return groups
