"""The queue command at the command line: papers worth an explainer wait in the content repo until a run takes them."""
import json

import pytest

from paperboy_pipeline import schemas
from paperboy_pipeline.cli import build_parser, main
from paperboy_pipeline.commands import explain_queue

from test_batch_select import judged, write_lines

NOW = "2026-11-13T05:00:00Z"


def queue(content, work, *argv, now=NOW):
    args = build_parser().parse_args(["queue", argv[0], "--content", str(content), *(["--work", str(work)] if argv[0] in ("add", "take") else []), *argv[1:]])
    return explain_queue.run(args, now=now)


def queued(content):
    return sorted(p.stem for p in (content / "state/queue").glob("*.json"))


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


ARXIV = {"available": True, "kind": "arxiv_html", "url": "https://arxiv.org/html/x"}
BIORXIV = {"available": True, "kind": "biorxiv", "url": "https://www.biorxiv.org/x.xml"}
NONE = {"available": False, "kind": None, "url": None}


def test_add_queues_papers_with_allowed_full_text_at_or_above_the_floor(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    write_lines(work / "judged.jsonl", [
        judged(1, 8.0), judged(2, 6.5), judged(3, 6.4), judged(4, 9.0, fulltext=NONE), judged(5, 9.0, fulltext=BIORXIV)])

    assert queue(content, work, "add") == 0

    assert queued(content) == ["arxiv-2611.00001", "arxiv-2611.00002"]
    entry = json.loads((content / "state/queue/arxiv-2611.00001.json").read_text())
    assert entry["queued_at"] == NOW
    record = {k: v for k, v in entry.items() if k != "queued_at"}
    assert record == judged(1, 8.0)
    assert schemas.errors("judged", record) == []


def test_add_takes_the_floor_and_the_kinds_from_the_command_line(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    write_lines(work / "judged.jsonl", [judged(1, 8.0), judged(2, 7.0), judged(5, 9.0, fulltext=BIORXIV)])
    assert queue(content, work, "add", "--explain-floor", "7.5", "--kinds", "arxiv_html,biorxiv") == 0
    assert queued(content) == ["arxiv-2611.00001", "arxiv-2611.00005"]


def test_add_never_overwrites_a_waiting_paper(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    write_lines(work / "judged.jsonl", [judged(1, 8.0)])
    queue(content, work, "add", now="2026-11-01T00:00:00Z")
    queue(content, work, "add", now=NOW)
    assert json.loads((content / "state/queue/arxiv-2611.00001.json").read_text())["queued_at"] == "2026-11-01T00:00:00Z"


def test_take_chooses_the_best_waiting_papers_and_prepares_their_work_folders(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    write_lines(work / "judged.jsonl", [
        judged(1, 7.0, published="2026-11-10"),
        judged(2, 9.0, published="2026-11-01"),
        judged(3, 7.0, published="2026-11-12"),
        judged(4, 7.0, published="2026-11-12"),
        judged(5, 6.8),
    ])
    queue(content, work, "add")
    write_lines(work / "judged.jsonl", [judged(4, 7.0, published="2026-11-12")])
    capsys.readouterr()

    assert queue(content, work, "take", "--n", "3") == 0

    order = ["arxiv-2611.00002", "arxiv-2611.00003", "arxiv-2611.00004"]
    assert capsys.readouterr().out.split() == order
    assert (work / "explain-queue.txt").read_text().split() == order
    for paper_id in order:
        candidate = json.loads((work / "papers" / paper_id / "candidate.json").read_text())
        assert candidate["id"] == paper_id and "queued_at" not in candidate
    # Each taken paper is in judged.jsonl once, so publish gives it its explainer.
    assert sorted(r["id"] for r in lines(work / "judged.jsonl")) == order
    for record in lines(work / "judged.jsonl"):
        assert schemas.errors("judged", record) == []
    # Taking a paper does not remove it from the queue; done or fail does.
    assert len(queued(content)) == 5


def test_take_skips_papers_that_failed_before(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    write_lines(work / "judged.jsonl", [judged(1, 9.0), judged(2, 8.0)])
    queue(content, work, "add")
    (content / "state/queue-failed.jsonl").write_text(json.dumps({"id": "arxiv-2611.00001", "reason": "x", "at": NOW}) + "\n")
    capsys.readouterr()
    assert queue(content, work, "take", "--n", "3") == 0
    assert capsys.readouterr().out.split() == ["arxiv-2611.00002"]


def test_done_removes_the_paper_from_the_queue(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    write_lines(work / "judged.jsonl", [judged(1, 9.0), judged(2, 8.0)])
    queue(content, work, "add")
    assert queue(content, work, "done", "--id", "arxiv-2611.00001") == 0
    assert queued(content) == ["arxiv-2611.00002"]
    assert queue(content, work, "done", "--id", "arxiv-2611.00001") == 1


def test_fail_removes_the_paper_and_records_why_so_it_is_never_queued_again(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    write_lines(work / "judged.jsonl", [judged(1, 9.0)])
    queue(content, work, "add")

    assert queue(content, work, "fail", "--id", "arxiv-2611.00001", "--reason", "no lawful full text") == 0

    assert queued(content) == []
    [failed] = lines(content / "state/queue-failed.jsonl")
    assert failed == {"id": "arxiv-2611.00001", "reason": "no lawful full text", "at": NOW}
    assert schemas.errors("queue-failed", failed) == []
    queue(content, work, "add")
    assert queued(content) == []


def test_prune_deletes_papers_waiting_longer_than_the_limit(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    write_lines(work / "judged.jsonl", [judged(1, 9.0)])
    queue(content, work, "add", now="2026-10-22T04:59:59Z")
    write_lines(work / "judged.jsonl", [judged(2, 9.0)])
    queue(content, work, "add", now="2026-10-23T05:00:01Z")

    assert queue(content, work, "prune", "--days", "21") == 0

    assert queued(content) == ["arxiv-2611.00002"]
    assert "pruned 1" in capsys.readouterr().out


def test_list_prints_the_count_and_the_top_ten(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    write_lines(work / "judged.jsonl", [judged(n, 6.5 + n / 10) for n in range(1, 13)])
    queue(content, work, "add")
    capsys.readouterr()

    assert queue(content, work, "list") == 0

    out = capsys.readouterr().out.splitlines()
    assert out[0] == "12 papers waiting"
    assert len(out) == 11
    assert out[1].split("\t")[:2] == ["7.7", "arxiv-2611.00012"]


def test_an_empty_queue_takes_nothing(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    work.mkdir()
    assert main(["queue", "take", "--content", str(content), "--work", str(work), "--n", "3"]) == 0
    assert (work / "explain-queue.txt").read_text() == ""
    assert main(["queue", "list", "--content", str(content)]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == "0 papers waiting"


@pytest.mark.parametrize("argv", [["take"], ["done"], ["fail", "--id", "x"]])
def test_required_options_are_enforced(tmp_path, argv):
    with pytest.raises(SystemExit):
        build_parser().parse_args(["queue", argv[0], "--content", str(tmp_path), *argv[1:]])
