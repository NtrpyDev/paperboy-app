#!/usr/bin/env bash
# Prints the Claude subscription usage of the logged-in account as JSON:
#   {"five_hour": {"used_percentage": N, "resets_at": T}, "seven_day": {...}}
# Exit 0 with JSON on stdout when the reading worked, exit 1 otherwise.
#
# How: Claude Code hands its status line command a JSON document that includes
# rate_limits (documented at https://code.claude.com/docs/en/statusline.md).
# The status line only runs in an interactive session, so this script opens one
# inside tmux, sends a one-word prompt, saves the status line input, and exits.
set -uo pipefail

work="$(mktemp -d "${TMPDIR:-/tmp}/paperboy-usage-probe.XXXXXX")"
session="paperboy-usage-probe-$$"
trap 'tmux kill-session -t "$session" 2>/dev/null; rm -rf "$work"' EXIT

cat > "$work/dump.sh" <<DUMP
#!/bin/sh
cat > "$work/status.json.tmp" && mv "$work/status.json.tmp" "$work/status.json"
echo usage-probe
DUMP
chmod +x "$work/dump.sh"
printf '{"statusLine": {"type": "command", "command": "%s"}}\n' "$work/dump.sh" > "$work/settings.json"

tmux new-session -d -s "$session" -x 140 -y 45 -c "$work" \
  "claude --model sonnet --settings $work/settings.json" || { echo "tmux failed to start" >&2; exit 1; }

screen() { tmux capture-pane -t "$session" -p 2>/dev/null; }
sent=0
for _ in $(seq 1 60); do
  sleep 2
  s="$(screen)" || { echo "claude exited early" >&2; exit 1; }
  if grep -q "Yes, I trust this folder" <<<"$s"; then
    # Trust dialog for the scratch folder this script just created.
    tmux send-keys -t "$session" Down; sleep 1; tmux send-keys -t "$session" Enter; continue
  fi
  if grep -q "keep bypass permissions" <<<"$s"; then
    # Offer to change the default permission mode: decline, change nothing.
    tmux send-keys -t "$session" Down; sleep 1; tmux send-keys -t "$session" Enter; continue
  fi
  if [ "$sent" = 0 ] && grep -q "usage-probe" <<<"$s"; then
    tmux send-keys -t "$session" "Reply with the single word ok" Enter; sent=1; continue
  fi
  if [ -s "$work/status.json" ] && python3 - "$work/status.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
r = d.get("rate_limits")
if not r or "seven_day" not in r:
    sys.exit(1)
print(json.dumps(r))
PY
  then
    tmux send-keys -t "$session" "/exit" Enter
    exit 0
  fi
done
echo "no rate_limits in status line input after 120 s" >&2
screen | grep -v '^$' | tail -15 >&2
exit 1
