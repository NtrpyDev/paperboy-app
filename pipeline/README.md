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
