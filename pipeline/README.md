# Paperboy pipeline

Finds newly released papers, keeps the best in a backlog, builds a page for each (a full explainer for the best few, a quick explainer for the rest), and puts each paper into the content repo's feed once its page passes. `RUNBOOK.md` is the order a run follows.

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
  take.json                        queue take writes: {"run", "full": [ids], "quick": [ids]}
  outcomes.jsonl                   queue fail and queue back append what they did, so publish can do it again
  papers/<paper id>/
    candidate.json                 queue take writes; the paper's Judged record
    fulltext.md  source.json       fetch writes (full explainers)
    brief.md                       the expert writes (full explainers)
    card.json                      the expert writes: {"readout": {...} | null} (schema/card.schema.json);
                                   the quick agent writes {"readout": null} when the scout's readout is not in the abstract
    explainer/index.html           the visualizer writes, or the quick agent (a quick explainer, QUICK.md)
    explainer/hero.webp            check writes; the day plate
    explainer/hero-night.webp      check writes; the night plate
    check.json  shots/             check writes
    review.json                    the checker writes (full explainers): {"pass": true|false, "problems": [...]}
    retry.md                       the orchestrator writes when a quick explainer failed: what to fix
    made_by.json                   the orchestrator writes: {"expert", "visualizer", "checker"} model ids,
                                   or {"quick"} for a quick explainer
