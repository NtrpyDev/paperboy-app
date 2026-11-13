import json

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
