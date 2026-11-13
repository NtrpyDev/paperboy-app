"""The publish command, tested at the command line: a work folder in, a content repo tree out."""
import copy
import json
from pathlib import Path

from paperboy_pipeline.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "publish"
BASE = json.loads((FIXTURES / "judged-base.json").read_text())
NOW = "2026-11-12T08:00:00Z"


def judged(n: int, **overrides) -> dict:
    """A valid Judged record numbered n, so each one is a distinct paper."""
    record = copy.deepcopy(BASE)
    arxiv = f"2611.{n:05d}"
    record.update(
        id=f"arxiv-{arxiv}",
        arxiv_id=arxiv,
        title=f"Observation number {n} of a thing in a place",
        url=f"https://arxiv.org/abs/{arxiv}",
    )
    record.update(overrides)
    return record


def write_work(work: Path, records: list[dict], explained: dict[str, dict] | None = None) -> Path:
    """explained maps paper id to {"check": bool, "review": bool, "files": bool}; missing keys default to True."""
    work.mkdir(parents=True, exist_ok=True)
    (work / "judged.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    for paper_id, opts in (explained or {}).items():
        folder = work / "papers" / paper_id
        (folder / "explainer").mkdir(parents=True, exist_ok=True)
        if opts.get("files", True):
            (folder / "explainer" / "index.html").write_bytes((FIXTURES / "explainer.html").read_bytes())
            (folder / "explainer" / "hero.webp").write_bytes((FIXTURES / "hero.webp").read_bytes())
        (folder / "check.json").write_text(json.dumps({"pass": opts.get("check", True), "problems": []}))
        (folder / "review.json").write_text(json.dumps({"pass": opts.get("review", True), "problems": []}))
    return work


def publish(work: Path, content: Path, *extra: str, now: str = NOW) -> int:
    content.mkdir(parents=True, exist_ok=True)
    return main(["publish", "--work", str(work), "--content", str(content), "--now", now, *extra])


def read_json(path: Path):
    return json.loads(path.read_text())


def test_first_publish_into_empty_repo_writes_a_short_card(tmp_path):
    work = write_work(tmp_path / "work", [judged(1)])
    content = tmp_path / "content"

    assert publish(work, content) == 0

    chunk = read_json(content / "feed/v1/chunks/000001.json")
    assert chunk["v"] == 1
    assert chunk["number"] == 1
    assert chunk["items"] == [
        {
            "id": "arxiv-2611.00001",
            "title": "Observation number 1 of a thing in a place",
            "hook": "A thing turned up exactly where nobody looked",
            "summary": BASE["summary"],
            "field": "space",
            "tags": ["galaxies", "surveys"],
            "status": "preprint",
            "venue": "arXiv",
            "published": "2026-11-10",
            "authors_short": "Lovelace et al.",
            "url": "https://arxiv.org/abs/2611.00001",
            "has_explainer": False,
            "significance": 7.5,
            "added_at": NOW,
        }
    ]
    assert read_json(content / "feed/v1/head.json") == {
        "v": 1,
        "updated_at": NOW,
        "chunk_count": 1,
        "total_items": 1,
        "chunk_size": 40,
        "kit": 1,
        "min_app": 1,
    }
    paper = content / "papers/arxiv-2611.00001"
    assert sorted(p.name for p in paper.iterdir()) == ["meta.json"]
    meta = read_json(paper / "meta.json")
    assert meta["has_explainer"] is False
    assert meta["authors"] == ["Ada Lovelace", "Charles Babbage", "Mary Somerville"]
    assert meta["license"] == "cc-by"
    assert "abstract" not in meta