```

`publish` takes the work folder and a content repo checkout. A paper enters the feed only with a passing page: a full explainer when `check.json` and `review.json` both pass, a quick explainer when `check.json` passes with the numbers check. A paper without one is not published and keeps waiting in the backlog.

## publish

```
paperboy-pipeline publish --work WORK --content CONTENT_REPO [--commit] [--push] [--now RFC3339]
```

Reads every Judged record in `WORK/judged.jsonl` and puts each paper that has a passing page into the content repo checkout at `CONTENT_REPO`. Records without one are skipped: no page, no card. The run's papers enter best first (significance, then newest `published`), alternating preprints and peer-reviewed papers one for one while both kinds are left, as `queue take` orders them; ties keep the order of `judged.jsonl`.

- **A passing page**: `WORK/papers/<id>/explainer/index.html`, `explainer/hero.webp`, and `explainer/hero-night.webp` exist, `check.json` holds `"pass": true`, and by the page's depth (`check.json` `page.depth`, `"full"` when absent):
  - **full explainer**: `review.json` holds `"pass": true`;
  - **quick explainer** (`"abstract"`): `page.numbers` shows the numbers check ran and found nothing outside the title and abstract. There is no `review.json`.
- **What it writes**: `papers/<id>/index.html`, `hero.webp`, `hero-night.webp`, and `meta.json`, and a feed item with `has_explainer: true`, `explainer: "papers/<id>/"`, `depth` (`"full"` or `"abstract"`), and `hero`: the day plate's path and pixel size, `night` with the night plate's, and `kind` and `to_scale` copied from the hero in `check.json` when it has them. The item is new, so it is written complete; no upgrade is needed.
- **Card text**: `hook_turn` and `readout` are copied from the Judged record (the scout writes them) to the feed item and `meta.json` when the record has them. Without them the fields are left out. `WORK/papers/<id>/card.json`, when it exists, settles the readout: an object replaces the scout's and `null` removes it. An invalid `card.json` exits with status 1 and writes nothing.
- **Paper record**: `meta.json` gets `kit` (`page.kit` from `check.json`, the kit version the page loads; a passing `check.json` without it exits with status 1 and writes nothing), `depth`, `check` (`{"render": check.json, "review": review.json or null}`), `fulltext_source` (the full text's address for a full explainer, `null` for a quick one), and `made_by` from `WORK/papers/<id>/made_by.json` when that file exists: `{"expert", "visualizer", "checker"}` or `{"quick"}`, each a model id.
- **The backlog**: every paper in `judged.jsonl` that is in the feed after the write leaves the backlog (`state/queue/<id>.json` and its claim are deleted). The run's `queue fail` and `queue back` in `WORK/outcomes.jsonl` are applied again (a no-op when they already were), and every claim the run took (`WORK/take.json`) is released, published or not.

What it writes in the content repo (schemas in `schema/`):

```
feed/v2/head.json             Head: chunk count, total items, updated time, kit 1, min_app 2 (nothing reads kit yet)
feed/v2/chunks/000001.json    Chunk: up to 40 items, oldest first
papers/<id>/                  index.html, hero.webp, hero-night.webp, meta.json (PaperMeta)
state/seen/<YYYY-MM>.jsonl    Seen: one line per paper in the feed, by the month it was added
```

Rules:

- **Chunks.** New items append to the open chunk, the highest numbered chunk while it holds fewer than 40 items. When it is full the next item starts a new chunk. A full chunk is closed and is never written again.
- **No duplicates.** A paper whose id, DOI, arXiv id, or title key matches a line in `state/seen/` is not added again, and its page is never replaced.
- **Older feeds.** A feed published before pages were required holds items without one. When such a paper has a passing page, publish writes its files and an updated `meta.json`; the item is updated in place in the open chunk, or, in a closed chunk, the paper is added to `feed/v2/upgrades.json` as `{"explainer", "hero", "explained_at"}` plus `"readout"` when it has a `card.json`. The current flow never needs this: `reset-feed` removes those items.
- **All or nothing.** Every file is checked against its schema before anything is written. Invalid input or invalid output exits with status 1 and leaves the repo unchanged.
- **Reruns change nothing.** JSON is written with sorted keys, two-space indent, and a trailing newline, and a file is only written when its bytes change. The head is rewritten only in a run that changes something else. A second run with the same work folder leaves the tree byte-identical.
- **`--now`** fixes the clock (for tests). Without it the current UTC time is used.
- **`--commit`** makes one commit per changed top-level folder, each containing only that folder, so each folder's last commit subject describes it:
  - `feed/`: "Feed head and chunks the app reads"
  - `papers/`: "Published papers: explainer page, card image, and record for each"
  - `state/`: "Pipeline bookkeeping: papers in the feed, source cursors, the backlog, and claims"

  Other changes in the checkout are left uncommitted. A run that changes nothing makes no commit. Every command that commits uses these subjects (`src/paperboy_pipeline/gitsync.py`).
- **`--push`** commits as `--commit` does and runs `git push origin HEAD:main`, never forced. When the push is rejected because the remote moved (another run pushed), it resets the checkout to the new `origin/main` and builds the whole change again from the work folder: the feed, the backlog removals, the outcomes, the claim releases. Up to five attempts. That is why the run must never change the content repo by hand: a reset would lose it.

## Pushing when runs overlap

Runs overlap, and two runs that append to the same open chunk or seen file cannot be merged by git. So nothing merges: `queue add --push`, `queue take --push`, `cursors --push`, and `publish --push` each build their change from their arguments, the work folder, and what is on `main`, commit it, and push; on a rejected push they reset to the new `origin/main` and build it again (`gitsync.sync`). `queue add`, `queue take`, and `cursors` start from `origin/main` and refuse a checkout holding changes that are not on it, so they never throw work away; `publish` starts from the checkout as the run left it, because the run's `queue fail` and `queue back` live there and in `WORK/outcomes.jsonl`.

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
- **Already judged.** A paper whose id, DOI, arXiv id, or title key matches a line in `CONTENT_REPO/state/seen/` (in the feed) or `CONTENT_REPO/state/queued/` (ever entered the backlog, whether it waits, aged out, or failed) is skipped, so no paper is judged twice. Discover never writes to the content repo.
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
cd pipeline && uv run paperboy-pipeline check --explainer work/papers/<paper id>/explainer --kit ../kit [--out DIR] [--candidate FILE]
```

