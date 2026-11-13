# Cloudflare hosting research for Paperboy

Researched 2026-11-12 against developers.cloudflare.com, the cloudflare/wrangler-action repo, and docs.github.com. Every claim carries a source key; the keys resolve to URLs in the Sources table. Numbers marked "estimate" are arithmetic on the cited limits plus an assumption that is stated next to them; they are not Cloudflare figures. "NOT FOUND" means the primary sources read for this file do not answer the point.

Local state checked: `wrangler --version` prints `4.106.0`. `wrangler r2 object --help` lists only `get`, `put`, and `delete` (no bulk command).

## Sources

| Key | URL |
| --- | --- |
| W-LIMITS | https://developers.cloudflare.com/workers/platform/limits/ |
| W-PRICING | https://developers.cloudflare.com/workers/platform/pricing/ |
| W-ASSETS-BILLING | https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/ |
| W-ASSETS | https://developers.cloudflare.com/workers/static-assets/ |
| W-ASSETS-HEADERS | https://developers.cloudflare.com/workers/static-assets/headers/ |
| W-ASSETS-BINDING | https://developers.cloudflare.com/workers/static-assets/binding/ |
| W-ASSETS-DIRECT | https://developers.cloudflare.com/workers/static-assets/direct-upload/ |
| W-MIGRATE-PAGES | https://developers.cloudflare.com/workers/static-assets/migration-guides/migrate-from-pages/ |
| W-CACHE | https://developers.cloudflare.com/workers/cache/ |
| W-CACHE-LIMITS | https://developers.cloudflare.com/workers/cache/limitations/ |
| W-CACHE-KEYS | https://developers.cloudflare.com/workers/cache/cache-keys/ |
| W-CACHE-CONFIG | https://developers.cloudflare.com/workers/cache/configuration/ |
| W-CACHE-API | https://developers.cloudflare.com/workers/runtime-apis/cache/ |
| W-HOW-CACHE | https://developers.cloudflare.com/workers/reference/how-the-cache-works/ |
| W-WORKERSDEV | https://developers.cloudflare.com/workers/configuration/routing/workers-dev/ |
| W-CUSTOMDOMAIN | https://developers.cloudflare.com/workers/configuration/routing/custom-domains/ |
| W-RATELIMIT | https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/ |
| W-GHA | https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/ |
| W-CMD-R2 | https://developers.cloudflare.com/workers/wrangler/commands/r2/ |
| W-CMD-D1 | https://developers.cloudflare.com/workers/wrangler/commands/d1/ |
| PAGES | https://developers.cloudflare.com/pages/ |
| PAGES-LIMITS | https://developers.cloudflare.com/pages/platform/limits/ |
| PAGES-FN-PRICING | https://developers.cloudflare.com/pages/functions/pricing/ |
| PAGES-DIRECT | https://developers.cloudflare.com/pages/get-started/direct-upload/ |
| PAGES-DOMAINS | https://developers.cloudflare.com/pages/configuration/custom-domains/ |
| R2-PRICING | https://developers.cloudflare.com/r2/pricing/ |
| R2-LIMITS | https://developers.cloudflare.com/r2/platform/limits/ |
| R2-PUBLIC | https://developers.cloudflare.com/r2/buckets/public-buckets/ |
| R2-UPLOAD | https://developers.cloudflare.com/r2/objects/upload-objects/ |
| R2-RCLONE | https://developers.cloudflare.com/r2/examples/rclone/ |
| R2-AWSCLI | https://developers.cloudflare.com/r2/examples/aws/aws-cli/ |
| R2-TOKENS | https://developers.cloudflare.com/r2/api/tokens/ |
| R2-HOW | https://developers.cloudflare.com/r2/how-r2-works/ |
| R2-POSTMAN | https://developers.cloudflare.com/r2/tutorials/postman/ |
| D1-LIMITS | https://developers.cloudflare.com/d1/platform/limits/ |
| D1-PRICING | https://developers.cloudflare.com/d1/platform/pricing/ |
| D1-SQL | https://developers.cloudflare.com/d1/sql-api/sql-statements/ |
| D1-IMPORT | https://developers.cloudflare.com/d1/best-practices/import-export-data/ |
| D1-MIGRATIONS | https://developers.cloudflare.com/d1/reference/migrations/ |
| KV-LIMITS | https://developers.cloudflare.com/kv/platform/limits/ |
| OBS-PRICING | https://developers.cloudflare.com/observability/pricing/ |
| WAE-PRICING | https://developers.cloudflare.com/analytics/analytics-engine/pricing/ |
| VEC-PRICING | https://developers.cloudflare.com/vectorize/platform/pricing/ |
| VEC-LIMITS | https://developers.cloudflare.com/vectorize/platform/limits/ |
| WAI-PRICING | https://developers.cloudflare.com/workers-ai/platform/pricing/ |
| AIS | https://developers.cloudflare.com/ai-search/ |
| AIS-PRICING | https://developers.cloudflare.com/ai-search/platform/limits-pricing/ |
| AIS-LLMS | https://developers.cloudflare.com/ai-search/llms.txt |
| WAF-RL | https://developers.cloudflare.com/waf/rate-limiting-rules/ |
| BOTS-BFM | https://developers.cloudflare.com/bots/get-started/bot-fight-mode/ |
| DDOS | https://developers.cloudflare.com/ddos-protection/ |
| CACHE-DEFAULT | https://developers.cloudflare.com/cache/concepts/default-cache-behavior/ |
| CACHE-RULES | https://developers.cloudflare.com/cache/how-to/cache-rules/ |
| CACHE-TIERED | https://developers.cloudflare.com/cache/how-to/tiered-cache/ |
| CACHE-ORIGIN-CC | https://developers.cloudflare.com/cache/concepts/cache-control/ |
| CACHE-PURGE | https://developers.cloudflare.com/cache/how-to/purge-cache/ |
| BILL-ACCRUE | https://developers.cloudflare.com/billing/understand/how-charges-accrue/ |
| BILL-OPTIMIZE | https://developers.cloudflare.com/billing/manage/optimize-costs/ |
| DNS-PARTIAL | https://developers.cloudflare.com/dns/zone-setups/partial-setup/ |
| TOKEN-PERMS | https://developers.cloudflare.com/fundamentals/api/reference/permissions/ |
| TOKEN-TEMPLATES | https://developers.cloudflare.com/fundamentals/api/reference/template/ |
| WA-README | https://github.com/cloudflare/wrangler-action (README) |
| WA-RELEASE | https://github.com/cloudflare/wrangler-action/releases/tag/v4.1.3 |
| GH-REPO-LIMITS | https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits |
| GH-ACTIONS-BILLING | https://docs.github.com/en/billing/concepts/product-billing/github-actions |

