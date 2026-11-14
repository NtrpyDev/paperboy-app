# Runbook: one pipeline run

You are the orchestrator of one Paperboy pipeline run. You find new papers, have agents judge them and build their pages, and publish the results to the content repo. You delegate the reading and building to the six agents defined in `.claude/agents/`: `paperboy-triage`, `paperboy-scout`, `paperboy-quick`, `paperboy-expert`, `paperboy-visualizer`, `paperboy-checker`. You run the scripts and make the decisions between them.

Two checkouts sit side by side: this code repo and the content repo (`paperboy-content`). In the steps below, `CODE` is this repo's root and `CONTENT` is the content repo's root. Commands run from `CODE/pipeline` as `uv run paperboy-pipeline <command>`. The work folder is `CODE/work` (never committed). `YESTERDAY` is yesterday's date in UTC, `YYYY-MM-DD`.

Every paper in the feed has a page. A paper enters the feed only when its page passes, so the scout's picks wait in the backlog (`CONTENT/state/queue/`) until a run builds their pages: a **full explainer** (expert, visualizer, checker, from the full text) for the best few with lawful free full text, a **quick explainer** (one `paperboy-quick` agent, from the title and abstract) for the rest. About 230 papers a day pass the scout and the budget does not cover a page for each, so each run takes the best papers waiting, and the rest wait and age out.

## The numbers for one run

These are the owner's starting values. Change them here; nowhere else repeats them.

- **F = 1**: full explainers per run (`queue take --full`).
- **Q = 6**: quick explainers per run (`queue take --quick`).
- **D = 7**: days a paper waits in the backlog before it ages out (`queue take --days`).
- The usage gate's mark is 70 percent of the week with pacing on (the `gate` defaults; see the owner's section).

In API mode (below), F and the per-field count N come from the run's settings in place of F and Q; D stays.

Each step ends on a condition. Reach it before moving on.

## Which mode this run is in

Before step 1, run `echo "mode=$PAPERBOY_MODE fields_url=$PAPERBOY_FIELDS_URL per_field=$PAPERBOY_PER_FIELD full=$PAPERBOY_FULL budget_usd=$PAPERBOY_BUDGET_USD"`.

- **`mode=` with nothing after it: a subscription run.** Do every step as written and ignore every "API mode" line.
- **`mode=api`: a run on the Anthropic API account** (the GitHub Actions workflow sets these values). Three steps change, each named below as "API mode": the gate (step 1), the take (step 4), and the report (step 8), where the cost record is the workflow's job, not yours. Use the printed values as written: URL is `fields_url`, N is `per_field`, F is `full`, B is `budget_usd`.

## 1. Gate

Run `uv run paperboy-pipeline gate`. API mode: run `uv run paperboy-pipeline budget-gate --content CONTENT --budget-usd B` instead, here and every time a later step says to run the gate. Exit 0 means go. Any other exit means stop now: publish nothing, and end the run with the line the command printed. Run the gate again before each group of quick explainers in step 5 and before the full explainer in step 6; the same rule applies there (start nothing new, go straight to step 7 with what is already complete).

## 2. Set up

- `cd CODE/pipeline && uv sync`.
- `git -C CONTENT pull --ff-only` so state is current.
- Start with an empty work folder: remove `CODE/work` if it exists.

Done when `uv run paperboy-pipeline --help` lists the commands and the content repo is at the tip of `main`.

## 3. Discover and scout into the backlog

Read `CONTENT/state/cursors.json`. A cursor is the last day a source has been processed through. If all five sources (arxiv, biorxiv, medrxiv, europepmc, crossref) have a cursor of `YESTERDAY` or later, skip to step 4. Otherwise:

1. `uv run paperboy-pipeline discover --work ../work --content CONTENT --until YESTERDAY`. It prints one line per source. Note every source whose line says `failed`. Discover skips every paper already in the feed or that ever entered the backlog, so no paper is judged twice.
2. `uv run paperboy-pipeline batch --work ../work --triage` writes `work/triage/NNN.tsv`. Papers from the followed journals (`pipeline/journals.json`) skip triage.
3. For each triage file, start a `paperboy-triage` agent with the triage path and the output path `work/triage-picks/NNN.txt` (same number). Run up to four at a time. An agent that fails or writes no file is run once more; after a second failure that file's papers are not judged this run.
4. `uv run paperboy-pipeline batch --work ../work` writes `work/batches/NNN.jsonl` from the picks and the followed-journal papers.
5. For each batch file, start a `paperboy-scout` agent with the batch path and the output path `work/judged/NNN.jsonl` (same number). Run up to four at a time. A scout that fails or writes fewer lines than its batch is run once more; a second failure drops that batch for this run.
6. `uv run paperboy-pipeline select --work ../work` writes `work/judged.jsonl` and prints what it rejected.
7. `uv run paperboy-pipeline queue add --content CONTENT --work ../work --push` puts every paper select kept into the backlog, with its whole record, and pushes it. Nothing reaches the feed here.
8. `uv run paperboy-pipeline cursors --content CONTENT --set-through YESTERDAY --sources <every source not noted as failed, joined by commas with no spaces, for example arxiv,biorxiv,medrxiv,europepmc,crossref> --push`. A failed source keeps its cursor so the next run reads those days again.

If discover wrote no candidates, skip items 2 to 7 and still do item 8: those days are processed.

Done when both pushes succeeded. Each command pushes by itself: when the remote moved, it builds its change again on the new `main` and pushes again. If one exits 1, read its error, and if it says the checkout holds changes that are not on `origin/main`, the run broke a rule above; report it and stop.

## 4. Take this run's papers

`uv run paperboy-pipeline queue take --content CONTENT --work ../work --full 1 --quick 6 --days 7 --push` (F, Q, and D from the top of this file). It first ages out papers that have waited more than D days, then claims this run's papers and pushes the claims, so a run that overlaps this one takes different papers. It prints, and writes to `work/take.json`, two lists:

- `full`: up to F papers for full explainers, the best waiting papers that have lawful free full text.
- `quick`: up to Q papers for quick explainers, the best of the rest.

Both lists run best first and alternate preprints and peer-reviewed papers one for one while both kinds wait. Each taken paper has a work folder `work/papers/<id>/` with its `candidate.json`. A paper gets one kind of page, never both.

API mode: run `uv run paperboy-pipeline queue take --content CONTENT --work ../work --fields-url URL --per-field N --full F --days 7 --push` instead. It reads the active fields (the fields a paying subscriber picked) from URL and takes papers only in those fields: `full` holds up to F papers, `quick` up to N for each active field, and `field` says which field each paper is for. If it exits 1 with "the active field list is not usable", nothing was taken: go to step 8 and report that line.

If both lists are empty, go to step 8. Done when the command exits 0.

## 5. Quick explainers

Take the `quick` papers in groups of up to four. Before each group, run the gate (step 1). For each paper in the group, start a `paperboy-quick` agent with its work folder `work/papers/<id>/`; the group's agents run at the same time. After each agent replies:

1. **Check.** Run `uv run paperboy-pipeline check --explainer ../work/papers/<id>/explainer --kit ../kit` yourself. It is the render check plus the numbers check: it reads `candidate.json` in the work folder and fails the page (`number-not-in-abstract`) when it prints a number that is not in the title or abstract. The page passes when the command exits 0, `check.json` has `page.depth` `"abstract"`, and `page.numbers` is not `null`.
2. **Retry once.** If it did not pass, write `work/papers/<id>/retry.md` with one line per problem: each `rule` and `detail` from `check.json`'s `problems`, or "page.depth is not abstract", or "the agent wrote no explainer/index.html". Then start one new `paperboy-quick` agent with the work folder and tell it to fix what `retry.md` lists. Check again as in item 1.
3. **Set aside.** If it still does not pass, delete its `explainer` folder so it cannot be published by mistake, and run `uv run paperboy-pipeline queue fail --content CONTENT --work ../work --id <id> --reason "<one plain sentence: what failed>"`. The paper leaves the backlog for good.
4. **Close.** When it passes, write `work/papers/<id>/made_by.json` as `{"quick": "<model id>"}`, the full model id the last quick agent ran as.

