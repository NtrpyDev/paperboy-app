# Paperboy worker

The edge worker at https://paperboy.ntrpydev.workers.dev. It is the content base the app loads the feed and explainers from.

## What it serves

- `/` and other site pages: static assets from `../site`.
- `/kit/v1/*`, `/kit/v2/*`, and every later kit version: static assets, a copy of `../kit`. Old kit versions stay served.
- `/feed/*` and `/papers/*`: files from the R2 bucket `paperboy-content`. On a miss the worker fetches the file from `https://raw.githubusercontent.com/NtrpyDev/paperboy-content/main/<path>`, stores it in the bucket, and serves it. `/papers/<id>/` serves that folder's `index.html`.

The feed is in `feed/v2/`: `head.json`, `chunks/<6 digits>.json`, and `upgrades.json`. Each feed version has its own folder, `feed/v<N>/`, and a chunk is judged open or closed by the head in its own folder (`feed/v<N>/head.json`). `feed/v1/` is the feed published before every paper needed a page; when the feed restarted in `feed/v2/` it was left as a stub, a head with no chunks and `min_app` 2 so a 0.1.0 install shows its update cover, and its chunks are 404.

Files under `feed/` and `papers/` are either fixed or changing:

- Fixed: everything under `papers/`, and every closed chunk (a chunk lower than its folder's head's `chunk_count` that holds all 40 items). Stored once and served with `cache-control: public, max-age=31536000, immutable`.
- Changing: every `feed/v<N>/head.json`, the open chunk, and any other file under `feed/`. Fetched again when the stored copy is older than 60 seconds; if the content repo fails, the stored copy is served, and if the content repo no longer has the file, the stored copy is deleted and the answer is 404. Served with `cache-control: public, max-age=60`.

A chunk stored while it was open is fetched again after it closes, and keeps being refreshed until it holds 40 items, because the raw host caches files for up to five minutes and can hand out the copy from before the last items.

Every response from the bucket carries `x-paperboy-source: origin` (fetched from the content repo for this request) or `bucket` (read from the bucket). HTML from `papers/` carries the explainer content security policy. Files under `feed/` carry `access-control-allow-origin: *`.

Paths outside `feed/` and `papers/` that are not assets, and files the content repo does not have, are 404. A file the bucket does not have while the content repo is unreachable is 502.

## Commands

Run from this folder after `npm install`.

| Command | What it does |
| --- | --- |
| `npm test` | Assembles the assets and runs every worker test. |
| `npm run typecheck` | Regenerates the binding types and runs `tsc`. |
| `npm run build` | Assembles `public/` from `../site` and every kit version in `../kit`. |
| `npm run deploy` | Assembles the assets and deploys with wrangler. |

The tests come in two vitest projects. `handler` runs `src/handler.ts` inside the Workers runtime with a local bucket and a fake content repo. `assets` starts the whole worker with wrangler's test harness to check the static assets, because the Workers test pool does not serve them.