- `--explainer` is the folder holding `index.html`. `--kit` is the repo's `kit` folder. `--out` defaults to the explainer's parent. `--candidate` is the paper's record for the numbers check, by default `candidate.json` in the out folder (the work folder, where `queue take` puts it); a `--candidate` that does not exist is a tool error.
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
  "page": {"height_px": 5128, "figures": 2, "data_figures": 2, "kit": 2, "depth": "abstract", "numbers": {"checked": 31, "not_in_abstract": 0}}
}
```

`rule` is one of the ids in `EXPLAINER-CONTRACT.md`. `theme` is `light`, `dark`, `still` (light with reduced motion), or `still-dark` (dark with reduced motion); rules about the document itself are reported once, under `light`, and the hero is captured under `still` and `still-dark`. Shots are the full page cut into pieces at most 2400 px tall (`light-01.png`, `light-02.png`, ...). `hero` is `null` when either plate still could not be captured. `kind` is the hero stage's `data-kind` when it is `data` or `illustration`; `to_scale` is present for an illustration and true only with `data-scale="true"`. `page.kit` is the kit version N of the page's `/kit/v<N>/` paths, `null` when they do not come from exactly one version. `page.depth` is what the page was built from, read from the `article.pb`'s `data-depth`: `"full"` (no mark, or `data-depth="full"`) or `"abstract"` (a quick explainer, see `QUICK.md`), `null` when the mark has any other value.

**The numbers check** (`src/paperboy_pipeline/numbers.py`) runs on a page with `page.depth` `"abstract"` when the record is at hand. The probe collects every text the page prints, labels drawn in SVG included, and text in a folded table, as runs tagged by where they sit: `scale` inside the kit's ruler and value line labels (`.pb-tick-label`, `.pb-value-label`), `slug` in the plate slug, `source` in the source footer, `text` elsewhere; `<sup>` and `<sub>` are kept as `^{...}` and `_{...}`, KaTeX math is read from its TeX source, and element edges are word edges. Every number in a `text` or `source` run must be printed in the title or abstract, or the page fails with `number-not-in-abstract`, which names each number and its run. `page.numbers` is `{"checked", "not_in_abstract"}`, or `null` when the check did not run (no record); publish will not take a quick explainer with `null` there.

- **A number on the page**: a digit run with thousands separators (comma or thin space), a decimal point, and a sign; ranges, plus or minus, and percent marks split into their numbers. Compared by value and magnitude, so `0.630` matches `0.63` and `-12` matches a "12 percent drop". A power of ten (`1.0×10⁻²¹`, `10<sup>6</sup>`) checks its mantissa and exponent, not the base 10. Rounding is a new number.
- **Exempt**: `scale` and `slug` runs; figure, plate, table, step, panel, section, and equation numbers (`Fig. 2`, `Step 3`); the paper's URL, DOI, arXiv id (and its version), and venue; its publication date written as a date (`November 12, 2026`, `12 Nov 2026`, `2026-11-12`, `Nov 12`) and its year anywhere; digits glued to a letter or joined to one by a hyphen (`Cas9`, `DR3`, `O2`, `COVID-19`, `v2`); `2D` and `3D`; subscripts; a power right after a letter (`m²`, `year⁻¹`).
- **The title and abstract are read generously**: every digit run, LaTeX as written (`$63{,}254$`, `$10^{-21}$`, `$4\pi$`), a superscript that tag stripping flattened (`× 106` also allows the exponent 6), and number words (`twenty-five`, `twofold`, `first`).
- **What the kit would need for more**: nothing. Tick labels are told apart by the `pb-tick-label` group `PB.ruler` already draws; a label an agent draws by hand with `label()` or a bare `<text>` is a claim and is checked.

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
paperboy-pipeline cursors --content CONTENT_REPO --set-through YYYY-MM-DD [--sources arxiv,biorxiv,medrxiv,europepmc,crossref] [--push]
```

