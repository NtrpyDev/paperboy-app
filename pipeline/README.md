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

## fetch

`paperboy-pipeline fetch --work WORK --id PAPER_ID` reads `WORK/papers/<id>/candidate.json` and saves the paper's free full text as `fulltext.md` (title, authors, abstract, sections in order, LaTeX math, Markdown tables, a Figures list of captions, footnotes, and a reference count) plus `source.json` (`available`, `url`, `kind`, `license`, `retrieved_at`, `chars`, `sections`).

Routes by `fulltext.kind`:

- `arxiv_html`: `https://arxiv.org/html/<id>`. A paper with no HTML rendering is unavailable; the PDF is never parsed.
- `biorxiv` (bioRxiv and medRxiv): the JATS XML the bioRxiv API lists as `jatsxml` (looked up by DOI when the candidate gives no `.xml` link). Equations and tables that the XML holds only as images are marked in place, not transcribed.
- `europepmc`: `https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/fullTextXML` (the PMCID is found by DOI when the candidate gives none).

Exit codes: 0 fetched; 3 no lawful full text is reachable (a missing rendering, a 404, a 403, or a bot challenge page, which is never bypassed): `source.json` then holds `"available": false` and the reason, and no `fulltext.md` is left; 1 a real error (bad candidate, a server that kept failing).

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
