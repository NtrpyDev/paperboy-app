"""The queue command at the command line: every kept paper waits in the backlog until a run claims it
and builds its page."""
import json
import subprocess
from pathlib import Path

import pytest

from paperboy_pipeline import ids, schemas
from paperboy_pipeline.cli import build_parser, main
from paperboy_pipeline.commands import explain_queue

from test_batch_select import judged, write_lines

NOW = "2026-11-13T05:00:00Z"
WORK_ACTIONS = ("add", "take", "fail", "back")


def queue(content, work, *argv, now=NOW):
    args = build_parser().parse_args(["queue", argv[0], "--content", str(content), *(["--work", str(work)] if argv[0] in WORK_ACTIONS else []), *argv[1:]])
    return explain_queue.run(args, now=now)


def queued(content):
    return sorted(p.stem for p in (content / "state/queue").glob("*.json"))


def claimed(content):
    return {p.stem: json.loads(p.read_text()) for p in sorted((content / "state/claims").glob("*.json"))}


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def entry(content, paper_id):
    return json.loads((content / "state/queue" / f"{paper_id}.json").read_text())


ARXIV = {"available": True, "kind": "arxiv_html", "url": "https://arxiv.org/html/x"}
BIORXIV = {"available": True, "kind": "biorxiv", "url": "https://www.biorxiv.org/x.xml"}
NONE = {"available": False, "kind": None, "url": None}


def peer(n, significance, **over):
    """A peer-reviewed paper from a followed journal, with no free full text."""
    return judged(n, significance, id=f"doi-10.1-{n}", arxiv_id=None, doi=f"10.1/{n}", venue="Nature", source="crossref",
                  status="peer_reviewed", fulltext=NONE, **over)


# add

