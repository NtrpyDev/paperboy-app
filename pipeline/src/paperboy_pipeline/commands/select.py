"""select: merge the scout's judged batches, drop weak papers, and queue the best for explainers."""
import json
from pathlib import Path

from .. import schemas


def register(subparsers) -> None:
    p = subparsers.add_parser("select", help="merge work/judged/*.jsonl into work/judged.jsonl and pick the explain queue")
    p.add_argument("--work", required=True, type=Path)
    p.add_argument("--floor", type=float, default=5.0, help="papers scoring below this never reach the feed")
    p.add_argument("--explain", type=int, default=3, help="how many papers to queue for explainers")
    p.add_argument("--explain-floor", type=float, default=6.5, help="lowest significance worth an explainer")
    p.set_defaults(run=run)


def run(args) -> int:
    records, problems, seen = [], [], set()
    for path in sorted((args.work / "judged").glob("*.jsonl")):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError as exc:
                problems.append(f"{path.name}:{number}: not JSON ({exc})")
                continue
            record["explain"] = False
            errors = schemas.errors("judged", record)
            if errors:
                problems.append(f"{path.name}:{number}: {'; '.join(errors[:3])}")
                continue
            if record["id"] in seen:
                continue
            seen.add(record["id"])
            records.append(record)

    kept = [r for r in records if r["significance"] >= args.floor]
    explainable = sorted(
        (r for r in kept if r["fulltext"]["available"] and r["significance"] >= args.explain_floor),
        key=lambda r: (-r["significance"], r["id"]),
    )
    queue = explainable[: max(0, args.explain)]
    for record in queue:
        record["explain"] = True
        folder = args.work / "papers" / record["id"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "candidate.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")

    (args.work / "judged.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept))
    (args.work / "explain-queue.txt").write_text("".join(r["id"] + "\n" for r in queue))
    print(json.dumps({
        "judged": len(records), "kept": len(kept), "dropped_below_floor": len(records) - len(kept),
        "queued_for_explainer": [r["id"] for r in queue], "rejected_lines": problems,
    }, indent=2))
    return 0
