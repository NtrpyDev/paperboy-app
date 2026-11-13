"""reset-feed: one-time rewrite of a content repo checkout to the rule that every paper in the feed has a page.

Feeds published before that rule hold short cards: papers with no page. This command keeps only
the items that have an explainer and starts the feed again from them:

- the feed: those items, in their old order, merged with their upgrades.json entries (explainer,
  plates, readout) and given their depth, in new chunks from chunk 1; the head rewritten; the
  other chunks and upgrades.json deleted;
- papers/: only those papers' folders, each meta.json given its depth;
- state/seen/: only those papers, with their new chunk numbers;
- the backlog (state/queue/), the claims (state/claims/), and the backlog ledger (state/queued/)
  emptied, so the papers they held can be found and judged again;
- state/queue-failed.jsonl kept, so a paper given up on stays given up on;
- every cursor later than --rewind-cursors-to set to that day, so the next run reads the days
  after it again under the current rules (a cursor is the last day counted as processed).

It prints what it will do and changes nothing without --yes. It never commits or pushes.
"""
import json
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from .. import backlog, schemas
from ..content_repo import CHUNK_SIZE, CHUNKS, CURSORS, HEAD, HEAD_KIT, MIN_APP, SEEN, UPGRADES, QUEUED, chunk_path, dump_json, set_readout


def register(subparsers) -> None:
    p = subparsers.add_parser("reset-feed", help="one-time: keep only feed items that have a page, empty the backlog, rewind the cursors",
                              description=__doc__)
    p.add_argument("--content", type=Path, required=True, help="content repo checkout to rewrite")
    p.add_argument("--keep-explained", action="store_true", required=True, help="keep the items that have an explainer (the only mode)")
    p.add_argument("--rewind-cursors-to", type=date.fromisoformat, required=True, help="YYYY-MM-DD: the last day to count as processed")
    p.add_argument("--yes", action="store_true", help="make the changes (without it, only print them)")
    p.add_argument("--now", help="RFC 3339 time for the head's updated_at (for tests)")
    p.set_defaults(run=run)


