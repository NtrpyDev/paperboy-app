"""The content repo's layout: feed head, chunks, upgrades, paper folders, and pipeline state.

ContentRepo loads what is already published, takes additions and upgrades in memory, and
writes everything in one step after every file has passed its schema. Nothing on disk
changes until save() is called, and save() writes nothing when any file is invalid.

Layout (paths relative to the content repo root):

    feed/v2/head.json              Head
    feed/v2/chunks/000001.json     Chunk, up to 40 items, oldest first
    feed/v2/upgrades.json          Upgrades: explainers added to items in closed chunks
    papers/<id>/index.html         the explainer (explained papers only)
    papers/<id>/hero.webp          the day plate, the card image in the light theme (explained papers only)
    papers/<id>/hero-night.webp    the night plate, the card image in the dark theme (explained papers only)
    papers/<id>/meta.json          PaperMeta
    state/seen/<YYYY-MM>.jsonl     one Seen line per paper in the feed, by month added
    state/queued/<YYYY-MM>.jsonl   one line per paper that ever entered the backlog (read here;
                                   the queue command writes it, see paperboy_pipeline.backlog)
    state/cursors.json             Cursors: the last day each source is processed through
                                   (read here; only the cursors command writes it)
    state/queue/<id>.json          the backlog: papers waiting for a page (the queue command)
    state/claims/<id>.json         papers a run is building a page for (the queue command)
    state/queue-failed.jsonl       papers that left the backlog without a page (the queue command)
    state/cost/<YYYY-MM>.jsonl     one cost record per API run (record-cost writes, budget-gate reads;
                                   see paperboy_pipeline.cost)

Rules this module keeps:
- Only the open chunk is ever rewritten. The open chunk is the highest numbered chunk while
  it holds fewer than 40 items. A full chunk is closed and never written again.
- An explainer added to an item in a closed chunk goes to upgrades.json, never into the chunk.
- A file whose new bytes equal what is on disk is not written, so a run that changes nothing
  leaves the tree byte-identical, head included.
"""
import json
import os
import re
from pathlib import Path

from . import ids, schemas

CHUNK_SIZE = 40
# head.json's kit. Neither the app nor the worker reads it yet, so it has no settled meaning
# and stays 1. A paper's own kit version is in its meta.json, from the page it loads.
HEAD_KIT = 1
# The lowest app versionCode that reads this feed: 2 is release 0.1.1, the first build that reads feed/v2/.
MIN_APP = 2

# The feed's folder. It moved from feed/v1/ to feed/v2/ when the feed restarted on 2026-11-13, so the new
# chunks do not reuse addresses that apps and the worker cache as permanent.
FEED = Path("feed/v2")
HEAD = FEED / "head.json"
CHUNKS = FEED / "chunks"
UPGRADES = FEED / "upgrades.json"
SEEN = Path("state/seen")
QUEUED = Path("state/queued")
CURSORS = Path("state/cursors.json")


class PublishError(Exception):
    """The input or the content repo is not in a state publish can safely write from."""


