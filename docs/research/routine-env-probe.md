# Routine environment probe

Run date: 2026-11-13. One-off probe, raw results, nothing fixed.

## Section 1: network reach

Command template: `curl -sS -m 20 -o /dev/null -w '%{http_code}' -A 'paperboy-probe/0.1' '<url>'`

| URL | Result |
|---|---|
| https://api.openalex.org/works?per-page=1 | 200 |
| https://export.arxiv.org/api/query?search_query=all:electron&max_results=1 | 200 |
| https://arxiv.org/abs/1706.03762 | 200 |
| https://arxiv.org/html/1706.03762 | 200 |
| https://api.biorxiv.org/details/biorxiv/2026-11-01/2026-11-02/0 | 200 |
| https://www.biorxiv.org/ | 429 |
| https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=crispr&format=json&pageSize=1 | 200 |
| https://api.crossref.org/works?rows=1 | 200 |
| https://api.unpaywall.org/v2/10.1038/nature12373?email=test@example.com | 422 |
| https://www.nature.com/ | 303 |
| https://journals.plos.org/ | 301 |
| https://elifesciences.org/ | 200 |
| https://api.cloudflare.com/client/v4/ | 404 |
| https://cdn.jsdelivr.net/npm/d3@7/package.json | 200 |
| https://registry.npmjs.org/playwright | 200 |
| https://cdn.playwright.dev/ | 400 |
| https://example.com/ | 200 |

## Section 2: tooling

| Command | Output |
|---|---|
| `node --version` | v22.23.4 |
| `python3 --version` | Python 3.11.18 |
| `uv --version` | uv 0.11.32 (x86_64-unknown-linux-gnu) |
| `git --version` | git version 2.43.0 |
| `gh --version \| head -1` | gh version 2.89.0 (2026-03-26) |
| `tmux -V` | tmux 3.4 |
| `which google-chrome chromium chromium-browser chrome` | /usr/bin/google-chrome (exit 1, others not found) |
| `google-chrome --version` | Google Chrome for Testing 153.0.8010.12 |
| `claude --version` | 2.1.323 (Claude Code) |
| `nproc` | 4 |
| `free -g \| sed -n 2p` | Mem: 15 0 15 0 0 15 |
| `df -h / \| tail -1` | /dev/vda 252G 8.5G 31G 22% / |

## Section 3: headless Chrome

| Command | Result |
|---|---|
| `google-chrome --headless=new --no-sandbox --disable-gpu --screenshot=/tmp/probe.png --window-size=390,844 'data:text/html,<h1>probe</h1>'` | exit 0, "4756 bytes written to file /tmp/probe.png" (plus dbus connection errors on stderr, harmless). /tmp/probe.png exists, 4756 bytes. |

## Section 4: usage reading

| Command | Result |
|---|---|
| `bash tools/usage-probe.sh` | exit code 1 (it took longer than 120 s and was moved to the background) |
| stdout | (empty) |
| stderr | `no rate_limits in status line input after 120 s`, followed by a Claude Code theme picker screen dump (Dark mode, Light mode, colorblind variants, Monokai Extended syntax theme preview) |

Environment variable names containing CLAUDE or ANTHROPIC (names only):

`env | grep -i -E 'claude|anthropic' | sed 's/=.*//' | sort`

