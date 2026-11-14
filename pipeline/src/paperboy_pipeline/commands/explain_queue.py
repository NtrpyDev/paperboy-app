"""queue: the backlog of papers waiting in the content repo for a page.

A paper enters the feed only with a page, so every paper select keeps waits in the backlog until
a run builds its page: a full explainer for the best few with lawful free full text, a quick
explainer for the rest. See paperboy_pipeline.backlog for the files.

  add     put every paper in WORK/judged.jsonl into the backlog, marking which may get a full explainer
  take    claim this run's papers: up to --full for full explainers and up to --quick for quick ones;
          with a field list (--fields-url or --fields-file), only papers in the active fields,
          and --per-field quick ones for each field in place of --quick
  done    take a paper out of the backlog (publish does this for every paper it adds to the feed)
  fail    take a paper out of the backlog without a page, for good, and record why
  back    a full explainer failed or had no full text: the paper waits again, for a quick page only
  prune   take out papers that have waited longer than --days
  list    print how many wait and the top ten

add and take with --push commit and push their change themselves, starting from origin/main and
building it again when the push is rejected (paperboy_pipeline.gitsync). The other actions only
change the checkout; fail and back also note what they did in the work folder, and publish
commits and pushes it all.
"""
import argparse
import json
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .. import active_fields, backlog, gitsync, schemas
from ..content_repo import ContentRepo, PublishError
from ..explaining import EXPLAIN_FLOOR, explain_kinds, worth_explaining

STATUSES = backlog.STATUSES