Done when every `quick` paper is closed or set aside, or the gate stopped the step.

## 6. Full explainer

For each `full` paper, with its work folder `work/papers/<id>/`:

1. **Gate.** As in step 1.
2. **Fetch.** `uv run paperboy-pipeline fetch --work ../work --id <id>`. Fetch already waits between requests to one host as that host's robots.txt asks, across fetch commands, so run it as is. Exit 3 means no lawful full text: run `queue back` (below) with the reason it printed and take the next paper.
3. **Brief.** Start a `paperboy-expert` agent with the work folder. It writes `brief.md` and `card.json` (the card's readout). If `brief.md` begins with `NOT EXPLAINABLE:`, run `queue back` with that line as the reason and take the next paper.
4. **Build.** Start a `paperboy-visualizer` agent with the work folder. It writes `explainer/index.html` and runs the render check itself until it passes.
5. **Check.** Run `uv run paperboy-pipeline check --explainer ../work/papers/<id>/explainer --kit ../kit` yourself so `check.json`, the screenshots, and the two plate stills are fresh. Then start a `paperboy-checker` agent with the work folder. Give it nothing else: not the visualizer's reply, not your opinion of the page.
6. **Revise.** If `review.json` says `"pass": false`, start a new `paperboy-visualizer` agent with the work folder and tell it to fix the problems in `review.json`. If one of the problems is the card's readout (a number the paper does not report, or the wrong unit or label), first overwrite `card.json` with `{"readout": null}` yourself: a card with no number is always true, and the visualizer does not write that file. Then repeat item 5. At most two revisions. A paper that still fails is set aside: delete its `explainer` folder so it cannot be published by mistake, and run `queue back` with the checker's main problem as the reason.
7. **Close.** When `check.json` and `review.json` both pass, write `work/papers/<id>/made_by.json` as `{"expert": "<model id>", "visualizer": "<model id>", "checker": "<model id>"}`, each the full model id that agent ran as (the last visualizer when there were revisions).

`queue back` is `uv run paperboy-pipeline queue back --content CONTENT --work ../work --id <id> --reason "<one plain sentence>"`. The paper is not dropped: it waits in the backlog again, marked so that a later run gives it a quick explainer and never a full one.

Done with a paper when it is closed or sent back. A paper left open because the gate stopped the run, or because fetch exited 1, waits in the backlog for a later run.

## 7. Publish

`uv run paperboy-pipeline publish --work ../work --content CONTENT --push`. It adds every paper whose page passed to the feed, with its explainer, plates, kind, depth, and readout, takes those papers out of the backlog, applies this run's `queue fail` and `queue back` again, releases every claim this run took, commits, and pushes. When the remote moved, it builds all of that again on the new `main` and pushes again, up to five times. A paper whose page did not pass stays in the backlog and does not enter the feed.

Done when it exits 0. If it exits 1, report its error; the claims go stale after three hours and the papers can be taken again.

## 8. Report

End the run with a short plain report: the days discovered and each source's line from discover, papers triaged and picked, judged, and added to the backlog; the papers taken; each quick explainer built (id, retried or not) and each set aside (with its reason); the full explainer (id and the checker's scores) or why it went back; the papers that entered the feed, from publish's last line; how many papers wait in the backlog (the first line of `uv run paperboy-pipeline queue list --content CONTENT`); and the weekly usage reading and pace limit from the last gate.