A cursor is the last day (UTC) a source has been processed through: discovered, judged, and put in the backlog. This command writes `CONTENT_REPO/state/cursors.json` (`{"v": 1, "cursors": {"<source>": "YYYY-MM-DD"}}`) for the named sources, all five by default. A cursor never moves backward: a date before the current cursor leaves it and prints `already through <date>`. Without `--push` it does not commit. With `--push` it commits and pushes the cursors, starting from `origin/main` (see "Pushing when runs overlap"). Only `reset-feed` moves cursors back.

## queue

```
paperboy-pipeline queue add   --content CONTENT_REPO --work WORK [--explain-floor 6.5] [--kinds arxiv_html,europepmc] [--push]
paperboy-pipeline queue take  --content CONTENT_REPO --work WORK --full F --quick Q [--days D] [--claim-hours 3] [--run NAME] [--push]
paperboy-pipeline queue done  --content CONTENT_REPO --id PAPER_ID
paperboy-pipeline queue fail  --content CONTENT_REPO --work WORK --id PAPER_ID --reason TEXT
paperboy-pipeline queue back  --content CONTENT_REPO --work WORK --id PAPER_ID --reason TEXT
paperboy-pipeline queue prune --content CONTENT_REPO [--days 7] [--claim-hours 3]
paperboy-pipeline queue list  --content CONTENT_REPO
```

Every paper select keeps waits in the content repo's backlog until a run builds its page, so each run takes the best papers found so far rather than only that hour's. Every action takes `--now` to fix the clock (for tests). The files (`src/paperboy_pipeline/backlog.py`):

```
state/queue/<id>.json          QueueEntry: the Judged record, "queued_at", and "full_failed" once a full explainer failed
state/claims/<id>.json         Claim: {"id", "run", "page": "full" | "quick", "claimed_at"}
state/queued/<YYYY-MM>.jsonl   Queued: one line per paper that ever entered the backlog; discover skips these
state/queue-failed.jsonl       QueueFailed: papers that left the backlog without a page, never taken again
```

- **`add`** writes `state/queue/<id>.json` for every record in `WORK/judged.jsonl`, with the whole record (abstract included, so a later run can build its quick explainer) plus `"queued_at"`, and a line in `state/queued/`. `explain` is set true when the paper may get a full explainer: full text available, a `fulltext.kind` in the allowlist, and significance at least `--explain-floor`. It never overwrites a waiting paper, and never adds a paper that is in the feed, ever entered the backlog, or failed. It prints `{"added", "may_get_full", "already_known", "failed_before", "waiting"}`. An invalid record exits 1 and changes nothing. `--push` commits and pushes the change (see "Pushing when runs overlap").
- **`take`** first, with `--days`, takes out papers that waited more than D days, as `prune` does. Then it claims this run's papers among those waiting, not failed, not in the feed, and not claimed within `--claim-hours`: **full**, up to F papers with `explain` true; **quick**, up to Q of the rest. Each list is best first (highest significance, then newest `published`, then id) and alternates preprints and peer-reviewed papers one for one while both kinds wait, starting with the kind of the best paper. Each taken paper gets a claim (`page` says which kind of page), `WORK/papers/<id>/candidate.json`, and a line in `WORK/judged.jsonl` when that file does not hold it yet. It writes `WORK/take.json` and prints it with each paper's status, the number pruned, and the number waiting. Taking leaves the paper in the backlog; publish takes it out when it enters the feed. `--push` commits and pushes the claims, and takes again on a newer `main` when the push is rejected, so overlapping runs take different papers. `--run` names the run in its claims (default: the time and a random suffix).
- **`done`** takes a paper out of the backlog and releases its claim. Exit 1 when it is not waiting. Publish does this for every paper it adds.
- **`fail`** takes the paper out, releases its claim, and appends `{"id", "reason", "at"}` to `state/queue-failed.jsonl` (once per paper), so it never comes back. It notes the action in `WORK/outcomes.jsonl`.
- **`back`** is for a full explainer that failed or could not start: the paper waits again with `explain` false and the reason in `full_failed`, so it can only get a quick explainer, and its claim is released. Exit 1 when it is not waiting. It notes the action in `WORK/outcomes.jsonl`.
- **`prune`** takes out papers whose `queued_at` is more than `--days` days old, except papers claimed within `--claim-hours`, and deletes claims whose paper is no longer waiting. A pruned paper stays in `state/queued/`, so it is not judged again.
- **`list`** prints the number waiting, by status, how many may get a full explainer, and how many are claimed, then the top ten as `significance`, `id`, `published`, `full` or `quick`, `hook`, separated by tabs.

