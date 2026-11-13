"""Writes the app's fixture feed in app/src/fixtures/feed/v1.

Chunks 1 to 8 are closed chunks of 40 generated papers each, oldest first. Some carry a
second voice (hook_turn) and a readout, with and without an exponent and a unit.

Most generated papers are explained, with day and night plates. The app shows only
papers with an explainer, so a few are not, to prove they stay hidden: one in each
closed chunk (HIDDEN), and papers 300, 301, and 302, which upgrades.json explains.
Preprints and peer-reviewed papers take turns, except in chunks 3 and 4, which are
lopsided: four preprints to every peer-reviewed paper (LOPSIDED).

Chunk 9 is the open chunk and is written by hand; this script leaves it alone and
counts its items for the head. upgrades.json explains three papers in closed chunks, one
for each meaning of an entry's readout key: an object replaces the item's readout, null
removes it, and no key keeps it. The first of them has the explainer in
app/src/fixtures/papers/arxiv-2609.10300/.

The plates are simple generated stills, day and night (hero.webp, hero-night.webp). The
open chunk's explained paper and the three upgraded papers have their own. The other
explained papers share a few stills in app/src/fixtures/fixture-plates/, which keeps the
fixtures small, and only arxiv-2611.04821 and arxiv-2609.10300 have explainer pages. The
stills need Pillow; without it they are skipped.

Run from the repo root: uv run --with pillow python tools/make-feed-fixtures.py
Check against the schemas: uv run --project pipeline python tools/make-feed-fixtures.py --check
"""
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "app/src/fixtures"
FEED = FIXTURES / "feed/v1"
CLOSED_CHUNKS = 8
CHUNK_SIZE = 40
UPGRADED = "arxiv-2609.10300"
# Papers 300 to 302 have no explainer in their chunk; upgrades.json gives them one.
UPGRADED_K = {300, 301, 302}
# One paper in each closed chunk has no explainer and no upgrade, so the app hides it.
HIDDEN_K = {number * CHUNK_SIZE + 17 for number in range(CLOSED_CHUNKS)}
# Chunks 3 and 4: only every fifth paper is peer-reviewed.
LOPSIDED = range(2 * CHUNK_SIZE, 4 * CHUNK_SIZE)
# Shared plate stills for the generated explained papers: fixture-plates/<n>/.
SHARED_PLATES = 4
# The open chunk's explained paper, written by hand in chunk 9; its stills are made here.
OPEN_EXPLAINED = "arxiv-2611.04821"
# Plates are 390 by 230 on the boards; the stills keep that ratio at 1200 wide.
PLATE_W, PLATE_H = 1200, 708

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


def readout(k: int) -> dict | None:
    """A readout for some generated papers: a count, a length with a unit, a time with an exponent."""
    return {
        0: None,
        1: {"value": str(k), "label": "Fixture count of things"},
        2: {"value": "0.5", "unit": "meters", "label": "Fixture length measured"},
        3: {"value": "2.4", "exponent": -6, "unit": "seconds", "label": "Fixture time measured"},
    }[k % 4]


def hero(paper: str, kind: str, to_scale: bool | None = None, folder: str | None = None) -> dict:
    """A plate with day and night stills in papers/<paper>/, or in [folder] when it is given."""
    folder = folder or f"papers/{paper}"
    out = {
        "path": f"{folder}/hero.webp",
        "width": PLATE_W,
        "height": PLATE_H,
        "night": {"path": f"{folder}/hero-night.webp", "width": PLATE_W, "height": PLATE_H},
        "kind": kind,
    }
    if to_scale is not None:
        out["to_scale"] = to_scale
    return out


