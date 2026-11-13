#!/usr/bin/env bash
# Prints the Claude subscription usage of the logged-in account as JSON:
#   {"five_hour": {"used_percentage": N, "resets_at": T}, "seven_day": {"used_percentage": N, "resets_at": T}}
# Exit 0 with JSON on stdout when the reading worked, exit 1 otherwise.
#
# How: a headless Claude Code call with --output-format stream-json emits one
# rate_limit_event whose unifiedWindows carry the five hour and seven day
# utilization. This script makes one one-word call and reads that event.
# Verified on the dev machine on 2026-11-12 with Claude Code 2.1.323.
set -uo pipefail

stream="$(timeout 180 claude -p "Reply with the single word ok" --model sonnet \
  --output-format stream-json --verbose 2>/dev/null)"
status=$?
if [ "$status" -ne 0 ] && [ -z "$stream" ]; then
  echo "claude -p failed with exit $status and printed nothing" >&2
  exit 1
fi

printf '%s\n' "$stream" | python3 -c '
import json, sys

windows = None
for line in sys.stdin:
    line = line.strip()
    if not line.startswith("{"):
        continue
    try:
        event = json.loads(line)
    except ValueError:
        continue
    if event.get("type") == "rate_limit_event":
        windows = (event.get("rate_limit_info") or {}).get("unifiedWindows") or windows

if not windows or "seven_day" not in windows:
    sys.stderr.write("no rate_limit_event with a seven_day window in the stream\n")
    sys.exit(1)

out = {}
for name in ("five_hour", "seven_day"):
    w = windows.get(name)
    if w is None:
        continue
    out[name] = {"used_percentage": round(float(w["utilization"]) * 100, 1), "resets_at": w.get("resetsAt")}
print(json.dumps(out))
'