## 1. Free plan limits today

### Workers (Workers Free)

Account plan limits table [W-LIMITS] (page "Last updated Oct 29, 2026"):

| Feature | Workers Free | Workers Paid |
| --- | --- | --- |
| Requests | 100,000/day | No limit |
| CPU time | 10 ms | 5 min |
| Memory | 128 MB | 128 MB |
| Subrequests | 50/request | 10,000/request |
| Worker size | 64 MiB | 64 MiB |
| Worker startup time | 1 second | 1 second |
| Number of Workers | 100 | 500 |
| Cron Triggers per account | 5 | 250 |
| Static Asset files per Worker version | 20,000 | 100,000 |
| Individual Static Asset file size | 25 MiB | 25 MiB |

- Worker size is uncompressed: "There is no compressed size limit. Only the uncompressed bundle size counts." [W-LIMITS]
- Daily limit: "Accounts on the Workers Free plan have a daily request limit of 100,000 requests, resetting at midnight UTC. When a Worker exceeds this limit, Cloudflare returns **Error 1027**." [W-LIMITS] The limit is per account, not per Worker [W-LIMITS]. Pages Functions requests count toward the same quota: "you could use 50,000 Functions requests and 50,000 Workers requests to use your full 100,000 daily request usage." [PAGES-FN-PRICING]
- CPU time excludes I/O waits: "Waiting on network requests (such as `fetch()` calls, KV reads, or database queries) does **not** count toward CPU time." [W-LIMITS]
- Static assets: "Requests to static assets are free and unlimited." [W-PRICING] [W-ASSETS-BILLING] "There is no additional cost for storing Assets." [W-ASSETS-BILLING]
- Other static asset limits: `_headers` rules 100, `_redirects` total 2,100. "To use the increased file count limits in Wrangler, you must use version 4.34.0 or higher." [W-LIMITS] (local Wrangler 4.106.0 meets this.)
- D1 queries per Worker invocation on Free: 50 [D1-LIMITS]. Cache API calls per request on Free: 50, sharing the subrequest quota [W-LIMITS].

### Pages (Free plan)

[PAGES-LIMITS] (page "Last updated Sep 5, 2026"):

- Files: "Cloudflare Pages sites can contain up to 20,000 files on the Free plan." "Paid plans (such as Pro, Business, and Enterprise plans) can have up to 100,000 files per site. To enable this increased limit, set the environment variable `PAGES_WRANGLER_MAJOR_VERSION=4` in your Pages project settings."
- File size: "The maximum file size for a single Cloudflare Pages site asset is 25 MiB."
- Builds: Free = "1 build at a time", "Builds per month" 500. "Builds will timeout after 20 minutes."
- Projects: 100 per account. Custom domains per project on Free: 100.
- Direct Upload limits: Wrangler 20,000 files and 25 MiB per file; drag and drop 1,000 files [PAGES-DIRECT].
- Whether Direct Upload deployments (`wrangler pages deploy`) count against the 500 builds per month: NOT FOUND.

### R2

Free tier, monthly [R2-PRICING] (page "Last updated Oct 30, 2026"):

| | Free |
| --- | --- |
| Storage | 10 GB-month / month |
| Class A Operations | 1 million requests / month |
| Class B Operations | 10 million requests / month |
| Egress (data transfer to Internet) | Free |

