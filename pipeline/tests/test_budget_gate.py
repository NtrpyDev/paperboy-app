"""budget-gate: the API run goes only while this month's recorded spend is under the paced budget."""
import json

import pytest

from paperboy_pipeline import schemas
from paperboy_pipeline.cli import main

# November 2026 has 30 days: it starts 2026-11-01T00:00Z and ends 2026-12-01T00:00Z.
START, MIDDLE, END = "2026-11-01T00:00:00Z", "2026-11-16T00:00:00Z", "2026-11-30T23:59:59Z"


def record(run, spend, *, complete=True, cost=..., cap=10.0):
    rec = {
        "v": 1, "run": run, "recorded_at": "2026-11-02T00:00:00Z", "complete": complete, "budget_cap_usd": cap,
        "total_cost_usd": spend if cost is ... else cost, "spend_usd": spend, "subtype": "success" if complete else None,
        "num_turns": 10, "duration_ms": 1000, "permission_denials": 0, "models": {}, "take_run": None,
        "taken": {"full": {}, "quick": {}}, "pages": {"full": {}, "quick": {}},
    }
    if not complete:
        rec["incomplete_reason"] = "the result file is empty"
    assert schemas.errors("cost-record", rec) == []
    return rec


def content_with(tmp_path, records, month="2026-11", raw=None):
    content = tmp_path / "content"
    (content / "state/cost").mkdir(parents=True)
    path = content / "state/cost" / f"{month}.jsonl"
    path.write_text(raw if raw is not None else "".join(json.dumps(r) + "\n" for r in records))
    return content


def gate(content, capsys, now, *extra, budget="300"):
    code = main(["budget-gate", "--content", str(content), "--budget-usd", budget, "--now", now, *extra])
    return code, json.loads(capsys.readouterr().out)


def test_at_the_start_of_the_month_only_the_head_start_may_be_spent(tmp_path, capsys):
    content = content_with(tmp_path, [record("a", 29.99)])
    code, out = gate(content, capsys, START)
    assert code == 0
    assert out == {"decision": "go", "month": "2026-11", "spent_usd": 29.99, "budget_usd": 300.0, "runs": 1, "incomplete_runs": 0,
                   "pace": {"month_elapsed": 0.0, "head_start": 10.0, "limit_usd": 30.0}}
    content = content_with(tmp_path / "b", [record("a", 20.0), record("b", 10.0)])
    code, out = gate(content, capsys, START)
    assert code == 10 and out["decision"] == "stop" and out["spent_usd"] == 30.0


def test_halfway_through_the_month_the_limit_is_half_the_budget_plus_the_head_start(tmp_path, capsys):
    content = content_with(tmp_path, [record("a", 179.99)])
    code, out = gate(content, capsys, MIDDLE)
    assert code == 0 and out["pace"]["month_elapsed"] == 0.5 and out["pace"]["limit_usd"] == 180.0
    content = content_with(tmp_path / "b", [record("a", 180.0)])
    assert gate(content, capsys, MIDDLE)[0] == 10


def test_at_the_end_of_the_month_the_limit_is_the_budget(tmp_path, capsys):
    content = content_with(tmp_path, [record("a", 299.0)])
    code, out = gate(content, capsys, END)
    assert code == 0 and out["pace"]["limit_usd"] == 300.0
    content = content_with(tmp_path / "b", [record("a", 300.0)])
    assert gate(content, capsys, END)[0] == 10


def test_only_this_months_records_count(tmp_path, capsys):
    content = content_with(tmp_path, [record("old", 500.0)], month="2026-10")
    code, out = gate(content, capsys, MIDDLE)
    assert code == 0 and out["spent_usd"] == 0 and out["runs"] == 0


def test_a_month_with_no_records_has_spent_nothing(tmp_path, capsys):
    content = tmp_path / "content"
    (content / "state").mkdir(parents=True)
    code, out = gate(content, capsys, START)
    assert code == 0 and out["spent_usd"] == 0


def test_an_incomplete_run_counts_its_recorded_spend(tmp_path, capsys):
    # A cut-off run recorded with no cost counts its cap (spend_usd, which record-cost sets).
    content = content_with(tmp_path, [record("a", 10.0, complete=False, cost=None)])
    code, out = gate(content, capsys, START, "--head-start", "3")
    assert code == 10 and out["spent_usd"] == 10.0 and out["incomplete_runs"] == 1 and out["pace"]["limit_usd"] == 9.0


def test_the_head_start_and_pacing_are_arguments(tmp_path, capsys):
    content = content_with(tmp_path, [record("a", 250.0)])
    code, out = gate(content, capsys, START, "--no-pace")
    assert code == 0 and out["pace"] is None
    content = content_with(tmp_path / "b", [record("a", 300.0)])
    assert gate(content, capsys, START, "--no-pace")[0] == 10
    content = content_with(tmp_path / "c", [record("a", 59.0)])
    assert gate(content, capsys, START, "--head-start", "20")[0] == 0


def test_december_ends_at_the_new_year(tmp_path, capsys):
    content = content_with(tmp_path, [], month="2026-12")
    code, out = gate(content, capsys, "2026-12-16T12:00:00Z")
    assert code == 0 and out["month"] == "2026-12" and out["pace"]["month_elapsed"] == 0.5


@pytest.mark.parametrize("raw", [
    '{"v": 1, "run": "a"\n',
    json.dumps({"v": 1, "run": "a", "spend_usd": 1.0}) + "\n",
    "[1, 2]\n",
], ids=["not json", "not a cost record", "not an object"])
def test_malformed_records_stop_the_run(tmp_path, capsys, raw):
    content = content_with(tmp_path, [], raw=json.dumps(record("ok", 1.0)) + "\n" + raw)
    code, out = gate(content, capsys, MIDDLE)
    assert code == 11 and out["decision"] == "stop" and "line 2" in out["reason"]


def test_unreadable_records_stop_the_run(tmp_path, capsys):
    content = content_with(tmp_path, [])
    path = content / "state/cost/2026-11.jsonl"
    path.unlink()
    path.mkdir()  # a folder where the file should be cannot be read
    code, out = gate(content, capsys, MIDDLE)
    assert code == 11 and out["decision"] == "stop"


def test_a_folder_that_is_not_a_content_repo_stops_the_run(tmp_path, capsys):
    code, out = gate(tmp_path / "nowhere", capsys, MIDDLE)
    assert code == 11 and "not a content repo" in out["reason"]


@pytest.mark.parametrize("argv", [[], ["--budget-usd", "0"], ["--budget-usd", ""], ["--budget-usd", "100", "--head-start", "120"]],
                         ids=["no budget", "zero budget", "empty budget", "head start over 100"])
def test_the_budget_is_required_and_sane(tmp_path, argv):
    with pytest.raises(SystemExit):
        main(["budget-gate", "--content", str(tmp_path), *argv])


def test_the_usage_gate_is_unchanged_and_separate(tmp_path, capsys):
    # The subscription gate still reads the usage probe; it knows nothing of cost records.
    probe = tmp_path / "probe.sh"
    probe.write_text('echo \'{"seven_day": {"used_percentage": 12.0, "resets_at": 1}}\'\n')
    assert main(["gate", "--probe", str(probe)]) == 0
    assert set(json.loads(capsys.readouterr().out)) == {"decision", "weekly_used_percentage", "max", "resets_at", "pace"}
