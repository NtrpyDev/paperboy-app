"""publish: write judged papers from a work folder into a content repo checkout.

Each Judged record in WORK/judged.jsonl becomes one feed item. It is an explained card when
WORK/papers/<id>/explainer/ holds index.html and hero.webp and both check.json and
review.json say {"pass": true}; otherwise it is a short card. An explained paper's meta.json gets
"made_by" from WORK/papers/<id>/made_by.json when that file exists. A paper already in the feed is
not added again, but a short card gains its explainer once one passes. See content_repo for
the layout and the rules that keep closed chunks unchanged.
"""
import argparse
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from .. import content_repo, schemas
from ..content_repo import KIT, ContentRepo, PublishError

# One commit per top-level folder, so each folder's last commit subject describes it.
COMMIT_SUBJECTS = {
    "papers": "Published papers: explainer page, card image, and record for each",
    "feed": "Feed head and chunks the app reads",
    "state": "Pipeline bookkeeping: papers in the feed, source cursors, and the explain queue",
}

FEED_FIELDS = ("id", "title", "hook", "summary", "field", "tags", "status", "venue", "published", "url", "significance")
META_FIELDS = (
    "id", "doi", "arxiv_id", "title", "authors", "venue", "published", "status", "license",
    "url", "field", "tags", "hook", "summary", "significance",
)


def register(subparsers) -> None:
    parser = subparsers.add_parser("publish", help="write judged papers into the content repo's feed", description=__doc__)
    parser.add_argument("--work", type=Path, required=True, help="work folder holding judged.jsonl and papers/")
    parser.add_argument("--content", type=Path, required=True, help="content repo checkout to write into")
    parser.add_argument("--commit", action="store_true", help="commit the changes, one commit per changed top-level folder")
    parser.add_argument("--push", action="store_true", help="push main to origin after writing (never forced)")
    parser.add_argument("--now", help="RFC 3339 time to use as the current time (for tests); default is the current UTC time")
    parser.set_defaults(run=run)


def run(args) -> int:
    try:
        now = _now(args.now)
        records = _read_judged(args.work / "judged.jsonl")
        repo = ContentRepo(args.content)
        for record in records:
            _publish_one(repo, record, args.work / "papers" / record["id"], now)
        written = repo.save(now)
    except PublishError as error:
        print(f"publish: {error}", file=sys.stderr)
        return 1
    print(f"publish: wrote {len(written)} files")
    try:
        if args.commit:
            _commit(args.content)
        if args.push:
            _git(args.content, "push", "origin", "main")
    except subprocess.CalledProcessError as error:
        print(f"publish: git {' '.join(error.cmd[3:])} failed: {error.stderr.strip()}", file=sys.stderr)
        return 1
    return 0


def _now(value: str | None) -> str:
    if value is None:
        moment = datetime.now(timezone.utc)
    else:
        try:
            moment = datetime.fromisoformat(value)
        except ValueError:
            raise PublishError(f"--now {value!r} is not an RFC 3339 time")
        if moment.tzinfo is None:
            raise PublishError(f"--now {value!r} needs a time zone")
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_judged(path: Path) -> list[dict]:
    if not path.exists():
        raise PublishError(f"{path} does not exist")
    records, problems = [], []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            problems.append(f"{path.name} line {number}: {error}")
            continue
        problems += [f"{path.name} line {number}: {e}" for e in schemas.errors("judged", record)]
        records.append(record)
    if problems:
        raise PublishError("invalid input, nothing was written:\n" + "\n".join(problems))
    return records