- "The free tier only applies to Standard storage, and does not apply to Infrequent Access storage." [R2-PRICING]
- Paid rates (Standard): storage $0.015 / GB-month, Class A $4.50 / million, Class B $0.36 / million [R2-PRICING]. Usage rounds up to the next billing unit [R2-PRICING].
- Class A includes `ListObjects`, `PutObject`, `CopyObject`, `CreateMultipartUpload`, `UploadPart`, `CompleteMultipartUpload`. Class B includes `HeadObject` and `GetObject`. `DeleteObject` is free [R2-PRICING].
- Egress: "Egressing directly from R2, including via the Workers API, S3 API, and `r2.dev` domains does not incur data transfer (egress) charges and is free." [R2-PRICING]
- Limits: storage and objects per bucket unlimited; object key 1,024 bytes; single-part upload 5 GiB; "Maximum concurrent writes to the same object name (key)" 1 per second; Cloudflare REST API "rate limited to 1,200 requests per five minutes across all R2 REST API operations on your account." [R2-LIMITS]
- Activation: "You must purchase R2 before you can generate an API token." [R2-TOKENS] The Postman tutorial step "1. Purchase R2" assumes "you have made a Cloudflare account and purchased R2." [R2-POSTMAN] Whether purchasing R2 requires a payment method on file: NOT FOUND in the pages read. Whether R2 usage beyond the free tier can be capped instead of billed: NOT FOUND (the pricing page only describes billing beyond the free tier).

### D1

[D1-LIMITS] and [D1-PRICING] (both "Last updated Oct 30, 2026"):

| | Workers Free |
| --- | --- |
| Rows read | 5 million / day |
| Rows written | 100,000 / day |
| Storage | 5 GB (total) |
| Databases | 10 |
| Maximum database size | 500 MB |
| Maximum storage per account | 5 GB |
| Time Travel | 7 days |

- Row size, statement size: "Maximum string, `BLOB` or table row size" 2 MB; "Maximum SQL statement length" 100 KB; "Maximum bound parameters per query" 100 [D1-LIMITS].
- A `db.batch()` "counts as a single query" against the per-invocation limit [D1-LIMITS].
- Indexes: "Indexes will add an additional written row when writes include the indexed column" [D1-PRICING].
- Over the limit: "When your account hits the daily read and/or write limits, you will not be able to run queries against D1. D1 API will return errors" [D1-PRICING]. Daily limits reset at 00:00 UTC [D1-PRICING].

### KV

[KV-LIMITS] and [W-PRICING]:

| | Free |
| --- | --- |
| Reads | 100,000 reads per day |
| Writes to different keys | 1,000 writes per day |
| Writes to same key | 1 per second |
| Deletes, list requests | 1,000 / day each |
| Storage/account | 1 GB |
| Value size | 25 MiB |

"If you exceed any one of these limits, further operations of that type will fail with an error." [W-PRICING]

### Workers Logs and analytics

- Workers Logs today: Free "200,000 per day" log events, "3 Days" retention [W-PRICING].
- "Beginning December 1, 2026, Workers Logs will use Cloudflare Observability pricing." [W-PRICING] Observability Free plan: "Included ingestion" 0.5 GB per day, "Included storage" seven days of retention; "On Free, Cloudflare stops ingesting new data when you reach the daily limit." [OBS-PRICING]
- Log data per request: 256 KB [W-LIMITS].
- Workers Analytics Engine, Workers Free: 100,000 data points written per day, 10,000 read queries per day. "Currently, you will not be billed for your use of Workers Analytics Engine." [WAE-PRICING]
- Workers Logpush: "only available on the Workers Paid plan." [W-PRICING]

## 2. Design comparison for tens of thousands of explainers

Per-paper file count and byte size drive everything below. The pipeline's image count and image sizes are not given, so the estimates use stated assumptions.

### (A) Everything as static files (Workers static assets or Pages) with pre-built feed JSON

- Hard limit: 20,000 files per Worker version on Free (100,000 on Paid) [W-LIMITS]; Pages 20,000 files per site on Free [PAGES-LIMITS]. Every version must list every file: "Include every file path the new version needs, including unchanged files." [W-ASSETS-DIRECT]
- Estimate: at 5 files per paper (1 HTML, 1 hero, 3 figures, assumption), Free tops out near 4,000 papers; at 1 file per paper (images inlined into the HTML, assumption) near 20,000 papers minus site and feed files. Workers Paid ($5 per month minimum [W-PRICING]) raises this to 100,000 files [W-LIMITS].
- Cost: request and storage cost for assets is zero [W-PRICING] [W-ASSETS-BILLING].
- Operations: each batch is a new deployment. Unchanged files are not re-uploaded: "Unmodified files will not be returned in the `buckets` field (as they do not need to be re-uploaded) if they have recently been uploaded in previous versions of your Worker." [W-ASSETS-DIRECT] Version skew applies: "requests for HTML and its assets can use different versions." [W-ASSETS] Pages with Git integration builds on each push, 500 builds per month on Free [PAGES-LIMITS]; batches all day would consume that. A limit on Worker deployments per day: NOT FOUND.
- First hard limit: the 20,000 file count.

### (B) R2 for explainers and images, D1 for metadata, Worker serves the feed API

- Hard limit: 100,000 Worker requests per day, account-wide, then Error 1027 [W-LIMITS]. Both feed pages and explainer fetches pass through the Worker in this design.
- Caching does not remove that count. With Workers Caching on, "all requests to your Worker are billed at the standard Workers request rate ... whether the response comes from cache or from your Worker" and it bills "requests that are normally free: static asset requests" [W-CACHE]. Whether cache hits count toward the Free plan's 100,000 per day: NOT FOUND (the docs state billing on Paid, not the Free counter). The Cache API still runs the Worker on every request: "every request still executes your Worker on the way in." [W-CACHE-LIMITS]
- D1: 500 MB per database [D1-LIMITS]. Estimate: a row with a 384-float embedding stored as float32 BLOB (1,536 bytes) plus about 2 KB of text is about 3.5 KB, so about 140,000 papers per database before indexes; stored as JSON text (about 4 KB for the vector, assumption) about 80,000. Rows read 5 million per day [D1-PRICING] is not the first limit for indexed page queries (a 20-row page read is about 20 rows when the filter uses an index [D1-PRICING]).
- R2: same storage and Class A math as design C. Reads through the binding are Class B (`GetObject`) [R2-PRICING].
- Cost: R2 storage past 10 GB at $0.015 / GB-month [R2-PRICING]; Workers Paid needed past 100,000 requests per day [W-LIMITS].
- First hard limit: Worker requests per day.

