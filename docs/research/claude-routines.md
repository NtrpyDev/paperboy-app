# Claude Code routines: what the docs say (2026-11-12)

Research for running the Paperboy content pipeline as scheduled cloud agents ("routines") on a Claude subscription. Every claim cites the official page it came from. Items the docs do not answer are listed at the end as NOT DOCUMENTED.

Sources:

- Routines: https://code.claude.com/docs/en/routines.md
- Cloud environments: https://code.claude.com/docs/en/cloud-environments.md
- Claude Code on the web: https://code.claude.com/docs/en/claude-code-on-the-web.md
- Subagents: https://code.claude.com/docs/en/sub-agents.md
- Status line: https://code.claude.com/docs/en/statusline.md
- Costs: https://code.claude.com/docs/en/costs.md
- GitHub Actions: https://code.claude.com/docs/en/github-actions.md

## 1. Network access

- Three access levels per environment: None, Limited (a default allowlist plus any domains the owner adds), Full (any domain). A new environment starts at Limited with "Allow package managers" checked. (cloud-environments.md, "Access levels" and "Network access")
- The default allowlist covers Anthropic services, version control, container registries, cloud platforms, package managers, Linux distros, and some dev tools. `api.openalex.org`, `export.arxiv.org`, `api.biorxiv.org`, `www.ebi.ac.uk`, and `api.cloudflare.com` are not on it. (cloud-environments.md, "Default allowed domains")
- Extra domains are added in the environment's "Allowed domains" field in the web UI, or the environment is set to Full. No API for this is documented for Anthropic-hosted environments. (cloud-environments.md, "Allow specific domains"; routines.md, "Environments and network access")
- GitHub traffic goes through its own proxy and is not subject to the allowlist.

## 2. Secrets and environment variables

- Environment variables: `.env` format, readable by any command the agent runs and by anyone who uses the environment. (cloud-environments.md, "Set environment variables")
- Network secrets: a key stored on the environment that Anthropic's proxy attaches to outbound requests for listed hosts. The key never enters the session VM. Set in the web UI. (cloud-environments.md, "Add network secrets")
- Network secrets are never attached to GitHub requests, `api.anthropic.com`, package registries, or setup script requests.

## 3. Tooling and setup scripts

- Preinstalled: Python 3 with pip, poetry, uv; Node 20, 21, 22; Ruby, PHP, Java, Go, Rust, C and C++; Docker; Postgres 16; Redis 7; Chrome; git, gh, jq, yq, ripgrep, tmux. (cloud-environments.md, "Installed tools")
- A setup script (Bash, root, Ubuntu 24.04, 64 KB max) runs before Claude Code starts. It must exit zero. If it finishes within about five minutes the filesystem is snapshotted and reused for about seven days. (cloud-environments.md, "Setup scripts" and "Environment caching")
- VM size: 4 vCPUs, 16 GB RAM, 30 GB disk. (cloud-environments.md, "Resource limits")

## 4. Git

- Each run clones the repo and pushes to a `claude/` branch unless the prompt directs another branch. Which branches a run may update is controlled only by GitHub branch protection. (routines.md, "Repositories and branch permissions")
- The GitHub proxy rejects branch deletions and non-branch pushes such as tags, and rejects GraphQL, so `gh pr` and `gh issue` subcommands fail. `gh api repos/...` REST calls work. (cloud-environments.md, "GitHub proxy")
- Repo access comes from the Claude GitHub App or `/web-setup`.

## 5. Run limits

- Cron schedules more frequent than hourly are rejected. (routines.md, "Usage and limits")
- Start caps: 100 scheduled runs per hour per account; 30 per hour per task for Run now, API fires, and reruns; 100 API fires per hour per account. No overage on these caps.
- An idle VM pauses after a few minutes and can later be reclaimed. Bash commands default to a 2 minute timeout, 10 minutes on request, 30 minutes in the background. (cloud-environments.md, "Time limits")

## 6. Usage accounting

- "Scheduled tasks draw down subscription usage the same way interactive sessions do." (routines.md, "Usage and limits")
- At the usage limit, runs are rejected until the window resets unless usage credits are turned on.

## 7. Reading usage from code

- The status line input JSON carries `rate_limits.five_hour.used_percentage` and `rate_limits.seven_day.used_percentage` with `resets_at`, for subscribers, after the first API response. (statusline.md, "Available data")
- Verified on the dev machine on 2026-11-12: `tools/usage-probe.sh` reads those fields by opening a short interactive session in tmux.
- Whether the same works inside a cloud session is NOT DOCUMENTED and has to be tested.

## 8. Subagents and models

- "Subagents work the same way they do locally." Agents defined in the repo's `.claude/agents/` load automatically. (claude-code-on-the-web.md, "Manage context")
- Subagent model resolution: the Agent call's `model`, then the agent file's `model:` frontmatter, then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main model. (sub-agents.md)

## 9. Other triggers

- An API trigger gives a routine an HTTP endpoint. A POST with the routine's bearer token starts a run. This is not bound by the hourly cron minimum, only by the hourly start caps. Beta header: `anthropic-beta: experimental-cc-routine-2026-04-01`. (routines.md, "Add an API trigger")
- GitHub event triggers (PR, issue, release) need the Claude GitHub App on the repo.

## 10. Fallback: Claude Code in GitHub Actions

- `anthropics/claude-code-action` with `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token` is documented for Pro, Max, Ultra, Team, and Enterprise. "If you authenticate with an OAuth token, runs use your Claude subscription instead of API billing." (github-actions.md, "Manual setup" and "Manage costs")
- Scheduled workflows run only from the default branch, and in public repos GitHub disables the schedule after 60 days without repository activity. (github-actions.md, "Run on a schedule")

## NOT DOCUMENTED

- A maximum total run duration for a cloud session.
- A cap on the number of routines per account, or a number for the concurrent session cap.
- Any difference in routine limits between subscription tiers.
- Whether status line data or `/usage` is reachable inside a cloud session.
- An API for an individual subscriber's weekly usage percentage.
- An API for setting an Anthropic-hosted environment's network access.
