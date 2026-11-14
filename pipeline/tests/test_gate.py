import json
from datetime import datetime, timezone

import pytest

from paperboy_pipeline.cli import main


def probe(tmp_path, body):
    script = tmp_path / "probe.sh"
    script.write_text(body)
    return str(script)


def test_gate_goes_below_the_mark(tmp_path, capsys):
    p = probe(tmp_path, 'echo \'{"seven_day": {"used_percentage": 12.0, "resets_at": 1}}\'\n')
    assert main(["gate", "--probe", p]) == 0
    assert json.loads(capsys.readouterr().out)["decision"] == "go"


def test_gate_stops_at_the_mark(tmp_path, capsys):
    p = probe(tmp_path, 'echo \'{"seven_day": {"used_percentage": 70.0, "resets_at": 1}}\'\n')
    assert main(["gate", "--probe", p]) == 10


def test_gate_goes_just_under_the_mark(tmp_path, capsys):
    p = probe(tmp_path, 'echo \'{"seven_day": {"used_percentage": 69.0, "resets_at": 1}}\'\n')
    assert main(["gate", "--probe", p]) == 0


def test_gate_respects_a_custom_mark(tmp_path, capsys):
    p = probe(tmp_path, 'echo \'{"seven_day": {"used_percentage": 12.0, "resets_at": 1}}\'\n')
    assert main(["gate", "--probe", p, "--max", "10"]) == 10


def test_gate_fails_closed_when_usage_is_unreadable(tmp_path, capsys):
    p = probe(tmp_path, "echo nonsense; exit 1\n")
    assert main(["gate", "--probe", p]) == 11
    assert json.loads(capsys.readouterr().out)["decision"] == "stop"


# Pacing. resets_at is Unix seconds, as the probe prints it.
RESET = int(datetime(2026, 11, 19, 5, tzinfo=timezone.utc).timestamp())
WEEK_START = "2026-11-12T05:00:00Z"


def paced(tmp_path, capsys, used, now, resets_at=RESET, *extra):
    body = json.dumps({"seven_day": {"used_percentage": used, "resets_at": resets_at}})
    code = main(["gate", "--probe", probe(tmp_path, f"echo '{body}'\n"), "--now", now, *extra])
    return code, json.loads(capsys.readouterr().out)


def test_at_the_start_of_the_week_only_the_head_start_may_be_spent(tmp_path, capsys):
    code, out = paced(tmp_path, capsys, 9.9, WEEK_START)
    assert code == 0
    assert out["pace"] == {"week_elapsed": 0.0, "head_start": 10.0, "limit": 10.0}
    assert paced(tmp_path, capsys, 10.0, WEEK_START)[0] == 10


def test_halfway_through_the_week_the_limit_is_half_the_mark_plus_the_head_start(tmp_path, capsys):
    code, out = paced(tmp_path, capsys, 44.9, "2026-11-15T17:00:00Z")
    assert code == 0 and out["pace"]["week_elapsed"] == 0.5 and out["pace"]["limit"] == 45.0
    assert paced(tmp_path, capsys, 45.0, "2026-11-15T17:00:00Z")[0] == 10


def test_at_the_end_of_the_week_the_limit_is_the_mark(tmp_path, capsys):
    code, out = paced(tmp_path, capsys, 69.9, "2026-11-19T04:59:00Z")
    assert code == 0 and out["pace"]["limit"] == 70.0
    assert paced(tmp_path, capsys, 70.0, "2026-11-19T04:59:00Z")[0] == 10


def test_a_reset_time_already_past_counts_as_the_end_of_the_week(tmp_path, capsys):
    code, out = paced(tmp_path, capsys, 60.0, "2026-11-20T00:00:00Z")
    assert code == 0 and out["pace"]["week_elapsed"] == 1.0 and out["pace"]["limit"] == 70.0


def test_resets_at_may_be_an_rfc_3339_time(tmp_path, capsys):
    code, out = paced(tmp_path, capsys, 20.0, WEEK_START, "2026-11-19T05:00:00.000Z")
    assert code == 10 and out["pace"]["limit"] == 10.0


@pytest.mark.parametrize("resets_at", [None, "soon", True], ids=["missing", "unreadable", "not a time"])
def test_without_a_readable_reset_time_the_limit_is_the_plain_mark(tmp_path, capsys, resets_at):
    code, out = paced(tmp_path, capsys, 50.0, WEEK_START, resets_at)
    assert code == 0
    assert out["pace"]["week_elapsed"] is None and out["pace"]["limit"] == 70.0
    assert paced(tmp_path, capsys, 70.0, WEEK_START, resets_at)[0] == 10


def test_the_head_start_is_an_argument(tmp_path, capsys):
    code, out = paced(tmp_path, capsys, 4.0, WEEK_START, RESET, "--head-start", "3")
    assert code == 10 and out["pace"]["limit"] == 3.0


def test_no_pace_stops_only_at_the_mark(tmp_path, capsys):
    code, out = paced(tmp_path, capsys, 60.0, WEEK_START, RESET, "--no-pace")
    assert code == 0 and out["pace"] is None
    assert paced(tmp_path, capsys, 70.0, WEEK_START, RESET, "--no-pace")[0] == 10