def _read(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


def _lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def plan(content: Path, through: str, now: str) -> dict:
    """What the rewrite writes and deletes, and the counts before and after."""
    head = _read(content / HEAD) or {"chunk_count": 0, "total_items": 0}
    chunk_files = sorted((content / CHUNKS).glob("*.json"))
    items = [item for path in chunk_files for item in _read(path)["items"]]
    upgrades = (_read(content / UPGRADES) or {"upgrades": {}})["upgrades"]

    kept, dropped_without_files = [], []
    for item in items:
        item = dict(item)
        upgrade = upgrades.get(item["id"])
        if upgrade is not None:
            item.update(has_explainer=True, explainer=upgrade["explainer"], hero=upgrade["hero"])
            if "readout" in upgrade:
                set_readout(item, upgrade["readout"])
        if not item.get("has_explainer"):
            continue
        folder = content / "papers" / item["id"]
        if not (folder / "index.html").is_file() or not (folder / "meta.json").is_file():
            dropped_without_files.append(item["id"])
            continue
        meta = _read(folder / "meta.json")
        render = (meta.get("check") or {}).get("render") or {}
        depth = meta.get("depth") or (render.get("page") or {}).get("depth") or "full"
        item["depth"] = depth
        kept.append((item, {**meta, "depth": depth}))

    writes: dict[Path, tuple[str | None, bytes]] = {}
    chunks = [kept[i:i + CHUNK_SIZE] for i in range(0, len(kept), CHUNK_SIZE)]
    chunk_of = {}
    for number, group in enumerate(chunks, 1):
        writes[chunk_path(number)] = ("chunk", dump_json({"v": 1, "number": number, "items": [item for item, _ in group]}))
        chunk_of.update({item["id"]: number for item, _ in group})
    writes[HEAD] = ("head", dump_json({"v": 1, "updated_at": now, "chunk_count": len(chunks), "total_items": len(kept),
                                        "chunk_size": CHUNK_SIZE, "kit": HEAD_KIT, "min_app": MIN_APP}))
    for item, meta in kept:
        writes[Path("papers") / item["id"] / "meta.json"] = ("paper-meta", dump_json(meta))

    seen_files = sorted((content / SEEN).glob("*.jsonl"))
    seen_lines = [line for path in seen_files for line in _lines(path)]
    by_month: dict[Path, list[dict]] = {}
    for line in seen_lines:
        if line["id"] in chunk_of:
            by_month.setdefault(SEEN / f"{line['added_at'][:7]}.jsonl", []).append({**line, "chunk": chunk_of[line["id"]]})
    for rel, lines in by_month.items():
        writes[rel] = ("seen", "".join(json.dumps(line, sort_keys=True, ensure_ascii=False) + "\n" for line in lines).encode())
    missing_seen = sorted(set(chunk_of) - {line["id"] for lines in by_month.values() for line in lines})

    cursors = _read(content / CURSORS)
    cursor_moves = {}
    if cursors is not None:
        new = {"v": 1, "cursors": dict(cursors["cursors"])}
        for source, day in cursors["cursors"].items():
            if day > through:
                new["cursors"][source] = through
                cursor_moves[source] = (day, through)
        writes[CURSORS] = ("cursors", dump_json(new))

    keep_ids = {item["id"] for item, _ in kept}
    deletes = [p.relative_to(content) for p in chunk_files if p.relative_to(content) not in writes]
    deletes += [UPGRADES] if (content / UPGRADES).exists() else []
    deletes += [p.relative_to(content) for p in sorted((content / "papers").glob("*")) if p.is_dir() and p.name not in keep_ids]
    deletes += [p.relative_to(content) for p in seen_files if p.relative_to(content) not in writes]
    for folder in (backlog.QUEUE, backlog.CLAIMS, QUEUED):
        deletes += [p.relative_to(content) for p in sorted((content / folder).glob("*")) if p.is_file()]

    failed = content / backlog.FAILED
    before = {
        "feed items": len(items), "items with a page": sum(1 for i in items if i.get("has_explainer") or i["id"] in upgrades),
        "chunks": len(chunk_files), "upgrades.json entries": len(upgrades),
        "paper folders": sum(1 for p in (content / "papers").glob("*") if p.is_dir()), "seen lines": len(seen_lines),
        "backlog": len(list((content / backlog.QUEUE).glob("*.json"))), "claims": len(list((content / backlog.CLAIMS).glob("*.json"))),
        "backlog ledger lines": sum(len(_lines(p)) for p in (content / QUEUED).glob("*.jsonl")),
        "queue-failed lines": len(_lines(failed)) if failed.exists() else 0,
    }
    after = {
        "feed items": len(kept), "items with a page": len(kept), "chunks": len(chunks), "upgrades.json entries": 0,
        "paper folders": len(kept), "seen lines": sum(len(v) for v in by_month.values()),
        "backlog": 0, "claims": 0, "backlog ledger lines": 0, "queue-failed lines": before["queue-failed lines"],
    }
    return {"writes": writes, "deletes": deletes, "kept": [item["id"] for item, _ in kept], "before": before, "after": after,
            "cursors": cursor_moves, "head_before": head, "dropped_without_files": dropped_without_files, "missing_seen": missing_seen}


def run(args) -> int:
    now = (datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content = args.content
    if not (content / HEAD).exists():
        print(f"reset-feed: {content / HEAD} does not exist; not a content repo checkout", file=sys.stderr)
        return 1
    p = plan(content, args.rewind_cursors_to.isoformat(), now)

    problems = []
    for rel, (schema, data) in sorted(p["writes"].items()):
        text = data.decode()
        records = [json.loads(line) for line in text.splitlines() if line.strip()] if rel.suffix == ".jsonl" else [json.loads(text)]
        for record in records:
            problems += [f"{rel}: {e}" for e in schemas.errors(schema, record)]
    if p["missing_seen"]:
        problems.append(f"no state/seen line for kept papers: {', '.join(p['missing_seen'])}")

    print(f"reset-feed: {content}")
    print("                         before  after")
    for key in p["before"]:
        print(f"  {key:<22} {p['before'][key]:>6} {p['after'][key]:>6}")
    print(f"  kept: {', '.join(p['kept']) or '(none)'}")
    for paper_id in p["dropped_without_files"]:
        print(f"  dropped although marked explained: {paper_id} has no index.html or meta.json in papers/")
    for source, (old, new) in sorted(p["cursors"].items()):
        print(f"  cursor {source}: {old} -> {new}")
    print(f"  files written: {len(p['writes'])}")
    for rel in sorted(p["writes"]):
        print(f"    write {rel}")
    print(f"  files and folders deleted: {len(p['deletes'])}")
    shown = [d for d in p["deletes"] if d.parts[0] != "papers"]
    for rel in shown:
        print(f"    delete {rel}")
    if len(shown) < len(p["deletes"]):
        print(f"    delete {len(p['deletes']) - len(shown)} paper folders under papers/ (every folder not kept)")
    if problems:
        print("reset-feed: the result would not match its schemas, nothing was changed:\n" + "\n".join(problems), file=sys.stderr)
        return 1
    if not args.yes:
        print("reset-feed: nothing changed. Run again with --yes to make these changes. It never commits or pushes.")
        return 0

    for rel in p["deletes"]:
        path = content / rel
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    for rel, (_, data) in p["writes"].items():
        path = content / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not (path.exists() and path.read_bytes() == data):
            path.write_bytes(data)
    print("reset-feed: done. Review with git status and git diff, then commit and push by hand.")
    return 0
