"""publish: put papers that have a passing page into the content repo's feed.

A paper enters the feed only with its page. Each Judged record in WORK/judged.jsonl whose folder
WORK/papers/<id>/ holds a passing page becomes one feed item, written with its explainer, plates,
kind, depth, and readout in place; a record without one is skipped and keeps waiting in the
backlog. A page passes when explainer/ holds index.html, hero.webp (the day plate), and
hero-night.webp (the night plate), check.json says {"pass": true}, and:

- a full explainer (check.json page.depth "full", or no depth) has review.json {"pass": true};
- a quick explainer (page.depth "abstract") has the numbers check in check.json (page.numbers,
  with nothing outside the title and abstract). It has no checker and no review.json.

The item carries the record's hook_turn and readout when it has them; WORK/papers/<id>/card.json,
when it exists, settles the readout (null removes it). meta.json gets the kit version and depth
from check.json and "made_by" from made_by.json when that file exists. Every paper that is in
the feed after the write leaves the backlog, and the run's claims are released; the run's
queue fail and queue back (WORK/outcomes.jsonl) are applied again, so a push that must start over
from a newer origin/main rebuilds the whole change (paperboy_pipeline.gitsync).

A paper already in the feed is not added again. An item published before pages were required
can still gain its explainer (through upgrades.json when its chunk is closed). See content_repo
for the layout and the rules that keep closed chunks unchanged.
"""
import argparse
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from .. import backlog, content_repo, gitsync, schemas
from ..content_repo import ContentRepo, PublishError, set_readout

# One commit per top-level folder, so each folder's last commit subject describes it.
COMMIT_SUBJECTS = gitsync.SUBJECTS

FEED_FIELDS = ("id", "title", "hook", "summary", "field", "tags", "status", "venue", "published", "url", "significance")
META_FIELDS = (
    "id", "doi", "arxiv_id", "title", "authors", "venue", "published", "status", "license",
    "url", "field", "tags", "hook", "summary", "significance",
)
# Card text a Judged record may carry. Copied to the feed item and meta.json only when present.
OPTIONAL_CARD_FIELDS = ("hook_turn", "readout")
PLATE_FILES = {"day": "hero.webp", "night": "hero-night.webp"}


def register(subparsers) -> None:
    parser = subparsers.add_parser("publish", help="write judged papers into the content repo's feed", description=__doc__)
    parser.add_argument("--work", type=Path, required=True, help="work folder holding judged.jsonl and papers/")
    parser.add_argument("--content", type=Path, required=True, help="content repo checkout to write into")
    parser.add_argument("--commit", action="store_true", help="commit the changes, one commit per changed top-level folder")
    parser.add_argument("--push", action="store_true", help="commit and push main to origin (never forced); when the remote moved, start again from it")
    parser.add_argument("--now", help="RFC 3339 time to use as the current time (for tests); default is the current UTC time")
    parser.set_defaults(run=run)


def run(args) -> int:
    try:
        now = _now(args.now)
        records = _read_judged(args.work / "judged.jsonl")
    except PublishError as error:
        print(f"publish: {error}", file=sys.stderr)
        return 1
    result = {}

    def apply():
        repo = ContentRepo(args.content)
        added = [r["id"] for r in records if _publish_one(repo, r, args.work / "papers" / r["id"], now)]
        result.update(written=repo.save(now), added=added)
        for record in records:
            if repo.find(record) is not None:
                backlog.leave(args.content, record["id"])
        backlog.replay(args.content, args.work)

    try:
        if args.push:
            gitsync.sync(args.content, apply, start_from_origin=False, label="publish")
        else:
            apply()
            if args.commit:
                gitsync.commit(args.content)
    except PublishError as error:
        print(f"publish: {error}", file=sys.stderr)
        return 1
    except gitsync.GitError as error:
        print(f"publish: {error}", file=sys.stderr)
        return 1
    print(f"publish: wrote {len(result['written'])} files")
    print(f"publish: {len(result['added'])} papers entered the feed" + (": " + ", ".join(result["added"]) if result["added"] else ""))
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


