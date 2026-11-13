# Paperboy pipeline

Finds newly released papers and turns them into feed items and explainers in the content repo.

Run the tests:

```
cd pipeline && uv run pytest
```

Run a command:

```
cd pipeline && uv run paperboy-pipeline <command> --help
```

## How the parts fit

Each command is one module in `src/paperboy_pipeline/commands/` that exposes `register(subparsers)`. The record shapes the commands pass to each other are JSON schemas in the repo's `schema/` folder; load them with `paperboy_pipeline.schemas`. Paper ids come from `paperboy_pipeline.ids`.

## The work folder

Commands read and write one work folder (never committed):

```
work/
  candidates.jsonl                 discover writes; one Candidate per line
  judged.jsonl                     the scout writes; one Judged per line
  papers/<paper id>/
    candidate.json                 the paper's Judged record
    fulltext.md  source.json       fetch writes
    brief.md                       the expert writes
    explainer/index.html           the visualizer writes
    explainer/hero.webp            check writes
    check.json  shots/             check writes
    review.json                    the checker writes: {"pass": true|false, "problems": [...]}
```

`publish` takes the work folder and a content repo checkout. A paper is published with its explainer only when `check.json` and `review.json` both pass; otherwise it is published as a short card.
