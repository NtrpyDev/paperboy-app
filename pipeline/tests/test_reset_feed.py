"""reset-feed: one-time rewrite of an old content repo to the rule that every paper in the feed has a page."""
import json
import subprocess

from paperboy_pipeline import schemas
from paperboy_pipeline.cli import main

from test_publish import HERO, LATER, judged, old_feed, publish, read_json, tree, write_work

NOW = "2026-11-13T20:00:00Z"


def reset(content, *extra):
    return main(["reset-feed", "--content", str(content), "--keep-explained", "--rewind-cursors-to", "2026-11-10", "--now", NOW, *extra])


def old_repo(tmp_path):
    """41 short cards in two chunks, one explained in the open chunk in place, one through upgrades.json,
    a backlog, a claim, a ledger line, a failed paper, and cursors."""
    content = tmp_path / "content"
    old_feed(tmp_path, content, [judged(n) for n in range(1, 42)])
    readout = {"value": "2.5", "label": "Something measured"}
    publish(write_work(tmp_path / "w2", [judged(3), judged(41)], explained={"arxiv-2611.00003": {"card": {"readout": readout}}, "arxiv-2611.00041": {}}),
            content, now=LATER)
    state = content / "state"
    (state / "queue").mkdir()
    (state / "queue/arxiv-2611.00050.json").write_text(json.dumps({**judged(50), "queued_at": NOW}))
    (state / "claims").mkdir()
    (state / "claims/arxiv-2611.00050.json").write_text(json.dumps({"id": "arxiv-2611.00050", "run": "r", "page": "quick", "claimed_at": NOW}))
    (state / "queued").mkdir()
    (state / "queued/2026-11.jsonl").write_text(json.dumps({"id": "arxiv-2611.00050", "doi": None, "arxiv_id": "2611.00050", "title_key": "0" * 20, "queued_at": NOW}) + "\n")
    (state / "queue-failed.jsonl").write_text(json.dumps({"id": "arxiv-2611.00060", "reason": "x", "at": NOW}) + "\n")
    (state / "cursors.json").write_text(json.dumps({"v": 1, "cursors": {"arxiv": "2026-11-12", "crossref": "2026-11-09"}}))
    return content, readout


def test_without_yes_it_prints_the_plan_and_changes_nothing(tmp_path, capsys):
    content, _ = old_repo(tmp_path)
    before = tree(content)

    assert reset(content) == 0

    assert tree(content) == before
    out = capsys.readouterr().out
    assert "feed items                 41      2" in out
    assert "kept: arxiv-2611.00003, arxiv-2611.00041" in out
    assert "cursor arxiv: 2026-11-12 -> 2026-11-10" in out
    assert "nothing changed" in out


def test_with_yes_the_feed_holds_only_papers_with_a_page(tmp_path):
    content, readout = old_repo(tmp_path)
    assert (content / "feed/v1/upgrades.json").exists()

    assert reset(content, "--yes") == 0

    assert read_json(content / "feed/v1/head.json") == {"v": 1, "updated_at": NOW, "chunk_count": 1, "total_items": 2,
                                                         "chunk_size": 40, "kit": 1, "min_app": 1}
    assert sorted(p.name for p in (content / "feed/v1/chunks").iterdir()) == ["000001.json"]
    assert not (content / "feed/v1/upgrades.json").exists()
    first, second = read_json(content / "feed/v1/chunks/000001.json")["items"]
    # The upgrades.json entry is merged into the item, readout included.
    assert (first["id"], first["has_explainer"], first["depth"], first["readout"]) == ("arxiv-2611.00003", True, "full", readout)
    assert first["hero"] == {**HERO, "path": "papers/arxiv-2611.00003/hero.webp",
                             "night": {**HERO["night"], "path": "papers/arxiv-2611.00003/hero-night.webp"}}
    assert (second["id"], second["has_explainer"], second["explainer"]) == ("arxiv-2611.00041", True, "papers/arxiv-2611.00041/")
    assert sorted(p.name for p in (content / "papers").iterdir()) == ["arxiv-2611.00003", "arxiv-2611.00041"]
    assert read_json(content / "papers/arxiv-2611.00003/meta.json")["depth"] == "full"
    seen = [json.loads(line) for line in (content / "state/seen/2026-11.jsonl").read_text().splitlines()]
    assert [(s["id"], s["chunk"]) for s in seen] == [("arxiv-2611.00003", 1), ("arxiv-2611.00041", 1)]
    for folder in ("queue", "claims", "queued"):
        assert list((content / "state" / folder).glob("*")) == []
    assert "arxiv-2611.00060" in (content / "state/queue-failed.jsonl").read_text()
    # A cursor later than the day moves back to it; an earlier one stays.
    assert read_json(content / "state/cursors.json")["cursors"] == {"arxiv": "2026-11-10", "crossref": "2026-11-09"}
    for path in content.glob("feed/v1/chunks/*.json"):
        assert schemas.errors("chunk", read_json(path)) == []


def test_the_reset_repo_takes_new_papers_in_its_open_chunk(tmp_path):
    content, _ = old_repo(tmp_path)
    reset(content, "--yes")
    assert publish(write_work(tmp_path / "w3", [judged(70)]), content) == 0
    assert [i["id"] for i in read_json(content / "feed/v1/chunks/000001.json")["items"]] == ["arxiv-2611.00003", "arxiv-2611.00041", "arxiv-2611.00070"]


def test_it_never_commits(tmp_path):
    content, _ = old_repo(tmp_path)
    subprocess.run(["git", "-C", str(content), "init", "-q", "-b", "main"], check=True)
    assert reset(content, "--yes") == 0
    log = subprocess.run(["git", "-C", str(content), "log", "--oneline"], capture_output=True, text=True)
    assert log.returncode != 0  # no commits at all


def test_it_refuses_a_folder_that_is_not_a_content_repo(tmp_path, capsys):
    assert reset(tmp_path, "--yes") == 1
    assert "head.json" in capsys.readouterr().err
