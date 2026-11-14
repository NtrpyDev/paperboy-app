"""queue take with a field list: quick explainers per active field, full explainers only from
active fields, and nothing at all when the list cannot be read."""
import json

import httpx
import pytest

from paperboy_pipeline import active_fields
from paperboy_pipeline.cli import main

from test_batch_select import judged, write_lines
from test_queue import NONE, NOW, claimed, peer, queue, queued, remote_and_clones, git, seed


def fields_file(tmp_path, fields, **over):
    body = {"v": 1, "fields": fields, "updated_at": "2026-11-13T04:00:00Z", **over}
    path = tmp_path / "active-fields.json"
    path.write_text(json.dumps(body))
    return path


def per_field(content, work, fields_path, n, full=0, *extra, now=NOW):
    code = queue(content, work, "take", "--full", str(full), "--per-field", str(n), "--fields-file", str(fields_path),
                 "--run", "r1", *extra, now=now)
    taken = json.loads((work / "take.json").read_text()) if (work / "take.json").exists() else None
    return code, taken


def infield(record, field):
    """judged() always writes field physics; set the paper's field after it."""
    return {**record, "field": field}


def p(n, significance, field, **over):
    """A preprint without free full text (quick explainers only) in a field."""
    return infield(judged(n, significance, fulltext=NONE, **over), field)


def test_takes_up_to_n_per_active_field_from_uneven_backlogs(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [p(1, 9.0, "math"), p(2, 8.0, "math"), p(3, 7.0, "math"), p(4, 6.0, "math"),
                         p(5, 8.5, "space"), p(6, 5.5, "physics"), p(7, 9.5, "physics")])

    code, taken = per_field(content, work, fields_file(tmp_path, ["math", "space"]), 2)

    assert code == 0
    # Two for math, only one waits for space; physics is not active. Round robin by rank across fields.
    assert taken["quick"] == ["arxiv-2611.00001", "arxiv-2611.00005", "arxiv-2611.00002"]
    assert taken["full"] == []
    assert taken["field"] == {"arxiv-2611.00001": "math", "arxiv-2611.00005": "space", "arxiv-2611.00002": "math"}
    assert taken["active_fields"] == ["math", "space"] and taken["per_field"] == 2
    assert set(claimed(content)) == {"arxiv-2611.00001", "arxiv-2611.00002", "arxiv-2611.00005"}


def test_alternates_preprints_and_peer_reviewed_within_a_field(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [p(1, 9.0, "biology"), p(2, 8.0, "biology"), p(3, 7.0, "biology"),
                         infield(peer(4, 6.0), "biology"), infield(peer(5, 5.0), "biology"), infield(peer(6, 9.9), "math")])

    code, taken = per_field(content, work, fields_file(tmp_path, ["biology"]), 4)

    assert code == 0
    assert taken["quick"] == ["arxiv-2611.00001", "doi-10.1-4", "arxiv-2611.00002", "doi-10.1-5"]


def test_full_explainers_come_only_from_active_fields(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    # Paper 1 has full text and the highest score but is in an inactive field.
    seed(content, work, [judged(1, 9.5), infield(judged(2, 8.0), "math"), p(3, 7.0, "math")])

    code, taken = per_field(content, work, fields_file(tmp_path, ["math"]), 2, 1)

    assert code == 0
    assert taken["full"] == ["arxiv-2611.00002"]
    assert taken["quick"] == ["arxiv-2611.00003"]
    assert taken["field"] == {"arxiv-2611.00002": "math", "arxiv-2611.00003": "math"}
    assert {k: v["page"] for k, v in claimed(content).items()} == {"arxiv-2611.00002": "full", "arxiv-2611.00003": "quick"}


def test_papers_in_inactive_fields_stay_in_the_backlog_and_age_out_as_today(tmp_path):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [p(1, 9.0, "physics")], now="2026-11-05T04:59:59Z")
    seed(content, work, [p(2, 8.0, "physics"), p(3, 7.0, "math")], now="2026-11-12T00:00:00Z")

    code, taken = per_field(content, work, fields_file(tmp_path, ["math"]), 3, 0, "--days", "7")

    assert code == 0 and taken["quick"] == ["arxiv-2611.00003"]
    # Paper 1 waited more than 7 days and aged out; paper 2 waits on, unclaimed.
    assert queued(content) == ["arxiv-2611.00002", "arxiv-2611.00003"]
    assert "arxiv-2611.00002" not in claimed(content)


def test_an_empty_list_is_valid_and_takes_nothing(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [judged(1, 9.0), p(2, 8.0, "math")])
    capsys.readouterr()

    code, taken = per_field(content, work, fields_file(tmp_path, []), 5, 1)

    assert code == 0
    assert (taken["full"], taken["quick"], taken["active_fields"]) == ([], [], [])
    assert claimed(content) == {}
    summary = json.loads(capsys.readouterr().out)
    assert summary["field"] == {} and summary["waiting"] == 2


