"""The publish command, tested at the command line: a work folder in, a content repo tree out."""
import copy
import json
from pathlib import Path

import pytest

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


def test_paper_with_a_passing_explainer_is_published_as_an_explained_card(tmp_path):
    work = write_work(tmp_path / "work", [judged(1)], explained={"arxiv-2611.00001": {}})
    content = tmp_path / "content"

    assert publish(work, content) == 0

    [item] = read_json(content / "feed/v1/chunks/000001.json")["items"]
    assert item["has_explainer"] is True
    assert item["explainer"] == "papers/arxiv-2611.00001/"
    assert item["hero"] == {"path": "papers/arxiv-2611.00001/hero.webp", "width": 120, "height": 63}
    paper = content / "papers/arxiv-2611.00001"
    assert sorted(p.name for p in paper.iterdir()) == ["hero.webp", "index.html", "meta.json"]
    assert (paper / "index.html").read_bytes() == (FIXTURES / "explainer.html").read_bytes()
    assert (paper / "hero.webp").read_bytes() == (FIXTURES / "hero.webp").read_bytes()
    meta = read_json(paper / "meta.json")
    assert meta["has_explainer"] is True
    assert meta["explained_at"] == NOW
    assert meta["kit"] == 1
    assert meta["check"]["render"]["pass"] is True
    assert meta["check"]["review"]["pass"] is True


@pytest.mark.parametrize(
    "opts",
    [{"check": False}, {"review": False}, {"files": False}],
    ids=["render check failed", "review failed", "explainer files missing"],
)
def test_explainer_that_is_missing_or_failed_gives_a_short_card(tmp_path, opts):
    work = write_work(tmp_path / "work", [judged(1)], explained={"arxiv-2611.00001": opts})
    content = tmp_path / "content"

    assert publish(work, content) == 0

    [item] = read_json(content / "feed/v1/chunks/000001.json")["items"]
    assert item["has_explainer"] is False
    assert "hero" not in item and "explainer" not in item
    assert sorted(p.name for p in (content / "papers/arxiv-2611.00001").iterdir()) == ["meta.json"]


def tree(root: Path) -> dict[str, bytes]:
    """Every file under root (outside .git) and its bytes."""
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


def chunk_ids(content: Path, number: int) -> list[str]:
    return [i["id"] for i in read_json(content / f"feed/v1/chunks/{number:06d}.json")["items"]]


def test_chunk_rolls_over_after_40_items(tmp_path):
    work = write_work(tmp_path / "work", [judged(n) for n in range(1, 42)])
    content = tmp_path / "content"

    assert publish(work, content) == 0

    assert chunk_ids(content, 1) == [f"arxiv-2611.{n:05d}" for n in range(1, 41)]
    assert chunk_ids(content, 2) == ["arxiv-2611.00041"]
    head = read_json(content / "feed/v1/head.json")
    assert (head["chunk_count"], head["total_items"]) == (2, 41)


def test_items_append_to_the_open_chunk_across_runs_in_the_order_added(tmp_path):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(3), judged(1)]), content)
    publish(write_work(tmp_path / "w2", [judged(2)]), content, now="2026-11-12T09:00:00Z")

    assert chunk_ids(content, 1) == ["arxiv-2611.00003", "arxiv-2611.00001", "arxiv-2611.00002"]
    assert read_json(content / "feed/v1/head.json")["updated_at"] == "2026-11-12T09:00:00Z"


def test_second_run_with_the_same_work_folder_changes_nothing(tmp_path):
    records = [judged(n) for n in range(1, 45)]
    work = write_work(tmp_path / "work", records, explained={"arxiv-2611.00002": {}, "arxiv-2611.00043": {}})
    content = tmp_path / "content"
    publish(work, content)
    before = tree(content)

    assert publish(work, content, now="2026-11-13T00:00:00Z") == 0

    assert tree(content) == before


def test_a_paper_already_in_the_feed_is_never_added_twice(tmp_path):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(1)]), content)
    same_doi = judged(7, doi="10.1000/ABC")
    publish(write_work(tmp_path / "w2", [same_doi]), content)
    later = [
        judged(1),
        judged(1),
        judged(8, title=judged(1)["title"].upper() + "!"),
        judged(9, id="doi-10.1000-abc", arxiv_id=None, doi="https://doi.org/10.1000/abc"),
        judged(10),
    ]

    publish(write_work(tmp_path / "w3", later), content)

    assert chunk_ids(content, 1) == ["arxiv-2611.00001", "arxiv-2611.00007", "arxiv-2611.00010"]
    assert read_json(content / "feed/v1/head.json")["total_items"] == 3


def test_closed_chunks_are_never_modified(tmp_path):
    content = tmp_path / "content"
    publish(write_work(tmp_path / "w1", [judged(n) for n in range(1, 81)]), content)
    closed = {k: v for k, v in tree(content).items() if k in ("feed/v1/chunks/000001.json", "feed/v1/chunks/000002.json")}
    assert len(closed) == 2

    later = [judged(n) for n in range(1, 101)]
    publish(write_work(tmp_path / "w2", later, explained={"arxiv-2611.00005": {}, "arxiv-2611.00045": {}}), content)

    after = tree(content)
    assert {k: after[k] for k in closed} == closed
    assert chunk_ids(content, 3) == [f"arxiv-2611.{n:05d}" for n in range(81, 101)]