API mode: report the month's spend, the budget, and the pace limit from the last budget gate in place of the weekly usage reading, and the active fields and the papers taken for each. Do not record the run's cost: the workflow records it from Claude Code's own result after you finish.

## Rules that hold throughout

- Sources are open APIs and lawful free full text only. If a site answers with a challenge page or a refusal, that paper has no full text; do not try another route to the same file.
- Published text is original. Abstracts are input and never appear in the feed or an explainer.
- A paper figure is reproduced only when its license is `cc-by` or `cc0`, with its credit line.
- When a script fails, read its error and fix the cause if it is in this run's inputs; otherwise set that paper aside and report it. Do not edit pipeline code during a run.
- Never edit files in `CONTENT` by hand. The commands above change it, and the ones that push rebuild their change from the work folder when the remote moved.
- Never push to the code repo from a run.
- Send no push notifications and no messages of any kind. The report in step 8 is the run's only output.

## For the owner: the cloud routine

This section is not part of a run.

The pipeline runs as the Claude Code cloud routine `paperboy-pipeline`, hourly. Each run clones this repo and `paperboy-content` at the tip of `main`, and its whole prompt is to follow this runbook. Nothing runs on the owner's computer. Runs can overlap: claims keep two runs off the same paper, and every push rebuilds on the newer `main` instead of merging.

- **See it, pause it, resume it:** https://claude.ai/code/routines lists the routine. Its switch pauses and resumes the schedule; "Run now" starts one run by hand. A paused routine starts no runs.
- **Inspect a run:** open the routine and pick a run to read its transcript. The last message is the step 8 report.
- **The usage gate and pacing:** every run starts with `paperboy-pipeline gate`, which stops the run when it cannot read usage, and otherwise when weekly Claude usage is at or over the pace limit. The mark M is 70 percent (the owner's mark, raised from 50 on 2026-11-13). Pacing spreads it over the week, so the budget is not spent in the first days after the weekly reset with the feed going stale for the rest: with f the fraction of the seven day usage window already elapsed (from the reading's reset time), the limit is the smaller of M and M times f plus a head start H of 10 points. A fresh week can use 10 points at once; halfway through, the limit is 45; at the end, 70. Without a reset time in the reading, the limit is the plain mark. The gate's JSON line prints the limit it used. Change M with `--max`, H with `--head-start`, or turn pacing off with `--no-pace`, in step 1 of this runbook. Verified in a cloud run on 2026-11-13, before pacing: with the mark set to 1 and usage at 35 percent, the run stopped at step 1 and published nothing.
- **Papers per run:** F, Q, and D at the top of this runbook. The pace rule is what holds the daily total, which the owner expects to be roughly 35 quick explainers and 4 full explainers a day.
- **What a page costs:** a full explainer costs about half a point of weekly usage, measured on the first cloud run, 2026-11-13, on the Max plan: that run read two days of new papers (590 judged by 40 scout batches), then built three full explainers, one of which needed two revisions and was set aside; it took 95 minutes and moved weekly usage from 35 to 37 percent, with discovery under one point of that. The meter reads in whole points, so this is a rough figure. A quick explainer on Opus, the owner's pick for cleaner pictures, measured about 104,000 tokens and 3.5 minutes per page in the cost test, against about 83,000 tokens and 85 seconds on Sonnet. The quick agent's model is the `model:` line of `.claude/agents/paperboy-quick.md`.
- **Change what a run does:** edit this runbook and the agent definitions in `.claude/agents/` on `main`. The next run picks them up.
- **One-time: reset a feed published before every paper needed a page.** `uv run paperboy-pipeline reset-feed --content CONTENT --keep-explained --rewind-cursors-to YYYY-MM-DD` on a checkout of the content repo prints what it would do: start the feed again in `feed/v2/` with only the feed items with a page (merged with their `upgrades.json` entries into a new chunk 1), leave `feed/v1/` as a stub head with no chunks and `min_app` 2 so 0.1.0 installs show their update cover, delete the other paper folders, keep `state/seen` for those papers only, empty the backlog, claims, and backlog ledger, keep `queue-failed.jsonl`, and set every cursor later than the given day back to it, so the next run reads the days after it again under these rules. Add `--yes` to make the changes. It never commits or pushes: review with `git status`, then commit and push by hand, with the routine paused.

