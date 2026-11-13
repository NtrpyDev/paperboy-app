"""Writes the app's fixture feed in app/src/fixtures/feed/v1.

Chunks 1 to 8 are closed chunks of 40 generated short cards each, oldest first.
Chunk 9 is the open chunk and is written by hand; this script leaves it alone and
counts its items for the head. upgrades.json gives one paper in a closed chunk the
explainer in app/src/fixtures/papers/arxiv-2609.10300/.

Run from the repo root: python3 tools/make-feed-fixtures.py
Check against the schemas: uv run --project pipeline python tools/make-feed-fixtures.py --check
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "app/src/fixtures/feed/v1"
CLOSED_CHUNKS = 8
CHUNK_SIZE = 40
UPGRADED = "arxiv-2609.10300"

FIELDS = {
    "physics": ["optics", "superconductors", "lasers"],
    "space": ["exoplanets", "black holes", "galaxies"],
    "math": ["combinatorics", "number theory", "topology"],
    "cs": ["machine learning", "cryptography", "compilers"],
    "biology": ["genetics", "ecology", "evolution"],
    "neuroscience": ["memory", "sleep", "vision"],
    "medicine": ["clinical trial", "vaccines", "cancer"],
    "chemistry": ["catalysis", "batteries", "polymers"],
    "earth": ["climate", "earthquakes", "oceans"],
    "engineering": ["robotics", "materials", "bridges"],
    "social": ["economics", "cities", "education"],
}
START = datetime(2026, 9, 15, tzinfo=timezone.utc)


def rfc3339(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def item(k: int) -> dict:
    field = list(FIELDS)[k % len(FIELDS)]
    tag = FIELDS[field][k % 3]
    added = START + timedelta(hours=4 * k)
    return {
        "id": f"arxiv-2609.{10000 + k:05d}",
        "title": f"Fixture study {k} on {tag}",
        "hook": f"Fixture paper {k}: a {field} finding about {tag}",
        "summary": f"This is fixture paper {k} in {field}, used by the app tests. "
                   f"It stands in for a plain summary of a study about {tag}.",
        "field": field,
        "tags": [tag],
        "status": "peer_reviewed" if k % 2 else "preprint",
        "venue": "arXiv" if k % 2 == 0 else "Fixture Journal",
        "published": added.strftime("%Y-%m-%d"),
        "authors_short": "Fixture et al.",
        "url": f"https://arxiv.org/abs/2609.{10000 + k:05d}",
        "has_explainer": False,
        # 3.0 to 7.4, below every hand-written paper in the open chunk.
        "significance": round(3.0 + (k * 7 % 45) / 10, 1),
        "added_at": rfc3339(added),
    }


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def generate() -> None:
    k = 0
    for number in range(1, CLOSED_CHUNKS + 1):
        items = [item(k + i) for i in range(CHUNK_SIZE)]
        k += CHUNK_SIZE
        write(FEED / f"chunks/{number:06d}.json", {"v": 1, "number": number, "items": items})
    open_chunk = json.loads((FEED / f"chunks/{CLOSED_CHUNKS + 1:06d}.json").read_text())
    write(FEED / "head.json", {
        "v": 1,
        "updated_at": "2026-11-12T18:00:00Z",
        "chunk_count": CLOSED_CHUNKS + 1,
        "total_items": k + len(open_chunk["items"]),
        "chunk_size": CHUNK_SIZE,
        "kit": 1,
        "min_app": 1,
    })
    write(FEED / "upgrades.json", {
        "v": 1,
        "upgrades": {
            UPGRADED: {
                "explainer": f"papers/{UPGRADED}/",
                "hero": {"path": f"papers/{UPGRADED}/hero.webp", "width": 1200, "height": 675},
                "explained_at": "2026-11-12T16:00:00Z",
            },
        },
    })


def check() -> None:
    sys.path.insert(0, str(ROOT / "pipeline/src"))
    from paperboy_pipeline import schemas

    problems = []
    problems += [f"head: {e}" for e in schemas.errors("head", json.loads((FEED / "head.json").read_text()))]
    problems += [f"upgrades: {e}" for e in schemas.errors("upgrades", json.loads((FEED / "upgrades.json").read_text()))]
    for path in sorted((FEED / "chunks").glob("*.json")):
        problems += [f"{path.name}: {e}" for e in schemas.errors("chunk", json.loads(path.read_text()))]
    print("\n".join(problems) or "all fixture files match their schemas")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    check() if "--check" in sys.argv else generate()
