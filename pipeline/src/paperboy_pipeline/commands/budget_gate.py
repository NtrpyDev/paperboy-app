"""budget-gate: stop an API run when this month's recorded spend has reached the paced budget.

The gate for runs on the Anthropic API account, where the usage gate (gate) has no subscription
usage to read. It sums spend_usd over this month's cost records in CONTENT/state/cost/<YYYY-MM>.jsonl
(the month in UTC) and lets the run go only while that spend is under the pace limit. The idea is
the usage gate's: with B the month's budget (--budget-usd), H the head start (--head-start, a
percentage of B, default 10) and f the fraction of the calendar month already elapsed, the
limit is min(B, B * f + B * H / 100). A fresh month can spend H percent at once; the rest comes
linearly; at the end of the month the limit is B. --no-pace makes the limit B always.

Fail closed: a checkout without state/, or a cost record that is not valid JSON or not a valid
CostRecord, stops the run. A month with no records yet has spent nothing. A run can still pass
the limit by up to its own per-run cap, which Claude Code enforces (--max-budget-usd).
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .. import cost

GO, STOP, UNREADABLE = 0, 10, 11


def register(subparsers) -> None:
    p = subparsers.add_parser("budget-gate", help="for API runs: exit 0 to continue, 10 when this month's spend is at or over the paced budget, 11 when the cost records cannot be read",
                              description=__doc__)
    p.add_argument("--content", type=Path, required=True, help="content repo checkout holding state/cost/")
    p.add_argument("--budget-usd", type=_positive, required=True, help="the month's API budget in US dollars")
    p.add_argument("--head-start", type=_percent, default=10.0, help="percent of the month's budget a run may spend ahead of pace (default 10)")
    p.add_argument("--no-pace", action="store_true", help="stop only at the whole budget, however early in the month")
    p.add_argument("--now", help="RFC 3339 time to use as the current time (for tests)")
    p.set_defaults(run=run)


def _positive(text: str) -> float:
    value = float(text)
    if not value > 0:
        raise argparse.ArgumentTypeError("must be more than 0")
    return value


def _percent(text: str) -> float:
    value = float(text)
    if not 0 <= value <= 100:
        raise argparse.ArgumentTypeError("must be between 0 and 100")
    return value


def month_bounds(now: datetime) -> tuple[datetime, datetime]:
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
    return start, end


def pace_limit(budget: float, head_start_pct: float, now: datetime) -> tuple[float, float]:
    """(limit in dollars, fraction of the month elapsed)."""
    start, end = month_bounds(now)
    elapsed = min(1.0, max(0.0, (now - start) / (end - start)))
    return min(budget, budget * elapsed + budget * head_start_pct / 100), elapsed


def run(args) -> int:
    now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else datetime.now(timezone.utc)
    now = now.astimezone(timezone.utc)
    month = now.strftime("%Y-%m")
    if not (args.content / "state").is_dir():
        print(json.dumps({"decision": "stop", "reason": f"{args.content} has no state/ folder, so it is not a content repo checkout"}))
        return UNREADABLE
    try:
        records = cost.read_month(args.content, month)
    except cost.CostError as error:
        # Fail closed: without a reading the pipeline must not spend the API budget.
        print(json.dumps({"decision": "stop", "reason": f"cost records could not be read: {error}"}))
        return UNREADABLE
    spent = round(sum(r["spend_usd"] for r in records), 6)
    report = {"month": month, "spent_usd": spent, "budget_usd": args.budget_usd, "runs": len(records),
              "incomplete_runs": sum(not r["complete"] for r in records)}
    if args.no_pace:
        limit = args.budget_usd
        report["pace"] = None
    else:
        limit, elapsed = pace_limit(args.budget_usd, args.head_start, now)
        report["pace"] = {"month_elapsed": round(elapsed, 4), "head_start": args.head_start, "limit_usd": round(limit, 2)}
    decision = "stop" if spent >= limit else "go"
    print(json.dumps({"decision": decision, **report}))
    return STOP if decision == "stop" else GO