def item(k: int) -> dict:
    field = list(FIELDS)[k % len(FIELDS)]
    tag = FIELDS[field][k % 3]
    added = START + timedelta(hours=4 * k)
    extra = {}
    if k % 5 == 0:
        # An exact suffix of the hook, as the schema requires.
        extra["hook_turn"] = f"about {tag}"
    if readout(k):
        extra["readout"] = readout(k)
    paper = f"arxiv-2609.{10000 + k:05d}"
    peer_reviewed = k % 5 == 0 if k in LOPSIDED else k % 2 == 1
    explained = k not in HIDDEN_K and k not in UPGRADED_K
    if explained:
        n = k % SHARED_PLATES
        extra["explainer"] = f"papers/{paper}/"
        extra["hero"] = hero(paper, "data" if n % 2 == 0 else "illustration",
                             to_scale=None if n % 2 == 0 else n == 1, folder=f"fixture-plates/{n}")
    return {
        "id": paper,
        "title": f"Fixture study {k} on {tag}",
        "hook": f"Fixture paper {k}: a {field} finding about {tag}",
        **({"hook_turn": extra["hook_turn"]} if "hook_turn" in extra else {}),
        "summary": f"This is fixture paper {k} in {field}, used by the app tests. "
                   f"It stands in for a plain summary of a study about {tag}.",
        "field": field,
        "tags": [tag],
        "status": "peer_reviewed" if peer_reviewed else "preprint",
        "venue": "Fixture Journal" if peer_reviewed else "arXiv",
        "published": added.strftime("%Y-%m-%d"),
        "authors_short": "Fixture et al.",
        "url": f"https://arxiv.org/abs/2609.{10000 + k:05d}",
        "has_explainer": explained,
        **({"explainer": extra["explainer"], "hero": extra["hero"]} if explained else {}),
        # 3.0 to 7.4, below every hand-written paper in the open chunk.
        "significance": round(3.0 + (k * 7 % 45) / 10, 1),
        "added_at": rfc3339(added),
        **({"readout": extra["readout"]} if "readout" in extra else {}),
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
    # Papers 300, 301, and 302: 301 and 302 have readouts of their own (readout() above).
    replaced, removed, kept = UPGRADED, "arxiv-2609.10301", "arxiv-2609.10302"
    write(FEED / "upgrades.json", {
        "v": 1,
        "upgrades": {
            replaced: {
                "explainer": f"papers/{replaced}/",
                "hero": hero(replaced, "data"),
                "readout": {"value": ">5.1", "unit": "sigma", "label": "Fixture significance of the result"},
                "explained_at": "2026-11-12T16:00:00Z",
            },
            removed: {
                "explainer": f"papers/{removed}/",
                "hero": hero(removed, "illustration", to_scale=False),
                "readout": None,
                "explained_at": "2026-11-12T16:10:00Z",
            },
            kept: {
                "explainer": f"papers/{kept}/",
                "hero": hero(kept, "illustration", to_scale=True),
                "explained_at": "2026-11-12T16:20:00Z",
            },
        },
    })
    stills([f"papers/{p}" for p in (OPEN_EXPLAINED, replaced, removed, kept)]
           + [f"fixture-plates/{n}" for n in range(SHARED_PLATES)])


def stills(folders: list[str]) -> None:
    """A day and a night still per folder: rings in plate ink, a live line, a ruler. Not board art."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow is not installed: the plate stills were not written", file=sys.stderr)
        return
    themes = {
        "hero.webp": dict(ground="#E9E6DE", plate="#1F3FD0", ink="#16130F", live="#E0330A", ring=2),
        "hero-night.webp": dict(ground="#0E1116", plate="#4D63C9", ink="#9C988D", live="#FFA63D", ring=2),
    }
    s = 2  # drawn at twice the size, then reduced, for smooth edges
    W, H = PLATE_W * s, PLATE_H * s
    band = round(H * 196 / 230)
    for n, folder in enumerate(folders):
        for name, t in themes.items():
            img = Image.new("RGB", (W, H), t["ground"])
            d = ImageDraw.Draw(img)
            # The shared stills (from the fifth on) put their rings further left, to tell them apart.
            cx, cy = W * (0.62 + 0.08 * n if n < 4 else 0.12 + 0.16 * (n - 4)), band * 0.38
            r = 40 * s
            while r < W:
                d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=t["plate"], width=t["ring"] * s)
                r += 22 * s
            d.rectangle((0, band, W, H), fill=t["ground"])
            zero = band - 120 * s
            pts = []
            for i in range(0, 801):
                x = 60 * s + i * (W - 140 * s) / 800
                u = i / 800
                amp = 90 * s * math.sin(math.pi * u) ** 2 if u < 0.85 else 0
                pts.append((x, zero - amp * math.sin(2 * math.pi * (3 + 9 * u) * u)))
            d.line(pts, fill=t["ground"], width=22 * s, joint="curve")
            d.line(pts, fill=t["live"], width=6 * s, joint="curve")
            px, py = pts[-1]
            d.ellipse((px - 20 * s, py - 20 * s, px + 20 * s, py + 20 * s), fill=t["ground"])
            d.ellipse((px - 11 * s, py - 11 * s, px + 11 * s, py + 11 * s), fill=t["live"])
            d.line((60 * s, band, W, band), fill=t["ink"], width=3 * s)
            for i in range(13):
                x = 60 * s + i * 90 * s
                d.line((x, band, x, band + (22 if i % 4 == 0 else 12) * s), fill=t["ink"], width=3 * s)
            out = FIXTURES / folder / name
            out.parent.mkdir(parents=True, exist_ok=True)
            img.resize((PLATE_W, PLATE_H), Image.LANCZOS).save(out, "WEBP", quality=80)


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
