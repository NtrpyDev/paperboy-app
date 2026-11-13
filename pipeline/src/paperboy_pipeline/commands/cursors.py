"""cursors: record that sources are processed through a day.

A cursor in CONTENT_REPO/state/cursors.json is the last day (UTC) whose papers from that source
have been discovered, judged, and published. Discover starts each source the day after its
cursor. This command only moves a cursor forward; a date before the current cursor leaves it.
"""
import json
import sys
from datetime import date
from pathlib import Path

from .. import schemas
from ..content_repo import CURSORS, dump_json
from ..sources import ADAPTERS
from .discover import source_list


def register(subparsers) -> None:
    parser = subparsers.add_parser("cursors", help="mark sources as processed through a day", description=__doc__)
    parser.add_argument("--content", type=Path, required=True, help="content repo checkout holding state/cursors.json")
    parser.add_argument("--set-through", type=date.fromisoformat, required=True, help="last processed day, YYYY-MM-DD")
    parser.add_argument("--sources", type=source_list, default=list(ADAPTERS), help="comma separated: " + ",".join(ADAPTERS))
    parser.set_defaults(run=run)


def run(args) -> int:
    path = args.content / CURSORS
    state = {"v": 1, "cursors": {}}
    if path.exists():
        state = json.loads(path.read_text())
    through = args.set_through.isoformat()
    for name in args.sources:
        current = state["cursors"].get(name)
        if current is not None and current >= through:
            print(f"{name}: already through {current}")
            continue
        state["cursors"][name] = through
        print(f"{name}: through {through}" + (f" (was {current})" if current else ""))
    problems = schemas.errors("cursors", state)
    if problems:
        print(f"cursors: {path} would not match its schema, nothing was written: {'; '.join(problems)}", file=sys.stderr)
        return 1
    data = dump_json(state)
    if not (path.exists() and path.read_bytes() == data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return 0
