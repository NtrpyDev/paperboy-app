"""fetch: save one paper's free full text as Markdown.

Reads WORK/papers/<id>/candidate.json and writes fulltext.md and source.json next to it.
Exit codes: 0 fetched; 3 no lawful full text is reachable (source.json then says
"available": false and why, and no fulltext.md is left behind); 1 a real error.
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .. import schemas
from ..fulltext import sources
from ..fulltext.document import render
from ..fulltext.http import FetchError, PoliteClient, Unavailable

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_UNAVAILABLE = 3


def register(subparsers) -> None:
    parser = subparsers.add_parser("fetch", help="save a paper's free full text as Markdown", description=__doc__)
    parser.add_argument("--work", required=True, type=Path, help="the work folder")
    parser.add_argument("--id", required=True, dest="paper_id", help="the paper id, such as arxiv-2611.15301")
    parser.set_defaults(run=run)


def _timestamp(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(path: Path, record: dict) -> None:
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")


def run(args, *, transport=None, sleep=time.sleep, clock=time.time) -> int:
    folder = args.work / "papers" / args.paper_id
    candidate_path = folder / "candidate.json"
    try:
        record = json.loads(candidate_path.read_text())
    except (OSError, ValueError) as error:
        print(f"fetch: cannot read {candidate_path}: {error}", file=sys.stderr)
        return EXIT_ERROR
    problems = schemas.errors("candidate", record)
    if problems and schemas.errors("judged", record):
        print(f"fetch: {candidate_path} is not a valid candidate or judged record:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return EXIT_ERROR
    if record["id"] != args.paper_id:
        print(f"fetch: {candidate_path} is for {record['id']}, not {args.paper_id}", file=sys.stderr)
        return EXIT_ERROR

    fulltext_path = folder / "fulltext.md"
    source_path = folder / "source.json"
    with PoliteClient(transport=transport, sleep=sleep, clock=clock, stamp_dir=args.work / ".fetch-hosts") as client:
        try:
            fetched = sources.fetch(record, client)
        except Unavailable as reason:
            fulltext_path.unlink(missing_ok=True)
            _write_json(source_path, {
                "available": False,
                "reason": str(reason),
                "kind": record.get("fulltext", {}).get("kind"),
                "url": record.get("fulltext", {}).get("url"),
                "retrieved_at": _timestamp(clock()),
            })
            print(f"fetch: {args.paper_id}: no full text: {reason}")
            return EXIT_UNAVAILABLE
        except FetchError as error:
            print(f"fetch: {args.paper_id}: {error}", file=sys.stderr)
            return EXIT_ERROR

    markdown = render(fetched.paper)
    fulltext_path.write_text(markdown)
    _write_json(source_path, {
        "available": True,
        "url": fetched.url,
        "kind": fetched.kind,
        "license": fetched.license,
        "retrieved_at": _timestamp(clock()),
        "chars": len(markdown),
        "sections": fetched.paper.section_count(),
    })
    print(f"fetch: {args.paper_id}: {len(markdown)} chars, {fetched.paper.section_count()} sections, license {fetched.license}")
    return EXIT_OK