def dump_json(obj) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def dump_line(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n"


def set_readout(record: dict, readout: dict | None) -> None:
    """Replace a feed item's or paper record's readout, or remove it when readout is None."""
    if readout is None:
        record.pop("readout", None)
    else:
        record["readout"] = readout


def chunk_path(number: int) -> Path:
    return CHUNKS / f"{number:06d}.json"


def paper_dir(paper_id: str) -> Path:
    return Path("papers") / paper_id


def _match_keys(*, id, doi, arxiv_id, title_key) -> set[str]:
    keys = {f"id:{id}"}
    if doi:
        keys.add(f"doi:{ids.normalize_doi(doi)}")
    if arxiv_id:
        keys.add(f"arxiv:{ids.paper_id(arxiv_id=arxiv_id)}")
    if title_key:
        keys.add(f"title:{title_key}")
    return keys


class ContentRepo:
    def __init__(self, root: Path):
        self.root = Path(root)
        self._writes: dict[Path, tuple[str | None, bytes]] = {}
        self._changed = False

        self.head = self._read_json(HEAD)
        on_disk = sorted(int(p.stem) for p in (self.root / CHUNKS).glob("*.json") if re.fullmatch(r"\d{6}", p.stem))
        highest = on_disk[-1] if on_disk else 0
        if self.head is None:
            if on_disk:
                raise PublishError(f"{CHUNKS} has chunks but {HEAD} is missing")
            self.head = {"chunk_count": 0, "total_items": 0}
        if self.head["chunk_count"] != highest:
            raise PublishError(f"{HEAD} says {self.head['chunk_count']} chunks but the highest chunk file is {highest}")

        self.chunk_count = highest
        self.total_items = self.head["total_items"]
        self.last_chunk = self._read_json(chunk_path(highest)) if highest else None

        self.upgrades = self._read_json(UPGRADES) or {"v": 1, "upgrades": {}}
        self.cursors = self._read_json(CURSORS) or {"v": 1, "cursors": {}}

        self._seen_by_key: dict[str, dict] = {}
        self._seen_text: dict[Path, str] = {}
        for path in sorted((self.root / SEEN).glob("*.jsonl")):
            rel = path.relative_to(self.root)
            self._seen_text[rel] = path.read_text()
            for line in self._seen_text[rel].splitlines():
                if line.strip():
                    self._index_seen(json.loads(line))

        self._queued_keys: set[str] = set()
        for path in sorted((self.root / QUEUED).glob("*.jsonl")):
            for line in path.read_text().splitlines():
                if line.strip():
                    entry = json.loads(line)
                    self._queued_keys |= _match_keys(**{k: entry.get(k) for k in ("id", "doi", "arxiv_id", "title_key")})

    # Reading

    def _read_json(self, rel: Path):
        path = self.root / rel
        return json.loads(path.read_text()) if path.exists() else None

    def _index_seen(self, entry: dict) -> None:
        for key in _match_keys(**{k: entry.get(k) for k in ("id", "doi", "arxiv_id", "title_key")}):
            self._seen_by_key.setdefault(key, entry)

    def find(self, record: dict) -> dict | None:
        """The Seen entry for this paper when it is already in the feed, matched on id, DOI, arXiv id, or title."""
        keys = _match_keys(
            id=record["id"], doi=record.get("doi"), arxiv_id=record.get("arxiv_id"), title_key=ids.title_key(record["title"])
        )
        for key in sorted(keys):
            if key in self._seen_by_key:
                return self._seen_by_key[key]
        return None

    def known(self, record: dict) -> bool:
        """True when the paper is in the feed or ever entered the backlog: it is never judged again."""
        if self.find(record) is not None:
            return True
        keys = _match_keys(
            id=record["id"], doi=record.get("doi"), arxiv_id=record.get("arxiv_id"), title_key=ids.title_key(record["title"])
        )
        return bool(keys & self._queued_keys)

    def meta(self, paper_id: str) -> dict | None:
        rel = paper_dir(paper_id) / "meta.json"
        if rel in self._writes:
            return json.loads(self._writes[rel][1])
        return self._read_json(rel)

    def _open_chunk(self) -> dict | None:
        if self.last_chunk is not None and len(self.last_chunk["items"]) < CHUNK_SIZE:
            return self.last_chunk
        return None

    # Changing

    def _put(self, rel: Path, data: bytes, schema: str | None) -> None:
        self._writes[rel] = (schema, data)

    def _put_paper(self, paper_id: str, meta: dict, files: dict[str, bytes]) -> None:
        for name, data in files.items():
            self._put(paper_dir(paper_id) / name, data, None)
        self._put(paper_dir(paper_id) / "meta.json", dump_json(meta), "paper-meta")

    def _put_chunk(self, chunk: dict) -> None:
        self._put(chunk_path(chunk["number"]), dump_json(chunk), "chunk")

    def add(self, *, item: dict, meta: dict, files: dict[str, bytes], record: dict) -> None:
        """Append a new feed item to the open chunk (starting a new chunk when the last is full)."""
        chunk = self._open_chunk()
        if chunk is None:
            self.chunk_count += 1
            chunk = {"v": 1, "number": self.chunk_count, "items": []}
            self.last_chunk = chunk
        chunk["items"].append(item)
        self.total_items += 1
        self._put_chunk(chunk)
        self._put_paper(item["id"], meta, files)

        entry = {
            "id": item["id"],
            "doi": record.get("doi"),
            "arxiv_id": record.get("arxiv_id"),
            "title_key": ids.title_key(record["title"]),
            "chunk": chunk["number"],
            "added_at": item["added_at"],
        }
        rel = SEEN / f"{item['added_at'][:7]}.jsonl"
        self._seen_text[rel] = self._seen_text.get(rel, "") + dump_line(entry)
        self._put(rel, self._seen_text[rel].encode(), "seen")
        self._index_seen(entry)
        self._changed = True

    def upgrade(self, *, seen: dict, explainer: dict, meta: dict, files: dict[str, bytes]) -> None:
        """Give an item already in the feed its explainer.

        explainer is {"explainer": "papers/<id>/", "hero": {...}, "explained_at": "..."}, plus
        "readout" when the expert settled one: an object replaces the item's readout and None
        removes it. The item is changed in place when its chunk is the open one; otherwise the
        chunk is left alone and the explainer is recorded in upgrades.json.
        """
        paper_id = seen["id"]
        chunk = self._open_chunk()
        if chunk is not None and chunk["number"] == seen["chunk"]:
            matches = [i for i in chunk["items"] if i["id"] == paper_id]
            if not matches:
                raise PublishError(f"{paper_id} is recorded in chunk {seen['chunk']} but is not in it")
            matches[0].update(has_explainer=True, explainer=explainer["explainer"], hero=explainer["hero"])
            if "readout" in explainer:
                set_readout(matches[0], explainer["readout"])
            self._put_chunk(chunk)
        else:
            self.upgrades["upgrades"][paper_id] = explainer
            self._put(UPGRADES, dump_json(self.upgrades), "upgrades")
        self._put_paper(paper_id, meta, files)
        self._changed = True

    # Writing

    def save(self, now: str) -> list[Path]:
        """Validate every pending file, then write those whose bytes differ from disk. Returns what was written."""
        if self._changed:
            head = {
                "v": 1,
                "updated_at": now,
                "chunk_count": self.chunk_count,
                "total_items": self.total_items,
                "chunk_size": CHUNK_SIZE,
                "kit": HEAD_KIT,
                "min_app": MIN_APP,
            }
            self._put(HEAD, dump_json(head), "head")

        problems = []
        for rel, (schema, data) in sorted(self._writes.items()):
            if schema is None:
                continue
            text = data.decode()
            records = [json.loads(line) for line in text.splitlines() if line.strip()] if rel.suffix == ".jsonl" else [json.loads(text)]
            for record in records:
                problems += [f"{rel}: {e}" for e in schemas.errors(schema, record)]
        if problems:
            raise PublishError("output failed its schema, nothing was written:\n" + "\n".join(problems))

        written = []
        for rel, (_, data) in sorted(self._writes.items()):
            path = self.root / rel
            if path.exists() and path.read_bytes() == data:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_bytes(data)
            os.replace(tmp, path)
            written.append(rel)
        return written