## For the owner: the API run

This section is not part of a run.

**What it is.** The same runbook, run by Claude Code headless (`claude -p`) in the GitHub Actions workflow `.github/workflows/pipeline-api.yml`, billed to an Anthropic API account instead of the Claude subscription. The workflow sets `PAPERBOY_MODE=api`, so the run takes its three API forms: the budget gate in place of the usage gate, a take for the active fields only (`--per-field` quick explainers for each field a paying subscriber picked, full explainers only from those fields), and a cost record written by the workflow after Claude Code exits. Two API runs never overlap (the workflow's `concurrency` group). The job can read this repo but cannot push to it.

**It is off.** The workflow only runs when started by hand, and it fails at its first steps until the setup below exists. The schedule is in the file as a commented block; remove the `#` in front of its three lines to turn it on.

**One-time setup, in this repo's Settings > Secrets and variables > Actions:**

- Secret `ANTHROPIC_API_KEY`: a Claude API key from the Claude Console. Make it in a workspace of its own and give that workspace a monthly spend limit; the default workspace cannot have one.
- Secret `PAPERBOY_CONTENT_TOKEN`: a fine-grained personal access token with repository access to `NtrpyDev/paperboy-content` only and the Contents permission set to read and write. The run pushes the backlog, claims, feed, and cost records with it.
- Variable `PAPERBOY_FIELDS_URL`: the worker's `GET /v1/active-fields` address.
- Variable `PAPERBOY_MONTHLY_BUDGET_USD`: the month's API budget in dollars.

**Start one run:** the repo's Actions tab, "Pipeline on the API account", "Run workflow". Its three inputs are the quick explainers per active field (default 2), the full explainers for the run (default 1), and the run's hard spend cap in dollars (default 20), which Claude Code enforces as `--max-budget-usd` on its own cost estimate, so a run can end a little over it. A scheduled run uses the defaults.

**The budget gate and pacing:** before Claude Code starts, and at every gate in the runbook, `paperboy-pipeline budget-gate` sums this month's recorded spend from `CONTENT/state/cost/<YYYY-MM>.jsonl` and stops the run at the pace limit: with B the budget and f the fraction of the calendar month elapsed (UTC), the smaller of B and B times f plus a head start of 10 percent of B. A fresh month can spend 10 percent at once; halfway through, the limit is 60 percent; at the end, all of B. Change the head start with `--head-start` or turn pacing off with `--no-pace`, in step 1's API form and in the workflow's "Budget gate" step alike. It stops the run when a cost record cannot be read.

**Cost records:** after every run that started Claude Code, finished or not, the workflow runs `paperboy-pipeline record-cost`, which appends one line to `state/cost/<YYYY-MM>.jsonl` (`schema/cost-record.schema.json`): Claude Code's estimated total cost and tokens per model, the papers taken and pages built by kind and field, and how many tool calls the permission rules denied. A run that was cut off is marked incomplete and counts its whole cap against the budget, because its real spend is unknown. These are Claude Code's own estimates; the Console's billing is the authority.

**Inspect a run:** open the run in the Actions tab. "Show the run's report" prints the step 8 report; "Record what the run cost" prints the cost line. The full transcript is not kept.

**What is not verified yet:** no run has been made on an API key, because no API account exists. Unchecked until the first run: that the allow list covers every command the runbook and agents use (a `permission_denials` count above 0 in the cost record names a gap), that `ubuntu-24.04`'s Google Chrome passes the render check, and that the cost and token fields arrive as the Claude Code docs describe.