def register(subparsers) -> None:
    parser = subparsers.add_parser("queue", help="the backlog of papers waiting for a page", description=__doc__,
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
    actions = parser.add_subparsers(dest="action", required=True)

    def action(name: str, help: str, work: bool = False) -> argparse.ArgumentParser:
        p = actions.add_parser(name, help=help)
        p.add_argument("--content", type=Path, required=True, help="content repo checkout holding state/queue/")
        if work:
            p.add_argument("--work", type=Path, required=True, help="work folder")
        p.add_argument("--now", help="RFC 3339 time to use as the current time (for tests)")
        return p

    p = action("add", "put the papers in work/judged.jsonl into the backlog", work=True)
    p.add_argument("--explain-floor", type=float, default=EXPLAIN_FLOOR, help=f"lowest significance that may get a full explainer (default {EXPLAIN_FLOOR})")
    p.add_argument("--kinds", type=_kinds, help="comma separated full text kinds that may get a full explainer (default: explain_fulltext_kinds in pipeline/config.json)")
    p.add_argument("--push", action="store_true", help="commit and push the backlog, starting from origin/main")
    p = action("take", "claim this run's papers", work=True)
    p.add_argument("--full", type=_count, required=True, help="most papers to take for full explainers")
    # Either the run's quick count (today's form) or a count per active field (with a field list), never both.
    count = p.add_mutually_exclusive_group(required=True)
    count.add_argument("--quick", type=_count, help="most papers to take for quick explainers")
    count.add_argument("--per-field", type=_count, help="most quick explainers to take for each active field (needs --fields-url or --fields-file)")
    source = p.add_mutually_exclusive_group()
    source.add_argument("--fields-url", help="URL of the worker's /v1/active-fields: take only for these fields")
    source.add_argument("--fields-file", type=Path, help="a file of the /v1/active-fields shape: take only for these fields")
    p.add_argument("--days", type=_count, help="first prune papers that have waited longer than this many days")
    p.add_argument("--claim-hours", type=float, default=backlog.CLAIM_HOURS, help=f"a claim older than this is stale and its paper can be taken again (default {backlog.CLAIM_HOURS})")
    p.add_argument("--run", dest="run_name", help="this run's name in its claims (default: the time and a random suffix)")
    p.add_argument("--push", action="store_true", help="commit and push the claims, starting from origin/main; take again when the push is rejected")
    p = action("done", "take a paper out of the backlog")
    p.add_argument("--id", required=True)
    p = action("fail", "take a paper out of the backlog without a page and record why", work=True)
    p.add_argument("--id", required=True)
    p.add_argument("--reason", required=True)
    p = action("back", "a full explainer failed: the paper waits again for a quick page", work=True)
    p.add_argument("--id", required=True)
    p.add_argument("--reason", required=True)
    p = action("prune", "take out papers that have waited too long")
    p.add_argument("--days", type=_count, default=7)
    p.add_argument("--claim-hours", type=float, default=backlog.CLAIM_HOURS)
    action("list", "print the count and the top ten")
    parser.set_defaults(run=run)


def _kinds(text: str) -> list[str]:
    return [kind.strip() for kind in text.split(",") if kind.strip()]


def _count(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError("must be 0 or more")
    return value


def _now(value: str | None) -> str:
    moment = datetime.fromisoformat(value.replace("Z", "+00:00")) if value else datetime.now(timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(args, *, now: str | None = None) -> int:
    now = now or _now(getattr(args, "now", None))
    try:
        return ACTIONS[args.action](args, now)
    except (gitsync.GitError, PublishError) as error:
        print(f"queue {args.action}: {error}", file=sys.stderr)
        return 1


# add

def _add_to(content: Path, records: list[dict], floor: float, kinds, now: str) -> dict:
    repo = ContentRepo(content)
    failed = backlog.failed_ids(content)
    present = backlog.waiting(content)
    counts = {"added": 0, "may_get_full": 0, "already_known": 0, "failed_before": 0}
    entered = []
    for rec in records:
        if rec["id"] in failed:
            counts["failed_before"] += 1
            continue
        if rec["id"] in present or repo.known(rec):
            counts["already_known"] += 1
            continue
        entry = {**rec, "explain": worth_explaining(rec, floor, kinds), "queued_at": now}
        backlog.write_entry(content, entry)
        entered.append(backlog.ledger_entry(rec, now))
        counts["added"] += 1
        counts["may_get_full"] += entry["explain"]
    backlog.append_ledger(content, entered)
    counts["waiting"] = len(backlog.waiting(content))
    return counts


def _add(args, now: str) -> int:
    kinds = args.kinds if args.kinds is not None else explain_kinds()
    records = backlog.read_lines(args.work / "judged.jsonl")
    for number, rec in enumerate(records, 1):
        problems = schemas.errors("judged", rec)
        if problems:
            print(f"queue add: judged.jsonl line {number} is not a valid Judged record: {'; '.join(problems[:3])}", file=sys.stderr)
            return 1
    result = {}

    def apply():
        result.update(_add_to(args.content, records, args.explain_floor, kinds, now))

    if args.push:
        gitsync.sync(args.content, apply, start_from_origin=True, label="queue add")
    else:
        apply()
    print(json.dumps(result))
    return 0


# take

best_first = backlog.best_first
alternate = backlog.alternate


def _prune_in(content: Path, days: int, now: str, claim_hours: float) -> int:
    cutoff = backlog.parse_time(now) - timedelta(days=days)
    claimed = backlog.fresh_claims(content, now, claim_hours)
    pruned = 0
    for paper_id, entry in backlog.waiting(content).items():
        if paper_id in claimed:
            continue
        if backlog.parse_time(entry["queued_at"]) < cutoff:
            backlog.leave(content, paper_id)
            pruned += 1
    waiting = backlog.waiting(content)
    for paper_id in backlog.claims(content):
        if paper_id not in waiting:
            backlog.release(content, paper_id)
    return pruned


def _free(content: Path, now: str, claim_hours: float) -> list[dict]:
    """Backlog entries a run may take: waiting, not failed, not freshly claimed, valid, not in the feed."""
    repo = ContentRepo(content)
    failed = backlog.failed_ids(content)
    claimed = backlog.fresh_claims(content, now, claim_hours)
    free = []
    for paper_id, entry in backlog.waiting(content).items():
        if paper_id in failed or paper_id in claimed:
            continue
        problems = backlog.errors(entry)
        if problems:
            print(f"queue take: state/queue/{paper_id}.json is not a valid backlog entry, skipped: {'; '.join(problems[:3])}", file=sys.stderr)
            continue
        if repo.find(entry) is not None:  # already in the feed: its page is never replaced
            continue
        free.append(entry)
    return free


def _choose(content: Path, full: int, quick: int, now: str, claim_hours: float) -> tuple[list[dict], list[dict]]:
    free = _free(content, now, claim_hours)
    for_full = alternate([e for e in free if e["explain"]])[:full]
    taken = {e["id"] for e in for_full}
    for_quick = alternate([e for e in free if e["id"] not in taken])[:quick]
    return for_full, for_quick


def _choose_per_field(content: Path, full: int, per_field: int, fields: list[str], now: str,
                      claim_hours: float) -> tuple[list[dict], list[dict]]:
    """Full explainers only from the active fields, up to `full` for the run; then up to
    `per_field` quick explainers for each active field, each field's papers best first and
    alternating preprints and peer-reviewed as alternate() does across the feed. The quick list
    goes round the fields in the list's order, one paper each, so a run the gate cuts short
    has served every field before any field gets its second."""
    active = set(fields)
    free = [e for e in _free(content, now, claim_hours) if e["field"] in active]
    for_full = alternate([e for e in free if e["explain"]])[:full]
    taken = {e["id"] for e in for_full}
    lanes = [alternate([e for e in free if e["field"] == field and e["id"] not in taken])[:per_field] for field in fields]
    for_quick = [lane[rank] for rank in range(per_field) for lane in lanes if rank < len(lane)]
    return for_full, for_quick


def _active_fields(args) -> list[str] | None:
    """The field list for a per-field take, or None for today's take. Raises FieldsError."""
    if args.fields_url is None and args.fields_file is None:
        return None
    return active_fields.load(url=args.fields_url, file=args.fields_file)


def _take(args, now: str) -> int:
    with_fields = args.fields_url is not None or args.fields_file is not None
    if with_fields != (args.per_field is not None):
        print("queue take: --per-field and a field list (--fields-url or --fields-file) go together; "
              "without a field list use --quick", file=sys.stderr)
        return 2
    try:
        fields = _active_fields(args)
    except active_fields.FieldsError as error:
        # No list, no spend: nothing is pruned, claimed, or written.
        print(f"queue take: the active field list is not usable, nothing was taken: {error}", file=sys.stderr)
        return 1
    run_name = args.run_name or f"{now}-{secrets.token_hex(3)}"
    result = {}

    def apply():
        pruned = _prune_in(args.content, args.days, now, args.claim_hours) if args.days is not None else 0
        if fields is None:
            for_full, for_quick = _choose(args.content, args.full, args.quick, now, args.claim_hours)
        else:
            for_full, for_quick = _choose_per_field(args.content, args.full, args.per_field, fields, now, args.claim_hours)
        for page, entries in (("full", for_full), ("quick", for_quick)):
            for entry in entries:
                claim = {"id": entry["id"], "run": run_name, "page": page, "claimed_at": now}
                path = args.content / backlog.CLAIMS / f"{entry['id']}.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(backlog.dump(claim))
        result.update(full=for_full, quick=for_quick, pruned=pruned)

    if args.push:
        gitsync.sync(args.content, apply, start_from_origin=True, label="queue take")
    else:
        apply()

    args.work.mkdir(parents=True, exist_ok=True)
    judged_path = args.work / "judged.jsonl"
    present = {r["id"] for r in backlog.read_lines(judged_path)}
    with judged_path.open("a") as judged:
        for entry in result["full"] + result["quick"]:
            rec = backlog.record(entry)
            folder = args.work / "papers" / rec["id"]
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "candidate.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
            if rec["id"] not in present:
                judged.write(json.dumps(rec, ensure_ascii=False) + "\n")
    taken = {"run": run_name, "full": [e["id"] for e in result["full"]], "quick": [e["id"] for e in result["quick"]]}
    if fields is not None:
        # Which field each paper is taken for, and the list it was taken under.
        taken.update(field={e["id"]: e["field"] for e in result["full"] + result["quick"]},
                     active_fields=fields, per_field=args.per_field)
    (args.work / "take.json").write_text(json.dumps(taken, indent=2) + "\n")
    summary = {**taken, "status": {e["id"]: e["status"] for e in result["full"] + result["quick"]},
               "pruned": result["pruned"], "waiting": len(backlog.waiting(args.content))}
    print(json.dumps(summary, indent=2))
    return 0


# done, fail, back, prune, list

def _done(args, now: str) -> int:
    if not backlog.leave(args.content, args.id):
        print(f"queue: {args.id} is not in the backlog", file=sys.stderr)
        return 1
    return 0


def _note(work: Path, outcome: dict) -> None:
    work.mkdir(parents=True, exist_ok=True)
    with (work / "outcomes.jsonl").open("a") as out:
        out.write(json.dumps(outcome, sort_keys=True, ensure_ascii=False) + "\n")


def _fail(args, now: str) -> int:
    problems = schemas.errors("queue-failed", {"id": args.id, "reason": args.reason, "at": now})
    if problems:
        print(f"queue: {'; '.join(problems)}", file=sys.stderr)
        return 1
    backlog.fail(args.content, args.id, args.reason, now)  # recorded even when it was no longer waiting
    _note(args.work, {"action": "fail", "id": args.id, "reason": args.reason, "at": now})
    return 0


def _back(args, now: str) -> int:
    if not args.reason.strip():
        print("queue: --reason must say why", file=sys.stderr)
        return 1
    if not backlog.back(args.content, args.id, args.reason):
        print(f"queue: {args.id} is not in the backlog", file=sys.stderr)
        return 1
    _note(args.work, {"action": "back", "id": args.id, "reason": args.reason, "at": now})
    return 0


def _prune(args, now: str) -> int:
    pruned = _prune_in(args.content, args.days, now, args.claim_hours)
    print(f"queue: pruned {pruned}, {len(backlog.waiting(args.content))} waiting")
    return 0


def _list(args, now: str) -> int:
    failed = backlog.failed_ids(args.content)
    entries = [e for e in backlog.waiting(args.content).values() if e.get("id") not in failed]
    claimed = backlog.fresh_claims(args.content, now)
    by_status = {s: sum(e["status"] == s for e in entries) for s in STATUSES}
    print(f"{len(entries)} papers waiting ({by_status['preprint']} preprints, {by_status['peer_reviewed']} peer-reviewed; "
          f"{sum(e['explain'] for e in entries)} may get a full explainer; {len(claimed)} claimed)")
    for entry in best_first(entries)[:10]:
        page = "full" if entry["explain"] else "quick"
        print(f"{entry['significance']:g}\t{entry['id']}\t{entry['published']}\t{page}\t{entry.get('hook', '')}")
    return 0


ACTIONS = {"add": _add, "take": _take, "done": _done, "fail": _fail, "back": _back, "prune": _prune, "list": _list}
