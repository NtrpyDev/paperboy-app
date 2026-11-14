"""record-cost: one line per API run in state/cost/<YYYY-MM>.jsonl, written from Claude Code's
JSON result and the run's work folder, safe after a run that failed or was cut off."""
import json

import pytest

from paperboy_pipeline import schemas
from paperboy_pipeline.cli import main

from test_publish import judged as published_judged, write_work
from test_queue import git, remote_and_clones

NOW = "2026-11-13T09:30:00Z"

# A result message as `claude -p --output-format json` prints it. Built by hand from the documented
# shape (SDKResultMessage and ModelUsage in https://code.claude.com/docs/en/agent-sdk/typescript.md,
# read 2026-11-13), not captured from a real run: no API account exists yet. The numbers are made up.
RESULT = {
    "type": "result",
    "subtype": "success",
    "uuid": "00000000-0000-4000-8000-000000000000",
    "session_id": "11111111-1111-4111-8111-111111111111",
    "duration_ms": 3_600_000,
    "duration_api_ms": 2_900_000,
    "is_error": False,
    "num_turns": 57,
    "result": "Run report: ...",
    "stop_reason": "end_turn",
    "total_cost_usd": 7.4125,
    "usage": {"input_tokens": 1200, "output_tokens": 40000, "cache_creation_input_tokens": 90000,
              "cache_read_input_tokens": 2_100_000, "cache_creation": {"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 90000},
              "server_tool_use": None, "service_tier": "standard", "speed": "standard", "inference_geo": None,
              "iterations": None, "output_tokens_details": None, "fallback_credit": None},
    "modelUsage": {
        "claude-opus-5-5": {"inputTokens": 5400, "outputTokens": 180000, "cacheReadInputTokens": 6_500_000,
                            "cacheCreationInputTokens": 410000, "webSearchRequests": 0, "costUSD": 6.9075,
                            "contextWindow": 1_000_000, "maxOutputTokens": 64000, "costBasis": "list"},
        "claude-sonnet-5-5": {"inputTokens": 800, "outputTokens": 9000, "cacheReadInputTokens": 1_400_000,
                              "cacheCreationInputTokens": 60000, "webSearchRequests": 0, "costUSD": 0.505,
                              "contextWindow": 1_000_000, "maxOutputTokens": 64000},
    },
    "permission_denials": [{"tool_name": "Bash", "tool_use_id": "toolu_1", "tool_input": {"command": "cp a b"}}],
}


def work_folder(tmp_path):
    """A run that took one full and two quick papers: the full one and one quick one passed."""
    records = [published_judged(1), published_judged(2), published_judged(3)]
    records[0]["field"], records[1]["field"], records[2]["field"] = "physics", "math", "space"
    work = write_work(tmp_path / "work", records, {
        records[0]["id"]: {},
        records[1]["id"]: {"depth": "abstract"},
        records[2]["id"]: {"depth": "abstract", "check": False},
    })
    for rec in records:
        (work / "papers" / rec["id"] / "candidate.json").write_text(json.dumps(rec))
    (work / "take.json").write_text(json.dumps({"run": "2026-11-13T08:00:00Z-abc123", "full": [records[0]["id"]],
                                                "quick": [records[1]["id"], records[2]["id"]]}))
    return work


def record_cost(content, work, result, *extra, now=NOW):
    return main(["record-cost", "--content", str(content), "--work", str(work), "--result", str(result),
                 "--run", "gh-101-1", "--cap-usd", "15", "--now", now, *extra])


def lines(content, month="2026-11"):
    path = content / "state/cost" / f"{month}.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_a_finished_run_records_its_cost_tokens_and_pages(tmp_path, capsys):
    content, work = tmp_path / "content", work_folder(tmp_path)
    (content / "state").mkdir(parents=True)
    result = tmp_path / "result.json"
    result.write_text(json.dumps(RESULT))

    assert record_cost(content, work, result, "--outcome", "success") == 0

    [line] = lines(content)
    assert schemas.errors("cost-record", line) == []
    assert line == {
        "v": 1, "run": "gh-101-1", "recorded_at": NOW, "complete": True, "budget_cap_usd": 15.0,
        "total_cost_usd": 7.4125, "spend_usd": 7.4125, "subtype": "success", "num_turns": 57, "duration_ms": 3_600_000,
        "permission_denials": 1,
        "models": {
            "claude-opus-5-5": {"input_tokens": 5400, "output_tokens": 180000, "cache_read_input_tokens": 6_500_000,
                                "cache_creation_input_tokens": 410000, "web_search_requests": 0, "cost_usd": 6.9075},
            "claude-sonnet-5-5": {"input_tokens": 800, "output_tokens": 9000, "cache_read_input_tokens": 1_400_000,
                                  "cache_creation_input_tokens": 60000, "web_search_requests": 0, "cost_usd": 0.505},
        },
        "take_run": "2026-11-13T08:00:00Z-abc123",
        "taken": {"full": {"physics": 1}, "quick": {"math": 1, "space": 1}},
        "pages": {"full": {"physics": 1}, "quick": {"math": 1}},
    }
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1]) == line


