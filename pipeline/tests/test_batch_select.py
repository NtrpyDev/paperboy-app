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


def journal(n, venue="Nature", source="crossref"):
    return candidate(n, id=f"doi-10.1-{n}", arxiv_id=None, doi=f"10.1/{n}", venue=venue, source=source,
                     status="peer_reviewed", fulltext={"available": False, "kind": None, "url": None})


def batch(work, *flags):
    return main(["batch", "--work", str(work), *flags])


def test_batch_all_splits_every_candidate_without_triage(tmp_path, capsys):
    write_lines(tmp_path / "candidates.jsonl", [candidate(n) for n in range(7)])
    assert batch(tmp_path, "--all", "--size", "3") == 0
    files = sorted(p.name for p in (tmp_path / "batches").glob("*.jsonl"))
    assert files == ["001.jsonl", "002.jsonl", "003.jsonl"]
    assert len((tmp_path / "batches" / "003.jsonl").read_text().splitlines()) == 1
    assert json.loads(capsys.readouterr().out)["batches"] == 3


def test_triage_writes_title_files_of_at_most_150_lines_split_evenly(tmp_path, capsys):
    write_lines(tmp_path / "candidates.jsonl", [candidate(n, categories=["hep-th", "gr-qc"]) for n in range(320)])
    assert batch(tmp_path, "--triage") == 0
    files = sorted((tmp_path / "triage").glob("*.tsv"))
    assert [p.name for p in files] == ["001.tsv", "002.tsv", "003.tsv"]
    # Even sizes, so the last file is never a short tail where 15 percent rounds down to nothing.
    assert [len(p.read_text().splitlines()) for p in files] == [107, 107, 106]
    assert files[0].read_text().splitlines()[0] == "arxiv-2611.00000\tarxiv\tarXiv\thep-th gr-qc\tPaper 0"
    assert json.loads(capsys.readouterr().out) == {"candidates": 320, "passed_through": 0, "triaged": 320, "triage_files": 3}


def test_triage_lines_never_carry_a_tab_or_line_break_from_the_record(tmp_path):
    write_lines(tmp_path / "candidates.jsonl", [candidate(1, title="Two\tparts\nof a title", venue="A\tB")])
    batch(tmp_path, "--triage")
    assert (tmp_path / "triage/001.tsv").read_text() == "arxiv-2611.00001\tarxiv\tA B\thep-th\tTwo parts of a title\n"


def test_papers_from_followed_journals_skip_triage(tmp_path, capsys):
    write_lines(tmp_path / "candidates.jsonl", [
        candidate(1),
        journal(2, venue="Nature", source="crossref"),
        journal(3, venue="eLife", source="europepmc"),
        journal(4, venue="Crop Health", source="crossref"),
        candidate(5, venue="Nature", source="arxiv"),
    ])
    assert batch(tmp_path, "--triage") == 0
    triaged = [line.split("\t")[0] for line in (tmp_path / "triage/001.tsv").read_text().splitlines()]
    assert triaged == ["arxiv-2611.00001", "doi-10.1-4", "arxiv-2611.00005"]
    assert json.loads(capsys.readouterr().out)["passed_through"] == 2


def test_batch_judges_only_picked_papers_and_followed_journal_papers(tmp_path, capsys):
    write_lines(tmp_path / "candidates.jsonl", [candidate(n) for n in range(40)] + [journal(100), journal(101, venue="Neuron")])
    batch(tmp_path, "--triage")
    capsys.readouterr()
    (tmp_path / "triage-picks").mkdir()
    (tmp_path / "triage-picks/001.txt").write_text("arxiv-2611.00003\n\narxiv-2611.00030\narxiv-2611.99999\n")

    assert batch(tmp_path) == 0

    batches = sorted((tmp_path / "batches").glob("*.jsonl"))
    judged_ids = [json.loads(line)["id"] for p in batches for line in p.read_text().splitlines()]
    assert judged_ids == ["arxiv-2611.00003", "arxiv-2611.00030", "doi-10.1-100", "doi-10.1-101"]
    report = json.loads(capsys.readouterr().out)
    assert (report["picked"], report["passed_through"], report["batches"]) == (2, 2, 1)
    assert report["triage_files_without_picks"] == []


def test_batches_hold_15_papers(tmp_path, capsys):
    write_lines(tmp_path / "candidates.jsonl", [journal(n) for n in range(31)])
    (tmp_path / "triage-picks").mkdir()
    assert batch(tmp_path) == 0
    assert [len(p.read_text().splitlines()) for p in sorted((tmp_path / "batches").glob("*.jsonl"))] == [15, 15, 1]


def test_a_triage_file_without_picks_is_reported(tmp_path, capsys):
    write_lines(tmp_path / "candidates.jsonl", [candidate(n) for n in range(200)])
    batch(tmp_path, "--triage")
    assert len(list((tmp_path / "triage").glob("*.tsv"))) == 2
    capsys.readouterr()
    (tmp_path / "triage-picks").mkdir()
    (tmp_path / "triage-picks/001.txt").write_text("arxiv-2611.00001\n")
    assert batch(tmp_path) == 0
    assert json.loads(capsys.readouterr().out)["triage_files_without_picks"] == ["002"]


def test_batch_without_triage_picks_refuses(tmp_path, capsys):
    write_lines(tmp_path / "candidates.jsonl", [candidate(1)])
    assert batch(tmp_path) == 1
    assert "work/triage-picks" in capsys.readouterr().err.replace(str(tmp_path), "work")
    assert not (tmp_path / "batches").exists()


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