def test_add_puts_every_kept_paper_in_the_backlog_and_marks_which_may_get_a_full_explainer(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    write_lines(work / "judged.jsonl", [
        judged(1, 8.0), judged(2, 6.5), judged(3, 6.4), judged(4, 9.0, fulltext=NONE), judged(5, 9.0, fulltext=BIORXIV)])

    assert queue(content, work, "add") == 0

    assert queued(content) == [f"arxiv-2611.0000{n}" for n in range(1, 6)]
    assert {n: entry(content, f"arxiv-2611.0000{n}")["explain"] for n in range(1, 6)} == {1: True, 2: True, 3: False, 4: False, 5: False}
    first = entry(content, "arxiv-2611.00001")
    assert first["queued_at"] == NOW
    assert {k: v for k, v in first.items() if k != "queued_at"} == {**judged(1, 8.0), "explain": True}
    assert first["abstract"] == "An abstract."
    for n in range(1, 6):
        assert schemas.errors("queue-entry", entry(content, f"arxiv-2611.0000{n}")) == []
    assert json.loads(capsys.readouterr().out) == {"added": 5, "may_get_full": 2, "already_known": 0, "failed_before": 0, "waiting": 5}


def test_add_records_each_paper_in_the_ledger_discover_reads(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    write_lines(work / "judged.jsonl", [judged(1, 8.0, doi="10.1/A"), judged(2, 5.0)])
    queue(content, work, "add")
    ledger = lines(content / "state/queued/2026-11.jsonl")
    assert ledger[0] == {"id": "arxiv-2611.00001", "doi": "10.1/A", "arxiv_id": "2611.00001",
                         "title_key": ids.title_key("Paper 1"), "queued_at": NOW}
    assert [e["id"] for e in ledger] == ["arxiv-2611.00001", "arxiv-2611.00002"]
    for line in ledger:
        assert schemas.errors("queued", line) == []


def test_add_takes_the_floor_and_the_kinds_from_the_command_line(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    write_lines(work / "judged.jsonl", [judged(1, 8.0), judged(2, 7.0), judged(5, 9.0, fulltext=BIORXIV)])
    assert queue(content, work, "add", "--explain-floor", "7.5", "--kinds", "arxiv_html,biorxiv") == 0
    assert [entry(content, i)["explain"] for i in queued(content)] == [True, False, True]


def test_add_never_overwrites_a_waiting_paper_and_never_takes_back_one_that_left(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    write_lines(work / "judged.jsonl", [judged(1, 8.0), judged(2, 8.0)])
    queue(content, work, "add", now="2026-11-01T00:00:00Z")
    queue(content, work, "prune", "--days", "7", now="2026-11-09T00:00:00Z")  # both aged out
    write_lines(work / "judged.jsonl", [judged(1, 8.0), judged(3, 8.0)])
    queue(content, work, "add", now="2026-11-01T00:00:00Z")
    assert queued(content) == ["arxiv-2611.00003"]
    capsys.readouterr()
    queue(content, work, "add", now=NOW)
    assert entry(content, "arxiv-2611.00003")["queued_at"] == "2026-11-01T00:00:00Z"
    assert json.loads(capsys.readouterr().out)["already_known"] == 2


def test_add_skips_papers_that_failed_before_and_papers_already_in_the_feed(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    (content / "state/seen").mkdir(parents=True)
    (content / "state/seen/2026-11.jsonl").write_text(json.dumps(
        {"id": "x", "doi": "10.1/feed", "arxiv_id": None, "title_key": "0" * 20, "chunk": 1, "added_at": NOW}) + "\n")
    (content / "state/queue-failed.jsonl").write_text(json.dumps({"id": "arxiv-2611.00001", "reason": "x", "at": NOW}) + "\n")
    write_lines(work / "judged.jsonl", [judged(1, 9.0), judged(2, 9.0, doi="10.1/FEED"), judged(3, 9.0)])
    assert queue(content, work, "add") == 0
    assert queued(content) == ["arxiv-2611.00003"]


def test_add_refuses_an_invalid_judged_record(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    bad = judged(2, 9.0)
    del bad["hook"]
    write_lines(work / "judged.jsonl", [judged(1, 9.0), bad])
    assert queue(content, work, "add") == 1
    assert not (content / "state").exists()
    assert "line 2" in capsys.readouterr().err


# take

def take(content, work, full, quick, *extra, now=NOW, capsys=None):
    code = queue(content, work, "take", "--full", str(full), "--quick", str(quick), "--run", "r1", *extra, now=now)
    return code, json.loads((work / "take.json").read_text())


def seed(content, work, records, now=NOW):
    write_lines(work / "judged.jsonl", records)
    assert queue(content, work, "add", now=now) == 0
    (work / "judged.jsonl").unlink()


def test_take_alternates_preprints_and_peer_reviewed_papers_best_first(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [judged(1, 9.0, fulltext=NONE), judged(2, 8.0, fulltext=NONE), judged(3, 7.0, fulltext=NONE),
                         judged(4, 6.0, fulltext=NONE), peer(5, 8.5), peer(6, 5.0)])

    code, taken = take(content, work, 0, 5)

    assert code == 0
    assert taken["quick"] == ["arxiv-2611.00001", "doi-10.1-5", "arxiv-2611.00002", "doi-10.1-6", "arxiv-2611.00003"]
    assert taken["full"] == []


def test_take_starts_with_the_kind_of_the_best_paper(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [judged(1, 6.0, fulltext=NONE), judged(2, 5.5, fulltext=NONE), peer(5, 8.5), peer(6, 8.0)])
    assert take(content, work, 0, 3)[1]["quick"] == ["doi-10.1-5", "arxiv-2611.00001", "doi-10.1-6"]


def test_take_gives_full_explainers_to_the_best_papers_with_full_text_and_quick_pages_to_the_rest(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [judged(1, 9.0), judged(2, 8.0), judged(3, 8.5, fulltext=NONE), peer(4, 7.0), peer(5, 6.0)])
    capsys.readouterr()

    code, taken = take(content, work, 1, 3)

    assert code == 0
    assert taken == {"run": "r1", "full": ["arxiv-2611.00001"], "quick": ["arxiv-2611.00003", "doi-10.1-4", "arxiv-2611.00002"]}
    summary = json.loads(capsys.readouterr().out)
    assert summary["full"] == taken["full"] and summary["quick"] == taken["quick"]
    assert summary["status"]["doi-10.1-4"] == "peer_reviewed" and summary["waiting"] == 5
    # Each paper gets one claim for one kind of page.
    claims = claimed(content)
    assert {k: v["page"] for k, v in claims.items()} == {"arxiv-2611.00001": "full", "arxiv-2611.00003": "quick",
                                                         "doi-10.1-4": "quick", "arxiv-2611.00002": "quick"}
    for claim in claims.values():
        assert claim["run"] == "r1" and claim["claimed_at"] == NOW
        assert schemas.errors("claim", claim) == []


def test_take_prepares_each_papers_work_folder(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [judged(1, 9.0), peer(2, 8.0)])
    write_lines(work / "judged.jsonl", [judged(1, 9.0)])

    take(content, work, 1, 1)

    for paper_id in ("arxiv-2611.00001", "doi-10.1-2"):
        candidate = json.loads((work / "papers" / paper_id / "candidate.json").read_text())
        assert candidate["id"] == paper_id and "queued_at" not in candidate
        assert schemas.errors("judged", candidate) == []
    # Each taken paper is in judged.jsonl once, so publish can add it.
    assert sorted(r["id"] for r in lines(work / "judged.jsonl")) == ["arxiv-2611.00001", "doi-10.1-2"]
    # Taking a paper leaves it in the backlog until publish or fail takes it out.
    assert queued(content) == ["arxiv-2611.00001", "doi-10.1-2"]


def test_a_second_take_hands_out_different_papers_until_a_claim_goes_stale(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [judged(n, 9.0 - n / 10, fulltext=NONE) for n in range(1, 6)])

    first = take(content, work, 0, 2)[1]["quick"]
    second = take(content, tmp_path / "w2", 0, 2)[1]["quick"]
    stale = take(content, tmp_path / "w3", 0, 2, now="2026-11-13T08:00:01Z")[1]["quick"]

    assert first == ["arxiv-2611.00001", "arxiv-2611.00002"]
    assert second == ["arxiv-2611.00003", "arxiv-2611.00004"]
    # Three hours on, the first two claims are stale; the second take's are too.
    assert stale == ["arxiv-2611.00001", "arxiv-2611.00002"]


def test_take_skips_failed_papers_and_papers_already_in_the_feed(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [judged(1, 9.0), judged(2, 8.0), judged(3, 7.0)])
    (content / "state/queue-failed.jsonl").write_text(json.dumps({"id": "arxiv-2611.00001", "reason": "x", "at": NOW}) + "\n")
    (content / "state/seen").mkdir(parents=True)
    (content / "state/seen/2026-11.jsonl").write_text(json.dumps(
        {"id": "arxiv-2611.00002", "doi": None, "arxiv_id": "2611.00002", "title_key": "0" * 20, "chunk": 1, "added_at": NOW}) + "\n")
    assert take(content, work, 3, 3)[1] == {"run": "r1", "full": ["arxiv-2611.00003"], "quick": []}


def test_a_paper_whose_full_explainer_failed_is_only_taken_for_a_quick_page(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [judged(1, 9.0), judged(2, 7.0)])
    take(content, work, 1, 0)
    assert queue(content, work, "back", "--id", "arxiv-2611.00001", "--reason", "No lawful full text.") == 0
    back = entry(content, "arxiv-2611.00001")
    assert (back["explain"], back["full_failed"]) == (False, "No lawful full text.")
    assert schemas.errors("queue-entry", back) == []
    assert claimed(content) == {}
    assert lines(work / "outcomes.jsonl") == [{"action": "back", "id": "arxiv-2611.00001", "reason": "No lawful full text.", "at": NOW}]

    assert take(content, tmp_path / "w2", 1, 1)[1] == {"run": "r1", "full": ["arxiv-2611.00002"], "quick": ["arxiv-2611.00001"]}


def test_take_prunes_first_when_given_days(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [judged(1, 9.0)], now="2026-11-05T04:59:59Z")
    seed(content, work, [judged(2, 8.0)], now="2026-11-06T05:00:01Z")
    code, taken = take(content, work, 0, 5, "--days", "7")
    assert taken["quick"] == ["arxiv-2611.00002"]
    assert queued(content) == ["arxiv-2611.00002"]


def test_an_empty_backlog_takes_nothing(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    work.mkdir()
    assert main(["queue", "take", "--content", str(content), "--work", str(work), "--full", "1", "--quick", "6"]) == 0
    taken = json.loads((work / "take.json").read_text())
    assert (taken["full"], taken["quick"]) == ([], [])
    assert main(["queue", "list", "--content", str(content)]) == 0
    assert capsys.readouterr().out.splitlines()[-1].startswith("0 papers waiting")


# done, fail, prune, list

def test_done_takes_the_paper_out_and_releases_its_claim(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [judged(1, 9.0), judged(2, 8.0)])
    take(content, work, 1, 0)
    assert queue(content, work, "done", "--id", "arxiv-2611.00001") == 0
    assert queued(content) == ["arxiv-2611.00002"] and claimed(content) == {}
    assert queue(content, work, "done", "--id", "arxiv-2611.00001") == 1


def test_fail_takes_the_paper_out_for_good_and_notes_it_for_publish(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [judged(1, 9.0)])
    take(content, work, 0, 1)

    assert queue(content, work, "fail", "--id", "arxiv-2611.00001", "--reason", "Two quick pages failed the numbers check.") == 0

    assert queued(content) == [] and claimed(content) == {}
    [failed] = lines(content / "state/queue-failed.jsonl")
    assert failed == {"id": "arxiv-2611.00001", "reason": "Two quick pages failed the numbers check.", "at": NOW}
    assert schemas.errors("queue-failed", failed) == []
    assert lines(work / "outcomes.jsonl")[0]["action"] == "fail"
    write_lines(work / "judged.jsonl", [judged(1, 9.0)])
    queue(content, work, "add")
    assert queued(content) == []


def test_back_needs_a_waiting_paper(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    assert queue(content, work, "back", "--id", "arxiv-2611.00001", "--reason", "x") == 1
    assert not (work / "outcomes.jsonl").exists()


def test_prune_takes_out_papers_waiting_longer_than_the_limit_but_not_claimed_ones(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [judged(1, 9.0), judged(2, 9.0)], now="2026-11-06T04:59:59Z")
    seed(content, work, [judged(3, 9.0)], now="2026-11-06T05:00:01Z")
    take(content, work, 0, 1, now="2026-11-13T04:00:00Z")  # claims paper 1

    assert queue(content, work, "prune", "--days", "7") == 0

    assert queued(content) == ["arxiv-2611.00001", "arxiv-2611.00003"]
    assert "pruned 1" in capsys.readouterr().out


def test_list_prints_the_count_and_the_top_ten(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [judged(n, 6.5 + n / 10) for n in range(1, 12)] + [peer(12, 5.0)])
    capsys.readouterr()

    assert queue(content, work, "list") == 0

    out = capsys.readouterr().out.splitlines()
    assert out[0] == "12 papers waiting (11 preprints, 1 peer-reviewed; 11 may get a full explainer; 0 claimed)"
    assert len(out) == 11
    assert out[1].split("\t")[:4] == ["7.6", "arxiv-2611.00011", "2026-11-10", "full"]


@pytest.mark.parametrize("argv", [["take"], ["take", "--full", "1"], ["done"], ["fail", "--id", "x"], ["back", "--id", "x"]])
def test_required_options_are_enforced(tmp_path, argv):
    with pytest.raises(SystemExit):
        build_parser().parse_args(["queue", argv[0], "--content", str(tmp_path), "--work", str(tmp_path), *argv[1:]])


# Pushing

def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


def remote_and_clones(tmp_path, *names):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    seed_repo = tmp_path / "seed"
    seed_repo.mkdir()
    git(seed_repo, "init", "-q", "-b", "main")
    (seed_repo / "README.md").write_text("content repo\n")
    git(seed_repo, "add", "README.md")
    git(seed_repo, "-c", "user.name=T", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "Start")
    git(seed_repo, "push", "-q", str(remote), "main")
    clones = []
    for name in names:
        subprocess.run(["git", "clone", "-q", str(remote), str(tmp_path / name)], check=True)
        git(tmp_path / name, "config", "user.name", "Test")
        git(tmp_path / name, "config", "user.email", "test@example.invalid")
        clones.append(tmp_path / name)
    return remote, clones


def test_add_and_take_push_their_change(tmp_path):
    remote, (content,) = remote_and_clones(tmp_path, "content")
    work = tmp_path / "work"
    write_lines(work / "judged.jsonl", [judged(1, 9.0), judged(2, 8.0)])

    assert queue(content, work, "add", "--push") == 0
    assert git(remote, "ls-tree", "-r", "--name-only", "main", "state").split() == [
        "state/queue/arxiv-2611.00001.json", "state/queue/arxiv-2611.00002.json", "state/queued/2026-11.jsonl"]
    assert take(content, work, 1, 0, "--push")[0] == 0
    assert "state/claims/arxiv-2611.00001.json" in git(remote, "ls-tree", "-r", "--name-only", "main", "state")
    assert git(remote, "log", "-1", "--format=%s", "main").strip() == "Pipeline bookkeeping: papers in the feed, source cursors, the backlog, and claims"
    assert git(content, "status", "--porcelain").strip() == ""


def test_overlapping_takes_claim_different_papers(tmp_path):
    remote, (a, b) = remote_and_clones(tmp_path, "a", "b")
    work = tmp_path / "work"
    write_lines(work / "judged.jsonl", [judged(n, 9.0 - n / 10, fulltext=NONE) for n in range(1, 5)])
    assert queue(a, work, "add", "--push") == 0
    git(b, "pull", "-q", "--ff-only")
    # Run A takes and pushes first; run B was cut from the same main and takes after it.
    assert take(a, tmp_path / "wa", 0, 2, "--push")[1]["quick"] == ["arxiv-2611.00001", "arxiv-2611.00002"]
    assert take(b, tmp_path / "wb", 0, 2, "--push")[1]["quick"] == ["arxiv-2611.00003", "arxiv-2611.00004"]
    assert sorted(Path(p).stem for p in git(remote, "ls-tree", "-r", "--name-only", "main", "state/claims").split()) == [
        f"arxiv-2611.0000{n}" for n in range(1, 5)]


def test_a_push_starting_from_origin_refuses_a_checkout_with_unpushed_changes(tmp_path, capsys):
    remote, (content,) = remote_and_clones(tmp_path, "content")
    work = tmp_path / "work"
    write_lines(work / "judged.jsonl", [judged(1, 9.0)])
    queue(content, work, "add")  # not pushed
    assert queue(content, work, "take", "--full", "1", "--quick", "0", "--push") == 1
    assert "not on origin/main" in capsys.readouterr().err
    assert not (work / "take.json").exists()
    assert queued(content) == ["arxiv-2611.00001"]
