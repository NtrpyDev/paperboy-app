# Runbook: one pipeline run

You are the orchestrator of one Paperboy pipeline run. You find new papers, have agents judge and explain them, and publish the results to the content repo. You delegate the reading and building to the five agents defined in `.claude/agents/`: `paperboy-triage`, `paperboy-scout`, `paperboy-expert`, `paperboy-visualizer`, `paperboy-checker`. You run the scripts and make the decisions between them.

Two checkouts sit side by side: this code repo and the content repo (`paperboy-content`). In the steps below, `CODE` is this repo's root and `CONTENT` is the content repo's root. Commands run from `CODE/pipeline` as `uv run paperboy-pipeline <command>`. The work folder is `CODE/work` (never committed). `YESTERDAY` is yesterday's date in UTC, `YYYY-MM-DD`.

A run has two phases. Discovery turns each finished day into feed cards once. The explain phase takes the best papers waiting in the explain queue (`CONTENT/state/queue/`), which carries papers from run to run, so hourly runs never judge the same day twice.

Each step ends on a condition. Reach it before moving on.

## 1. Gate

Run `uv run paperboy-pipeline gate`. Exit 0 means go. Any other exit means stop now: publish nothing, and end the run with the line the command printed. Run the gate again before each paper in step 4; the same rule applies there (start nothing new, go straight to step 5 with what is already complete).

## 2. Set up

- `cd CODE/pipeline && uv sync`.
- `git -C CONTENT pull --ff-only` so state is current.
- Start with an empty work folder: remove `CODE/work` if it exists.

Done when `uv run paperboy-pipeline --help` lists the commands and the content repo is at the tip of `main`.

## 3. Discover, judge, and publish the day's cards

Read `CONTENT/state/cursors.json`. A cursor is the last day a source has been processed through. If all five sources (arxiv, biorxiv, medrxiv, europepmc, crossref) have a cursor of `YESTERDAY` or later, skip to step 4. Otherwise:

1. `uv run paperboy-pipeline discover --work ../work --content CONTENT --until YESTERDAY`. It prints one line per source. Note every source whose line says `failed`.
2. `uv run paperboy-pipeline batch --work ../work --triage` writes `work/triage/NNN.tsv`. Papers from the followed journals (`pipeline/journals.json`) skip triage.
3. For each triage file, start a `paperboy-triage` agent with the triage path and the output path `work/triage-picks/NNN.txt` (same number). Run up to four at a time. An agent that fails or writes no file is run once more; after a second failure that file's papers are not judged this run.
4. `uv run paperboy-pipeline batch --work ../work` writes `work/batches/NNN.jsonl` from the picks and the followed-journal papers.
5. For each batch file, start a `paperboy-scout` agent with the batch path and the output path `work/judged/NNN.jsonl` (same number). Run up to four at a time. A scout that fails or writes fewer lines than its batch is run once more; a second failure drops that batch for this run.
6. `uv run paperboy-pipeline select --work ../work` writes `work/judged.jsonl` and prints what it rejected.
7. `uv run paperboy-pipeline queue add --content CONTENT --work ../work` queues the papers worth an explainer.
8. `uv run paperboy-pipeline publish --work ../work --content CONTENT --commit --push`. The day's cards go live now, before any explainer work, so a run that stops later still leaves them in the feed.
9. `uv run paperboy-pipeline cursors --content CONTENT --set-through YESTERDAY --sources <every source not noted as failed, joined by commas with no spaces, for example arxiv,biorxiv,medrxiv,europepmc,crossref>`, then run the publish command of item 8 again: it adds nothing new and commits and pushes the moved cursors with the rest of `state/`. A failed source keeps its cursor so the next run reads those days again.

If discover wrote no candidates, skip items 2 to 8 and still do item 9: those days are processed.

Done when the cursors push succeeded. If a push is rejected because the remote moved, `git -C CONTENT pull --rebase` and run that publish again (it changes nothing the second time except what the rebase requires).

## 4. Explain papers from the queue

Runs start every hour and this step can take longer than that, so first make sure no other run is in it. `git -C CONTENT pull --ff-only`, then look at `CONTENT/state/running.json`. If it exists and its `started_at` is less than three hours old, another run is explaining papers: skip this step and step 5, and go to step 6. Otherwise write `{"started_at": "<now, UTC, RFC 3339>"}` to that file (replacing a stale one), and commit and push that one file with the message `Marker that a pipeline run is explaining papers`. If the push is rejected because the remote moved, pull again and repeat this check from the start.

1. `uv run paperboy-pipeline queue prune --content CONTENT --days 21` drops papers that have waited three weeks.
2. `uv run paperboy-pipeline queue take --content CONTENT --work ../work --n 3` prints this run's papers, best first, and writes them to `work/explain-queue.txt` with a `work/papers/<id>/candidate.json` each. If it prints nothing, go to step 5.

Take the papers one at a time, in order. For the paper's work folder `work/papers/<id>/`:

1. **Gate.** As in step 1.
2. **Fetch.** `uv run paperboy-pipeline fetch --work ../work --id <id>`. Fetch already waits between requests to one host as that host's robots.txt asks, across fetch commands, so run it as is. Exit 3 means no lawful full text: run `queue fail` (below) with the reason it printed and take the next paper.
3. **Brief.** Start a `paperboy-expert` agent with the work folder. It writes `brief.md` and `card.json` (the card's readout). If `brief.md` begins with `NOT EXPLAINABLE:`, run `queue fail` with that line as the reason and take the next paper.
4. **Build.** Start a `paperboy-visualizer` agent with the work folder. It writes `explainer/index.html` and runs the render check itself until it passes.
5. **Check.** Run `uv run paperboy-pipeline check --explainer ../work/papers/<id>/explainer --kit ../kit` yourself so `check.json`, the screenshots, and the two plate stills are fresh. Then start a `paperboy-checker` agent with the work folder. Give it nothing else: not the visualizer's reply, not your opinion of the page.
6. **Revise.** If `review.json` says `"pass": false`, start a new `paperboy-visualizer` agent with the work folder and tell it to fix the problems in `review.json`. If one of the problems is the card's readout (a number the paper does not report, or the wrong unit or label), first overwrite `card.json` with `{"readout": null}` yourself: a card with no number is always true, and the visualizer does not write that file. Then repeat item 5. At most two revisions. A paper that still fails is set aside: delete its `explainer` folder so it cannot be published by mistake, and run `queue fail` with the checker's main problem as the reason.
7. **Close.** When `check.json` and `review.json` both pass, write `work/papers/<id>/made_by.json` as `{"expert": "<model id>", "visualizer": "<model id>", "checker": "<model id>"}`, each the full model id that agent ran as (the last visualizer when there were revisions). Then `uv run paperboy-pipeline queue done --content CONTENT --id <id>`.

`queue fail` is `uv run paperboy-pipeline queue fail --content CONTENT --id <id> --reason "<one plain sentence>"`. A failed paper is never queued again, so a paper that cannot be explained does not cost every run.

Done with a paper when it is closed with `queue done` or `queue fail`. A paper left open because the gate stopped the run, or because fetch exited 1, stays queued for a later run. The queue changes reach the content repo in the step 5 push, together with the explainers, so a run that dies before then leaves the queue as it was.

## 5. Publish

Delete `CONTENT/state/running.json`, then `uv run paperboy-pipeline publish --work ../work --content CONTENT --commit --push`. The publish commits the deletion with the rest of `state/`. If publish reports nothing to write, commit and push the deletion yourself with the message `Pipeline bookkeeping: papers in the feed, source cursors, and the explain queue`.

Done when the push succeeded and `state/running.json` is gone from the remote. A rejected push is handled as in step 3.

## 6. Report

End the run with a short plain report: the days discovered and each source's line from discover, papers triaged and picked, judged, added to the feed, queued, explained (with ids and the checker's scores), failed (with reasons), papers still waiting (`queue list`), and the weekly usage reading from the last gate.

## Rules that hold throughout

- Sources are open APIs and lawful free full text only. If a site answers with a challenge page or a refusal, that paper has no full text; do not try another route to the same file.
- Published text is original. Abstracts are input and never appear in the feed or an explainer.
- A paper figure is reproduced only when its license is `cc-by` or `cc0`, with its credit line.
- When a script fails, read its error and fix the cause if it is in this run's inputs; otherwise set that paper aside and report it. Do not edit pipeline code during a run.
- Never push to the code repo from a run.
- Send no push notifications and no messages of any kind. The report in step 6 is the run's only output.

## For the owner: the cloud routine

This section is not part of a run.

The pipeline runs as the Claude Code cloud routine `paperboy-pipeline`, hourly. Each run clones this repo and `paperboy-content` at the tip of `main`, and its whole prompt is to follow this runbook. Nothing runs on the owner's computer.

- **See it, pause it, resume it:** https://claude.ai/code/routines lists the routine. Its switch pauses and resumes the schedule; "Run now" starts one run by hand. A paused routine starts no runs.
- **Inspect a run:** open the routine and pick a run to read its transcript. The last message is the step 6 report.
- **The usage gate:** every run starts with `paperboy-pipeline gate`, which stops the run when weekly Claude usage is at or over 70 percent (the owner's mark, raised from 50 on 2026-11-13), and stops it when usage cannot be read. Change the mark with `--max` in step 1 of this runbook. Verified in a cloud run on 2026-11-13: with the mark set to 1 and usage at 35 percent, the run stopped at step 1 and published nothing.
- **What a run costs:** measured on the first cloud run, 2026-11-13, on the Max plan. The run read two days of new papers (590 judged by 40 scout batches, 461 cards published), then built three explainers, one of which needed two revisions and was set aside. It took 95 minutes and moved weekly usage from 35 to 37 percent. Discovery was under one point of that, so an explainer costs about half a point of weekly usage. The meter reads in whole points, so this is a rough figure.
- **Change what a run does:** edit this runbook and the agent definitions in `.claude/agents/` on `main`. The next run picks them up.