def test_the_field_from_take_json_wins_when_it_has_one(tmp_path):
    content, work = tmp_path / "content", work_folder(tmp_path)
    take = json.loads((work / "take.json").read_text())
    take["field"] = {take["full"][0]: "earth"}
    (work / "take.json").write_text(json.dumps(take))
    result = tmp_path / "result.json"
    result.write_text(json.dumps(RESULT))
    assert record_cost(content, work, result) == 0
    assert lines(content)[0]["pages"]["full"] == {"earth": 1}


@pytest.mark.parametrize("setup, reason", [
    (lambda path: None, "no result file"),
    (lambda path: path.write_text(""), "empty"),
    (lambda path: path.write_text(json.dumps(RESULT)[:200]), "cut off"),
], ids=["no file", "empty file", "truncated file"])
def test_a_cut_off_run_is_recorded_as_incomplete_and_counts_its_cap(tmp_path, setup, reason):
    content, work = tmp_path / "content", work_folder(tmp_path)
    result = tmp_path / "result.json"
    setup(result)

    assert record_cost(content, work, result, "--outcome", "cancelled") == 0

    [line] = lines(content)
    assert schemas.errors("cost-record", line) == []
    assert line["complete"] is False and reason in line["incomplete_reason"]
    assert line["total_cost_usd"] is None and line["spend_usd"] == 15.0 and line["models"] == {}
    # What the work folder shows is still recorded.
    assert line["pages"] == {"full": {"physics": 1}, "quick": {"math": 1}}


def test_a_run_stopped_at_its_cap_counts_what_it_reported_when_that_is_more(tmp_path):
    content, work = tmp_path / "content", work_folder(tmp_path)
    over = {**RESULT, "subtype": "error_max_budget_usd", "is_error": True, "total_cost_usd": 15.8,
            "errors": ["Reached maximum budget"]}
    del over["result"]
    result = tmp_path / "result.json"
    result.write_text(json.dumps(over))

    assert record_cost(content, work, result, "--outcome", "failure") == 0

    [line] = lines(content)
    assert line["complete"] is False and "error_max_budget_usd" in line["incomplete_reason"]
    assert line["total_cost_usd"] == 15.8 and line["spend_usd"] == 15.8


def test_a_crash_result_with_zeroed_cost_counts_the_cap(tmp_path):
    content, work = tmp_path / "content", work_folder(tmp_path)
    crash = {**RESULT, "subtype": "error_during_execution", "is_error": True, "total_cost_usd": 0, "modelUsage": {}, "errors": []}
    result = tmp_path / "result.json"
    result.write_text(json.dumps(crash))
    assert record_cost(content, work, result) == 0
    assert lines(content)[0]["spend_usd"] == 15.0


def test_a_success_result_from_a_failed_step_is_incomplete(tmp_path):
    content, work = tmp_path / "content", work_folder(tmp_path)
    result = tmp_path / "result.json"
    result.write_text(json.dumps(RESULT))
    assert record_cost(content, work, result, "--outcome", "failure") == 0
    line = lines(content)[0]
    assert line["complete"] is False and "outcome was failure" in line["incomplete_reason"]
    assert line["spend_usd"] == 15.0


def test_a_run_that_never_reached_take_records_no_pages(tmp_path):
    content, work = tmp_path / "content", tmp_path / "nowork"
    result = tmp_path / "result.json"
    result.write_text(json.dumps(RESULT))
    assert record_cost(content, work, result) == 0
    line = lines(content)[0]
    assert line["take_run"] is None and line["taken"] == line["pages"] == {"full": {}, "quick": {}}