def _publish_one(repo: ContentRepo, record: dict, folder: Path, now: str) -> None:
    explained = _explainer(record["id"], folder)
    seen = repo.find(record)
    if seen is None:
        item = {k: record[k] for k in FEED_FIELDS}
        item.update(authors_short=authors_short(record["authors"]), has_explainer=False, added_at=now)
        meta = {k: record.get(k) for k in META_FIELDS}
        meta.update(has_explainer=False, added_at=now, explained_at=None, kit=None, fulltext_source=None)
        files = {}
        if explained:
            item.update(has_explainer=True, explainer=explained["explainer"], hero=explained["hero"])
            files = _explain_meta(meta, record, explained, now)
        repo.add(item=item, meta=meta, files=files, record=record)
        return

    if seen["id"] != record["id"] or not explained:
        return
    meta = repo.meta(seen["id"])
    if meta is None or meta.get("has_explainer"):
        return
    files = _explain_meta(meta, record, explained, now)
    repo.upgrade(
        seen=seen,
        explainer={"explainer": explained["explainer"], "hero": explained["hero"], "explained_at": now},
        meta=meta,
        files=files,
    )


def _explain_meta(meta: dict, record: dict, explained: dict, now: str) -> dict[str, bytes]:
    """Mark meta as explained and return the paper folder files to write."""
    meta.update(
        has_explainer=True,
        explained_at=now,
        kit=KIT,
        fulltext_source=record["fulltext"].get("url"),
        check={"render": explained["check"], "review": explained["review"]},
    )
    if explained["made_by"] is not None:
        meta["made_by"] = explained["made_by"]
    return {"index.html": explained["index_html"], "hero.webp": explained["hero_bytes"]}


def _explainer(paper_id: str, folder: Path) -> dict | None:
    """The finished explainer for this paper, or None when it is missing or has not passed both checks."""
    page, hero = folder / "explainer" / "index.html", folder / "explainer" / "hero.webp"
    if not (page.is_file() and hero.is_file() and (folder / "check.json").is_file() and (folder / "review.json").is_file()):
        return None
    verdicts = {}
    for name in ("check", "review"):
        try:
            verdicts[name] = json.loads((folder / f"{name}.json").read_text())
        except json.JSONDecodeError as error:
            raise PublishError(f"{folder / (name + '.json')} is not valid JSON: {error}")
        if not isinstance(verdicts[name], dict):
            raise PublishError(f"{folder / (name + '.json')} is not a JSON object")
    if verdicts["check"].get("pass") is not True or verdicts["review"].get("pass") is not True:
        return None
    made_by = None
    if (folder / "made_by.json").is_file():
        try:
            made_by = json.loads((folder / "made_by.json").read_text())
        except json.JSONDecodeError as error:
            raise PublishError(f"{folder / 'made_by.json'} is not valid JSON: {error}")
    hero_bytes = hero.read_bytes()
    try:
        with Image.open(io.BytesIO(hero_bytes)) as image:
            width, height = image.size
    except OSError as error:
        raise PublishError(f"{hero} is not a readable image: {error}")
    base = content_repo.paper_dir(paper_id).as_posix()
    return {
        "explainer": f"{base}/",
        "hero": {"path": f"{base}/hero.webp", "width": width, "height": height},
        "index_html": page.read_bytes(),
        "hero_bytes": hero_bytes,
        "check": verdicts["check"],
        "review": verdicts["review"],
        "made_by": made_by,
    }


def authors_short(authors: list[str]) -> str:
    """Lovelace; Lovelace and Babbage; Lovelace et al. Family name is the part before a comma, else the last word."""
    def family(name: str) -> str:
        name = name.strip()
        return name.split(",")[0].strip() if "," in name else (name.split() or [""])[-1]

    if not authors:
        return ""
    if len(authors) == 1:
        return family(authors[0])
    if len(authors) == 2:
        return f"{family(authors[0])} and {family(authors[1])}"
    return f"{family(authors[0])} et al."


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
    return result.stdout


def _commit(root: Path) -> None:
    for folder, subject in COMMIT_SUBJECTS.items():
        if not _git(root, "status", "--porcelain", "--", folder).strip():
            continue
        _git(root, "add", "-A", "--", folder)
        _git(root, "commit", "-q", "-m", subject, "--", folder)
