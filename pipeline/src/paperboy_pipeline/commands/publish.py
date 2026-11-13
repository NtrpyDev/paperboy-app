"""publish: write judged papers from a work folder into a content repo checkout.

Each Judged record in WORK/judged.jsonl becomes one feed item, carrying the record's hook_turn
and readout when it has them. It is an explained card when WORK/papers/<id>/explainer/ holds
index.html, hero.webp (the day plate), and hero-night.webp (the night plate) and both check.json
and review.json say {"pass": true}; otherwise it is a short card. The plate's kind and to_scale
come from the hero in check.json, and meta.json's kit is the kit version check.json says the
page loads. When WORK/papers/<id>/card.json exists, the readout the expert settled there
replaces the scout's on the explained card (null removes it), through upgrades.json when the
item sits in a closed chunk. An explained paper's meta.json gets
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
from ..content_repo import ContentRepo, PublishError, set_readout

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
# Card text a Judged record may carry. Copied to the feed item and meta.json only when present.
OPTIONAL_CARD_FIELDS = ("hook_turn", "readout")
PLATE_FILES = {"day": "hero.webp", "night": "hero-night.webp"}


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
        optional = {k: record[k] for k in OPTIONAL_CARD_FIELDS if k in record}
        item = {k: record[k] for k in FEED_FIELDS}
        item.update(optional, authors_short=authors_short(record["authors"]), has_explainer=False, added_at=now)
        meta = {k: record.get(k) for k in META_FIELDS}
        meta.update(optional)
        meta.update(has_explainer=False, added_at=now, explained_at=None, kit=None, fulltext_source=None)
        files = {}
        if explained:
            item.update(has_explainer=True, explainer=explained["explainer"], hero=explained["hero"])
            if explained["card"] is not None:
                set_readout(item, explained["card"]["readout"])
            files = _explain_meta(meta, record, explained, now)
        repo.add(item=item, meta=meta, files=files, record=record)
        return

    if seen["id"] != record["id"] or not explained:
        return
    meta = repo.meta(seen["id"])
    if meta is None or meta.get("has_explainer"):
        return
    files = _explain_meta(meta, record, explained, now)
    upgrade = {"explainer": explained["explainer"], "hero": explained["hero"], "explained_at": now}
    if explained["card"] is not None:
        upgrade["readout"] = explained["card"]["readout"]
    repo.upgrade(seen=seen, explainer=upgrade, meta=meta, files=files)


def _explain_meta(meta: dict, record: dict, explained: dict, now: str) -> dict[str, bytes]:
    """Mark meta as explained and return the paper folder files to write."""
    meta.update(
        has_explainer=True,
        explained_at=now,
        kit=explained["kit"],
        fulltext_source=record["fulltext"].get("url"),
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
    files = [page, *plates.values(), folder / "check.json", folder / "review.json"]
    if not all(path.is_file() for path in files):
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
    card = None
    if (folder / "card.json").is_file():
        try:
            card = json.loads((folder / "card.json").read_text())
        except json.JSONDecodeError as error:
            raise PublishError(f"{folder / 'card.json'} is not valid JSON: {error}")
        problems = schemas.errors("card", card)
        if problems:
            raise PublishError(f"{folder / 'card.json'} does not match schema/card.schema.json: " + "; ".join(problems))
    page_info = verdicts["check"].get("page")
    kit = page_info.get("kit") if isinstance(page_info, dict) else None
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
