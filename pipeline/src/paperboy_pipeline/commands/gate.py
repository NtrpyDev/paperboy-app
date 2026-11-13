"""gate: stop the run when weekly Claude usage has reached the owner's mark, or is ahead of pace.

The mark M (--max, 70) caps the week. Pacing spreads it over the week, so the budget is not spent
in the first days after the weekly reset and the feed does not go stale for the rest: with f the
fraction of the seven day usage window already elapsed (from the probe's seven_day resets_at),
the run goes only while weekly usage is under min(M, M * f + H), where H (--head-start, 10
points) lets a fresh week start. Without a readable resets_at the limit is the plain mark.
--no-pace turns pacing off. The JSON line printed says which numbers were used.
"""
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

GO, STOP, UNREADABLE = 0, 10, 11
DEFAULT_PROBE = Path(__file__).resolve().parents[4] / "tools" / "usage-probe.sh"
WEEK = timedelta(days=7)


def register(subparsers) -> None:
    p = subparsers.add_parser("gate", help="exit 0 to continue, 10 when weekly usage is at or over the limit, 11 when usage cannot be read",
                              description=__doc__)
    p.add_argument("--max", type=float, default=70.0, help="weekly usage percentage at which the pipeline stops (default 70)")
    p.add_argument("--head-start", type=float, default=10.0, help="points of the week's budget a run may use ahead of pace (default 10)")
    p.add_argument("--no-pace", action="store_true", help="stop only at --max, however early in the week")
    p.add_argument("--probe", default=str(DEFAULT_PROBE), help="command that prints the usage JSON")
    p.add_argument("--now", help="RFC 3339 time to use as the current time (for tests)")
    p.set_defaults(run=run)


def _resets(value) -> datetime | None:
    """resets_at as the probe gives it: Unix seconds, or an RFC 3339 time."""
    try:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return datetime.fromtimestamp(value, timezone.utc)
        if isinstance(value, str) and value.strip():
            moment = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
            return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None
    return None


def pace_limit(mark: float, head_start: float, resets_at, now: datetime) -> tuple[float, float | None]:
    """(limit, fraction of the week elapsed). The fraction is None, and the limit the mark, when
    resets_at cannot be read."""
    resets = _resets(resets_at)
    if resets is None:
        return mark, None
    elapsed = 1 - (resets - now) / WEEK
    elapsed = min(1.0, max(0.0, elapsed))
    return min(mark, mark * elapsed + head_start), elapsed


def run(args) -> int:
    now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else datetime.now(timezone.utc)
    try:
        result = subprocess.run(["bash", args.probe], capture_output=True, text=True, timeout=300)
        usage = json.loads(result.stdout.strip().splitlines()[-1])
        weekly = float(usage["seven_day"]["used_percentage"])
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, IndexError, TypeError) as exc:
        # Fail closed: without a reading the pipeline must not spend the owner's usage.
        print(json.dumps({"decision": "stop", "reason": f"usage could not be read: {exc.__class__.__name__}"}))
        return UNREADABLE
    resets_at = usage["seven_day"].get("resets_at")
    report = {"weekly_used_percentage": weekly, "max": args.max, "resets_at": resets_at}
    if args.no_pace:
        limit = args.max
        report["pace"] = None
    else:
        limit, elapsed = pace_limit(args.max, args.head_start, resets_at, now)
        report["pace"] = {
            "week_elapsed": None if elapsed is None else round(elapsed, 4),
            "head_start": args.head_start,
            "limit": round(limit, 2),
        }
        if elapsed is None:
            report["pace"]["note"] = "resets_at unreadable, the limit is the plain mark"
    decision = "stop" if weekly >= limit else "go"
    print(json.dumps({"decision": decision, **report}))
    return STOP if decision == "stop" else GO
