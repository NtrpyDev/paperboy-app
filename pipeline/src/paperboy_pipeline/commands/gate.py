"""gate: stop the run when weekly Claude usage has reached the owner's mark."""
import json
import subprocess
from pathlib import Path

GO, STOP, UNREADABLE = 0, 10, 11
DEFAULT_PROBE = Path(__file__).resolve().parents[4] / "tools" / "usage-probe.sh"


def register(subparsers) -> None:
    p = subparsers.add_parser("gate", help="exit 0 to continue, 10 when weekly usage is at or over the mark, 11 when usage cannot be read")
    p.add_argument("--max", type=float, default=70.0, help="weekly usage percentage at which the pipeline stops")
    p.add_argument("--probe", default=str(DEFAULT_PROBE), help="command that prints the usage JSON")
    p.set_defaults(run=run)


def run(args) -> int:
    try:
        result = subprocess.run(["bash", args.probe], capture_output=True, text=True, timeout=300)
        usage = json.loads(result.stdout.strip().splitlines()[-1])
        weekly = float(usage["seven_day"]["used_percentage"])
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, IndexError, TypeError) as exc:
        # Fail closed: without a reading the pipeline must not spend the owner's usage.
        print(json.dumps({"decision": "stop", "reason": f"usage could not be read: {exc.__class__.__name__}"}))
        return UNREADABLE
    decision = "stop" if weekly >= args.max else "go"
    print(json.dumps({"decision": decision, "weekly_used_percentage": weekly, "max": args.max,
                      "resets_at": usage["seven_day"].get("resets_at")}))
    return STOP if decision == "stop" else GO