Without `--push`, `add` and `take` only change files in the checkout. `fail` and `back` never push; `publish --push` commits and pushes them with the run's pages.

**Full text kinds.** `pipeline/config.json` holds `explain_fulltext_kinds`, the full text kinds a paper may get a full explainer from: `arxiv_html` and `europepmc`. The kind `biorxiv`, which covers both bioRxiv and medRxiv, is left out on purpose: bioRxiv's robots.txt (`https://www.biorxiv.org/robots.txt`, read 2026-11-13) disallows ClaudeBot, GPTBot, and CCBot by name, and the owner has not yet decided whether to fetch full text from bioRxiv and medRxiv. Their papers get quick explainers. `queue add --kinds` overrides the list for one call; `select` always reads the file.

## gate

```
paperboy-pipeline gate [--max 70] [--head-start 10] [--no-pace] [--probe tools/usage-probe.sh] [--now RFC3339]
```

Runs the usage probe and exits 0 (go), 10 (stop: weekly usage is at or over the limit), or 11 (stop: usage could not be read). The limit is the pace limit `min(M, M * f + H)`, with M the mark (`--max`), H the head start (`--head-start`), and f the fraction of the seven day usage window elapsed, from the probe's `seven_day.resets_at` (Unix seconds, or an RFC 3339 time): `f = 1 - (resets_at - now) / 7 days`, held between 0 and 1. A missing or unreadable `resets_at` makes the limit the plain mark. `--no-pace` makes it the plain mark always. It prints one JSON line: `{"decision", "weekly_used_percentage", "max", "resets_at", "pace": {"week_elapsed", "head_start", "limit"}}` (`pace` is `null` with `--no-pace`).

## reset-feed

```
paperboy-pipeline reset-feed --content CONTENT_REPO --keep-explained --rewind-cursors-to YYYY-MM-DD [--yes] [--now RFC3339]
```

One time, for a feed published before every paper needed a page, which is in `feed/v1/`. Starts the feed again in `feed/v2/` with only the items that have an explainer (merged with their `upgrades.json` entries, given their `depth`, in chunks from chunk 1, with a head and no `upgrades.json`). The new feed gets a new folder because apps and the worker keep closed chunks as permanent, so a new chunk 1 at the old address would never reach a phone that kept the old one. `feed/v1/` is left as a stub: its chunks and `upgrades.json` are deleted and its head is rewritten with `chunk_count` 0, `total_items` 0, and `min_app` 2, so a 0.1.0 install, which reads `feed/v1/` and has version code 1, shows its update cover. It keeps only those papers' folders under `papers/`, and only those papers' lines in `state/seen/` (with their new chunk numbers); empties `state/queue/`, `state/claims/`, and `state/queued/`; keeps `state/queue-failed.jsonl`; and sets every cursor later than the given day to it, so the next run reads the days after it again. An item marked explained whose folder has no `index.html` is dropped and named. It prints the counts before and after and every file it writes and deletes, changes nothing without `--yes`, checks every file it writes against its schema first, and never commits or pushes. It refuses a checkout that already has `feed/v2/`.
