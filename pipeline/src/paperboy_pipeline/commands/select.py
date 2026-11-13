"""select: merge the scout's judged batches, drop weak papers, and mark those worth an explainer.

Reads WORK/judged/*.jsonl, validates each line as a Judged record, keeps the first of each id,
drops papers below --floor, and writes WORK/judged.jsonl. `explain` is set true on a paper
worth an explainer (paperboy_pipeline.explaining: full text of an allowed kind and at least
--explain-floor); `queue add` puts those papers in the content repo's explain queue.
"""
import json
from pathlib import Path

from .. import schemas
from ..explaining import EXPLAIN_FLOOR, explain_kinds, worth_explaining


def register(subparsers) -> None:
    p = subparsers.add_parser("select", help="merge work/judged/*.jsonl into work/judged.jsonl", description=__doc__)
    p.add_argument("--work", required=True, type=Path)
    p.add_argument("--floor", type=float, default=5.0, help="papers scoring below this never reach the feed")
    p.add_argument("--explain-floor", type=float, default=EXPLAIN_FLOOR, help=f"lowest significance worth an explainer (default {EXPLAIN_FLOOR})")
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
    kinds = explain_kinds()
    for record in kept:
        record["explain"] = worth_explaining(record, args.explain_floor, kinds)

    (args.work / "judged.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept))
    print(json.dumps({
        "judged": len(records), "kept": len(kept), "dropped_below_floor": len(records) - len(kept),
        "worth_an_explainer": sum(r["explain"] for r in kept), "rejected_lines": problems,
    }, indent=2))
    return 0
