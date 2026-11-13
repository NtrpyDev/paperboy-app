"""batch: split discovered candidates into small files for the scout to judge."""
import json
from pathlib import Path


def register(subparsers) -> None:
    p = subparsers.add_parser("batch", help="split work/candidates.jsonl into work/batches/NNN.jsonl")
    p.add_argument("--work", required=True, type=Path)
    p.add_argument("--size", type=int, default=15, help="candidates per batch")
    p.set_defaults(run=run)


def run(args) -> int:
    source = args.work / "candidates.jsonl"
    lines = [line for line in source.read_text().splitlines() if line.strip()] if source.exists() else []
    out = args.work / "batches"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.jsonl"):
        old.unlink()
    count = 0
    for start in range(0, len(lines), args.size):
        count += 1
        (out / f"{count:03d}.jsonl").write_text("\n".join(lines[start:start + args.size]) + "\n")
    print(json.dumps({"candidates": len(lines), "batches": count}))
    return 0
