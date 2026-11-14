"""record-cost: append what one API run cost to the content repo's state/cost/<YYYY-MM>.jsonl.

Reads Claude Code's JSON result from a headless run (claude -p --output-format json, saved to a
file) for the total cost and per-model token counts, and the run's work folder for the papers
taken and the pages built, by kind and field. Safe to run after a Claude step that failed or
was cut off: the record holds what is known and is marked incomplete (see paperboy_pipeline.cost).
A run already recorded in the month is not recorded again.

With --push it commits and pushes the record itself, starting from origin/main and appending it
again on a newer main when the push is rejected (paperboy_pipeline.gitsync).
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .. import cost, gitsync, schemas
from ..content_repo import dump_line

OUTCOMES = ("success", "failure", "cancelled", "skipped")


def register(subparsers) -> None:
    p = subparsers.add_parser("record-cost", help="append one API run's cost to state/cost/ in the content repo",
                              description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--content", type=Path, required=True, help="content repo checkout")
    p.add_argument("--work", type=Path, required=True, help="the run's work folder (take.json and papers/)")
    p.add_argument("--result", type=Path, required=True, help="Claude Code's JSON result file; missing or cut off is allowed")
    p.add_argument("--run", dest="run_name", required=True, help="this run's unique name (the workflow passes the GitHub run id and attempt)")
    p.add_argument("--cap-usd", type=_positive, required=True, help="the per-run cap the Claude step ran with (--max-budget-usd)")
    p.add_argument("--outcome", choices=OUTCOMES, help="the Claude step's outcome; anything but success marks the run incomplete")
    p.add_argument("--push", action="store_true", help="commit and push the record, starting from origin/main")
    p.add_argument("--now", help="RFC 3339 time to use as the current time (for tests)")
    p.set_defaults(run=run)


def _positive(text: str) -> float:
    value = float(text)
    if not value > 0:
        raise argparse.ArgumentTypeError("must be more than 0")
    return value


def _now(value: str | None) -> str:
    moment = datetime.fromisoformat(value.replace("Z", "+00:00")) if value else datetime.now(timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(args) -> int:
    now = _now(args.now)
    record = cost.build(run=args.run_name, result_path=args.result, work=args.work, cap_usd=args.cap_usd,
                        outcome=args.outcome, now=now)
    problems = schemas.errors("cost-record", record)
    if problems:
        print(f"record-cost: the record would not match schema/cost-record.schema.json, nothing was written: {'; '.join(problems)}", file=sys.stderr)
        return 1
    month = cost.month_of(now)
    state = {}

    def apply():
        path = args.content / cost.month_path(month)
        present = cost.read_month(args.content, month)
        state["already"] = any(r["run"] == record["run"] for r in present)
        if state["already"]:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as out:
            out.write(dump_line(record))

    try:
        if args.push:
            gitsync.sync(args.content, apply, start_from_origin=True, label="record-cost")
        else:
            apply()
    except (gitsync.GitError, cost.CostError) as error:
        print(f"record-cost: {error}", file=sys.stderr)
        return 1
    if state["already"]:
        print(f"record-cost: run {record['run']} is already recorded in {cost.month_path(month)}, nothing was written", file=sys.stderr)
    print(json.dumps(record, sort_keys=True))
    return 0
