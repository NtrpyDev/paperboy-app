"""batch: split discovered candidates into files for the triage agents and the scout.

Two passes over WORK/candidates.jsonl:

- `batch --triage` writes WORK/triage/NNN.tsv, up to 150 lines each and split evenly, one
  paper per line:
  id, source, venue, categories joined by a space, title, separated by tabs. A triage agent
  reads only titles and writes the ids worth a closer look to WORK/triage-picks/NNN.txt.
- `batch` writes WORK/batches/NNN.jsonl, the abstract batches for the scout: the picked papers
  plus every paper from a followed journal (source crossref or europepmc with a venue in
  pipeline/journals.json), which skips triage. It refuses when WORK/triage-picks/ is missing.
- `batch --all` batches every candidate without triage.

Candidates keep their order (newest first). Prints a JSON summary.
"""
import json
import re
import sys
from pathlib import Path

from .. import journals

TRIAGE_SIZE = 150
JOURNAL_SOURCES = ("crossref", "europepmc")


def register(subparsers) -> None:
    p = subparsers.add_parser("batch", help="split work/candidates.jsonl into triage files or abstract batches", description=__doc__)
    p.add_argument("--work", required=True, type=Path)
    p.add_argument("--size", type=int, default=15, help="candidates per abstract batch")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--triage", action="store_true", help="write title files to work/triage/ for the triage agents")
    mode.add_argument("--all", action="store_true", help="batch every candidate, without triage")
    p.set_defaults(run=run)


def run(args) -> int:
    source = args.work / "candidates.jsonl"
    lines = [line for line in source.read_text().splitlines() if line.strip()] if source.exists() else []
    records = [json.loads(line) for line in lines]
    followed = journals.titles()
    passes = [r["source"] in JOURNAL_SOURCES and r["venue"] in followed for r in records]

    if args.triage:
        rows = [_triage_line(r) for r, skip in zip(records, passes) if not skip]
        count = _write_files(args.work / "triage", ".tsv", rows, TRIAGE_SIZE, even=True)
        print(json.dumps({"candidates": len(records), "passed_through": sum(passes), "triaged": len(rows), "triage_files": count}))
        return 0

    if args.all:
        count = _write_files(args.work / "batches", ".jsonl", lines, args.size)
        print(json.dumps({"candidates": len(records), "batches": count}))
        return 0

    picks_dir = args.work / "triage-picks"
    if not picks_dir.is_dir():
        print(f"batch: {picks_dir} does not exist; run the triage agents first, or pass --all to batch every candidate", file=sys.stderr)
        return 1
    picked = set()
    for path in sorted(picks_dir.glob("*.txt")):
        picked |= {line.strip() for line in path.read_text().splitlines() if line.strip()}
    chosen = [line for line, r, skip in zip(lines, records, passes) if skip or r["id"] in picked]
    count = _write_files(args.work / "batches", ".jsonl", chosen, args.size)
    triage_files = {p.stem for p in (args.work / "triage").glob("*.tsv")}
    print(json.dumps({
        "candidates": len(records),
        "picked": sum(1 for r, skip in zip(records, passes) if not skip and r["id"] in picked),
        "passed_through": sum(passes),
        "batches": count,
        "triage_files_without_picks": sorted(triage_files - {p.stem for p in picks_dir.glob("*.txt")}),
    }))
    return 0


def _triage_line(record: dict) -> str:
    fields = [record["id"], record["source"], record["venue"], " ".join(record.get("categories") or []), record["title"]]
    return "\t".join(re.sub(r"\s+", " ", field).strip() for field in fields)


def _write_files(folder: Path, suffix: str, rows: list[str], size: int, even: bool = False) -> int:
    """Write rows into numbered files of at most `size` rows. With even, the files differ by at most one row."""
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob(f"*{suffix}"):
        old.unlink()
    count = -(-len(rows) // size)
    if not even:
        bounds = [(n * size, (n + 1) * size) for n in range(count)]
    else:
        base, extra = divmod(len(rows), count) if count else (0, 0)
        starts = [n * base + min(n, extra) for n in range(count + 1)]
        bounds = list(zip(starts, starts[1:]))
    for number, (start, end) in enumerate(bounds, 1):
        (folder / f"{number:03d}{suffix}").write_text("\n".join(rows[start:end]) + "\n")
    return count
