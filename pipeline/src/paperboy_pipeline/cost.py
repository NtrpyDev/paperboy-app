"""Cost records: what each pipeline run on the Anthropic API account cost.

Paths are relative to the content repo root:

    state/cost/<YYYY-MM>.jsonl     one CostRecord per run (schema/cost-record), by the month it was
                                   recorded; record-cost appends, budget-gate reads

A record is built from Claude Code's JSON result (claude -p --output-format json) and the run's
work folder. The result fields are the ones documented for the result message: subtype, is_error,
num_turns, duration_ms, total_cost_usd, modelUsage (per model: inputTokens, outputTokens,
cacheReadInputTokens, cacheCreationInputTokens, webSearchRequests, costUSD), and
permission_denials (SDKResultMessage and ModelUsage in
https://code.claude.com/docs/en/agent-sdk/typescript.md, read 2026-11-13). modelUsage is used,
not usage, because usage leaves out subagents ("Use modelUsage ... for whole-tree token
accounting", https://code.claude.com/docs/en/agent-sdk/cost-tracking.md). Both costs are
client-side estimates, not billing data (same page).

A run the Claude step did not finish is still recorded, marked incomplete with what is known.
Its spend_usd, the amount the budget gate counts, is the larger of its reported cost and its
per-run cap: the result can be missing, cut off, or zeroed after a crash (cost-tracking.md,
"Recover totals after a session crash").
"""
import json
from datetime import datetime
from pathlib import Path

from . import schemas
from .content_repo import PublishError

COST = Path("state/cost")
SUCCESS_OUTCOME = "success"
MODEL_FIELDS = {
    "input_tokens": "inputTokens",
    "output_tokens": "outputTokens",
    "cache_read_input_tokens": "cacheReadInputTokens",
    "cache_creation_input_tokens": "cacheCreationInputTokens",
    "web_search_requests": "webSearchRequests",
}


class CostError(Exception):
    """The month's cost records cannot be read or are not valid."""


def month_path(month: str) -> Path:
    return COST / f"{month}.jsonl"


def read_month(content: Path, month: str) -> list[dict]:
    """Every record of the month, each checked against its schema. A missing file is an empty
    month. Raises CostError on a line that is not JSON or not a CostRecord."""
    path = Path(content) / month_path(month)
    if not path.exists():
        return []
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError) as error:
        raise CostError(f"{month_path(month)} cannot be read: {error}")
    records = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise CostError(f"{month_path(month)} line {number} is not valid JSON: {error}")
        problems = schemas.errors("cost-record", record)
        if problems:
            raise CostError(f"{month_path(month)} line {number} is not a valid cost record: {'; '.join(problems[:3])}")
        records.append(record)
    return records


# Reading Claude Code's result

def _number(value) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0 else None


def _count(value) -> int | None:
    return int(value) if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def read_result(path: Path) -> tuple[dict | None, str | None]:
    """(the result message, None) or (None, why there is none). With --output-format json the
    file holds one JSON object; a stream-json file's last result line is accepted too."""
    path = Path(path)
    if not path.exists():
        return None, "the Claude step left no result file"
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError) as error:
        return None, f"the result file cannot be read: {error}"
    if not text.strip():
        return None, "the result file is empty, so the Claude step was cut off before it finished"
    candidates = []
    try:
        candidates.append(json.loads(text))
    except json.JSONDecodeError:
        for line in reversed(text.splitlines()):
            try:
                candidates.append(json.loads(line))
                break
            except json.JSONDecodeError:
                continue
    for value in candidates:
        if isinstance(value, dict) and value.get("type") == "result":
            return value, None
    return None, "the result file holds no result message, so the Claude step was cut off before it finished"


def _models(result: dict) -> dict:
    usage = result.get("modelUsage")
    if not isinstance(usage, dict):
        return {}
    out = {}
    for model, numbers in sorted(usage.items()):
        if not isinstance(numbers, dict):
            continue
        out[model] = {ours: _count(numbers.get(theirs)) for ours, theirs in MODEL_FIELDS.items()}
        out[model]["cost_usd"] = _number(numbers.get("costUSD"))
    return out


