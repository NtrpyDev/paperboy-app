"""queue: papers worth an explainer wait in the content repo until a run gets to them.

Each waiting paper is CONTENT/state/queue/<id>.json: its Judged record plus "queued_at" (UTC,
RFC 3339). Papers the queue gave up on are lines {"id", "reason", "at"} in
CONTENT/state/queue-failed.jsonl and are never queued or taken again.

  add     queue every paper in WORK/judged.jsonl worth an explainer (paperboy_pipeline.explaining)
  take    choose the best K waiting papers and prepare their work folders
  done    remove a paper from the queue (its explainer is published)
  fail    remove a paper and record why it cannot be explained
  prune   remove papers that have waited longer than --days
  list    print how many are waiting and the top ten

These commands only change files in the checkout; publish --commit commits them with state/.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .. import schemas
from ..explaining import EXPLAIN_FLOOR, explain_kinds, worth_explaining

QUEUE = Path("state/queue")
FAILED = Path("state/queue-failed.jsonl")


def register(subparsers) -> None:
    parser = subparsers.add_parser("queue", help="the explain queue in the content repo", description=__doc__,
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
    actions = parser.add_subparsers(dest="action", required=True)

    def action(name: str, help: str, work: bool = False) -> argparse.ArgumentParser:
        p = actions.add_parser(name, help=help)
        p.add_argument("--content", type=Path, required=True, help="content repo checkout holding state/queue/")
        if work:
            p.add_argument("--work", type=Path, required=True, help="work folder")
        return p

    p = action("add", "queue the papers in work/judged.jsonl worth an explainer", work=True)
    p.add_argument("--explain-floor", type=float, default=EXPLAIN_FLOOR, help=f"lowest significance worth an explainer (default {EXPLAIN_FLOOR})")
    p.add_argument("--kinds", type=_kinds, help="comma separated full text kinds to queue (default: explain_fulltext_kinds in pipeline/config.json)")
    p = action("take", "choose the best waiting papers for this run", work=True)
    p.add_argument("--n", type=int, required=True, help="how many papers to take")
    p = action("done", "remove a paper whose explainer is published")
    p.add_argument("--id", required=True)
    p = action("fail", "remove a paper that cannot be explained and record why")
    p.add_argument("--id", required=True)
    p.add_argument("--reason", required=True)
    p = action("prune", "remove papers that have waited too long")
    p.add_argument("--days", type=int, default=21)
    action("list", "print the count and the top ten")
    parser.set_defaults(run=run)


def _kinds(text: str) -> list[str]:
    return [kind.strip() for kind in text.split(",") if kind.strip()]


def run(args, *, now: str | None = None) -> int:
    now = now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return ACTIONS[args.action](args, now)


def _failed_ids(content: Path) -> set[str]:
    path = content / FAILED
    if not path.exists():
        return set()
    return {json.loads(line)["id"] for line in path.read_text().splitlines() if line.strip()}


def _waiting(content: Path) -> list[tuple[Path, dict]]:
    entries = []
    for path in sorted((content / QUEUE).glob("*.json")):
        try:
            entries.append((path, json.loads(path.read_text())))
        except json.JSONDecodeError as error:
            print(f"queue: {path} is not valid JSON, skipped: {error}", file=sys.stderr)
    return entries


def _best_first(entries: list[tuple[Path, dict]]) -> list[tuple[Path, dict]]:
    ordered = sorted(entries, key=lambda e: e[1]["id"])
    ordered.sort(key=lambda e: e[1]["published"], reverse=True)
    ordered.sort(key=lambda e: e[1]["significance"], reverse=True)
    return ordered


def _record(entry: dict) -> dict:
    return {k: v for k, v in entry.items() if k != "queued_at"}


def _read_lines(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _add(args, now: str) -> int:
    kinds = args.kinds if args.kinds is not None else explain_kinds()
    failed = _failed_ids(args.content)
    added = 0
    for record in _read_lines(args.work / "judged.jsonl"):
        if not worth_explaining(record, args.explain_floor, kinds) or record["id"] in failed:
            continue
        path = args.content / QUEUE / f"{record['id']}.json"
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({**record, "queued_at": now}, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        added += 1
    print(f"queue: added {added}, {len(_waiting(args.content))} waiting")
    return 0


def _take(args, now: str) -> int:
    failed = _failed_ids(args.content)
    chosen = []
    for path, entry in _best_first(_waiting(args.content)):
        if len(chosen) >= args.n:
            break
        if entry.get("id") in failed:
            continue
        record = _record(entry)
        problems = schemas.errors("judged", record)
        if problems:
            print(f"queue: {path} is not a valid Judged record, skipped: {'; '.join(problems[:3])}", file=sys.stderr)
            continue
        chosen.append(record)

    judged_path = args.work / "judged.jsonl"
    present = {r["id"] for r in _read_lines(judged_path)}
    args.work.mkdir(parents=True, exist_ok=True)
    with judged_path.open("a") as judged:
        for record in chosen:
            folder = args.work / "papers" / record["id"]
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "candidate.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
            if record["id"] not in present:
                judged.write(json.dumps(record, ensure_ascii=False) + "\n")
    ids = [r["id"] for r in chosen]
    (args.work / "explain-queue.txt").write_text("".join(i + "\n" for i in ids))
    for paper_id in ids:
        print(paper_id)
    return 0


def _remove(content: Path, paper_id: str) -> bool:
    path = content / QUEUE / f"{paper_id}.json"
    if not path.exists():
        print(f"queue: {paper_id} is not in the queue", file=sys.stderr)
        return False
    path.unlink()
    return True


def _done(args, now: str) -> int:
    return 0 if _remove(args.content, args.id) else 1


def _fail(args, now: str) -> int:
    entry = {"id": args.id, "reason": args.reason, "at": now}
    problems = schemas.errors("queue-failed", entry)
    if problems:
        print(f"queue: {'; '.join(problems)}", file=sys.stderr)
        return 1
    _remove(args.content, args.id)  # recorded as failed even when it was no longer waiting
    path = args.content / FAILED
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as failed:
        failed.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n")
    return 0


def _prune(args, now: str) -> int:
    cutoff = datetime.fromisoformat(now) - timedelta(days=args.days)
    pruned = 0
    for path, entry in _waiting(args.content):
        if datetime.fromisoformat(entry["queued_at"]) < cutoff:
            path.unlink()
            pruned += 1
    print(f"queue: pruned {pruned}, {len(_waiting(args.content))} waiting")
    return 0


def _list(args, now: str) -> int:
    failed = _failed_ids(args.content)
    waiting = [e for _, e in _best_first(_waiting(args.content)) if e.get("id") not in failed]
    print(f"{len(waiting)} papers waiting")
    for entry in waiting[:10]:
        print(f"{entry['significance']:g}\t{entry['id']}\t{entry['published']}\t{entry.get('hook', '')}")
    return 0


ACTIONS = {"add": _add, "take": _take, "done": _done, "fail": _fail, "prune": _prune, "list": _list}