### (C) R2 with a public custom domain (or r2.dev) plus static feed JSON shards

- r2.dev: "not intended for production usage and has a variable rate limit applied to it"; over "hundreds of requests/second" returns `429 Too Many Requests`; "Bandwidth (throughput) may also be throttled" [R2-LIMITS]. Caching, WAF, and bot features are "not available when using the `r2.dev` development url." [R2-PUBLIC] So C is production-viable only with a custom domain.
- Custom domain requirement: "The domain being used must have been added as a zone in the same account as the R2 bucket." [R2-PUBLIC] The non-Cloudflare-DNS route (partial CNAME setup) "is only available to customers on a Business or Enterprise plan." [DNS-PARTIAL]
- Cache hits skip R2: "Every cache hit avoids origin fetch costs, Argo routing charges, Workers execution, and R2 operations." [BILL-ACCRUE] "cached objects do not hit R2" [BILL-OPTIMIZE]. HTML and JSON are not cached by default: "The Cloudflare CDN does not cache HTML or JSON by default." [CACHE-DEFAULT] Cache Rules are available on Free, 10 rules [CACHE-RULES].
- Storage: 10 GB-month free [R2-PRICING]. Estimate of total papers inside the free 10 GB: 0.25 MB per paper about 40,000; 0.5 MB about 20,000; 1 MB about 10,000; 2 MB about 5,000. Past that, billing at $0.015 / GB-month (estimate: 50,000 papers at 1 MB is 50 GB, 40 GB billable, about $0.60 per month).
- Writes: Class A 1 million per month [R2-PRICING], about 33,333 per day on a 30-day month (arithmetic). Listing the bucket (`ListObjects`) is also Class A [R2-PRICING], so upload tools that list the destination spend from the same pool.
- Reads on cache miss: Class B 10 million per month [R2-PRICING], about 333,333 per day (arithmetic).
- No Worker involved, so the 100,000 per day limit does not apply to feed or explainer traffic.
- First limit: R2 storage free allowance (billing, not errors) for the scale described; with r2.dev instead of a custom domain, the r2.dev rate limit.

### Summary

| | First limit hit | Where | Result at the limit |
| --- | --- | --- | --- |
| A | 20,000 files per version (Free) | [W-LIMITS] [PAGES-LIMITS] | Deploy cannot include more files (exact error NOT FOUND) |
| B | 100,000 Worker requests per day | [W-LIMITS] | Error 1027 until midnight UTC |
| C | 10 GB-month R2 storage | [R2-PRICING] | Billed at $0.015 / GB-month |

Operational simplicity: A has no runtime code but needs a deploy per batch and hits the file cap; B has the most moving parts (Worker, D1 schema, migrations, R2) and the tightest free request cap; C has no runtime code for the feed and accepts direct uploads at any time, but needs a domain on Cloudflare and a Cache Rule.

## 3. Pages or Workers for new projects

The Pages docs landing page says: "Are you sure you want to use Pages? Workers supports most Pages use cases and offers a broader feature set. It is Cloudflare's primary platform for building applications. Start new projects with Workers." [PAGES]

The migration guide says: "Like Pages, requests for static assets on Workers are free, and Pages Functions invocations are charged at the same rate as Workers, so you can expect a similar cost structure." and "Unlike Pages, Workers has a distinctly broader set of features available to it, (including Durable Objects, Cron Triggers, and more comprehensive Observability)." [W-MIGRATE-PAGES]

## 4. Edge caching

### Worker responses

- Workers Caching (configured with `"cache": { "enabled": true }` in the Wrangler config) checks the cache before running the Worker and is controlled by the `Cache-Control` headers the Worker returns [W-CACHE] [W-CACHE-CONFIG]. "Workers Caching is **tiered by default**" and collapses concurrent requests for the same key [W-CACHE].
- It works on `workers.dev`: the cache "follows the Worker, not a zone" and a Worker can "run on `workers.dev`" [W-CACHE]; the quickstart verifies `cf-cache-status: HIT` against a `workers.dev` URL [W-CACHE].
- Zone cache settings do not apply to it: "Cache Rules, Cache Response Rules, Page Rules, cache level settings ... have no effect on a Worker's cache." [W-CACHE]
- Cache key includes path and query string and, by default, the Worker version: "Each deployed version has its own cache, so a new deployment does not serve responses written by a previous version." This can be turned off with `cache.cross_version_cache` [W-CACHE-KEYS].
- Limits: "At launch, all Workers Caching responses are subject to the Free plan size limit regardless of your account's plan." [W-CACHE-LIMITS] The Free cacheable size limit is 512 MB [CACHE-DEFAULT]. Purges from `ctx.cache.purge()` always use Free tier purge rate limits [W-CACHE-LIMITS]. "There is no API to pre-populate the cache" [W-CACHE-LIMITS].
- Billing: cache hits are billed at the request rate; CPU time is billed only when the Worker runs [W-CACHE] [W-PRICING]. Effect on the Free 100,000 per day counter: NOT FOUND.
- Cache API (`caches.default`): "Workers deployed to custom domains have access to functional `cache` operations." [W-CACHE-API] It is per data center: "the contents of the cache do not replicate outside of the originating data center" and it is "not compatible with tiered caching." [W-CACHE-API] For new Workers the docs say "prefer Workers Caching." [W-CACHE-LIMITS] An explicit statement on whether the Cache API stores anything on `workers.dev`: NOT FOUND (the page mentions `.workers.dev` only for query strings in redirect cache keys [W-CACHE-API]).
- Static assets from a Worker are cached automatically with tiered caching [W-ASSETS]; default header is `Cache-Control: public, max-age=0, must-revalidate`, overridable with a `_headers` file [W-ASSETS-HEADERS].