```
ANTHROPIC_BASE_URL
CLAUDECODE
CLAUDE_ADDITIONAL_DIRECTORIES
CLAUDE_AFTER_LAST_COMPACT
CLAUDE_AUTOCOMPACT_PCT_OVERRIDE
CLAUDE_AUTO_BACKGROUND_TASKS
CLAUDE_CODE_ACCOUNT_UUID
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD
CLAUDE_CODE_ARTIFACT_ASSETS
CLAUDE_CODE_BG_TASKS_REPORT_RUNNING
CLAUDE_CODE_CCR_EVENT_FLUSH_POLICY
CLAUDE_CODE_CHILD_SESSION
CLAUDE_CODE_CONFIG_WATCH_EVENTS
CLAUDE_CODE_CONTAINER_ID
CLAUDE_CODE_DEBUG
CLAUDE_CODE_DIAGNOSTICS_FILE
CLAUDE_CODE_DISABLE_BUILTIN_ANTMCP
CLAUDE_CODE_ELEGANT_MEADOW
CLAUDE_CODE_ENABLE_PROMPT_SUGGESTION
CLAUDE_CODE_ENTRYPOINT
CLAUDE_CODE_ENVIRONMENT_RUNNER_VERSION
CLAUDE_CODE_EXECPATH
CLAUDE_CODE_GZIP_REQUEST_BODIES
CLAUDE_CODE_HIDE_SETTINGS_HINT
CLAUDE_CODE_HOLD_UNANSWERED_PARKED_PERMISSION
CLAUDE_CODE_HOSTED_DESKTOP
CLAUDE_CODE_JIT_POLICY_AFTER_STARTUP
CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH
CLAUDE_CODE_MESSAGING_SOCKET
CLAUDE_CODE_MESSAGING_TOKEN
CLAUDE_CODE_ORGANIZATION_UUID
CLAUDE_CODE_POST_FOR_SESSION_INGRESS_V2
CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST
CLAUDE_CODE_PROXY_RESOLVES_HOSTS
CLAUDE_CODE_REMOTE
CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE
CLAUDE_CODE_REMOTE_HERMETIC_MODE
CLAUDE_CODE_REMOTE_SDK_URL
CLAUDE_CODE_REMOTE_SEND_KEEPALIVES
CLAUDE_CODE_REMOTE_SESSION_ID
CLAUDE_CODE_SESSION_ATTENDED
CLAUDE_CODE_SESSION_ID
CLAUDE_CODE_SYNC_PLUGINS
CLAUDE_CODE_SYNC_SESSION_REFS
CLAUDE_CODE_SYNC_SKILLS
CLAUDE_CODE_TEE_SDK_STDOUT
CLAUDE_CODE_USER_EMAIL
CLAUDE_CODE_USE_CCR_V2
CLAUDE_CODE_VERSION
CLAUDE_CODE_WORKER_EPOCH
CLAUDE_EFFORT
CLAUDE_ENABLE_STREAM_WATCHDOG
CLAUDE_PID
CLAUDE_SESSION_INGRESS_TOKEN_FILE
```

## Section 5: subagents

| Check | Result |
|---|---|
| Agent tool available | Yes |
| Subagent reply | `SUBAGENT_OK. I am running as Sonnet 5.5 (model ID claude-sonnet-5-5).` |

## Section 6: git

Commit 538c4ad on branch claude/env-probe.

| Command | Result |
|---|---|
| `git push -u origin claude/env-probe` | Succeeded (exit 0), new branch created on origin. No error. |
| `git push origin HEAD:refs/heads/probe/non-claude-branch` | Succeeded (exit 0), new branch created on origin. No error. |

No push to main. No pull request opened.

## Second probe: reading usage inside a cloud run (2026-11-13)

A second one-off run tested the headless usage reading and the pipeline package in the cloud environment.

| Command | Result |
|---|---|
| `bash tools/usage-probe.sh` | exit 0, `{"five_hour": {"used_percentage": 6.0, ...}, "seven_day": {"used_percentage": 9.0, ...}}` |
| `cd pipeline && uv sync` | exit 0 |
| `cd pipeline && uv run pytest -q` | 13 passed (Python 3.11.18) |
| `cd pipeline && uv run paperboy-pipeline gate` | exit 0, `{"decision": "go", "weekly_used_percentage": 9.0, "max": 50.0, ...}` |

So a nested headless `claude -p` call works inside a cloud run and reports the same weekly usage the dev machine sees. The usage gate can run inside the routine itself.
