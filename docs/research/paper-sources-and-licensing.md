# Paper sources and licensing (research, 2026-11-12)

Scope: where Paperboy can discover new papers, what each source allows, and what the app may publicly show per license class. Every claim cites its source URL. Live HTTP tests were run on 2026-11-13 between 02:42 and 02:55 UTC (evening of 2026-11-12 US time) with `curl -A "paperboy-research/0.1"`, no API keys, and no email address. "NOT FOUND" means the primary source did not answer the question. "Legal judgment" marks conclusions that are interpretation, not a documented rule; none of this is legal advice.

## 1. OpenAlex

### Access rules (changed since the prototype)

- Keys: "OpenAlex data is free, and so is casual use of the API: you can make basic queries with no key at all." A free key "raises your daily budget 10x, lets you track your usage, and is required for cursor paging past the first page." (paraphrase of punctuation only; source: https://help.openalex.org/api/authentication.md)
- Budget, not request count: "Every account gets $1 of API usage per day for free." Without a key "you get $0.10/day". (https://help.openalex.org/access/pricing.md, https://help.openalex.org/access/example-costs.md)
- Per-call prices: single entity lookup by ID or DOI is "Free"; list + filter is "$0.10" per 1,000 calls; search is "$1" per 1,000; content (PDF) download is "$10" per 1,000. With the free $1/day that is 10,000 list calls (1,000,000 results at `per_page=100`) or 100 PDF downloads. (https://help.openalex.org/access/example-costs.md)
- Rate limits: no key 10 requests/second; free key or prepaid 30/second; annual plan 50/second. `per_page` maximum 100; basic paging limit 10,000 results. (https://help.openalex.org/api/authentication.md)
- New accounts: "A new free account spends its first $1 at up to $0.10 every 5 minutes." (https://help.openalex.org/api/authentication.md)
- Paid tiers: prepaid usage in $1 increments; Member $5,000/year ($20/day budget); Member+ $10,000/year ($100/day, daily sync); Partner from $20,000/year. (https://help.openalex.org/access/pricing.md)
- Polite pool is gone: "Before February 2026, OpenAlex used a "polite pool" system where you could get higher rate limits by including `mailto=you@example.com` in your requests. This system has been replaced by API keys." and "The `mailto` parameter is ignored". (https://help.openalex.org/api/deprecations.md)
- Key provisioning: a key works only after its email is verified; an agent may request one with `POST https://api.openalex.org/api-keys` and the user's email. (https://help.openalex.org/api/authentication.md) Not done here, by instruction.

Live test, keyless request (headers trimmed):

```
HTTP/2 200
x-ratelimit-cost-usd: 0.0001
x-ratelimit-limit-usd: 0.1
x-ratelimit-remaining-usd: 0.0999
meta.notice: "No API key, so this request shares one free daily budget ($0.10) with everyone on your network's IP address. ..."
```

### Listing newest works (big change)

- Sorting by `publication_date:desc` is free; `created_date` and `updated_date` sorting and the `from_created_date`, `from_updated_date`, `to_created_date`, `to_updated_date` filters need a Member+ or Partner plan: "Without one of these plans, the API answers `429` with "Plan upgrade required"." (https://help.openalex.org/api/filtering.md, https://help.openalex.org/api/sorting.md)

Live test of `sort=created_date:desc` and `filter=from_created_date:2026-11-10`, both keyless:

```
HTTP 429
{"error":"Plan upgrade required","message":"Sorting by \"created_date:desc\" is part of daily sync, which comes with the Member+ and Partner plans. See https://help.openalex.org/access/sync/ for details."}
HTTP 429
{"error":"Plan upgrade required","message":"The \"from_created_date:2026-11-10\" filter is part of daily sync, ..."}
```

- `publication_date` is "The day the work was published ... Where several dates exist, OpenAlex usually picks the earliest electronic-publication date." (https://help.openalex.org/data/works/attributes.md) Observed: an unbounded `sort=publication_date:desc` returned a work dated `2027-11-12` (future), so a window is needed.

Working free query (live, trimmed):

```
GET https://api.openalex.org/works?filter=from_publication_date:2026-11-10,to_publication_date:2026-11-12,type:preprint&sort=publication_date:desc&per_page=1&select=id,doi,title,publication_date,type,open_access,best_oa_location,primary_topic,is_retracted,has_fulltext,content_urls,abstract_inverted_index
{
 "meta": {"count": 6000, "per_page": 1, "cost_usd": 0.0001},
 "results": [{
   "id": "https://openalex.org/W7214372117",
   "publication_date": "2026-11-12",
   "type": "preprint",
   "open_access": {"is_oa": true, "oa_status": "green", "oa_url": "https://arxiv.org/pdf/2610.14130", "any_repository_has_fulltext": true},
   "best_oa_location": {"landing_page_url": "https://arxiv.org/abs/2610.14130", "pdf_url": "https://arxiv.org/pdf/2610.14130",
                        "source": {"display_name": "arXiv (Cornell University)", "type": "repository"},
                        "license": null, "license_id": null, "version": "submittedVersion"},
   "primary_topic": {"display_name": "Software Engineering Research", "subfield": {...}, "field": {"display_name": "Computer Science"}, "domain": {"display_name": "Physical Sciences"}},
   "is_retracted": false,
   "has_fulltext": true,
   "content_urls": {"pdf": "https://content.openalex.org/works/W7214372117.pdf", "grobid_xml": "https://content.openalex.org/works/W7214372117.grobid-xml"},
   "abstract_inverted_index": {"Tesler's": [0], "conservation": [1], "law": [2], "holds": [3], ...}
 }]
}
```

Note: this arXiv location carries `license: null` even though arXiv records a license for every paper (see section 2). Do not treat null as "no license"; get arXiv licenses from arXiv OAI-PMH.

### Fields

- `abstract_inverted_index`: "OpenAlex does not ship plaintext abstracts for legal reasons; reconstruct the abstract from the index." Coverage: "over 60% of 2022 works vs. ~45% of pre-2000 works". (https://help.openalex.org/data/works/attributes.md)
- `open_access`: object with `is_oa`, `oa_status` (one of `diamond`, `gold`, `green`, `hybrid`, `bronze`, `closed`), `oa_url`, `any_repository_has_fulltext`. (https://help.openalex.org/data/works/attributes.md)
- `best_oa_location`: "The best openly available location, or null if none." Ranking: publisher beats repository; `publishedVersion` beats `acceptedVersion` beats `submittedVersion`; a direct PDF link beats none. (https://help.openalex.org/data/works/attributes.md)
- License: "A license is a property of a location (each copy of a work can have its own license)". Vocabulary of 14 IDs: `cc-by`, `cc-by-sa`, `cc-by-nd`, `cc-by-nc`, `cc-by-nc-sa`, `cc-by-nc-nd`, `public-domain`, `mit`, `apache-2-0`, `gpl-v2`, `gpl-v3`, `isc`, `other-oa`, `publisher-specific-oa`. Filters: `primary_location.license:cc-by`, `locations.license:cc-by`. (https://help.openalex.org/data/licenses.md) Each location "carries the `license` OpenAlex found for that copy, or null if none was found." (https://help.openalex.org/data/works/open-access.md)
- Topic/field: `primary_topic` is "The top-ranked topic for the work, with its `subfield`, `field`, and `domain`." (https://help.openalex.org/data/works/attributes.md) Concepts are deprecated in favor of Topics. (https://help.openalex.org/api/deprecations.md)
- `type`: one value from a controlled vocabulary that includes `article`, `preprint`, `review`, `erratum`, `retraction`, `letter`, `editorial`, `paratext`, `dataset`, and others. `preprint` is "An article whose primary location is a preprint repository such as arXiv, bioRxiv, medRxiv, SSRN, or Research Square." `review` is "A journal article that summarizes and evaluates the existing research on a topic without reporting new findings". (https://help.openalex.org/data/work-types.md)
- `is_retracted`: true if Retraction Watch lists the DOI as retracted (and not reinstated), "or Crossref or PubMed records a retraction of it, or its title starts "Retracted"". (https://help.openalex.org/data/works/attributes.md) See section 9.
- Full text: `best_oa_location.pdf_url` and `landing_page_url` link out. OpenAlex also caches files: `content_urls` holds `pdf` and `grobid_xml` URLs under `content.openalex.org`; "Fetching requires your API key (a free one is fine); each download is metered". (https://help.openalex.org/data/works/attributes.md) Live: keyless `HEAD https://content.openalex.org/works/W7214372117.pdf` returned `HTTP 401`. "The PDFs retain their original copyright. OpenAlex does not grant any additional rights to the content." (https://help.openalex.org/access/fulltext.md)
- `has_fulltext` means searchable text exists, which "is not the same as a downloadable file"; use `has_content.pdf:true` to find downloadable works. (https://help.openalex.org/data/works/attributes.md)

### License of OpenAlex data and abstracts

- "Every record is released under a CC0 public-domain license, with no "personal use only" carve-out and no permission to ask." (https://help.openalex.org/access/pricing.md) "all the data is free and open under CC0". (https://help.openalex.org/access/overview.md)
- Abstracts: OpenAlex ships only the inverted index "for legal reasons" (https://help.openalex.org/data/works/attributes.md). An explicit OpenAlex statement on whether a reconstructed abstract may be redisplayed publicly: NOT FOUND. Legal judgment: OpenAlex's CC0 can only waive rights OpenAlex holds; Crossref states abstract copyright stays with publishers or authors (section 7), so CC0 on OpenAlex records does not clear abstract text.

### chemRxiv through OpenAlex (still works)

OpenAlex has a ChemRxiv source `S4393918830` (live: `"display_name": "ChemRxiv", "works_count": 24246, "type": "repository"`). Filtering `locations.source.id:S4393918830` sorted by `publication_date:desc` returned works dated 2026-11-12, with `best_oa_location.pdf_url` on `https://chemrxiv.org/doi/pdf/10.26434/...` and `license: "cc-by"` on the example records.

## 2. arXiv

### API terms and rate limits

- Terms of Use page: "Our APIs include our OAI-PMH interface, RSS feeds, the legacy arXiv API, bulk data downloads, and SWORD bulk deposit API." (https://info.arxiv.org/help/api/tou.html)
- Rate limit: "When using the legacy APIs (including OAI-PMH, RSS, and the arXiv API), make no more than one request every three seconds, and limit requests to a single connection at a time." These limits "apply to all of the machines under your control as a whole." (https://info.arxiv.org/help/api/tou.html)
- A second arXiv page gives a different number for custom harvesting on `export.arxiv.org`: "we suggest that a reasonable rate to be bursts at 4 requests per second with a 1 second sleep, per burst." (https://info.arxiv.org/help/bulk_data.html) The two pages conflict; the API terms page is the stricter one.
- Allowed: "Retrieve, store, transform, and share descriptive metadata about arXiv e-prints." "Retrieve, store, and use the content of arXiv e-prints for your own personal use, or for research purposes." "Provide tools and services to users that helps them to discover or be notified about arXiv e-prints", including "A mobile app that notifies users about e-prints that might be of interest to them". "Direct users to arXiv.org to retrieve e-print content (PDF, source files, etc). We encourage you to link to the abstract page." (https://info.arxiv.org/help/api/tou.html)
- Not allowed: "Store and serve arXiv e-prints (PDFs, source files, or other content) from your servers, unless you have the permission of the copyright holder or are permitted to do so by the license with which the e-print was submitted." Also "Represent your project as endorsed or supported by arXiv.org without our permission." (https://info.arxiv.org/help/api/tou.html)

### Metadata and abstract license

- "You are free to use descriptive metadata about arXiv e-prints under the terms of the Creative Commons Universal (CC0 1.0) Public Domain Declaration." Footnote: "Descriptive metadata includes information for discovery and identification purposes, and includes fields such as title, abstract, authors, identifiers, and classification terms." (https://info.arxiv.org/help/api/tou.html)
- "A Creative Commons CC0 1.0 Universal Public Domain Dedication will apply to all metadata." (https://info.arxiv.org/help/license/index.html)

So arXiv abstracts may be shown in full regardless of the paper's own license, per arXiv's own statement.

### Per-paper licenses

Options arXiv lists: CC BY 4.0, CC BY-SA 4.0, CC BY-NC-SA 4.0, CC BY-NC-ND 4.0, "arXiv.org perpetual, non-exclusive license 1.0", and CC Zero. "For all licenses here, with the exception of CC Zero, the original copyright holder retains ownership after posting on arXiv." "different versions of the work can have different licenses." (https://info.arxiv.org/help/license/index.html)

- The non-exclusive license text: "I grant arXiv.org a perpetual, non-exclusive license to distribute this article." (https://arxiv.org/licenses/nonexclusive-distrib/1.0/license.html) arXiv: it "gives limited rights to arXiv to distribute the article, and also limits re-use of any type from other entities or individuals." (https://info.arxiv.org/help/license/index.html)
- "The vast majority of e-prints are submitted under the arXiv.org non-exclusive right to distribute." (https://info.arxiv.org/help/api/tou.html) "Articles between 1991 and 2003 have an assumed license. These are functionally equivalent to the arXiv non-exclusive license." (https://info.arxiv.org/help/license/reuse.html)
- Where the license is exposed: "the license for the full text is not a part of the current search API schema. The license is, however, provided within arXiv's output from the OAI-PMH in either arXiv or arXivRaw formats." Abstract pages "indicate an assigned license underneath the "Download:" options." (https://info.arxiv.org/help/license/reuse.html) Observed: the HTML full-text page also shows it, e.g. `License: CC BY-NC-ND 4.0` on https://arxiv.org/html/2611.15043v1.

### What may be redistributed

- Figures: "If the license applied to the work allows for remixing or reuse with citation, then yes. If not, then the version is assigned one of the arXiv perpetual non-exclusive licenses, and you will need to contact the submitter or copyright holder (if published) to determine applicable permissions." (https://info.arxiv.org/help/license/reuse.html)
- Full text: the non-exclusive license "does not grant further reuse permissions directly. In these cases you will need to contact the author directly with your request." (https://info.arxiv.org/help/license/reuse.html)
- Bulk: "We are thus unable to grant others the right to distribute arXiv articles. If you build indexes or tools based on the full-text, you must link back to arXiv for downloads." (https://info.arxiv.org/help/bulk_data.html)
- Per CC license (PDF, source, figures): governed by the CC license itself; see section 6. arXiv-specific rules per CC license beyond the above: NOT FOUND.

### HTML full text

- arxiv.org/html: "arXiv has successfully launched papers in HTML format. We are gradually backfilling HTML for arXiv's corpus" and "Not every paper can be successfully converted". (https://info.arxiv.org/about/accessible_HTML.html) Live: `GET https://arxiv.org/html/2611.15043v1` returned `HTTP/2 200`.
- ar5iv: "Converted from TeX with LaTeXML. Sources upto the end of October 2026. Not a live preview service. For articles with multiple revisions, only a single version is made available. When in doubt, always use the main arXiv.org article page." (https://ar5iv.labs.arxiv.org/) ar5iv robots.txt only disallows `/log/`. (https://ar5iv.labs.arxiv.org/robots.txt) ar5iv terms of use: NOT FOUND.
- Automated fetching: arxiv.org robots.txt says "Indiscriminate automated downloads from this site are not permitted", sets `Crawl-delay: 15` for `User-agent: *`, and `Allow: /html`, `Allow: /pdf`, `Allow: /abs`, `Allow: /list`; it disallows `/e-print`, `/src`, `/api`, `/search`. (https://arxiv.org/robots.txt) "arXiv monitors activity and will deny access to sites that violate these guidelines." (https://info.arxiv.org/help/robots.html) `export.arxiv.org/robots.txt` is `User-agent: *` / `Disallow: /` even though arXiv asks harvesters to use that host (https://export.arxiv.org/robots.txt, https://info.arxiv.org/help/bulk_data.html). An HTML-specific automated-access policy beyond these: NOT FOUND.
- Redistributing the HTML follows the paper's license (TOU "Store and serve ... other content" clause above).

### Getting all new submissions daily

- OAI-PMH base URL (new since March 2025): `https://oaipmh.arxiv.org/oai`, replacing `http://export.arxiv.org/oai2`. Formats `oai_dc`, `arXiv` ("Includes author names separated out, category and license information"), `arXivRaw`. Sets like `math`, `physics:hep-th`, `math:math:NA`. "metadata is made available via the OAI-PMH interface once they are announced, typically around 10:30pm ET Sunday through Thursday." Caveat: "The OAI-PMH interface does not support selective harvesting based on submission date." Datestamps are last modification times. (https://info.arxiv.org/help/oa/index.html)
- RSS/Atom: `https://rss.arxiv.org/rss/<category>` or `/atom/<category>`; "Feeds are updated daily at midnight Eastern Standard Time." Multiple categories joined with `+`, "Limit 2000 results." (https://info.arxiv.org/help/rss.html)
- API: Atom results; supports `sortBy=submittedDate&sortOrder=descending`.

Live OAI-PMH test (trimmed; note an old paper re-surfacing because its metadata changed, so filter on `<created>`):

```
GET https://oaipmh.arxiv.org/oai?verb=ListRecords&metadataPrefix=arXiv&set=math&from=2026-11-12
<record><header><identifier>oai:arXiv.org:1208.4977</identifier><datestamp>2026-11-12</datestamp>
  <setSpec>math:math:AP</setSpec>...</header>
<metadata><arXiv>
  <id>1208.4977</id><created>2021-05-08</created><updated>2026-11-12</updated>
  <authors><author><keyname>Li</keyname><forenames>Dong</forenames></author></authors>
  <title>Global wellposedness of hedgehog solutions for the (3+1) Skyrme model</title>
  <categories>math.AP hep-th math-ph math.MP</categories>
  <doi>10.1215/00127094-2020-0067</doi>
  <license>http://arxiv.org/licenses/nonexclusive-distrib/1.0/</license>
  <abstract>We consider the dynamics of hedgehog solutions ...</abstract>
</arXiv></metadata></record>
```

Live API test (trimmed; no license element in the Atom entry):

```
GET https://export.arxiv.org/api/query?search_query=cat:math.*&sortBy=submittedDate&sortOrder=descending&max_results=1
<opensearch:totalResults>705017</opensearch:totalResults>
<entry>
  <id>http://arxiv.org/abs/2611.15043v1</id>
  <title>Positivity in symplectic groups and electrical networks</title>
  <link href="https://arxiv.org/pdf/2611.15043v1" rel="related" type="application/pdf"/>
  <summary>We study the relation between electrical positivity ...</summary>
  <category term="math.CO"/> <published>2026-11-11T05:09:49Z</published>
  <arxiv:primary_category term="math.CO"/> <author><name>V. Gorbounov</name></author>
</entry>
```

Live RSS test: `https://rss.arxiv.org/rss/math.CO` and `https://rss.arxiv.org/rss/math` both returned a valid channel (`lastBuildDate Thu, 12 Nov 2026 05:00:08 +0000`) with 0 items at test time. Why it was empty: NOT FOUND.

## 3. bioRxiv, medRxiv, chemRxiv

### bioRxiv and medRxiv API

- Endpoint: `https://api.biorxiv.org/details/[server]/[interval]/[cursor]/[format]` where interval is two dates, "a numeric value for the N most recent posts", or "a numeric with the letter 'd' for the most recent N days of posts". 30 papers per call. `server` is `biorxiv` or `medrxiv`. Optional `?category=cell_biology`. Formats JSON, XML (OAI-PMH XML), HTML. Fields: "doi title authors author_corresponding author_corresponding_institution date version type license category jats xml path abstract published server". (https://api.biorxiv.org/)
- Also `/pubs/` (preprint to published article links, 100 per call), `/publisher/`, `/funder/` (funder metadata from 2025-04-10). (https://api.biorxiv.org/)
- Rate limits and API terms of use: NOT FOUND on the API page. bioRxiv robots.txt sets `Crawl-delay: 7` for `User-agent: *` and blocks several named crawlers including `openai`. (https://www.biorxiv.org/robots.txt)

Live test (trimmed):

```
GET https://api.biorxiv.org/details/biorxiv/2026-11-10/2026-11-12/0/json
{"messages":[{"status":"ok","category":"all","interval":"2026-11-10:2026-11-12","cursor":0,"count":30,"count_new_papers":"487","total":"753"}],
 "collection":[{"title":"High-throughput light-sheet 3D microscopy of whole rodent brain microstructure ...",
   "authors":"Hanmer, J. M.; ...","doi":"10.64898/2026.10.12.758500","date":"2026-11-10","version":"2",
   "type":"new results","license":"cc_by","category":"neuroscience",
   "jatsxml":"https://www.biorxiv.org/content/early/2026/11/10/2026.10.12.758500.source.xml",
   "abstract":"Whole-brain cellular mapping is essential ...","published":"NA","server":"bioRxiv"}]}
```

Observed: the DOI prefix in this record is `10.64898`, not the `10.1101` prefix used in the API page's examples (https://api.biorxiv.org/). Pipelines that match bioRxiv by `10.1101/` will miss these. `/details/biorxiv/2d/0/json` returned `"Both dates must be in yyyy-mm-dd format"`, while `/details/biorxiv/2d` (no cursor) worked.

- License values seen live across 90 medRxiv records (2026-11-05 to 2026-11-12): `cc_by` 30, `cc_by_nc_nd` 29, `cc_no` 16, `cc_by_nc` 12, `cc_by_nd` 2, `cc0` 1.
- License options per bioRxiv FAQ: "No reuse/adaptation without permission", CC-BY-NC-ND, CC-BY-ND, CC-BY-NC, CC-BY, CC0. "Authors retain copyright of their manuscripts". (https://www.biorxiv.org/about/FAQ) The mapping of `cc_no` to "No reuse/adaptation without permission" is not stated in a primary source: NOT FOUND (inferred from the option list only).

### Full text and text mining terms

- Formats: "Each version of a manuscript is available in PDF, HTML, and XML formats." HTML/XML conversion "can take up to 48 hours". "XML is available for text mining purposes." (https://www.biorxiv.org/about/FAQ) Live: the `jatsxml` URL above (posted 2026-11-10) returned `HTTP 404` at test time, consistent with that delay (cause unconfirmed).
- TDM: "Bulk access to the full text of bioRxiv articles for the purposes of text and data mining (TDM) is available via a dedicated Amazon S3 resource. This is intended for bulk TDM, which authors explicitly consent to during submission to bioRxiv and is consistent with fair use doctrine applied to US copyright law. The TDM repository is not intended as a source for further redistribution of articles posted on bioRxiv, or their derivatives, nor does it grant others permission to re-host content posted on bioRxiv." "If you build indexing services or tools based on the full text of articles, you must therefore link back to the text hosted at bioRxiv rather than re-host content." "For reuse/redistribution of individual articles or their derivatives, please consult the licensing terms applied by the authors, which are provided in the metadata." Bucket: `s3://biorxiv-src-monthly`, requester pays, monthly. (https://www.biorxiv.org/tdm) medRxiv has the same text. (https://www.medrxiv.org/tdm)

### chemRxiv

- Platform change: Wiley's release dated March 9, 2026 says ChemRxiv "has selected Research Exchange Preprints as its platform provider", "built on the Atypon Experience Platform". (https://newsroom.wiley.com/press-releases/press-release-details/2026/Leading-Preprint-Server-ChemRxiv-Joins-Wileys-Newly-Launched-Research-Exchange-Preprints/default.aspx) The release does not mention APIs or text mining.
- Live: `https://chemrxiv.org/`, the old `https://chemrxiv.org/engage/chemrxiv/public-api/v1/items`, the old docs URL, and `/engage/chemrxiv/public-api/v1/oai` all returned a Cloudflare "Just a moment..." challenge or `403` to a scripted client. chemrxiv.org robots.txt disallows `/rss`. (https://chemrxiv.org/robots.txt)
- Crossref still has chemRxiv DOIs: `10.26434/chemrxiv.15002888/v1` is `posted-content`/`preprint`, publisher "American Chemical Society (ACS)", `license: null`, primary URL `https://chemrxiv.org/doi/full/...`. (live, https://api.crossref.org/works/10.26434/chemrxiv.15002888/v1)
- Current chemRxiv API status, its documentation, and its TDM terms: NOT FOUND (pages not reachable by an automated client). OpenAlex coverage works (section 1).

## 4. Peer-reviewed open access full text

### Europe PMC

- Search: `https://www.ebi.ac.uk/europepmc/webservices/rest/search`; "The search module additionally provides a sort parameter available for every single-valued field, e.g. P_PDATE_D, AUTH_FIRST, CITED." `resultType=core` "returns full metadata for a given publication ID; including abstract, full text links". (https://europepmc.org/RestfulWebService)
- Full text: `/{id}/fullTextXML`: "Use this module to retrieve the full text in XML format for the Open Access subset of our full text publications." (https://www.ebi.ac.uk/europepmc/webservices/rest/v3/api-docs)
- OA subset: "Articles in the open access subset are still protected by copyright, but are made available under a Creative Commons license, or similar ... The license terms are not identical for all articles in this subset." Find them with `OPEN_ACCESS:y`. (https://europepmc.org/downloads/openaccess)
- Automated access: "Crawlers and other automated processes may NOT be used to systematically retrieve batches of articles from the Europe PMC web site." The OAI, RESTful, SOAP and bulk download services "are the only services that may be used for automated downloading of articles in Europe PMC." (https://europepmc.org/Copyright)
- Rate limits, API key: NOT FOUND (no key was needed in tests).
- What it adds: life-science journal articles and preprints with a `license` field per record and JATS full text for the OA subset.

Live tests (trimmed). The first attempt returned `{"errCode":503,"errMsg":"Search service is temporarily unavailable. Please retry later."}`; the retry worked:

```
GET .../rest/search?query=OPEN_ACCESS:y AND LICENSE:"cc by"&sort=P_PDATE_D desc&resultType=core&pageSize=1&format=json
{"hitCount": 5400508,
 "result": {"source":"MED","pmcid":"PMC13715329","doi":"10.1080/10495398.2026.2743468","firstPublicationDate":"2026-10-22",
   "pubTypeList":{"pubType":["research-article","Journal Article"]},"isOpenAccess":"Y","license":"cc by","hasPDF":"Y",
   "abstractText":"Xylooligosaccharides (XOS) are recognized ...",
   "fullTextUrlList":{"fullTextUrl":[{"availabilityCode":"S","url":"https://doi.org/..."},{"availabilityCode":"OA","site":"Europe_PMC","url":"https://europepmc.org/articles/PMC13715329"}]}}}

GET .../rest/PMC13715329/fullTextXML
<article xml:lang="en" article-type="research-article"> ...
<permissions><copyright-statement>(c) 2026 The Author(s). Published by Informa UK Limited ...</copyright-statement>
<license><license-p>This is an Open Access article distributed under the terms of the Creative Commons Attribution License
(<ext-link xlink:href="https://creativecommons.org/licenses/by/4.0/">...</ext-link>) ...
```

Observed: sorting by `P_PDATE_D desc` put a record with `pubYear 2027` first; the newest-first order follows publication date, not indexing date.

### PubMed Central OA subset

- "The PMC Open Access Subset includes journal articles and preprints that are made available under Creative Commons or similar licenses". "The PMC Cloud Service, PMC OAI-PMH Service, E-Utilities and BioC API are the only services that may be used for automated retrieval of PMC content. Systematic retrieval (or bulk retrieval) of articles through any other automated process is prohibited." (https://pmc.ncbi.nlm.nih.gov/tools/openftlist/)
- License groups: "Commercial use allowed: CC0, CC BY, CC BY-SA, CC BY-ND"; "Non-commercial use only: CC BY-NC, CC BY-NC-SA, CC BY-NC-ND"; "Other: no machine-readable Creative Commons license, no license tagged, or a custom license". Author Manuscript default license: "This file is available for text mining. It may also be used consistent with the principles of fair use under the copyright law." (https://pmc.ncbi.nlm.nih.gov/tools/textmining/)
- Change since the prototype: "All legacy PMC Article Dataset files on the FTP and Cloud Services were removed the week of August 24, 2026." Data is now in the world-readable S3 bucket `arn:aws:s3:::pmc-oa-opendata` (us-east-1, `--no-sign-request`). (https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/)
- Copyright: "Users of PMC are directly and solely responsible for compliance with copyright restrictions". "open access and public domain articles may still contain photographs or illustrations copyrighted by other commercial organizations or individuals". (https://pmc.ncbi.nlm.nih.gov/about/copyright/)
- E-utilities: "Make no more than 3 requests every 1 second. Use the URL parameter email, and tool for distributed software". "NCBI's Disclaimer and Copyright notice must be evident to users of your service." (https://www.ncbi.nlm.nih.gov/home/about/policies/)

### Unpaywall

- Now a format over OpenAlex: "In late 2025 we moved Unpaywall onto the OpenAlex database. Since then there has been one set of data." "The `is_oa`, `oa_status`, and PDF link in an Unpaywall record are the same values you'll find in the OpenAlex work's `open_access` and `best_oa_location` fields." Coverage: Crossref DOIs only; "DataCite DOIs aren't included." "We are not retiring Unpaywall." (https://help.openalex.org/access/unpaywall.md)
- Access: "Requests must include your email as a parameter at the end of the URL". "Please limit use to 100,000 calls per day." (Unpaywall API page, https://unpaywall.org/products/api, read from the page's own script bundle https://unpaywall.org/js/app.dd2a222a.js because the page is JavaScript-only)
- Live keyless test without email:

```
GET https://api.unpaywall.org/v2/10.7717/peerj.4375
HTTP 422 {"HTTP_status_code": 422, "error": true, "message": "Email address required in API call, see http://unpaywall.org/products/api"}
```

- What it adds over OpenAlex: nothing new in data; it is DOI-in, OA-answer-out. A separate Unpaywall data license statement: NOT FOUND (OpenAlex says its data is CC0, section 1).

### Crossref REST API

- "No sign-up is required to use the REST API, and almost none of the metadata is subject to copyright, and you may use it for any purpose. Some abstracts contained in the metadata may be subject to copyright by publishers or authors." (https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
- Pools: Public (no identification), Polite ("Include your email address in the mailto parameter or agent header"), Metadata Plus (paid key). (https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/)
- Rate limits since 1 December 2025, per second: Public pool single record 5 (concurrency 1), lists 1 (concurrency 1); Polite pool single DOI 10 (concurrency 3), lists 3 (concurrency 3). (https://www.crossref.org/blog/announcing-changes-to-rest-api-rate-limits/) The access page still shows the older single numbers "Public 5 1", "Polite 10 3", "Plus 150 None". (https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/)
- Fields: `license` (array with `URL`, `start`, `delay-in-days`, `content-version`), `abstract` (JATS), `link` (full-text links with `intended-application` such as `text-mining`), `update-to`. Filters: `has-abstract`, `has-license`, `license.url`, `from-created-date`, `from-pub-date`, `from-index-date`, `update-type`, `updates`, `is-update`. (https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/)
- Licensing summary: "Bibliographic metadata, including references: Facts, not subject to copyright"; "Crossref-generated data: CC0"; "Open Funder Registry, Retraction Watch database: CC0"; "Abstracts: Copyright held by publisher or author". (https://www.crossref.org/documentation/retrieve-metadata/)
- What it adds: a free `created` sort and `from-created-date` filter (OpenAlex now charges for the equivalent), publisher-asserted license URLs with start dates, and retraction links.

Live test (no mailto, so public pool; headers confirm the list limit):

```
GET https://api.crossref.org/works?filter=from-created-date:2026-11-11,type:journal-article,has-abstract:true,has-license:true&sort=created&order=desc&rows=1&select=DOI,title,type,created,license,abstract,link,update-to,publisher
x-rate-limit-limit: 1
x-rate-limit-interval: 1s
x-concurrency-limit: 1
x-api-pool: public-array
{"total-results": 19625,
 "items": [{"DOI": "10.64994/iemj.v3i2.96", "type": "journal-article",
   "created": {"date-time": "2026-11-13T02:19:28Z"},
   "license": [{"start": {"date-time": "2026-11-12T00:00:00Z"}, "content-version": "unspecified", "delay-in-days": 0, "URL": "https://creativecommons.org/licenses/by/4.0"}],
   "abstract": "<jats:p>The issue of inconsistency in students' religious practices ...",
   "link": [{"URL": "https://jurnal.staikap.ac.id/.../download/96/96", "content-type": "application/pdf", "content-version": "vor", "intended-application": "text-mining"}]}]}
```

### Semantic Scholar

- Keys: "Most Semantic Scholar endpoints are available to the public without authentication, but they are rate-limited to 1000 requests per second shared among all unauthenticated users." "The introductory rate limit for an API key is 1 RPS on all endpoints." (https://www.semanticscholar.org/product/api)
- License agreement (last updated May 17, 2023): a "limited, non-exclusive, non-transferable, non-sublicensable and terminable license to use the API solely in operation with compatible third-party platforms and software ... to access and display the data". Data is "separately governed by the licenses that accompany such S2 Data, such as CC BY-NC or ODC-BY", and third-party content "may be subject to separate license terms". Attribution: "Licensee will include an attribution to "Semantic Scholar" on its website or in any published materials". Restriction: do not "repackage, sell, rent, lease, lend, distribute, or sublicense the API". (https://www.semanticscholar.org/product/api/license)
- Datasets (release 2026-11-03): `abstracts` and `tldrs` READMEs say "This collection is licensed under ODC-BY." (https://api.semanticscholar.org/datasets/v1/release/latest)
- What it adds: `tldr` machine summaries, citation graph, `openAccessPdf` with a license guess and a disclaimer.

Live test (keyless, trimmed):

```
GET https://api.semanticscholar.org/graph/v1/paper/DOI:10.7717/peerj.4375?fields=title,abstract,isOpenAccess,openAccessPdf,publicationTypes,publicationDate,tldr,externalIds
HTTP/2 200
{"paperId": "c2fccee04fd91439096a80972659dd764e9c0e2d", "externalIds": {"DOI": "10.7717/peerj.4375", "PubMedCentral": "5815332", ...},
 "isOpenAccess": true,
 "openAccessPdf": {"url": "https://doi.org/10.7717/peerj.4375", "status": "GOLD", "license": "CCBY",
   "disclaimer": "Notice: Paper or abstract available at https://pmc.ncbi.nlm.nih.gov/articles/PMC5815332, which is subject to the license by the author or copyright owner provided with this content. Please go to the source to verify the license and copyright information for your use."},
 "tldr": {"model": "tldr@v2.0.0", "text": "The citation impact of OA articles is examined ..."},
 "publicationTypes": ["JournalArticle"], "publicationDate": "2018-02-13", "abstract": "Despite growing interest in Open Access ..."}
```

### DOAJ

- Rate limit: "There is a rate limit of two requests per second on all API routes. "Bursts" are permitted, which means up to five requests per user are queued". API keys "are usually only available to publishers who submit data to DOAJ". Sorting: `sort=field:direction`. (https://doaj.org/api/docs)
- Data license: journal-level metadata "is available with a CC0 waiver". "The article metadata provided to us by publishers or that we collect from EuropePMC, which we then process and display, is available with a CC0 waiver." (https://doaj.org/terms/) Article records include abstracts (live test below). Legal judgment: whether DOAJ's CC0 waiver can cover abstract text it does not own is not settled by the source; Crossref's position (section 7) is that abstracts keep the publisher's or author's copyright.
- What it adds: only fully OA journals, so every record has a free full-text link.

Live test (trimmed):

```
GET https://doaj.org/api/search/articles/bibjson.year:2026?sort=created_date:desc&pageSize=1
{"total": 1123034,
 "results": [{"id": "8786aea6d4ca41a6b22ddcdd7bc8ed37", "created_date": "2026-11-13T02:49:44Z",
   "bibjson": {"title": "Study on carbon reduction benefits of coal-based solid waste CO2 mineralization ...",
     "abstract": "Guided by the \"dual-carbon\" goals ...",
     "link": [{"content_type": "html", "type": "fulltext", "url": "http://www.mtkxjs.com.cn/article/doi/10.12438/cst.2026-0801"}],
     "identifier": [{"id": "0253-2336", "type": "pissn"}, {"id": "10.12438/cst.2026-0801", "type": "doi"}],
     "journal": {"publisher": "Editorial Department of Coal Science and Technology", "language": ["ZH"], ...}, "year": "2026"}}]}
```

## 5. Journal RSS and TOC feeds

All seven venues have an official feed that answered `HTTP 200` to a scripted client on 2026-11-13 UTC. Their terms differ a lot. Terms pages for Science, PNAS, and Cell returned a Cloudflare challenge (`403`) to scripted clients, so their terms are NOT FOUND.

| Venue | Feed URL | Item fields seen (first item) | Terms on feed/automated use | Site-wide article license |
|---|---|---|---|---|
| Nature | https://www.nature.com/nature.rss (RSS 1.0, 75 items, news mixed with papers) | title, link, one-line summary and DOI in `content:encoded`, `prism:doi`, `dc:date`; no author on the news item | Restrictive (quotes below) | None; channel rights: "All rights reserved." |
| Science | https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science (44 items) | title, link, citation-only `description` (no abstract), `dc:creator`, DOI, `dc:date` | NOT FOUND (blocked) | NOT FOUND |
| PNAS | https://www.pnas.org/action/showFeed?type=etoc&feed=rss&jc=pnas (98 items) | title, link, citation-only `description`, DOI, `dc:date` | NOT FOUND (blocked) | NOT FOUND |
| Cell | https://www.cell.com/cell/current.rss (24 items) | title, link, summary `description`, `dc:creator`, DOI, `dc:date` | NOT FOUND (blocked) | None; channel rights: "All rights reserved." |
| Physical Review Letters | https://feeds.aps.org/rss/recent/prl.xml (100 items), listed at https://journals.aps.org/feeds | title, link, authors, abstract excerpt in `content:encoded`, DOI, `dc:date`; per-item `dc:rights` "Personal use only, all commercial or other reuse prohibited" | Restrictive (quotes below) | CC BY only where marked |
| eLife | https://elifesciences.org/rss/recent.xml (RSS 2.0, 50 items) | title, link, full abstract in `description`, authors, DOI, `pubDate` | No RSS clause found | CC BY |
| PLOS ONE | https://journals.plos.org/plosone/feed/atom (Atom, 30 items) | title, HTML/PDF/XML links, authors, DOI, dates; no abstract | No RSS clause found | CC BY (or CC0 or similar) |

Quotes and notes:

- Nature terms: "You must not (whether directly or indirectly): ... distribute, transmit, syndicate, sell or offer to sell or otherwise make available any content, files, feeds or data from a Site, whether publically available or not, except as specifically permitted by that Site". Also no "copy, download, or store any content, files, feeds or data from any Site ... to make or populate a database or publication of any kind whatsoever". (https://www.nature.com/info/terms-and-conditions) The old https://www.nature.com/webfeeds page returns `410`. An RSS-specific Nature terms page: NOT FOUND. robots.txt has no rule for `.rss` (https://www.nature.com/robots.txt).
- Science and PNAS robots.txt: `Disallow: /action` with `Allow: /action/showFeed`. (https://www.science.org/robots.txt, https://www.pnas.org/robots.txt)
- Cell: robots.txt has `Disallow: /rss` (does not match `/cell/current.rss`) and `Crawl-delay: 1`. (https://www.cell.com/robots.txt) Elsevier's general website terms forbid using robots "to: (i) continuously and automatically search, scrape, extract, deep link or index any Content" and "systematic retrieval of Content from the Services to create or compile ... a collection, compilation, database or directory without our prior written permission". (https://www.elsevier.com/legal/elsevier-website-terms-and-conditions) Whether those terms govern cell.com: NOT FOUND.
- APS terms: "All materials contained herein, except where explicitly noted, including abstracts are fully copyrighted by the American Physical Society (APS)". "Users may not make systematic download of articles, tables of contents, abstracts, or any other information in the APS online journals for mounting on local servers or for any other purpose, whether commercial or not, without the written permission of APS." (https://journals.aps.org/info/terms.html)
- eLife: "Unless otherwise indicated, the articles and journal content published by eLife on the eLife Sites are licensed under a Creative Commons Attribution license (also known as a CC-BY license)." (https://elifesciences.org/terms) robots.txt: `Crawl-delay: 10`, no `/rss` rule. (https://elifesciences.org/robots.txt)
- PLOS: content is "licensed by the respective authors for use and distribution by you subject to citation of the original source in accordance with the Creative Commons Attribution (CC BY) license or other comparable license that allows free and unrestricted use (such as Creative Commons 1.0 Universal (CC0) or Open Governmental License)." (https://plos.org/terms-of-use/) robots.txt: `Crawl-delay: 30`. (https://journals.plos.org/robots.txt)
- Legal judgment: Nature and APS terms, read plainly, do not permit an app to ingest their feeds and republish their content without permission. eLife and PLOS content is CC BY, so feed data and abstracts can be shown with attribution. For Science, PNAS, and Cell the terms are NOT FOUND. Titles, authors, and DOIs for any of these venues are also available from Crossref and OpenAlex (sections 1 and 4), whose terms are documented.

## 6. What the app may show, per license class

### Creative Commons legal code, key points (4.0)

- Adapted Material: "material subject to Copyright and Similar Rights that is derived from or based upon the Licensed Material and in which the Licensed Material is translated, altered, arranged, transformed, or otherwise modified in a manner requiring permission under the Copyright and Similar Rights held by the Licensor." (https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en, Section 1; identical definition in the other 4.0 licenses)
- Licensed Rights "are limited to all Copyright and Similar Rights that apply to Your use of the Licensed Material". (same, Section 1)
- Exceptions: "where Exceptions and Limitations apply to Your use, this Public License does not apply, and You do not need to comply with its terms and conditions." (same, Section 2(a)(2)) "this Public License does not, and shall not be interpreted to, reduce, limit, restrict, or impose conditions on any use of the Licensed Material that could lawfully be made without permission under this Public License." (https://creativecommons.org/licenses/by/4.0/legalcode.en, Section 8(a))
- Format changes: "simply making modifications authorized by this Section 2(a)(4) never produces Adapted Material." (https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en, Section 2(a)(4))
- Attribution (Section 3(a)(1)): if You Share the material, retain, if supplied, "identification of the creator(s)", "a copyright notice", "a notice that refers to this Public License", "a notice that refers to the disclaimer of warranties", "a URI or hyperlink to the Licensed Material to the extent reasonably practicable"; "indicate if You modified the Licensed Material and retain an indication of any previous modifications"; and "indicate the Licensed Material is licensed under this Public License, and include the text of, or the URI or hyperlink to, this Public License." It may be satisfied "in any reasonable manner based on the medium, means, and context", for example "by providing a URI or hyperlink to a resource that includes the required information." (https://creativecommons.org/licenses/by/4.0/legalcode.en, Section 3(a))
- Adapter's License (BY): "If You Share Adapted Material You produce, the Adapter's License You apply must not prevent recipients of the Adapted Material from complying with this Public License." (same, Section 3(a)(4))
- CC recommended attribution: "Title, Author, Source, and License" (TASL); title is "optional for the 4.0 suites". (https://wiki.creativecommons.org/wiki/Recommended_practices_for_attribution)
- ShareAlike: "The Adapter's License You apply must be a Creative Commons license with the same License Elements, this version or later, or a BY-SA Compatible License." (https://creativecommons.org/licenses/by-sa/4.0/legalcode.en, Section 3(b))
- NonCommercial: "NonCommercial means not primarily intended for or directed towards commercial advantage or monetary compensation." (https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en, Section 1) CC: "NonCommercial turns on the use, not the identity of the reuser." "CC cannot advise you on what is and is not commercial use." (https://wiki.creativecommons.org/wiki/NonCommercial_interpretation, https://creativecommons.org/faq/)
- NoDerivatives: the grant is to "reproduce and Share the Licensed Material, in whole or in part, for NonCommercial purposes only; and produce and reproduce, but not Share, Adapted Material for NonCommercial purposes only." (https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en, Section 2(a)(1)) Deed: "If you remix, transform, or build upon the material, you may not distribute the modified material." (https://creativecommons.org/licenses/by-nd/4.0/deed.en)
- Excerpts: "Generally, no derivative work is made of the original from which the excerpt was taken when the excerpt is used to illuminate an idea or provide an example in another larger work." "a person could make copies of one chapter of an ND-licensed book and not be in violation of the license", with exceptions "when the excerpts are combined with other material in a way that creates some new version of the original". (https://creativecommons.org/faq/)
- Facts: "even where database contents are subject to copyright and published under a CC license, use of the facts and ideas embedded within the contents will not require attribution (or compliance with other applicable license conditions)". (https://creativecommons.org/faq/)
- What an adaptation is: "An adaptation is a work based on one or more pre-existing works. What constitutes an adaptation depends on applicable law". (https://creativecommons.org/faq/)
- CC0: the Affirmer "waives, abandons, and surrenders all of Affirmer's Copyright and Related Rights ... for any purpose whatsoever, including without limitation commercial, advertising or promotional purposes". "No trademark or patent rights held by Affirmer are waived". (https://creativecommons.org/publicdomain/zero/1.0/legalcode.en)

### US law: facts and data

- 17 U.S.C. 102(b): "In no case does copyright protection for an original work of authorship extend to any idea, procedure, process, system, method of operation, concept, principle, or discovery, regardless of the form in which it is described, explained, illustrated, or embodied in such work." (https://www.law.cornell.edu/uscode/text/17/102)
- Feist Publications, Inc. v. Rural Telephone Service Co., 499 U.S. 340 (1991): "That there can be no valid copyright in facts is universally understood." Facts "do not owe their origin to an act of authorship, they are not original, and thus are not copyrightable." "copyright in a factual compilation is thin. Notwithstanding a valid copyright, a subsequent compiler remains free to use the facts contained in another's publication to aid in preparing a competing work, so long as the competing work does not feature the same selection and arrangement." (https://supreme.justia.com/cases/federal/us/499/340/)
- 17 U.S.C. 107 (fair use) lists purposes "such as criticism, comment, news reporting, teaching ..., scholarship, or research" and four factors, including "the amount and substantiality of the portion used" and "the effect of the use upon the potential market". (https://www.law.cornell.edu/uscode/text/17/107)

### Does a summary or a new chart from the paper's facts count as an adaptation?

- Documented: a CC license only reaches material "in a manner requiring permission under the Copyright and Similar Rights" (definition of Adapted Material), and facts, ideas, and discoveries are outside copyright (17 U.S.C. 102(b); Feist). CC's FAQ says using embedded facts does not require compliance with license conditions.
- Legal judgment: an explainer written in original words and a chart drawn fresh from numbers the paper reports use facts, not protected expression, so they are not Adapted Material under any CC license, ND included, and need no license at all. That conclusion fails where the output copies protected expression: close paraphrase of sentences, the same selection and arrangement of a figure (layout, styling, annotations), or a traced or re-styled copy of a figure. Where that line falls for a given page is a case-by-case legal judgment. Database rights (EU sui generis) are outside this US analysis.
- Legal judgment: citing the paper (title, authors, DOI, link) is good scholarly practice and is required by license only when licensed material itself is shared.

### Per license class

| License | Reuse figures verbatim | Adapt figures | Quote abstract in full | Attribution |
|---|---|---|---|---|
| CC0 | Yes (CC0 waiver). Third-party images inside may still be protected (PMC notice above). | Yes | Yes | None required by CC0. bioRxiv's FAQ: reuse "without crediting the original authors or source" (https://www.biorxiv.org/about/FAQ). |
| CC BY | Yes | Yes; mark the change | Yes | Section 3(a): creator, copyright notice, license notice and link, warranty-disclaimer notice, link to material, note modifications. |
| CC BY-SA | Yes | Yes; the adapted figure must carry BY-SA 4.0 or a compatible license (Section 3(b)) | Yes | As CC BY, plus the Adapter's License link. |
| CC BY-NC | Only for NonCommercial use (legal judgment whether Paperboy's use qualifies) | Same | Same | As CC BY. |
| CC BY-NC-SA | Same as BY-NC | NonCommercial only, adapted figure under BY-NC-SA | Same as BY-NC | As BY-SA. |
| CC BY-ND | Yes, unmodified (format changes allowed, Section 2(a)(4)) | No (may not Share Adapted Material) | Yes, verbatim | As CC BY. |
| CC BY-NC-ND | NonCommercial only, unmodified | No | NonCommercial only, verbatim | As CC BY. |
| arXiv non-exclusive 1.0 | No, needs permission from submitter or copyright holder (https://info.arxiv.org/help/license/reuse.html) | No | Yes: arXiv metadata, including the abstract, is CC0 (https://info.arxiv.org/help/api/tou.html) | None for CC0 metadata; arXiv encourages linking to the abstract page. |
| Publisher all rights reserved (and bioRxiv "No reuse", OpenAlex `other-oa`/`publisher-specific-oa`/null) | No, without permission or a fair use defense (legal judgment) | No | Abstract copyright "held by publisher or author" (Crossref); full display relies on fair use (legal judgment) | n/a, link out. |

## 7. Titles and abstracts of paywalled papers

- Crossref: "Almost all of the metadata we hold is reusable without restriction, with the exception of abstracts which are subject to publisher or author copyright. The majority of metadata is considered to be 'facts' which are not copyrightable and are thus in the public domain (CC0). The agreement we have with our members permits us to distribute abstracts, but they retain the license under which they were published." (https://www.crossref.org/documentation/retrieve-metadata/)
- OpenAlex: "OpenAlex does not ship plaintext abstracts for legal reasons". (https://help.openalex.org/data/works/attributes.md) The snapshot docs: "Not every work has an abstract (availability and publisher restrictions)". (https://help.openalex.org/access/snapshot.md)
- NCBI: "NLM does not claim the copyright on the abstracts in PubMed; however, journal publishers or authors may." (https://www.ncbi.nlm.nih.gov/home/about/policies/)
- arXiv: abstracts are descriptive metadata under CC0. (https://info.arxiv.org/help/api/tou.html)
- DOAJ: article metadata under a CC0 waiver. (https://doaj.org/terms/)
- Semantic Scholar: abstracts dataset under ODC-BY, with third-party content "subject to separate license terms". (https://api.semanticscholar.org/datasets/v1/release/latest, https://www.semanticscholar.org/product/api/license)
- Titles: Crossref classes bibliographic metadata as "Facts, not subject to copyright". (https://www.crossref.org/documentation/retrieve-metadata/) A US primary source ruling that article titles are not copyrightable: NOT FOUND in this research.
- Legal judgment: for a paywalled paper, title, authors, venue, date, and DOI are safe to show. A short card written in original words from the abstract's facts is the 102(b)/Feist position. Reproducing the full abstract of an all-rights-reserved paper depends on fair use. Individual publisher abstract policies: NOT FOUND (not researched per publisher).

## 8. Open source license for the app, and a license for generated content

### Comparison

| Point | GPL-3.0 | AGPL-3.0 | Apache-2.0 | MIT (Expat) |
|---|---|---|---|---|
| Copyleft | Yes. Object code may be conveyed only with Corresponding Source (Section 6). | Yes, plus network clause (Section 13). | No | No |
| Patent grant | Explicit (Section 11) | Explicit (same as GPLv3) | Explicit, with termination on patent suit (Section 3) | None stated in the text |
| Closed fork possible | No, if the fork is distributed | No, if distributed or, when modified, offered over a network | Yes | Yes |
| Apache-2.0 libraries | Compatible (FSF) | Compatible (FSF, via GPLv3 terms) (legal judgment: FSF's statement names GPLv3; AGPLv3 Section 13 allows combining with GPLv3) | Same license | Compatible (one-way: MIT code into Apache works) (legal judgment) |
| F-Droid | Accepted | Accepted | Accepted | Accepted |
| Google Play | No documented conflict | No documented conflict | No documented conflict | No documented conflict |

Sources and quotes:

- GPLv3 Section 6: "You may convey a covered work in object code form under the terms of sections 4 and 5, provided that you also convey the machine-readable Corresponding Source". Section 11: "Each contributor grants you a non-exclusive, worldwide, royalty-free patent license under the contributor's essential patent claims". (https://www.gnu.org/licenses/gpl-3.0.txt)
- AGPLv3 Section 13: "if you modify the Program, your modified version must prominently offer all users interacting with it remotely through a computer network (if your version supports such interaction) an opportunity to receive the Corresponding Source of your version". (https://www.gnu.org/licenses/agpl-3.0.txt) Relevance (legal judgment): this is the only license here that would force someone running a modified copy of the Paperboy cloud pipeline or website as a service to publish their changes.
- Apache-2.0 Section 3: "each Contributor hereby grants to You a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable (except as stated in this section) patent license". Section 4 requires giving recipients "a copy of this License", marking modified files, retaining notices, and carrying the NOTICE file contents. Licensees "may provide additional or different license terms and conditions for use, reproduction, or distribution of Your modifications". (https://www.apache.org/licenses/LICENSE-2.0.txt)
- MIT: "Permission is hereby granted, free of charge, to any person obtaining a copy of this software ... to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies". (https://opensource.org/license/mit)
- FSF on Apache-2.0: "This is a free software license, compatible with version 3 of the GNU GPL. Please note that this license is not compatible with GPL version 2". "The patent termination provision is a good thing, which is why we recommend the Apache 2.0 license for substantial programs over other lax permissive licenses." On Expat: "compatible with the GNU GPL" and "For substantial programs it is better to use the Apache 2.0 license since it blocks patent treachery." On AGPLv3: "We recommend that developers consider using the GNU AGPL for any software which will commonly be run over a network." and "you are allowed to combine separate modules or source files released under both of those licenses in a single project". (https://www.gnu.org/licenses/license-list.html)
- Android: "Apache License, Version 2.0 (Apache 2.0) is the preferred license for AOSP, and the majority of Android software is licensed with Apache 2.0." (https://source.android.com/docs/setup/about/licenses)
- F-Droid: "All applications in the repository must be Free, Libre and Open Source Software (FLOSS)" and gives as examples software "released under a GPL or Apache license." It defers to DFSG, FSF, GNU and OSI. "The implementation of proprietary tracking or advertising libraries and analytics tools such as Google Play Services and Firebase and Crashlytics and proprietary ad/tracking SDKs are strictly forbidden". "F-Droid does not sign up for any API keys." (https://f-droid.org/docs/Inclusion_Policy/)
- F-Droid anti-features that may apply to a cloud-backed app: "Tethered Network Services" ("apps that depend entirely on a service which is impossible (or not easy) to replace"; not applied "if there is a simple configuration option that allows pointing the app to a running instance of an alternative, publicly available, self-hostable server solution"), "Non-Free Network Services" ("apps that promote or depend entirely on a proprietary network service"), and "Non-Free Assets" (artwork "under a license that restricts commercial usage or making derivative works (for example, any Creative Commons license with a "Non-Commercial" (NC) or "No Derivatives" (ND) restriction)"). (https://f-droid.org/docs/Anti-Features/) Legal judgment: NC/ND paper figures served from the cloud are not assets contained in the app; whether F-Droid reviewers see it that way: NOT FOUND.
- Google Play: the Developer Distribution Agreement (effective September 15, 2025) grants users "a nonexclusive, worldwide, and perpetual license to perform ... display ... and use the Product" (Section 5.3) and allows "a separate end user license agreement". (https://play.google/developer-distribution-agreement.html) Any Google Play rule against GPL or AGPL apps: NOT FOUND.
- Android developer verification (affects F-Droid installs): "Effective September 30, 2026 Protections begin for users installing apps from participating stores in select regions on certified Android devices. We'll continue rolling out user protections globally in 2027." The page links a guide to "Register an app on open-source registry". (https://developer.android.com/developer-verification) Its exact requirements for F-Droid-built apps: NOT FOUND (guide not read).

### License for the generated explainer content

- CC licenses should not be used for the code: FSF says CC BY "should not be used on software" and the same for CC BY-SA. (https://www.gnu.org/licenses/license-list.html)
- CC BY 4.0: FSF: "a non-copyleft free license ... compatible with all versions of the GNU GPL". (https://www.gnu.org/licenses/license-list.html)
- CC BY-SA 4.0: FSF: "one-way compatible with the GNU GPL version 3: this means you may license your modified versions of CC BY-SA 4.0 materials under GNU GPL version 3, but you may not relicense GPL 3 licensed works under CC BY-SA 4.0." (https://www.gnu.org/licenses/license-list.html)
- Embedding paper figures: "If the combination does not create an adaptation, then you may combine any CC-licensed content so long as you provide attribution and comply with the NonCommercial restriction if it applies." "The NoDerivatives licenses do not permit remixing except for private use". "if you create a remix with material licensed under a ShareAlike license, you need to make sure that all of the material contributed to the remix is licensed under the same license or one that CC has named as compatible". When using a yellow-box combination, "take additional care to mark the adaptation as involving multiple copyrights under different terms". (https://creativecommons.org/faq/) The color cells of the adapter's license chart did not survive text extraction: chart values NOT FOUND.
- CC licenses do not allow sublicensing: "Creative Commons licenses do not allow sublicensing, which means you cannot grant a license to a platform with respect to the rights in any CC-licensed content you do not own." (https://creativecommons.org/faq/)
- Legal judgment, options:
  - CC BY 4.0 for Paperboy's own text and charts, with each embedded paper figure labeled with its own license and attribution. Works with CC0, CC BY, and unmodified ND figures. Reusers get the most freedom; nothing forces them to keep derived pages open.
  - CC BY-SA 4.0 for Paperboy's own text and charts. Required if a page is itself an adaptation of a BY-SA paper; keeps derivatives open; reusers who want to mix with CC BY-only or proprietary material face more limits.
  - Either way, an embedded figure keeps the paper's license (Paperboy cannot relicense it, no sublicensing), so each figure needs its own notice, and NC figures stay NC inside a CC BY page.

## 9. Retractions and corrections

- Crossref: "In September 2023, we acquired the Retraction Watch database ... and have made it publicly available." "Retractions are included in the `update-to` field of json files in the REST API. Retractions and other updates from Retraction Watch are identified by a source field, which can have a value of `publisher` or `retraction-watch`." Example: `https://api.crossref.org/v1/works?filter=update-type:retraction`. CSV: `git clone https://gitlab.com/crossref/retraction-watch-data`, "updated once per working day". Columns include `RetractionNature` ("Retraction, Correction, Expression of concern, or Reinstatement"), `OriginalPaperDOI`, `RetractionDOI`, `Reason`. (https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/)
- License: "Open Funder Registry, Retraction Watch database: CC0". (https://www.crossref.org/documentation/retrieve-metadata/) Crossref asks for a citation when used in a published work: "if you make use of the Retraction Watch retraction metadata in a published work, we kindly request that you provide a citation to the source." (https://www.crossref.org/blog/retraction-watch-retractions-now-in-the-crossref-api/)
- To check one paper: `filter=updates:{DOI}` ("Is an update to the given DOI"), optionally with `update-type:retraction` or `update-type:correction`. (https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/) Note: `update-type:retraction` returns the notices; the retracted paper is the DOI in their `update-to`.
- OpenAlex: `filter=is_retracted:true`; the flag is refreshed from Retraction Watch daily ("a retraction added there usually shows here the next day"). (https://help.openalex.org/data/works/attributes.md) Type values `retraction` and `erratum` mark notices themselves. (https://help.openalex.org/data/work-types.md)
- Europe PMC and PMC: the PMC OA subset "includes retractions, corrections, and expressions of concern". (https://pmc.ncbi.nlm.nih.gov/tools/textmining/)

Live tests (trimmed):

```
GET https://api.crossref.org/v1/works?filter=update-type:retraction,from-created-date:2026-11-01&rows=1&select=DOI,type,title,update-to
{"total-results": 238,
 "items": [{"DOI": "10.1080/21655979.2026.2745458", "type": "journal-article",
   "title": ["Statement of Retraction: Long non-coding RNA HCG11 enhances osteosarcoma phenotypes ..."],
   "update-to": [{"DOI": "10.1080/21655979.2021.2010367", "type": "retraction", "label": "Retraction", "source": "publisher", "updated": {"date-time": "2026-11-05T00:00:00Z"}}]}]}

GET https://api.openalex.org/works?filter=is_retracted:true&per_page=1&select=id,doi,title,is_retracted
{"count": 144580, "results": [{"id": "https://openalex.org/W3046275966", "doi": "https://doi.org/10.1016/s0140-6736(20)30367-6",
  "title": "Dementia prevention, intervention, and care: 2020 report of the Lancet Commission", "is_retracted": true}]}

GET https://api.crossref.org/v1/works?filter=updates:10.1016/s0140-6736(20)30367-6
total 2
10.1016/s0140-6736(23)02043-3 ['Department of Error'] [('erratum', 'publisher')]
10.1016/s2468-2667(23)00083-x ['RETRACTED: Addressing hearing loss at all ages'] [('retraction', 'publisher') x4]
```

Observed: OpenAlex flags the 2020 Lancet Commission report as retracted. In Crossref, the record whose `update-to` points at that DOI with type `retraction` is itself titled "RETRACTED: Addressing hearing loss at all ages", a different paper. Legal judgment aside, this looks like a false positive inherited from publisher metadata (unconfirmed: the publisher's own retraction notice was not checked). Before badging a paper as retracted, check that the notice's title and DOI actually match.

## What the pipeline may do

"Full explainer" means an original page in Paperboy's words plus original charts built from reported numbers. Its permission rests on 17 U.S.C. 102(b) and Feist for every class (legal judgment), plus lawful access to the full text. "Abstract display" means showing the abstract verbatim.

| License class | Full explainer allowed | Verbatim figures allowed | Adapted figures allowed | Abstract display allowed | Required attribution |
|---|---|---|---|---|---|
| CC0 (and US government works) | Yes | Yes (check for third-party images) | Yes | Yes | None by license |
| CC BY | Yes | Yes | Yes, marked as modified | Yes | Creator, copyright notice, license name and link, disclaimer notice, link to source, note of changes (CC BY 3(a)) |
| CC BY-SA | Yes (legal judgment: if the page copies expression, the page must be BY-SA) | Yes | Yes, adapted figure under BY-SA 4.0 | Yes | As CC BY, plus BY-SA link for adapted figures |
| CC BY-NC | Yes from facts (legal judgment) | Only if Paperboy's use is NonCommercial (legal judgment) | Same | Same | As CC BY |
| CC BY-NC-SA | Yes from facts (legal judgment) | NonCommercial only (legal judgment) | NonCommercial only, under BY-NC-SA | NonCommercial only (legal judgment) | As CC BY-SA |
| CC BY-ND | Yes from facts (legal judgment: not Adapted Material) | Yes, unmodified | No | Yes | As CC BY |
| CC BY-NC-ND | Yes from facts (legal judgment) | NonCommercial only, unmodified (legal judgment) | No | NonCommercial only (legal judgment) | As CC BY |
| arXiv non-exclusive 1.0 | Yes from facts (legal judgment); link to arXiv for the PDF | No, needs permission | No | Yes (arXiv metadata is CC0) | None by license; link to the arXiv abstract page (encouraged) |
| Publisher all rights reserved (incl. bioRxiv no-reuse, `other-oa`, `publisher-specific-oa`, null) | Free full text: yes from facts (legal judgment). Paywalled: card only, per plan | No | No | No by right; fair use (legal judgment), unless the supplying source is CC0 for that record (arXiv) | Link out; cite title, authors, venue, DOI |

## Everything NOT FOUND

1. An OpenAlex statement on whether abstracts reconstructed from `abstract_inverted_index` may be redisplayed publicly.
2. An Unpaywall-specific data license statement.
3. An arXiv HTML-specific automated-access policy beyond robots.txt, the robots help page, and the API terms.
4. ar5iv terms of use.
5. arXiv-specific redistribution rules per CC license beyond "follow the license".
6. Why `rss.arxiv.org/rss/math` and `/math.CO` had 0 items at test time.
7. bioRxiv/medRxiv API rate limits and API terms of use.
8. A primary source mapping the bioRxiv API value `cc_no` to "No reuse/adaptation without permission".
9. chemRxiv's current API status, API documentation, and TDM terms (site blocks scripted clients).
10. Europe PMC REST API rate limits and key requirements.
11. The color values of CC's adapter's license chart (lost in text extraction).
12. Any Google Play rule against GPL-3.0 or AGPL-3.0 apps.
13. Requirements of Android developer verification for F-Droid-built apps (guide not read).
14. Whether F-Droid treats NC/ND figures served from a cloud backend as Non-Free Assets.
15. A US primary source ruling on the copyrightability of article titles.
16. Individual publisher policies on redisplaying abstracts.
17. Science, PNAS, and Cell terms of use and RSS terms (pages blocked scripted clients).
18. A Nature RSS-specific terms page.
19. Whether Elsevier's general website terms govern cell.com.
20. Whether Nature feed items for research papers carry author fields (only a news item was checked).
21. RSS or automated-access clauses in eLife and PLOS terms (none present).