### R2 objects

- Through a custom domain: "Domain access through a custom domain allows you to use Cloudflare Cache to accelerate access to your R2 bucket." "By default, only certain file types are cached. To cache all files in your bucket, you must set a Cache Everything page rule." Cloudflare recommends Smart Tiered Cache [R2-PUBLIC]. Cache Rules on Free: 10 rules [CACHE-RULES]. Tiered Cache and Smart Topology: available on Free [CACHE-TIERED].
- Origin `Cache-Control` is respected by default on Free: "Free, Pro and Business customers have this feature enabled by default." [CACHE-ORIGIN-CC] `s-maxage` can set the edge TTL separately from `max-age` [CACHE-ORIGIN-CC]. Per-object `Cache-Control` can be set at upload with `wrangler r2 object put --cache-control` [W-CMD-R2].
- Purge on Free: URL, Hostname, Tag, Prefix, and Purge Everything are all available [CACHE-PURGE].
- Through r2.dev: no caching features [R2-PUBLIC].

## 5. Deploying from GitHub Actions

- Current major version: v4. Latest release v4.1.3, published 2026-09-24 [WA-RELEASE]. "The action now defaults to **Wrangler v4**." Usage: `uses: cloudflare/wrangler-action@v4` with `apiToken` and `accountId` inputs, plus `command`, `preCommands`, `postCommands`, `wranglerVersion`, `workingDirectory` [WA-README]. The README notes "Workers Previews require Wrangler **4.136.3 or newer**" [WA-README]; local Wrangler is 4.106.0.
- GitHub Actions cost: standard GitHub-hosted runner use is free "In public repositories" [GH-ACTIONS-BILLING].
- API token: the Cloudflare guide says to create a token from the **Edit Cloudflare Workers** template [W-GHA]. That template contains: Workers Routes Write (Zone), Workers Scripts Write, Workers KV Storage Write, Workers Tail Read, Workers R2 Storage Write, Account Settings Read (Account), User Details Read, User Memberships Read (User) [TOKEN-TEMPLATES]. It does not contain D1. Add "D1 Edit" ("Grants write access to D1") [TOKEN-PERMS]. R2 write access ("Workers R2 Storage Write") is already in the template [TOKEN-TEMPLATES]. The exact extra zone permissions Wrangler needs to create a Worker Custom Domain from CI: NOT FOUND.
- R2 S3 credentials are separate: an R2 API token yields an Access Key ID and Secret Access Key; permissions are Admin Read & Write, Admin Read only, Object Read & Write, Object Read only, and object permissions "can scope your token to a set of buckets." [R2-TOKENS] Endpoint: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` [R2-TOKENS].
- Many objects from CI:
  - Wrangler: "Wrangler supports uploading files up to 315 MB and only allows one object at a time. For large files or bulk uploads, use rclone or another S3-compatible tool." [R2-UPLOAD] Whether `wrangler r2 object put` goes through the Cloudflare REST API and so counts against the 1,200 requests per five minutes REST limit [R2-LIMITS]: NOT FOUND.
  - rclone: "You can use rclone to upload objects to R2 concurrently." [R2-RCLONE] Directory upload: `rclone copy /path/to/local/folder r2:bucket_name` [R2-UPLOAD]. Needs rclone v1.59 or greater; with object-level token permissions add `no_check_bucket = true` [R2-RCLONE]. Multipart uploads use at least three Class A operations [R2-RCLONE].
  - AWS CLI: `aws configure` with region `auto` and `--endpoint-url https://<ACCOUNT_ID>.r2.cloudflarestorage.com` [R2-AWSCLI].
  - For high throughput, Cloudflare points to "the S3-compatible API or Workers API" over the REST API [R2-LIMITS].
