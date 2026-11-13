import json

from paperboy_pipeline.cli import main


def candidate(n, **over):
    record = {
        "id": f"arxiv-2611.{n:05d}", "doi": None, "arxiv_id": f"2611.{n:05d}", "title": f"Paper {n}",
        "authors": ["A. Author"], "abstract": "An abstract.", "venue": "arXiv", "published": "2026-11-10",
        "status": "preprint", "license": None, "url": f"https://arxiv.org/abs/2611.{n:05d}", "source": "arxiv",
        "categories": ["hep-th"], "fulltext": {"available": True, "kind": "arxiv_html", "url": "https://arxiv.org/html/x"},
    }
    record.update(over)
    return record


def judged(n, significance, **over):
    record = candidate(n, **over)
    record.update({
        "hook": f"A plain finding number {n}", "summary": "First sentence of the summary. Second sentence with the caveat here.",
        "field": "physics", "tags": ["test"], "significance": significance, "explain": False,
    })
    return record


def write_lines(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records))


def test_batch_splits_candidates(tmp_path, capsys):
    write_lines(tmp_path / "candidates.jsonl", [candidate(n) for n in range(7)])
    assert main(["batch", "--work", str(tmp_path), "--size", "3"]) == 0
    files = sorted(p.name for p in (tmp_path / "batches").glob("*.jsonl"))
    assert files == ["001.jsonl", "002.jsonl", "003.jsonl"]
    assert len((tmp_path / "batches" / "003.jsonl").read_text().splitlines()) == 1
    assert json.loads(capsys.readouterr().out) == {"candidates": 7, "batches": 3}


def test_select_applies_floor_and_queues_best_with_full_text(tmp_path, capsys):
    write_lines(tmp_path / "judged" / "001.jsonl", [
        judged(1, 4.0),
        judged(2, 9.0, fulltext={"available": False, "kind": None, "url": None}),
        judged(3, 8.0),
        judged(4, 7.0),
        judged(5, 6.0),
    ])
    assert main(["select", "--work", str(tmp_path), "--floor", "5", "--explain", "2"]) == 0
    kept = [json.loads(line) for line in (tmp_path / "judged.jsonl").read_text().splitlines()]
    assert [r["id"][-1] for r in kept] == ["2", "3", "4", "5"]
    assert [r["id"][-1] for r in kept if r["explain"]] == ["3", "4"]
    assert (tmp_path / "explain-queue.txt").read_text().split() == ["arxiv-2611.00003", "arxiv-2611.00004"]
    assert json.loads((tmp_path / "papers" / "arxiv-2611.00003" / "candidate.json").read_text())["explain"] is True


def test_select_rejects_invalid_lines_and_duplicates(tmp_path, capsys):
    bad = judged(1, 8.0)
    del bad["hook"]
    write_lines(tmp_path / "judged" / "001.jsonl", [bad, judged(2, 8.0), judged(2, 8.0)])
    assert main(["select", "--work", str(tmp_path)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["judged"] == 1 and len(report["rejected_lines"]) == 1
