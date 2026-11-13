"""The backlog: papers judged worth the feed that wait in the content repo for a page.

Paths are relative to the content repo root:

    state/queue/<id>.json          a waiting paper: its Judged record, "queued_at", and
                                   "full_failed" once a full explainer failed (schema/queue-entry)
    state/claims/<id>.json         a run building this paper's page now (schema/claim)
    state/queued/<YYYY-MM>.jsonl   every paper that ever entered the backlog, by the month it did
                                   (schema/queued); discover never judges these again
    state/queue-failed.jsonl       papers that left the backlog without a page (schema/queue-failed)

A Judged record's "explain" says whether the paper may get a full explainer: full text of an
allowed kind and significance at least the explain floor (paperboy_pipeline.explaining). A paper
whose full explainer failed has "explain": false and keeps the reason in "full_failed"; it can
only get a quick explainer. Every paper gets one kind of page, never both.

The work folder carries what a run did to the backlog, so a push that must start again from a
newer origin/main can rebuild it (paperboy_pipeline.gitsync):

    WORK/take.json                 what queue take handed this run: {"run", "full", "quick"}
    WORK/outcomes.jsonl            queue fail and queue back, one {"action", "id", "reason", "at"} per line
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from . import ids, schemas

QUEUE = Path("state/queue")
CLAIMS = Path("state/claims")
QUEUED = Path("state/queued")
FAILED = Path("state/queue-failed.jsonl")
CLAIM_HOURS = 3
NOT_JUDGED = ("queued_at", "full_failed")


def dump(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def read_lines(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def waiting(content: Path) -> dict[str, dict]:
    """Waiting papers by id. A file that is not valid JSON is skipped with a warning."""
    out = {}
    for path in sorted((content / QUEUE).glob("*.json")):
        try:
            entry = json.loads(path.read_text())
        except json.JSONDecodeError as error:
            print(f"backlog: {path} is not valid JSON, skipped: {error}", file=sys.stderr)
            continue
        out[path.stem] = entry
    return out


def record(entry: dict) -> dict:
    """The Judged record inside a backlog entry."""
    return {k: v for k, v in entry.items() if k not in NOT_JUDGED}


def failed_ids(content: Path) -> set[str]:
    return {line["id"] for line in read_lines(content / FAILED)}


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def claims(content: Path) -> dict[str, dict]:
    out = {}
    for path in sorted((content / CLAIMS).glob("*.json")):
        try:
            out[path.stem] = json.loads(path.read_text())
        except json.JSONDecodeError:
            out[path.stem] = {}
    return out


def fresh_claims(content: Path, now: str, hours: float = CLAIM_HOURS) -> dict[str, dict]:
    """Claims younger than `hours`. An older claim is stale: its run is presumed gone."""
    cutoff = parse_time(now) - timedelta(hours=hours)
    out = {}
    for paper_id, claim in claims(content).items():
        try:
            if parse_time(claim["claimed_at"]) >= cutoff:
                out[paper_id] = claim
        except (KeyError, TypeError, ValueError):
            continue
    return out


def write_entry(content: Path, entry: dict) -> None:
    path = content / QUEUE / f"{entry['id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump(entry))


def remove(content: Path, rel: Path) -> bool:
    path = content / rel
    if path.exists():
        path.unlink()
        return True
    return False


def release(content: Path, paper_id: str) -> None:
    remove(content, CLAIMS / f"{paper_id}.json")


def leave(content: Path, paper_id: str) -> bool:
    """Take a paper out of the backlog and release its claim. True when it was waiting."""
    release(content, paper_id)
    return remove(content, QUEUE / f"{paper_id}.json")


def ledger_entry(rec: dict, queued_at: str) -> dict:
    return {"id": rec["id"], "doi": rec.get("doi"), "arxiv_id": rec.get("arxiv_id"),
            "title_key": ids.title_key(rec["title"]), "queued_at": queued_at}


def append_ledger(content: Path, entries: list[dict]) -> None:
    by_month: dict[Path, list[dict]] = {}
    for entry in entries:
        by_month.setdefault(QUEUED / f"{entry['queued_at'][:7]}.jsonl", []).append(entry)
    for rel, lines in by_month.items():
        path = content / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as out:
            for line in lines:
                out.write(json.dumps(line, sort_keys=True, ensure_ascii=False) + "\n")


def fail(content: Path, paper_id: str, reason: str, at: str) -> None:
    """The paper leaves the backlog without a page and never comes back. Recording it twice is a no-op."""
    leave(content, paper_id)
    if paper_id in failed_ids(content):
        return
    path = content / FAILED
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as out:
        out.write(json.dumps({"id": paper_id, "reason": reason, "at": at}, sort_keys=True, ensure_ascii=False) + "\n")


def back(content: Path, paper_id: str, reason: str) -> bool:
    """A full explainer failed or had no full text: the paper waits again, for a quick explainer
    only. False when it is not waiting."""
    path = content / QUEUE / f"{paper_id}.json"
    release(content, paper_id)
    if not path.exists():
        return False
    entry = json.loads(path.read_text())
    entry.update(explain=False, full_failed=entry.get("full_failed") or reason)
    write_entry(content, entry)
    return True


def replay(content: Path, work: Path) -> None:
    """Apply the run's queue fail and queue back again (after a reset to a newer origin/main),
    and release every claim the run took."""
    for outcome in read_lines(work / "outcomes.jsonl"):
        if outcome["action"] == "fail":
            fail(content, outcome["id"], outcome["reason"], outcome["at"])
        elif outcome["action"] == "back":
            back(content, outcome["id"], outcome["reason"])
    take = work / "take.json"
    if take.exists():
        taken = json.loads(take.read_text())
        for paper_id in taken.get("full", []) + taken.get("quick", []):
            claim = claims(content).get(paper_id)
            if claim is not None and claim.get("run") == taken.get("run"):
                release(content, paper_id)


def errors(entry: dict) -> list[str]:
    return schemas.errors("queue-entry", entry)