- D1 migrations from CI: `wrangler d1 migrations apply <DATABASE> --remote`. "When running the apply command in a CI/CD environment or another non-interactive command line, the confirmation step will be skipped, but the backup will still be captured." A failed migration is rolled back [W-CMD-D1]. Migration files live in `migrations/` and applied ones are tracked in the `d1_migrations` table [D1-MIGRATIONS].
- D1 bulk inserts from CI: `wrangler d1 execute <DATABASE> --remote --file=batch.sql` (with `--yes` to answer prompts) [W-CMD-D1] [D1-IMPORT]. File limit 5 GiB; split long `INSERT` statements to stay under the statement length limit (the guide's example splits 1,000 rows into groups of 250) [D1-IMPORT]; 100 KB per statement and 100 bound parameters [D1-LIMITS]. Remove `BEGIN TRANSACTION` and `COMMIT` from dumps [D1-IMPORT].
- Git repository size (relevant if content arrives as pushes): GitHub recommends staying within 10 GB on-disk, 3,000 entries per directory, and "Store programmatically generated files outside of Git, such as in object storage." Single object recommended maximum 1 MB, enforced at 100 MB; push size enforced at 2 GB; recommended push rate 6 per minute [GH-REPO-LIMITS].

## 6. Full-text search on the free plan

- D1 FTS5: supported. "FTS5 module for full-text search (including `fts5vocab`)." [D1-SQL] Caveat: "Export is not supported for virtual tables, including databases with virtual tables." Workaround: delete virtual tables, export, recreate [D1-IMPORT]. How FTS5 shadow-table writes and reads are counted as D1 rows written and read: NOT FOUND. FTS5 tables count toward storage like other tables ("Tables and indexes both count towards storage consumed" [D1-PRICING]); FTS index size per paper: NOT FOUND.
- Vectorize (GA) on Workers Free: 30 million queried vector dimensions per month, 5 million stored vector dimensions, 100 indexes [VEC-PRICING]. Max 1,536 dimensions per vector, 20,000,000 vectors per index, topK 50 with values or metadata [VEC-LIMITS]. Estimate: 5 million stored dimensions holds about 13,020 vectors at 384 dimensions or 6,510 at 768, below "tens of thousands" of papers.
- Workers AI: "10,000 Neurons per day at no charge"; past that requires Workers Paid at $0.011 / 1,000 Neurons; "If you exceed any one of the above limits, further operations will fail with an error." [WAI-PRICING] Embedding rates include `@cf/baai/bge-small-en-v1.5` 1,841 neurons per M input tokens, `@cf/baai/bge-m3` 1,075, `@cf/qwen/qwen3-embedding-0.6b` 1,075, `@cf/google/embeddinggemma-2` 154 [WAI-PRICING]. Estimate: 10,000 neurons per day is about 5.4M tokens per day on bge-small or about 9.3M on bge-m3.
- AI Search (the former AutoRAG; the docs have migration pages "from the legacy AutoRAG REST API endpoints" and "from the legacy env.AI.autorag() binding" [AIS-LLMS]): "Available on all plans" [AIS]. Workers Free: 100 instances, 100,000 files per instance, 1,000 semantic and 1,000 full-text queries per month included. "AI Search billing begins on December 1, 2026." Overage: full-text queries $0.10 per 1,000, semantic $0.75 per 1,000 [AIS-PRICING]. Whether Workers Free accounts can exceed the included queries or get errors: NOT FOUND.

## 7. Domains

- workers.dev: every Worker gets `<YOUR_WORKER_NAME>.<YOUR_SUBDOMAIN>.workers.dev`. "It's recommended to run production Workers on a Workers route or custom domain ... Your `workers.dev` subdomain is treated as a Free website and is intended for personal or hobby projects that aren't business-critical." [W-WORKERSDEV] Browser Integrity Check always runs there and cannot be turned off; "Automated clients that send some default library `User-Agent` headers (for example, the default Python `urllib` user agent) receive error 1010 before your Worker runs." Fix: send a descriptive `User-Agent` [W-WORKERSDEV]. Whether the default Android HTTP client user agents are blocked: NOT FOUND.
- pages.dev: "Your project will be served from `<PROJECT_NAME>.pages.dev`." [PAGES-DIRECT]
- r2.dev: development only, variable rate limit, 429 at "hundreds of requests/second", throughput may be throttled, no cache, WAF, or bot features [R2-LIMITS] [R2-PUBLIC]. "Avoid creating a CNAME record pointing to the `r2.dev` subdomain. This is an **unsupported access path**" [R2-PUBLIC].
- With a custom domain on Cloudflare:
  - Workers Custom Domains need "An active Cloudflare zone"; Cloudflare creates DNS records and certificates [W-CUSTOMDOMAIN]. Free fail-open or fail-closed behavior for the daily limit is a route setting [W-LIMITS].
  - R2 custom domains need the domain as a zone in the same account, and unlock Cloudflare Cache, WAF custom rules, Access, and bot features [R2-PUBLIC].
  - Pages: apex domains need the site as a Cloudflare zone; subdomains can use a CNAME at another DNS provider [PAGES-DOMAINS].
  - WAF rate limiting rules, Cache Rules, Bot Fight Mode are zone features (see section 8) [WAF-RL] [CACHE-RULES] [BOTS-BFM].

## 8. Abuse protection for a public read API on the free plan

- WAF rate limiting rules, Free plan: 1 rule; expression fields Path and Verified Bot; counting by IP; counting period 10 s; mitigation timeout 10 s; "Cache exclusion" No [WAF-RL]. Counters are per data center and approximate [WAF-RL]. Requires a zone you own; workers.dev and r2.dev are not your zone (inferred from [W-WORKERSDEV] and [R2-PUBLIC]; no page states this for rate limiting rules directly: NOT FOUND as an explicit statement).
- Worker rate limit binding: configured under `ratelimits` with `name`, integer `namespace_id`, and `simple: { limit, period }` where period "Must be either `10` or `60`"; "Rate limits are approximate and apply separately in each Cloudflare location." [W-RATELIMIT] Free plan availability: NOT FOUND (the page has no plan statement). Inference, not stated on the page: a request the binding rejects has already invoked the Worker, so it still counts as an inbound Worker request [W-PRICING].
- Bot Fight Mode: "a simple, free product"; it protects entire domains, "Cannot be customized, adjusted, or reconfigured via WAF custom rules", and "they may challenge API or mobile app traffic." [BOTS-BFM]
- DDoS: "Standard, unmetered DDoS protection (layers 3-7)" on Free [DDOS].
- Over the Workers Free daily limit: errors, not billing. Error 1027 until midnight UTC; on routes, fail open bypasses the Worker and fail closed returns the 1027 page [W-LIMITS]. With static assets and `run_worker_first`, "If you exceed your free tier request limits, these requests will receive a 429 (Too Many Requests) response instead of falling back to static asset serving." [W-ASSETS-BILLING] D1, KV, and Workers AI also return errors past their Free limits [D1-PRICING] [W-PRICING] [WAI-PRICING]. R2 bills past its free tier rather than erroring [R2-PRICING].
- CPU cap as a cost guard on Paid: "configure the maximum amount of CPU time that can be used per invocation" to prevent "denial-of-wallet attacks" [W-PRICING].

## 9. APK download and marketing site on the same account

- Workers static assets and Pages: 25 MiB per file [W-LIMITS] [PAGES-LIMITS]. A 10 to 40 MB APK fits only at the low end (25 MiB is about 26.2 MB).
- Pages points large files to R2: "To serve larger files, consider uploading them to R2 and utilizing the public bucket feature." [PAGES-LIMITS]
- R2: single-part upload up to 5 GiB [R2-LIMITS]; Wrangler upload up to 315 MB [R2-UPLOAD]. The APK extension is on the default cached list [CACHE-DEFAULT], and Free cacheable size is 512 MB [CACHE-DEFAULT]. Egress is free [R2-PRICING].
- Static assets ignore `Range`: "Workers returns `200 OK` with the full file instead of `206 Partial Content`" [W-ASSETS-BILLING]. Range support on R2 custom domain downloads: NOT FOUND in the pages read.
- The marketing site fits Workers static assets: free and unlimited asset requests [W-PRICING].

## Recommended architecture

Open decision for Noah before building: this layout assumes a domain added to the Cloudflare account as a full-setup zone. R2 custom domains require that [R2-PUBLIC], and the CNAME alternative needs Business [DNS-PARTIAL]. Without a domain, the choices are r2.dev (development only, rate limited [R2-LIMITS]) or routing all content through a `workers.dev` Worker (100,000 requests per day [W-LIMITS]) or static assets (20,000 files [W-LIMITS]). `paperboy.example` below stands for that domain.

### Layout

| Product | Name | Holds | Why (citation) |
| --- | --- | --- | --- |
| Worker with static assets | `paperboy-web` | Marketing site, privacy page, download page | Cloudflare says start new projects on Workers [PAGES]; asset requests free and unlimited [W-PRICING] |
| Same Worker, script | `paperboy-web` | `/api/*` only (search, later) | `run_worker_first: ["/api/*"]` sends only those paths to the script [W-ASSETS-BINDING] |
| R2 bucket | `paperboy-content` | Feed shards, explainers, images, APK | No file cap, free egress, 10 GB free storage [R2-LIMITS] [R2-PRICING] |
| R2 custom domain | `content.paperboy.example` | Public reads of the bucket | Cache hits skip R2 operations [BILL-ACCRUE]; r2.dev is not for production [R2-LIMITS] |
| Cache Rule | 1 of 10 on Free | Cache everything on `content.paperboy.example` | HTML and JSON not cached by default [CACHE-DEFAULT] [CACHE-RULES] |
| Smart Tiered Cache | zone setting | Upper tier near the bucket | Recommended for R2, free [R2-PUBLIC] [CACHE-TIERED] |
| D1 database | `paperboy` | `papers` table + `papers_fts` FTS5 table (search phase only) | FTS5 supported [D1-SQL] |
| WAF rate limiting rule | 1 rule on Free | Path starts with `/api/`, per IP, 10 s | Free plan rule shape [WAF-RL] |
| r2.dev | disabled | n/a | Bucket stays public via r2.dev unless disabled [R2-PUBLIC] |
| Bot Fight Mode | off | n/a | Can challenge mobile app traffic, cannot be scoped [BOTS-BFM] |

Bindings in `paperboy-web` (`wrangler.jsonc`):

- `ASSETS`: static assets binding, `run_worker_first: ["/api/*"]` [W-ASSETS-BINDING].
- `DB`: D1 database `paperboy` [D1-MIGRATIONS].
- `SEARCH_LIMITER`: `ratelimits` entry, `simple.period` 60 [W-RATELIMIT].
- `cache.enabled: true` for search responses with `Cache-Control: public, max-age=...` [W-CACHE-CONFIG]. Note each deploy starts a new cache unless `cross_version_cache` is set [W-CACHE-KEYS].

No R2 binding is needed: the Worker does not read R2 in this layout, and CI writes over the S3 API [R2-RCLONE].

### Request paths

| Path | Served by | Cache-Control set at upload (design choice; header support per [CACHE-ORIGIN-CC] [W-CMD-R2]) |
| --- | --- | --- |
| `https://paperboy.example/` and site pages | Worker static assets | `_headers` file [W-ASSETS-HEADERS] |
| `https://content.paperboy.example/feed/v1/head.json` (newest chunk number per field) | R2 via CDN | short, for example `max-age=60` |
| `https://content.paperboy.example/feed/v1/new/all/{n}.json` | R2 via CDN | closed chunks `max-age=31536000, immutable`; open chunk short |
| `https://content.paperboy.example/feed/v1/new/{field}/{n}.json` | R2 via CDN | same as above |
| `https://content.paperboy.example/feed/v1/best/{field}.json` (top N, rebuilt per batch) | R2 via CDN | short |
| `https://content.paperboy.example/papers/{id}/index.html` | R2 via CDN | long |
| `https://content.paperboy.example/papers/{id}/{image}` | R2 via CDN | long |
| `https://content.paperboy.example/apk/paperboy-{version}.apk` | R2 via CDN | long; APK cached by default [CACHE-DEFAULT] |
| `https://paperboy.example/api/v1/search?q=...&field=...` (later) | Worker + D1 FTS5 | Workers Caching [W-CACHE] |

Chunks are numbered from the oldest paper so a closed chunk never changes and can be cached long; only `head.json`, the open chunk, and `best/*.json` change per batch. The value of N for "best" and the chunk size are product decisions not settled here.

### Publishing

- Pipeline or GitHub Action uploads with `rclone copy <dir> r2:paperboy-content` using an R2 token with Object Read & Write scoped to `paperboy-content` [R2-UPLOAD] [R2-TOKENS] [R2-RCLONE]. Direct upload from the pipeline avoids storing generated files in Git, which GitHub recommends [GH-REPO-LIMITS].
- Worker deploys and D1 work run in `cloudflare/wrangler-action@v4` [WA-README] with a token from the Edit Cloudflare Workers template plus D1 Edit [TOKEN-TEMPLATES] [TOKEN-PERMS]: `deploy`, `d1 migrations apply paperboy --remote`, `d1 execute paperboy --remote --file=batch.sql` [W-CMD-D1].
- Runners are free in a public repo [GH-ACTIONS-BILLING].

### Free-tier ceilings of this layout

Estimates use these assumptions: 5 R2 objects per paper (HTML, hero, 3 figures), 1 MB per paper total, about 2,000 shard writes per day for batch overhead (48 batches times about 42 shard files).

| Resource | Free allowance | Ceiling (estimate) | At the ceiling |
| --- | --- | --- | --- |
| R2 Class A writes | 1M / month [R2-PRICING] | (33,333 - 2,000) / 5, about 6,200 papers per day | Billed $4.50 / million |
| R2 storage | 10 GB-month [R2-PRICING] | about 10,000 papers total at 1 MB each (40,000 at 0.25 MB) | Billed $0.015 / GB-month |
| R2 Class B reads (cache misses only) | 10M / month [R2-PRICING] | about 333,000 misses per day | Billed $0.36 / million |
| Feed, explainer, APK, site requests | No Worker invocations | No daily cap found in the docs read (NOT FOUND) | n/a |
| Search requests | 100,000 / day, account-wide [W-LIMITS] | under 100,000 per day, shared with the owner's other Workers and Pages Functions [PAGES-FN-PRICING] | Error 1027 [W-LIMITS] |
| D1 rows written (search index) | 100,000 / day [D1-PRICING] | at most 100,000 papers per day at 1 row each; FTS5 row accounting NOT FOUND | Errors [D1-PRICING] |
| D1 size | 500 MB [D1-LIMITS] | depends on FTS5 index size, NOT FOUND | Inserts blocked [D1-PRICING] |

First limit this layout hits: the 10 GB-month R2 free storage allowance, at roughly 10,000 papers if each paper averages 1 MB (scales inversely with real per-paper size). It is a billing threshold, not an outage. The first hard (error) limit is the account-wide 100,000 Worker requests per day, and it applies only to search.

### NOT FOUND

1. Whether Pages Direct Upload deployments count against the 500 builds per month.
2. Whether purchasing R2 requires a payment method on file.
3. Whether R2 spend past the free tier can be capped instead of billed.
4. Whether Workers Caching cache hits count toward the Workers Free 100,000 requests per day.
5. An explicit statement on whether the Cache API stores responses on `workers.dev`.
6. The exact deploy error when static assets exceed 20,000 files.
7. Any limit on Worker deployments or versions per day.
8. Whether `wrangler r2 object put` uses the Cloudflare REST API and its 1,200 requests per five minutes limit.
9. The extra zone permissions a CI token needs for Wrangler to create a Worker Custom Domain.
10. How D1 counts rows read and written for FTS5 shadow tables, and FTS5 index size per row.
11. Whether Workers Free accounts get errors or overage after the AI Search included queries.
12. Plan availability of the Workers rate limit binding.
13. An explicit statement that WAF rate limiting rules cannot apply to `workers.dev` or `r2.dev` hostnames.
14. Whether default Android HTTP client user agents trigger error 1010 on `workers.dev`.
15. Range request support for R2 objects served through a custom domain.
16. Any daily request cap on cached CDN traffic for a Free zone.