def _publish_one(repo: ContentRepo, record: dict, folder: Path, now: str) -> bool:
    """Add the paper to the feed when it has a passing page. True when it was added."""
    explained = _explainer(record["id"], folder)
    seen = repo.find(record)
    if seen is None:
        if not explained:
            return False  # no page, no card: it keeps waiting in the backlog
        optional = {k: record[k] for k in OPTIONAL_CARD_FIELDS if k in record}
        item = {k: record[k] for k in FEED_FIELDS}
        item.update(optional, authors_short=authors_short(record["authors"]), added_at=now,
                    has_explainer=True, explainer=explained["explainer"], depth=explained["depth"], hero=explained["hero"])
        if explained["card"] is not None:
            set_readout(item, explained["card"]["readout"])
        meta = {k: record.get(k) for k in META_FIELDS}
        meta.update(optional)
        meta.update(added_at=now)
        files = _explain_meta(meta, record, explained, now)
        repo.add(item=item, meta=meta, files=files, record=record)
        return True

    # Already in the feed. Only an item published before pages were required can gain one;
    # a page, once published, is never replaced.
    if seen["id"] != record["id"] or not explained:
        return False
    meta = repo.meta(seen["id"])
    if meta is None or meta.get("has_explainer"):
        return False
    files = _explain_meta(meta, record, explained, now)
    upgrade = {"explainer": explained["explainer"], "hero": explained["hero"], "explained_at": now}
    if explained["card"] is not None:
        upgrade["readout"] = explained["card"]["readout"]
    repo.upgrade(seen=seen, explainer=upgrade, meta=meta, files=files)
    return False


def _explain_meta(meta: dict, record: dict, explained: dict, now: str) -> dict[str, bytes]:
    """Mark meta as explained and return the paper folder files to write."""
    meta.update(
        has_explainer=True,
        explained_at=now,
        kit=explained["kit"],
        depth=explained["depth"],
        fulltext_source=record["fulltext"].get("url") if explained["depth"] == "full" else None,
        check={"render": explained["check"], "review": explained["review"]},
    )
    if explained["made_by"] is not None:
        meta["made_by"] = explained["made_by"]
    if explained["card"] is not None:
        set_readout(meta, explained["card"]["readout"])
    return {"index.html": explained["index_html"], **explained["plate_bytes"]}


def _explainer(paper_id: str, folder: Path) -> dict | None:
    """The finished explainer for this paper, or None when it is missing or has not passed both checks."""
    page = folder / "explainer" / "index.html"
    plates = {name: folder / "explainer" / filename for name, filename in PLATE_FILES.items()}
    if not all(path.is_file() for path in [page, *plates.values(), folder / "check.json"]):
        return None
    check = _read_object(folder / "check.json")
    if check.get("pass") is not True:
        return None
    page_info = check.get("page") if isinstance(check.get("page"), dict) else {}
    depth = page_info.get("depth") or "full"
    review = None
    if depth == "abstract":
        numbers = page_info.get("numbers")
        if not (isinstance(numbers, dict) and numbers.get("not_in_abstract") == 0):
            print(f"publish: {paper_id}: its quick explainer has no numbers check in check.json; run check with its candidate.json", file=sys.stderr)
            return None
    elif depth == "full":
        if not (folder / "review.json").is_file():
            return None
        review = _read_object(folder / "review.json")
        if review.get("pass") is not True:
            return None
    else:
        return None
    verdicts = {"check": check, "review": review}
    made_by = None
    if (folder / "made_by.json").is_file():
        try:
            made_by = json.loads((folder / "made_by.json").read_text())
        except json.JSONDecodeError as error:
            raise PublishError(f"{folder / 'made_by.json'} is not valid JSON: {error}")
    card = None
    if (folder / "card.json").is_file():
        try:
            card = json.loads((folder / "card.json").read_text())
        except json.JSONDecodeError as error:
            raise PublishError(f"{folder / 'card.json'} is not valid JSON: {error}")
        problems = schemas.errors("card", card)
        if problems:
            raise PublishError(f"{folder / 'card.json'} does not match schema/card.schema.json: " + "; ".join(problems))
    kit = page_info.get("kit")
    if not isinstance(kit, int) or isinstance(kit, bool) or kit < 1:
        raise PublishError(f"{folder / 'check.json'} does not say which kit version the page loads (page.kit); run check again")
    base = content_repo.paper_dir(paper_id).as_posix()
    plate_bytes, sizes = {}, {}
    for name, path in plates.items():
        data = path.read_bytes()
        try:
            with Image.open(io.BytesIO(data)) as image:
                width, height = image.size
        except OSError as error:
            raise PublishError(f"{path} is not a readable image: {error}")
        plate_bytes[path.name] = data
        sizes[name] = {"path": f"{base}/{path.name}", "width": width, "height": height}
    hero = {**sizes["day"], "night": sizes["night"]}
    rendered = verdicts["check"].get("hero")
    if isinstance(rendered, dict):
        hero.update({k: rendered[k] for k in ("kind", "to_scale") if k in rendered})
    return {
        "explainer": f"{base}/",
        "hero": hero,
        "index_html": page.read_bytes(),
        "plate_bytes": plate_bytes,
        "check": verdicts["check"],
        "review": verdicts["review"],
        "made_by": made_by,
        "card": card,
        "kit": kit,
        "depth": depth,
    }


def _read_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise PublishError(f"{path} is not valid JSON: {error}")
    if not isinstance(value, dict):
        raise PublishError(f"{path} is not a JSON object")
    return value


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