@pytest.mark.parametrize("body", [
    "not json",
    "[]",
    json.dumps({"v": 2, "fields": ["math"], "updated_at": "2026-11-13T04:00:00Z"}),
    json.dumps({"v": 1, "fields": "math", "updated_at": "2026-11-13T04:00:00Z"}),
    json.dumps({"v": 1, "fields": ["math"]}),
    json.dumps({"v": 1, "fields": ["math", "astrology"], "updated_at": "2026-11-13T04:00:00Z"}),
    json.dumps({"v": 1, "fields": ["math", "math"], "updated_at": "2026-11-13T04:00:00Z"}),
], ids=["not json", "not an object", "wrong version", "fields not a list", "no updated_at", "unknown field", "repeated field"])
def test_an_invalid_list_takes_nothing_and_changes_nothing(tmp_path, capsys, body):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [p(1, 9.0, "math")], now="2026-11-01T00:00:00Z")
    before = sorted(str(x.relative_to(content)) for x in content.rglob("*"))
    path = tmp_path / "active-fields.json"
    path.write_text(body)
    capsys.readouterr()

    code, taken = per_field(content, work, path, 2, 1, "--days", "7")

    assert code == 1
    assert taken is None and not (work / "papers").exists()
    # Not even the age-out ran: the paper queued 12 days ago still waits.
    assert sorted(str(x.relative_to(content)) for x in content.rglob("*")) == before
    err = capsys.readouterr().err
    assert "nothing was taken" in err


def test_an_unreadable_file_takes_nothing(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [p(1, 9.0, "math")])
    code, taken = per_field(content, work, tmp_path / "missing.json", 2)
    assert code == 1 and taken is None and claimed(content) == {}
    assert "could not read" in capsys.readouterr().err


def serve(monkeypatch, handler):
    monkeypatch.setattr(active_fields, "_client", lambda: httpx.Client(transport=httpx.MockTransport(handler)))


def test_the_list_can_come_from_the_worker_url(tmp_path, monkeypatch):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [p(1, 9.0, "math"), p(2, 8.0, "space")])
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, json={"v": 1, "fields": ["space"], "updated_at": "2026-11-13T04:00:00Z"})

    serve(monkeypatch, handler)
    code = queue(content, work, "take", "--full", "0", "--per-field", "3", "--fields-url", "https://worker.example/v1/active-fields", "--run", "r1")
    assert code == 0
    assert json.loads((work / "take.json").read_text())["quick"] == ["arxiv-2611.00002"]
    assert seen == ["https://worker.example/v1/active-fields"]


@pytest.mark.parametrize("handler", [
    lambda request: httpx.Response(503, text="busy"),
    lambda request: httpx.Response(200, text="<html>challenge</html>"),
    lambda request: (_ for _ in ()).throw(httpx.ConnectError("refused", request=request)),
], ids=["server error", "not json", "unreachable"])
def test_a_url_that_cannot_be_read_takes_nothing(tmp_path, monkeypatch, capsys, handler):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [p(1, 9.0, "math")])
    serve(monkeypatch, handler)
    code = queue(content, work, "take", "--full", "1", "--per-field", "3", "--fields-url", "https://worker.example/v1/active-fields")
    assert code == 1
    assert not (work / "take.json").exists() and claimed(content) == {}
    assert "nothing was taken" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [
    ["--full", "1", "--per-field", "2"],                                   # a count per field without a list
    ["--full", "1", "--quick", "6", "--fields-file", "x.json"],            # a list with the run's quick count
], ids=["per-field without a list", "list with --quick"])
def test_a_field_list_and_per_field_go_together_and_quick_is_rejected_with_a_list(tmp_path, capsys, argv):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [p(1, 9.0, "math")])
    assert queue(content, work, "take", *argv) == 2
    assert claimed(content) == {} and not (work / "take.json").exists()


def test_quick_and_per_field_together_are_refused_by_the_parser(tmp_path):
    with pytest.raises(SystemExit):
        main(["queue", "take", "--content", str(tmp_path), "--work", str(tmp_path), "--full", "1", "--quick", "2", "--per-field", "2"])


def test_without_a_field_list_take_json_and_the_output_are_as_before(tmp_path, capsys):
    work, content = tmp_path / "work", tmp_path / "content"
    seed(content, work, [infield(judged(1, 9.0), "math"), p(2, 8.0, "space")])
    capsys.readouterr()
    assert queue(content, work, "take", "--full", "1", "--quick", "1", "--run", "r1") == 0
    assert (work / "take.json").read_text() == json.dumps(
        {"run": "r1", "full": ["arxiv-2611.00001"], "quick": ["arxiv-2611.00002"]}, indent=2) + "\n"
    assert set(json.loads(capsys.readouterr().out)) == {"run", "full", "quick", "status", "pruned", "waiting"}


def test_overlapping_per_field_takes_claim_different_papers(tmp_path):
    remote, (a, b) = remote_and_clones(tmp_path, "a", "b")
    work = tmp_path / "work"
    write_lines(work / "judged.jsonl", [p(n, 9.0 - n / 10, "math") for n in range(1, 5)])
    assert queue(a, work, "add", "--push") == 0
    git(b, "pull", "-q", "--ff-only")
    listing = fields_file(tmp_path, ["math"])
    assert per_field(a, tmp_path / "wa", listing, 2, 0, "--push")[1]["quick"] == ["arxiv-2611.00001", "arxiv-2611.00002"]
    assert per_field(b, tmp_path / "wb", listing, 2, 0, "--push")[1]["quick"] == ["arxiv-2611.00003", "arxiv-2611.00004"]
