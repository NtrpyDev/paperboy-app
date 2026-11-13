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

Each command is one module in `src/paperboy_pipeline/commands/` that exposes `register(subparsers)`. The record shapes the commands pass to each other are JSON schemas in the repo's `schema/` folder; load them with `paperboy_pipeline.schemas`. Its `errors()` also applies the one rule a schema cannot state: a `hook_turn` must be the hook's closing clause (an exact suffix of `hook` that starts at a word and is not the whole hook). Paper ids come from `paperboy_pipeline.ids`.

## The work folder

Commands read and write one work folder (never committed):

```
work/
  candidates.jsonl                 discover writes; one Candidate per line
  triage/NNN.tsv                   batch --triage writes; one title line per paper
  triage-picks/NNN.txt             the triage agent writes; picked ids, one per line
  batches/NNN.jsonl                batch writes; the scout's input
  judged/NNN.jsonl                 the scout writes; one Judged per line
  judged.jsonl                     select writes; queue take appends the papers it takes
  explain-queue.txt                queue take writes; this run's papers to explain, best first
  papers/<paper id>/
    candidate.json                 queue take writes; the paper's Judged record
    fulltext.md  source.json       fetch writes
    brief.md                       the expert writes
    card.json                      the expert writes: {"readout": {...} | null} (schema/card.schema.json)
    explainer/index.html           the visualizer writes
    explainer/hero.webp            check writes; the day plate
    explainer/hero-night.webp      check writes; the night plate
    check.json  shots/             check writes
    review.json                    the checker writes: {"pass": true|false, "problems": [...]}
    made_by.json                   the orchestrator writes: {"expert", "visualizer", "checker"} model ids
```

`publish` takes the work folder and a content repo checkout. A paper is published with its explainer only when `check.json` and `review.json` both pass; otherwise it is published as a short card.

## publish

```
paperboy-pipeline publish --work WORK --content CONTENT_REPO [--commit] [--push] [--now RFC3339]
```

Reads every Judged record in `WORK/judged.jsonl` and writes it into the content repo checkout at `CONTENT_REPO`, in file order.

- **Explained card**: when `WORK/papers/<id>/explainer/index.html`, `explainer/hero.webp`, and `explainer/hero-night.webp` exist and both `check.json` and `review.json` hold `"pass": true`, publish writes `papers/<id>/index.html`, `hero.webp`, `hero-night.webp`, and `meta.json`, and the feed item gets `has_explainer: true`, `explainer: "papers/<id>/"`, and `hero`: the day plate's path and pixel size, `night` with the night plate's, and `kind` and `to_scale` copied from the hero in `check.json` when it has them.
- **Short card**: otherwise only `papers/<id>/meta.json` is written and the item has `has_explainer: false`.
- **Card text**: `hook_turn` and `readout` are copied from the Judged record (the scout writes them) to the feed item and `meta.json` when the record has them, for short and explained cards alike. Without them the fields are left out. On an explained card, `WORK/papers/<id>/card.json`, when it exists, settles the readout: an object replaces the scout's and `null` removes it, in `meta.json` and in the feed item (or its `upgrades.json` entry, see Upgrades). An invalid `card.json` exits with status 1 and writes nothing.
- **Kit version**: an explained paper's `meta.json` `kit` is `page.kit` from `check.json`, the kit version the page loads. A passing `check.json` without it exits with status 1 and writes nothing.
- **Who made it**: an explained paper's `meta.json` gets `made_by` from `WORK/papers/<id>/made_by.json` (`{"expert", "visualizer", "checker"}`, each a model id) when that file exists. Without the file the field is left out.

What it writes in the content repo (schemas in `schema/`):

```
feed/v1/head.json             Head: chunk count, total items, updated time, kit 1, min_app 1 (nothing reads kit yet)
feed/v1/chunks/000001.json    Chunk: up to 40 items, oldest first
feed/v1/upgrades.json         Upgrades: explainers added to items in closed chunks
papers/<id>/meta.json         PaperMeta (plus index.html, hero.webp, and hero-night.webp when explained)
state/seen/<YYYY-MM>.jsonl    Seen: one line per paper in the feed, by the month it was added
```

Publish never writes `state/cursors.json` (the `cursors` command does) or `state/queue/` (the `queue` command does), but `--commit` commits whatever changed under `state/`, so cursor moves, queue additions, and queue removals go out in the state commit.

Rules:

- **Chunks.** New items append to the open chunk, the highest numbered chunk while it holds fewer than 40 items. When it is full the next item starts a new chunk. A full chunk is closed and is never written again.
- **No duplicates.** A paper whose id, DOI, arXiv id, or title key matches a line in `state/seen/` is not added again. Discover reads the same files.
- **Upgrades.** When a paper already in the feed as a short card now has a passing explainer, publish writes its explainer files and an updated `meta.json`. If the item is in the open chunk, it is updated in place. If its chunk is closed, the chunk is left alone and the paper is added to `feed/v1/upgrades.json` as `{"explainer", "hero", "explained_at"}`, plus `"readout"` (an object, or `null` to remove the card's) when the paper has a `card.json`; the app merges that entry over the item.
- **All or nothing.** Every file is checked against its schema before anything is written. Invalid input or invalid output exits with status 1 and leaves the repo unchanged.
- **Reruns change nothing.** JSON is written with sorted keys, two-space indent, and a trailing newline, and a file is only written when its bytes change. The head is rewritten only in a run that changes something else. A second run with the same work folder leaves the tree byte-identical.
- **`--now`** fixes the clock (for tests). Without it the current UTC time is used.
- **`--commit`** makes one commit per changed top-level folder, each containing only that folder, so each folder's last commit subject describes it:
  - `feed/`: "Feed head and chunks the app reads"
  - `papers/`: "Published papers: explainer page, card image, and record for each"
  - `state/`: "Pipeline bookkeeping: papers in the feed, source cursors, and the explain queue"

  Other changes in the checkout are left uncommitted. A run that changes nothing makes no commit.
- **`--push`** runs `git push origin main`. It never forces.

## discover

```
paperboy-pipeline discover --work WORK --content CONTENT_REPO [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--sources arxiv,biorxiv,medrxiv,europepmc,crossref] [--limit N]
```

Lists newly released papers and writes them to `WORK/candidates.jsonl`, one Candidate per line (`schema/candidate.schema.json`), newest first. Prints one line per source: `<source>: N found, N written, N dropped without abstract`, or `<source>: skipped, processed through <date>`, or `<source>: failed: <error>`.

- **Window.** Whole days, both ends inclusive, UTC. It ends on `--until`, by default yesterday. It starts on `--since` when given; otherwise the day after the source's cursor in `CONTENT_REPO/state/cursors.json` (the last day already processed, see `cursors`); otherwise the day before `--until`, so a source without a cursor, or a checkout without `state/`, reads the last two finished days. A source whose cursor is already `--until` or later is skipped. `--since` after `--until` exits with status 2.
- **Sources.** One adapter per source in `src/paperboy_pipeline/sources/`, each a function `fetch(since, until, limit, http)` that puts the window into its query on the date that source uses to decide newness:
  - arXiv: OAI-PMH at `https://oaipmh.arxiv.org/oai`, format `arXivRaw` (the only arXiv interface that states the license), `from` and `until` on the record datestamp (day granularity). All categories. A paper counts as new when its first version is at most 7 days older than the start date; older records that changed in the window (revisions, added DOIs) are context only.
  - bioRxiv and medRxiv: `https://api.biorxiv.org/details/<server>/<from>/<to>/<cursor>/json`. Only first versions are new; later versions are context only.
  - Europe PMC: two REST searches, both with a DOI and first published in the window (`FIRST_PDATE`), newest first: `OPEN_ACCESS:y` from anywhere, and every record from the followed journals (`ISSN:"..." OR ...`) whether or not it is open access, so a paywalled paper still arrives with its PubMed abstract. A paper both return is kept once. `fulltext.available` is true only for an open access record with a full text id. Records marked as preprints keep status `preprint`.
  - Crossref: journal articles from the followed journals created in the window (`from-created-date`, `until-created-date`), newest first, public pool (no mailto). Crossref ORs repeated `issn:` filters and ANDs different ones.
- **Followed journals.** `pipeline/journals.json` lists the peer-reviewed journals the feed follows as `{"title", "issn": [...], "field_hint"}`. Every ISSN was looked up from Crossref's journals endpoint on 2026-11-13 (print and electronic ISSNs only). The ISSNs are split across requests, at most 40 per request and never splitting a journal, so each URL stays under 2,000 characters. A Crossref or Europe PMC record whose ISSN belongs to a followed journal takes that journal's `title` as its venue, so `batch` can recognize it.
- **No abstract, no candidate.** After duplicates are merged, a paper that still has no abstract is dropped and counted in its source's line: an honest summary cannot be written from a title.
- **Duplicates.** Records of one paper (same DOI, arXiv id, or title key; or a journal DOI the preprint server names) become one candidate. A journal record supplies the metadata and status; a preprint lends its full text pointer and that text's license when the journal record has none. See `src/paperboy_pipeline/dedupe.py`.
- **Already published.** A paper whose id, DOI, arXiv id, or title key matches a line in `CONTENT_REPO/state/seen/` is skipped. Discover never writes to the content repo.
- **Requests.** One shared client with User-Agent `paperboy-pipeline/0.1 (+https://github.com/NtrpyDev/paperboy-app)` and no email or other personal detail. arXiv requests start at least 3 seconds apart, Crossref requests at least 1 second apart. 429, 5xx, and connection errors are retried up to 4 times with doubling backoff, waiting at least as long as `Retry-After` asks.
- **Abstracts** are pipeline input only. JATS and HTML tags are removed; LaTeX is kept as written.
- **Exit status** is 1 when a source failed after retries or a record did not match the schema. The candidates from the other sources are still written.

Live smoke run (not part of the test suite; makes one request per source):

```
cd pipeline
mkdir -p work/smoke-content
uv run paperboy-pipeline discover --work work/smoke --content work/smoke-content --limit 5
```

Every source should print `5 found`; Crossref may drop some of its five for having no abstract. The empty content folder means nothing is seen yet and the window is the last two finished days. `work/` is ignored by git.

## check

The render check. It loads one explainer in a headless Chromium-family browser at phone size and fails it if it breaks the explainer contract (`EXPLAINER-CONTRACT.md`).

```
cd pipeline && uv run paperboy-pipeline check --explainer work/papers/<paper id>/explainer --kit ../kit [--out DIR]
```

- `--explainer` is the folder holding `index.html`. `--kit` is the repo's `kit` folder. `--out` defaults to the explainer's parent.
- It serves the explainer at `/papers/x/` and the kit at `/kit/` from a local server on a free port, then loads the page at 390 by 844 px, device scale factor 2, four times: light, dark, and with reduced motion in light and in dark. The color scheme and motion setting are the browser's emulated `prefers-color-scheme` and `prefers-reduced-motion`, so the check works with any kit version. Each time it waits for `data-pb-ready`, scrolls through the page once, and lets animations run for 1.5 seconds before measuring and capturing.
- It writes `check.json` and `shots/` in the out folder, and the two plate stills, the hero `.pb-stage` at rest, at most 1200 px wide: `explainer/hero.webp` (the day plate, from the light capture with reduced motion) and `explainer/hero-night.webp` (the night plate, from the dark capture with reduced motion). Under kit v1 the stage is always dark, so the two look alike.
- Exit code: 0 pass, 1 fail, 2 tool error (no `index.html`, no kit version folder such as `v1`, no browser, or the browser would not start). On a tool error it writes no `check.json`.

Browser: `PAPERBOY_CHROME` (a path or a name on PATH), else the first of `google-chrome`, `chromium`, `chromium-browser`, `brave` on PATH. Nothing is downloaded. It always runs headless with `--no-sandbox` (needed when running as root, as in the cloud routine) and a throwaway profile. The tests skip when no browser is found.

`check.json`:

```
{
  "pass": false,
  "checked_at": "2026-11-13T03:37:00Z",
  "problems": [{"rule": "overflow-x", "detail": "...", "theme": "light"}],
  "shots": ["shots/light-01.png", "shots/dark-01.png", "shots/still-01.png", "shots/still-dark-01.png"],
  "hero": {
    "path": "explainer/hero.webp", "width": 700, "height": 526,
    "night": {"path": "explainer/hero-night.webp", "width": 700, "height": 526},
    "kind": "illustration", "to_scale": false
  },
  "page": {"height_px": 5128, "figures": 2, "data_figures": 2, "kit": 1}
}
```

`rule` is one of the ids in `EXPLAINER-CONTRACT.md`. `theme` is `light`, `dark`, `still` (light with reduced motion), or `still-dark` (dark with reduced motion); rules about the document itself are reported once, under `light`, and the hero is captured under `still` and `still-dark`. Shots are the full page cut into pieces at most 2400 px tall (`light-01.png`, `light-02.png`, ...). `hero` is `null` when either plate still could not be captured. `kind` is the hero stage's `data-kind` when it is `data` or `illustration`; `to_scale` is present for an illustration and true only with `data-scale="true"`. `page.kit` is the kit version N of the page's `/kit/v<N>/` paths, `null` when they do not come from exactly one version.

## fetch

`paperboy-pipeline fetch --work WORK --id PAPER_ID` reads `WORK/papers/<id>/candidate.json` and saves the paper's free full text as `fulltext.md` (title, authors, abstract, sections in order, LaTeX math, Markdown tables, a Figures list of captions, footnotes, and a reference count) plus `source.json` (`available`, `url`, `kind`, `license`, `retrieved_at`, `chars`, `sections`).

Routes by `fulltext.kind`:

- `arxiv_html`: `https://arxiv.org/html/<id>`. A paper with no HTML rendering is unavailable; the PDF is never parsed.
- `biorxiv` (bioRxiv and medRxiv): the JATS XML the bioRxiv API lists as `jatsxml` (looked up by DOI when the candidate gives no `.xml` link). Equations and tables that the XML holds only as images are marked in place, not transcribed.
- `europepmc`: `https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/fullTextXML` (the PMCID is found by DOI when the candidate gives none).

Exit codes: 0 fetched; 3 no lawful full text is reachable (a missing rendering, a 404, JATS XML with front matter only, a 403, or a bot challenge page, which is never bypassed): `source.json` then holds `"available": false` and the reason, and no `fulltext.md` is left; 1 a real error (bad candidate, a server that kept failing).

Requests send only the User-Agent `paperboy-pipeline/0.1 (+https://github.com/NtrpyDev/paperboy-app)`, retry 429 and 5xx with backoff and Retry-After, and wait between requests to one host for the Crawl-delay its robots.txt sets (arxiv.org 15 s, biorxiv.org and medrxiv.org 7 s, ebi.ac.uk 10 s). The last request time per host is kept in `WORK/.fetch-hosts/` so the wait holds across fetch commands.

Live smoke run (network; one paper per source, about a minute):

```
cd pipeline
WORK=$(mktemp -d)
uv run python - "$WORK" <<'PY'
import json, sys
from pathlib import Path
base = dict(doi=None, arxiv_id=None, title="smoke", authors=[], abstract="", published="2026-11-10",
            status="preprint", license=None, categories=[])
for r in [
    dict(base, id="arxiv-2611.14797", arxiv_id="2611.14797", venue="arXiv", source="arxiv",
         url="https://arxiv.org/abs/2611.14797",
         fulltext={"available": True, "kind": "arxiv_html", "url": "https://arxiv.org/html/2611.14797"}),
    dict(base, id="doi-10.64898-2026.10.30.763149", doi="10.64898/2026.10.30.763149", venue="bioRxiv",
         source="biorxiv", url="https://www.biorxiv.org/content/10.64898/2026.10.30.763149v1",
         fulltext={"available": True, "kind": "biorxiv", "url": None}),
    dict(base, id="doi-10.64898-2026.10.30.26366919", doi="10.64898/2026.10.30.26366919", venue="medRxiv",
         source="medrxiv", url="https://www.medrxiv.org/content/10.64898/2026.10.30.26366919v1",
         fulltext={"available": True, "kind": "biorxiv", "url": None}),
    dict(base, id="doi-10.7554-elife.102635", doi="10.7554/eLife.102635", venue="eLife", status="peer_reviewed",
         source="europepmc", url="https://doi.org/10.7554/eLife.102635",
         fulltext={"available": True, "kind": "europepmc", "url": "https://europepmc.org/articles/PMC13727076"}),
]:
    folder = Path(sys.argv[1]) / "papers" / r["id"]
    folder.mkdir(parents=True)
    (folder / "candidate.json").write_text(json.dumps(r))
PY
for id in arxiv-2611.14797 doi-10.64898-2026.10.30.763149 doi-10.64898-2026.10.30.26366919 doi-10.7554-elife.102635; do
  uv run paperboy-pipeline fetch --work "$WORK" --id "$id"
done
```

Each line reports the characters, section count, and license; read `$WORK/papers/*/fulltext.md` to judge the result.

## batch

```
paperboy-pipeline batch --work WORK --triage
paperboy-pipeline batch --work WORK [--size 15]
paperboy-pipeline batch --work WORK --all [--size 15]
```

Judging every abstract with a model is wasteful, so judging starts with titles.

- **`--triage`** writes `WORK/triage/NNN.tsv`, at most 150 lines each and split evenly (so no file is a short tail), one paper per line: `id`, `source`, `venue`, the categories joined by a space, and `title`, separated by tabs, with any tab or line break inside a field turned into a space. A `paperboy-triage` agent reads one file and writes the ids worth a closer look to `WORK/triage-picks/NNN.txt`, at most 15 percent of its lines.
- **Followed journals skip triage.** A paper with source `crossref` or `europepmc` whose venue is a `title` in `pipeline/journals.json` is never put in a triage file; it goes straight to the abstract batches.
- **Plain `batch`** writes `WORK/batches/NNN.jsonl`, `--size` candidates each (default 15): the picked ids plus the followed-journal papers, in `candidates.jsonl` order. Without `WORK/triage-picks/` it exits with status 1 and writes nothing. Its JSON summary lists `triage_files_without_picks`, the triage files no agent answered.
- **`--all`** batches every candidate without triage.

## select

```
paperboy-pipeline select --work WORK [--floor 5.0] [--explain-floor 6.5]
```

Merges the scout's `WORK/judged/*.jsonl`, drops lines that are not valid Judged records (printed as `rejected_lines`), keeps the first record of each id, drops papers below `--floor`, and writes `WORK/judged.jsonl`. It sets `explain` to true on a paper worth an explainer: full text available, its `fulltext.kind` listed in `pipeline/config.json`, and significance at least `--explain-floor`. The default floor is defined once, in `src/paperboy_pipeline/explaining.py`, and `queue add` uses the same rule. Select does not choose which papers to explain this run; `queue take` does.

## cursors

```
paperboy-pipeline cursors --content CONTENT_REPO --set-through YYYY-MM-DD [--sources arxiv,biorxiv,medrxiv,europepmc,crossref]
```

A cursor is the last day (UTC) a source has been processed through: discovered, judged, and published. This command writes `CONTENT_REPO/state/cursors.json` (`{"v": 1, "cursors": {"<source>": "YYYY-MM-DD"}}`) for the named sources, all five by default. A cursor never moves backward: a date before the current cursor leaves it and prints `already through <date>`. It does not commit; `publish --commit` commits it with `state/`.

## queue

```
paperboy-pipeline queue add   --content CONTENT_REPO --work WORK [--explain-floor 6.5] [--kinds arxiv_html,europepmc]
paperboy-pipeline queue take  --content CONTENT_REPO --work WORK --n K
paperboy-pipeline queue done  --content CONTENT_REPO --id PAPER_ID
paperboy-pipeline queue fail  --content CONTENT_REPO --id PAPER_ID --reason TEXT
paperboy-pipeline queue prune --content CONTENT_REPO [--days 21]
paperboy-pipeline queue list  --content CONTENT_REPO
```

A paper worth an explainer waits in the content repo until a run gets to it, so the explain phase of each run takes the best papers found so far rather than only that hour's.

- **`add`** writes `CONTENT_REPO/state/queue/<id>.json` for every record in `WORK/judged.jsonl` with full text available, a `fulltext.kind` in the allowlist, and significance at least `--explain-floor`: the Judged record plus `"queued_at"` (UTC, RFC 3339). It never overwrites a waiting paper and never queues a paper listed in `state/queue-failed.jsonl`.
- **`take`** chooses the K best waiting papers, highest significance first, then newest `published`, then id, skipping failed ones. For each it writes `WORK/papers/<id>/candidate.json` and appends its record to `WORK/judged.jsonl` when that file does not hold it yet, so publish gives it its explainer. It prints the ids, one per line, and writes them to `WORK/explain-queue.txt`. Taking a paper leaves it in the queue until `done` or `fail`.
- **`done`** deletes the paper's queue file once its explainer is published. Exit 1 when it is not waiting.
- **`fail`** deletes the queue file and appends `{"id", "reason", "at"}` to `state/queue-failed.jsonl` (`schema/queue-failed.schema.json`), so a paper that cannot be explained is not retried forever.
- **`prune`** deletes queue files whose `queued_at` is more than `--days` days old.
- **`list`** prints the number of papers waiting, then the top ten as `significance`, `id`, `published`, `hook`, separated by tabs.

The queue commands only change files in the checkout; `publish --commit` commits them with `state/`.

**Full text kinds.** `pipeline/config.json` holds `explain_fulltext_kinds`, the full text kinds a paper may be explained from: `arxiv_html` and `europepmc`. The kind `biorxiv`, which covers both bioRxiv and medRxiv, is left out on purpose: bioRxiv's robots.txt (`https://www.biorxiv.org/robots.txt`, read 2026-11-13) disallows ClaudeBot, GPTBot, and CCBot by name, and the owner has not yet decided whether to fetch full text from bioRxiv and medRxiv. Their papers still become cards. `queue add --kinds` overrides the list for one call; `select` always reads the file.
