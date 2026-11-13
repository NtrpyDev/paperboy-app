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

## publish

```
paperboy-pipeline publish --work WORK --content CONTENT_REPO [--commit] [--push] [--now RFC3339]
```

Reads every Judged record in `WORK/judged.jsonl` and writes it into the content repo checkout at `CONTENT_REPO`, in file order.

- **Explained card**: when `WORK/papers/<id>/explainer/index.html` and `explainer/hero.webp` exist and both `check.json` and `review.json` hold `"pass": true`, publish writes `papers/<id>/index.html`, `hero.webp`, and `meta.json`, and the feed item gets `has_explainer: true`, `explainer: "papers/<id>/"`, and `hero` with the image's pixel size.
- **Short card**: otherwise only `papers/<id>/meta.json` is written and the item has `has_explainer: false`.

What it writes in the content repo (schemas in `schema/`):

```
feed/v1/head.json             Head: chunk count, total items, updated time, kit 1, min_app 1
feed/v1/chunks/000001.json    Chunk: up to 40 items, oldest first
feed/v1/upgrades.json         Upgrades: explainers added to items in closed chunks
papers/<id>/meta.json         PaperMeta (plus index.html and hero.webp when explained)
state/seen/<YYYY-MM>.jsonl    Seen: one line per paper in the feed, by the month it was added
state/cursors.json            Cursors: per source, the newest published date publish has added
```

Rules:

- **Chunks.** New items append to the open chunk, the highest numbered chunk while it holds fewer than 40 items. When it is full the next item starts a new chunk. A full chunk is closed and is never written again.
- **No duplicates.** A paper whose id, DOI, arXiv id, or title key matches a line in `state/seen/` is not added again. Discover reads the same files.
- **Upgrades.** When a paper already in the feed as a short card now has a passing explainer, publish writes its explainer files and an updated `meta.json`. If the item is in the open chunk, it is updated in place. If its chunk is closed, the chunk is left alone and the paper is added to `feed/v1/upgrades.json` as `{"explainer", "hero", "explained_at"}`; the app merges that entry over the item.
- **Cursors.** Each source's cursor moves forward to the newest `published` date among the papers added from it. It never moves back.
- **All or nothing.** Every file is checked against its schema before anything is written. Invalid input or invalid output exits with status 1 and leaves the repo unchanged.
- **Reruns change nothing.** JSON is written with sorted keys, two-space indent, and a trailing newline, and a file is only written when its bytes change. The head is rewritten only in a run that changes something else. A second run with the same work folder leaves the tree byte-identical.
- **`--now`** fixes the clock (for tests). Without it the current UTC time is used.
- **`--commit`** makes one commit per changed top-level folder, each containing only that folder, so each folder's last commit subject describes it:
  - `feed/`: "Feed head and chunks the app reads"
  - `papers/`: "Published papers: explainer page, card image, and record for each"
  - `state/`: "Pipeline bookkeeping: which papers are already in the feed"

  Other changes in the checkout are left uncommitted. A run that changes nothing makes no commit.
- **`--push`** runs `git push origin main`. It never forces.

## check

The render check. It loads one explainer in a headless Chromium-family browser at phone size and fails it if it breaks the explainer contract (`EXPLAINER-CONTRACT.md`).

```
cd pipeline && uv run paperboy-pipeline check --explainer work/papers/<paper id>/explainer --kit ../kit [--out DIR]
```

- `--explainer` is the folder holding `index.html`. `--kit` is the repo's `kit` folder. `--out` defaults to the explainer's parent.
- It serves the explainer at `/papers/x/` and the kit at `/kit/` from a local server on a free port, then loads the page at 390 by 844 px, device scale factor 2, three times: light, dark, and light with reduced motion. Each time it waits for `data-pb-ready`, scrolls through the page once, and lets animations run for 1.5 seconds before measuring and capturing.
- It writes `check.json` and `shots/` in the out folder, and the hero still as `explainer/hero.webp` (from the dark capture, at most 1200 px wide).
- Exit code: 0 pass, 1 fail, 2 tool error (no `index.html`, no kit, no browser, or the browser would not start). On a tool error it writes no `check.json`.

Browser: `PAPERBOY_CHROME` (a path or a name on PATH), else the first of `google-chrome`, `chromium`, `chromium-browser`, `brave` on PATH. Nothing is downloaded. It always runs headless with `--no-sandbox` (needed when running as root, as in the cloud routine) and a throwaway profile. The tests skip when no browser is found.

`check.json`:

```
{
  "pass": false,
  "checked_at": "2026-11-13T03:37:00Z",
  "problems": [{"rule": "overflow-x", "detail": "...", "theme": "light"}],
  "shots": ["shots/light-01.png", "shots/dark-01.png", "shots/still-01.png"],
  "hero": {"path": "explainer/hero.webp", "width": 700, "height": 526},
  "page": {"height_px": 5128, "figures": 2, "data_figures": 2}
}
```

`rule` is one of the ids in `EXPLAINER-CONTRACT.md`. `theme` is `light`, `dark`, or `still`; rules about the document itself are reported once, under `light`, and the hero is checked under `dark`. Shots are the full page cut into pieces at most 2400 px tall (`light-01.png`, `light-02.png`, ...). `hero` is `null` when the hero could not be captured.
