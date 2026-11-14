"""The cost records in schema/fixtures/cost/ are read by this suite and by the worker's tests
(worker/test/handler/owner.test.ts), so budget-gate and the owner's numbers page count a month's
spend the same way: a complete run counts total_cost_usd, an incomplete run the larger of
total_cost_usd and budget_cap_usd."""
import json
import shutil
from pathlib import Path

import pytest

from paperboy_pipeline import schemas
from paperboy_pipeline.cli import main

FIXTURES = Path(__file__).resolve().parents[2] / "schema" / "fixtures" / "cost"
EXPECTED = json.loads((FIXTURES / "expected.json").read_text())["months"]


@pytest.mark.parametrize("month", sorted(EXPECTED))
def test_every_fixture_record_is_a_cost_record_whose_spend_follows_the_rule(month):
    for line in (FIXTURES / f"{month}.jsonl").read_text().splitlines():
        record = json.loads(line)
        assert schemas.errors("cost-record", record) == []
        reported = record["total_cost_usd"] or 0.0
        rule = reported if record["complete"] else max(reported, record["budget_cap_usd"])
        assert record["spend_usd"] == round(rule, 6)


@pytest.mark.parametrize("month", sorted(EXPECTED))
def test_budget_gate_reads_the_fixture_month_as_expected(month, tmp_path, capsys):
    content = tmp_path / "content"
    (content / "state/cost").mkdir(parents=True)
    shutil.copy(FIXTURES / f"{month}.jsonl", content / "state/cost" / f"{month}.jsonl")

    main(["budget-gate", "--content", str(content), "--budget-usd", "1000", "--no-pace", "--now", f"{month}-20T00:00:00Z"])
    out = json.loads(capsys.readouterr().out)

    assert out["spent_usd"] == EXPECTED[month]["spend_usd"]
    assert out["runs"] == EXPECTED[month]["runs"]
    assert out["incomplete_runs"] == EXPECTED[month]["incomplete_runs"]
