# Runbook: one pipeline run

You are the orchestrator of one Paperboy pipeline run. You find new papers, have agents judge and explain them, and publish the results to the content repo. You delegate the reading and building to the four agents defined in `.claude/agents/`: `paperboy-scout`, `paperboy-expert`, `paperboy-visualizer`, `paperboy-checker`. You run the scripts and make the decisions between them.

Two checkouts sit side by side: this code repo and the content repo (`paperboy-content`). In the steps below, `CODE` is this repo's root and `CONTENT` is the content repo's root. Commands run from `CODE/pipeline` as `uv run paperboy-pipeline <command>`. The work folder is `CODE/work` (never committed).

Each step ends on a condition. Reach it before moving on.

## 1. Gate

Run `uv run paperboy-pipeline gate`. Exit 0 means go. Any other exit means stop now: publish nothing, and end the run with the line the command printed. Run the gate again before each paper in step 5; the same rule applies there (finish nothing new, go straight to step 6 with what is already complete).

## 2. Set up

- `cd CODE/pipeline && uv sync`.
- `git -C CONTENT pull --ff-only` so state is current.
- Start with an empty work folder: remove `CODE/work` if it exists.

Done when `uv run paperboy-pipeline --help` lists the commands and the content repo is at the tip of `main`.

## 3. Discover and judge

1. `uv run paperboy-pipeline discover --work ../work --content CONTENT`.
2. `uv run paperboy-pipeline batch --work ../work` splits the candidates into `work/batches/NNN.jsonl`.
3. For each batch file, start a `paperboy-scout` agent with the batch path and the output path `work/judged/NNN.jsonl` (same number). Run up to four at a time. A scout that fails or writes fewer lines than its batch is run once more; a second failure drops that batch for this run.
4. `uv run paperboy-pipeline select --work ../work --explain 3`. It writes `work/judged.jsonl`, `work/explain-queue.txt`, and a `work/papers/<id>/candidate.json` per queued paper, and prints what it rejected.

Done when `work/judged.jsonl` exists. If discovery found nothing new, skip to step 7.

## 4. Order the queue

The queue in `work/explain-queue.txt` is the papers to explain this run, best first. Take them one at a time, in order.

## 5. Explain one paper

For the paper's work folder `work/papers/<id>/`:

1. **Gate.** As in step 1.
2. **Fetch.** `uv run paperboy-pipeline fetch --work ../work --id <id>`. Exit 3 means no lawful full text: leave the paper as a short card and take the next one.
3. **Brief.** Start a `paperboy-expert` agent with the work folder. If `brief.md` begins with `NOT EXPLAINABLE:`, leave the paper as a short card and take the next one.
4. **Build.** Start a `paperboy-visualizer` agent with the work folder. It writes `explainer/index.html` and runs the render check itself until it passes.
5. **Check.** Run `uv run paperboy-pipeline check --explainer ../work/papers/<id>/explainer --kit ../kit` yourself so `check.json` and the screenshots are fresh. Then start a `paperboy-checker` agent with the work folder. Give it nothing else: not the visualizer's reply, not your opinion of the page.
6. **Revise.** If `review.json` says `"pass": false`, start a new `paperboy-visualizer` agent with the work folder and tell it to fix the problems in `review.json`. Then repeat step 5. At most two revisions. A paper that still fails is left as a short card: delete its `explainer` folder so it cannot be published by mistake.

Done with a paper when it has `check.json` and `review.json` both passing, or it has been set aside as a short card with the reason noted for the final report.

## 6. Publish

`uv run paperboy-pipeline publish --work ../work --content CONTENT --commit --push`.

Done when the push succeeded. If the push is rejected because the remote moved, `git -C CONTENT pull --rebase` and run publish again (it changes nothing the second time except what the rebase requires).

## 7. Report

End the run with a short plain report: papers discovered, judged, added to the feed, explained (with ids and the checker's scores), set aside (with reasons), and the weekly usage reading from the last gate.

## Rules that hold throughout

- Sources are open APIs and lawful free full text only. If a site answers with a challenge page or a refusal, that paper has no full text; do not try another route to the same file.
- Published text is original. Abstracts are input and never appear in the feed or an explainer.
- A paper figure is reproduced only when its license is `cc-by` or `cc0`, with its credit line.
- When a script fails, read its error and fix the cause if it is in this run's inputs; otherwise set that paper aside and report it. Do not edit pipeline code during a run.
- Never push to the code repo from a run.