# Reading the work folder

def _by_kind() -> dict:
    return {"full": {}, "quick": {}}


def _add(counts: dict, kind: str, field: str) -> None:
    counts[kind][field] = counts[kind].get(field, 0) + 1


def pages(work: Path) -> tuple[str | None, dict, dict]:
    """(take run name, papers taken, pages built), each by kind and field, from WORK/take.json and
    WORK/papers/<id>/. A page counts as built when it passes the rule publish uses."""
    from .commands.publish import _explainer  # the one rule for a passing page

    taken, built = _by_kind(), _by_kind()
    take_path = Path(work) / "take.json"
    try:
        take = json.loads(take_path.read_text()) if take_path.exists() else {}
    except (OSError, json.JSONDecodeError):
        take = {}
    if not isinstance(take, dict):
        take = {}
    named = take.get("field") if isinstance(take.get("field"), dict) else {}
    for kind in ("full", "quick"):
        ids = take.get(kind) if isinstance(take.get(kind), list) else []
        for paper_id in ids:
            if not isinstance(paper_id, str):
                continue
            folder = Path(work) / "papers" / paper_id
            field = named.get(paper_id)
            if not isinstance(field, str):
                try:
                    field = json.loads((folder / "candidate.json").read_text()).get("field")
                except (OSError, json.JSONDecodeError, AttributeError):
                    field = None
            field = field if isinstance(field, str) and field else "unknown"
            _add(taken, kind, field)
            try:
                page = _explainer(paper_id, folder)
            except (PublishError, OSError, ValueError):
                page = None
            if page is not None:
                _add(built, "full" if page["depth"] == "full" else "quick", field)
    run = take.get("run") if isinstance(take.get("run"), str) and take.get("run") else None
    return run, taken, built


# The record

def build(*, run: str, result_path: Path, work: Path, cap_usd: float, outcome: str | None, now: str) -> dict:
    result, missing = read_result(result_path)
    take_run, taken, built = pages(work)
    record = {
        "v": 1,
        "run": run,
        "recorded_at": now,
        "budget_cap_usd": cap_usd,
        "total_cost_usd": None,
        "subtype": None,
        "num_turns": None,
        "duration_ms": None,
        "permission_denials": None,
        "models": {},
        "take_run": take_run,
        "taken": taken,
        "pages": built,
    }
    reason = missing
    if result is not None:
        denials = result.get("permission_denials")
        record.update(
            total_cost_usd=_number(result.get("total_cost_usd")),
            subtype=result.get("subtype") if isinstance(result.get("subtype"), str) else None,
            num_turns=_count(result.get("num_turns")),
            duration_ms=_count(result.get("duration_ms")),
            permission_denials=len(denials) if isinstance(denials, list) else None,
            models=_models(result),
        )
        if record["subtype"] != "success" or result.get("is_error") is not False:
            errors = [e for e in result.get("errors") or [] if isinstance(e, str)]
            reason = (f"Claude Code ended the run with {record['subtype'] or 'no subtype'}"
                      + (f" and is_error {result.get('is_error')!r}" if result.get("is_error") is not False else "")
                      + (f": {'; '.join(errors[:3])}" if errors else ""))
        elif record["total_cost_usd"] is None:
            reason = "the result message has no total_cost_usd"
    if reason is None and outcome not in (None, SUCCESS_OUTCOME):
        reason = f"the Claude step's outcome was {outcome}"
    record["complete"] = reason is None
    if reason is not None:
        record["incomplete_reason"] = reason
    reported = record["total_cost_usd"] or 0.0
    record["spend_usd"] = round(reported if record["complete"] else max(reported, cap_usd), 6)
    return record


def month_of(now: str) -> str:
    return datetime.fromisoformat(now.replace("Z", "+00:00")).strftime("%Y-%m")
