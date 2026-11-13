"""discover: list newly released papers from the sources as candidates for the scout.

Reads each source from its start date, merges records of the same paper (see
paperboy_pipeline.dedupe), skips papers already in the content repo's state/seen/, and writes
WORK/candidates.jsonl, one Candidate per line, newest first. Prints one count line per source.

The start date is --since when given; otherwise the source's cursor in
CONTENT_REPO/state/cursors.json; otherwise two days before today (UTC). Discover only reads
the content repo. Exit status is 1 when a source failed or a record did not match the Candidate
schema; the candidates that could be read are still written.
"""
import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx

from .. import dedupe, ids, schemas
from ..content_repo import ContentRepo, PublishError
from ..sources import ADAPTERS
from ..sources.http import Http, SourceError, make_client

DEFAULT_DAYS = 2


def register(subparsers) -> None:
    parser = subparsers.add_parser("discover", help="list new papers from the sources as candidates", description=__doc__)
    parser.add_argument("--work", type=Path, required=True, help="work folder; candidates.jsonl is written here")
    parser.add_argument("--content", type=Path, required=True, help="content repo checkout to read state/ from")
    parser.add_argument("--since", type=date.fromisoformat, help="start date YYYY-MM-DD for every source (default: each source's cursor)")
    parser.add_argument("--sources", type=source_list, default=list(ADAPTERS), help="comma separated: " + ",".join(ADAPTERS))
    parser.add_argument("--limit", type=_positive, help="at most this many new papers from each source")
    parser.set_defaults(run=run)


def source_list(text: str) -> list[str]:
    names = [name.strip() for name in text.split(",") if name.strip()]
    unknown = [name for name in names if name not in ADAPTERS]
    if unknown or not names:
        raise argparse.ArgumentTypeError(f"unknown source {', '.join(unknown) or '(none)'}; choose from {','.join(ADAPTERS)}")
    return names


def _positive(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def run(args, *, transport: httpx.BaseTransport | None = None, clock=time.monotonic, sleep=time.sleep, today: date | None = None) -> int:
    today = today or datetime.now(timezone.utc).date()
    try:
        repo = ContentRepo(args.content)
    except (PublishError, ValueError) as error:
        print(f"discover: cannot read {args.content}: {error}", file=sys.stderr)
        return 1
    cursors = repo.cursors.get("cursors", {})

    fetched: dict[str, list[dict]] = {}
    failed: dict[str, str] = {}
    with make_client(transport) as client:
        http = Http(client, clock=clock, sleep=sleep, today=lambda: today)
        for name in args.sources:
            since = _since(args.since, cursors.get(name), today)
            try:
                fetched[name] = ADAPTERS[name](since, args.limit, http)
            except SourceError as error:
                failed[name] = str(error)

    papers = dedupe.merge([record for name in args.sources for record in fetched.get(name, [])])
    candidates, invalid = [], 0
    for paper in papers:
        if _seen(repo, paper):
            continue
        candidate = {k: v for k, v in paper.record.items() if not k.startswith("_")}
        problems = schemas.errors("candidate", candidate)
        if problems:
            invalid += 1
            print(f"discover: {candidate.get('id')} is not a valid Candidate: {'; '.join(problems)}", file=sys.stderr)
            continue
        candidates.append(candidate)
    candidates.sort(key=lambda c: c["id"])
    candidates.sort(key=lambda c: c["published"], reverse=True)

    args.work.mkdir(parents=True, exist_ok=True)
    out = args.work / "candidates.jsonl"
    partial = out.with_suffix(".jsonl.partial")
    partial.write_text("".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in candidates))
    partial.replace(out)

    for name in args.sources:
        if name in failed:
            print(f"{name}: failed: {failed[name]}")
            continue
        found = sum(r["_new"] for r in fetched[name])
        written = sum(c["source"] == name for c in candidates)
        print(f"{name}: {found} found, {written} written")
    return 1 if failed or invalid else 0


def _since(given: date | None, cursor: str | None, today: date) -> date:
    if given is not None:
        start = given
    elif cursor:
        start = date.fromisoformat(cursor[:10])
    else:
        start = today - timedelta(days=DEFAULT_DAYS)
    return min(start, today)


def _seen(repo: ContentRepo, paper: dedupe.Paper) -> bool:
    title = paper.record["title"]
    probes = [paper.record, *paper.members]
    probes += [{"id": ids.paper_id(doi=doi), "doi": doi, "title": title} for doi in paper.record.get("_aliases", [])]
    return any(repo.find(probe) is not None for probe in probes)