def test_a_run_is_recorded_once(tmp_path, capsys):
    content, work = tmp_path / "content", work_folder(tmp_path)
    result = tmp_path / "result.json"
    result.write_text(json.dumps(RESULT))
    assert record_cost(content, work, result) == 0
    assert record_cost(content, work, result, now="2026-11-13T10:00:00Z") == 0
    assert len(lines(content)) == 1
    assert "already recorded" in capsys.readouterr().err


def test_the_month_of_the_record_names_its_file(tmp_path):
    content, work = tmp_path / "content", work_folder(tmp_path)
    result = tmp_path / "result.json"
    result.write_text(json.dumps(RESULT))
    assert record_cost(content, work, result, now="2026-12-01T00:05:00Z") == 0
    assert lines(content, "2026-12")[0]["recorded_at"] == "2026-12-01T00:05:00Z"


def test_the_budget_gate_reads_what_record_cost_writes(tmp_path, capsys):
    content, work = tmp_path / "content", work_folder(tmp_path)
    result = tmp_path / "result.json"
    result.write_text(json.dumps(RESULT))
    assert record_cost(content, work, result) == 0
    capsys.readouterr()
    assert main(["budget-gate", "--content", str(content), "--budget-usd", "100", "--now", NOW, "--no-pace"]) == 0
    assert json.loads(capsys.readouterr().out)["spent_usd"] == 7.4125


def test_record_cost_pushes_and_rebuilds_on_a_moved_remote(tmp_path):
    remote, (a, b) = remote_and_clones(tmp_path, "a", "b")
    work = work_folder(tmp_path)
    result = tmp_path / "result.json"
    result.write_text(json.dumps(RESULT))
    # Another run pushes its own cost record after this checkout was cut.
    other = tmp_path / "other.json"
    other.write_text(json.dumps({**RESULT, "total_cost_usd": 1.0}))
    assert main(["record-cost", "--content", str(b), "--work", str(tmp_path / "none"), "--result", str(other),
                 "--run", "gh-100-1", "--cap-usd", "15", "--now", NOW, "--push"]) == 0

    assert record_cost(a, work, result, "--push") == 0

    shown = git(remote, "show", "main:state/cost/2026-11.jsonl").splitlines()
    assert [json.loads(x)["run"] for x in shown] == ["gh-100-1", "gh-101-1"]
    assert git(remote, "log", "-1", "--format=%s", "main").strip() == "Pipeline bookkeeping: papers in the feed, source cursors, the backlog, and claims"
    assert git(a, "status", "--porcelain").strip() == ""


def test_an_invalid_month_file_stops_record_cost_without_writing(tmp_path, capsys):
    content, work = tmp_path / "content", work_folder(tmp_path)
    (content / "state/cost").mkdir(parents=True)
    (content / "state/cost/2026-11.jsonl").write_text("not json\n")
    result = tmp_path / "result.json"
    result.write_text(json.dumps(RESULT))
    assert record_cost(content, work, result) == 1
    assert (content / "state/cost/2026-11.jsonl").read_text() == "not json\n"
    assert "not valid JSON" in capsys.readouterr().err


def test_a_push_rejected_because_the_remote_moved_appends_the_record_again_on_top(tmp_path, monkeypatch, capsys):
    from paperboy_pipeline import gitsync

    remote, (a, b) = remote_and_clones(tmp_path, "a", "b")
    work = work_folder(tmp_path)
    result = tmp_path / "result.json"
    result.write_text(json.dumps(RESULT))
    other = tmp_path / "other.json"
    other.write_text(json.dumps({**RESULT, "total_cost_usd": 1.0}))
    real_push, calls = gitsync._push, []

    def push_after_another_run(root):
        if not calls:
            # Between this run's fetch and its push, another run records its cost and pushes.
            calls.append("moved")
            monkeypatch.setattr(gitsync, "_push", real_push)
            assert main(["record-cost", "--content", str(b), "--work", str(tmp_path / "none"), "--result", str(other),
                         "--run", "gh-100-1", "--cap-usd", "15", "--now", NOW, "--push"]) == 0
            monkeypatch.setattr(gitsync, "_push", push_after_another_run)
        return real_push(root)

    monkeypatch.setattr(gitsync, "_push", push_after_another_run)
    assert record_cost(a, work, result, "--push") == 0

    assert "origin/main moved" in capsys.readouterr().err
    shown = git(remote, "show", "main:state/cost/2026-11.jsonl").splitlines()
    assert [json.loads(x)["run"] for x in shown] == ["gh-100-1", "gh-101-1"]
