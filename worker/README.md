# Paperboy worker

The edge worker at https://paperboy.ntrpydev.workers.dev. It is the content base the app loads the feed and explainers from.

## What it serves

- `/` and other site pages: static assets from `../site`.
- `/kit/v1/*`, `/kit/v2/*`, and every later kit version: static assets, a copy of `../kit`. Old kit versions stay served.
- `/owner/numbers`: the owner's numbers page, below. Paid worker only, behind a password.
- `/v1/*`: the subscription API, below. Always handled by the Worker, never by static assets (`run_worker_first` in `wrangler.jsonc`).
- `/feed/*` and `/papers/*`: files from the R2 bucket `paperboy-content`. On a miss the worker fetches the file from `https://raw.githubusercontent.com/NtrpyDev/paperboy-content/main/<path>`, stores it in the bucket, and serves it. `/papers/<id>/` serves that folder's `index.html`.

The feed is in `feed/v2/`: `head.json`, `chunks/<6 digits>.json`, and `upgrades.json`. Each feed version has its own folder, `feed/v<N>/`, and a chunk is judged open or closed by the head in its own folder (`feed/v<N>/head.json`). `feed/v1/` is the feed published before every paper needed a page; when the feed restarted in `feed/v2/` it was left as a stub, a head with no chunks and `min_app` 2 so a 0.1.0 install shows its update cover, and its chunks are 404.

Files under `feed/` and `papers/` are either fixed or changing:

- Fixed: everything under `papers/`, and every closed chunk (a chunk lower than its folder's head's `chunk_count` that holds all 40 items). Stored once and served with `cache-control: public, max-age=31536000, immutable`.
- Changing: every `feed/v<N>/head.json`, the open chunk, and any other file under `feed/`. Fetched again when the stored copy is older than 60 seconds; if the content repo fails, the stored copy is served, and if the content repo no longer has the file, the stored copy is deleted and the answer is 404. Served with `cache-control: public, max-age=60`.

A chunk stored while it was open is fetched again after it closes, and keeps being refreshed until it holds 40 items, because the raw host caches files for up to five minutes and can hand out the copy from before the last items.

Every response from the bucket carries `x-paperboy-source: origin` (fetched from the content repo for this request) or `bucket` (read from the bucket). HTML from `papers/` carries the explainer content security policy. Files under `feed/` carry `access-control-allow-origin: *` while the content gate is off.

Paths outside `feed/` and `papers/` that are not assets, and files the content repo does not have, are 404. A file the bucket does not have while the content repo is unreachable is 502.

## Commands

Run from this folder after `npm install`.

| Command | What it does |
| --- | --- |
| `npm test` | Assembles the assets and runs every worker test. |
| `npm run typecheck` | Regenerates the binding types and runs `tsc`. |
| `npm run build` | Assembles `public/` from `../site` and every kit version in `../kit`. |
| `npm run deploy` | Assembles the assets and deploys the worker as it runs today, with no subscriber database. |
| `npm run deploy -- --env paid` | Assembles the assets and deploys the paid worker, with the subscriber database. Only after the going live steps below. |

The tests come in two vitest projects. `handler` runs the worker's handler inside the Workers runtime with the `paid` environment's bindings: a local bucket, a local D1 database with `migrations/` applied, a fake content repo, and a fake Google (`test/handler/fake-google.ts`, which generates its own RSA keys for the service account and for Pub/Sub push tokens). `../schema/fixtures/cost/` is read by both the worker's tests and `pipeline/tests/test_cost_fixture.py`. `assets` starts the whole worker with wrangler's test harness to check the static assets and that `/v1/*` reaches the worker, because the Workers test pool does not serve assets.

`wrangler deploy` with no `--env` prints a warning that several environments are defined. It deploys the top level, today's worker.

## Subscriptions

A subscriber is known by the Google Play purchase token; there are no accounts. The app sends its token to `POST /v1/entitlement`, the worker asks Google for the subscription's state, and an entitled subscriber gets a pass that opens the feed and explainers when the content gate is on. The contract is Contract 1 in the paid app spec; the JSON schemas are in `../schema/`.

Source files: `src/subscriptions.ts` (the three endpoints and the mapping from Google's states), `src/google.ts` (service account access token and the Play Developer API), `src/push.ts` (Pub/Sub push verification), `src/pass.ts` (the pass), `src/store.ts` (D1 queries), `migrations/` (the D1 schema).

### Endpoints

Every `/v1/` answer is JSON with `cache-control: no-store`, except `GET /v1/active-fields`, which is `public, max-age=60`. A method other than the ones listed is 405 with an `allow` header; an unknown `/v1/` path is 404 `{"error":"not_found"}`. Error bodies follow `../schema/api-error.schema.json`.

**`POST /v1/entitlement`.** Body `{"purchase_token", "product_id", "fields"}` (`../schema/entitlement-request.schema.json`): `fields` is 1 to 11 distinct field wire values, the product id is in Play's format, the token is 1 to 2048 printable ASCII characters, no other keys, at most 8 KiB. The worker calls `purchases.subscriptionsv2.get`, writes the subscriber row with the fields, acknowledges the purchase when Google reports `ACKNOWLEDGEMENT_STATE_PENDING` on a purchase that has left the pending state, and answers 200 `{"entitled", "state", "expires_at", "pass", "pass_expires_at"}` (`../schema/entitlement.schema.json`).

| Google's `subscriptionState` | `state` | Entitled |
| --- | --- | --- |
| `SUBSCRIPTION_STATE_ACTIVE` with `offerPhase.freeTrial` on the line item | `trial` | yes |
| `SUBSCRIPTION_STATE_ACTIVE` otherwise | `active` | yes |
| `SUBSCRIPTION_STATE_IN_GRACE_PERIOD` | `grace` | yes |
| `SUBSCRIPTION_STATE_ON_HOLD` | `on_hold` | no |
| `SUBSCRIPTION_STATE_PAUSED` | `paused` | no |
| `SUBSCRIPTION_STATE_CANCELED` | `canceled` | until `expires_at` |
| `SUBSCRIPTION_STATE_CANCELED` with `canceledStateContext.replacementCancellation` (another purchase replaced it) | `expired` | no |
| `SUBSCRIPTION_STATE_PENDING` | `pending` | no |
| `SUBSCRIPTION_STATE_EXPIRED`, `SUBSCRIPTION_STATE_PENDING_PURCHASE_CANCELED`, anything else | `expired` | no |

`expires_at` is the latest `expiryTime` among the line items. Errors: 400 `bad_request`; 404 `unknown_purchase` when Google answers 404, 410, or 400 for the token; 502 `store_unreachable` when Google or its token endpoint cannot be reached or answers anything else; 503 `not_configured` when the database, `PASS_SECRET`, the service account secret, or the package name is missing. A token Google did not know is answered 404 for the next 5 minutes without asking Google again (the `unknown_purchases` table holds only the token's hash and a time).

**`POST /v1/rtdn`.** The Pub/Sub push endpoint for Play Real-time Developer Notifications. The `Authorization: Bearer` JWT must be RS256, signed by a key listed at `https://www.googleapis.com/oauth2/v3/certs` (cached for the response's `max-age`), with `iss` `https://accounts.google.com` or `accounts.google.com`, `aud` equal to `RTDN_AUDIENCE`, `email` equal to `RTDN_SERVICE_ACCOUNT`, `email_verified` true, and `exp` in the future; otherwise 401. For a verified message about one of this app's subscriptions (`subscriptionNotification`, or `voidedPurchaseNotification` with `productType` 1) the worker reads the token's state from Google, updates the row, and acknowledges a new purchase; then 204. Test notifications, other apps' notifications, unknown tokens, and bodies it cannot read are 204 too. When Google or its keys cannot be reached the answer is 502, so Pub/Sub sends the message again.

**`GET /v1/active-fields`.** `{"v": 1, "fields": [...], "updated_at": "<now>"}` (`../schema/active-fields.schema.json`): the sorted fields of every subscriber whose state is `active`, `grace`, `canceled` with `expires_at` in the future, or `trial` when `COUNT_TRIALS` is `true`. No counts.

### Fields that carry over

A purchase that replaces another (Google's `linkedPurchaseToken` for an upgrade, downgrade, or resubscribe before expiry, or `outOfAppPurchaseContext.expiredPurchaseToken` for a resubscribe from the Play Store after expiry) takes over the old row: when the new token arrives without fields (a notification), it gets the old row's fields, and the old row is deleted. The app's next entitlement call sets the fields it sends.

### The pass

`v1.<P>.<S>`: `P` is base64url without padding of `{"exp": <epoch seconds>, "sub": "<first 16 hex chars of SHA-256 of the purchase token>"}`, and `S` is base64url without padding of HMAC-SHA256 over `v1.<P>` with `PASS_SECRET`. `exp` is the earlier of the subscription's expiry and 48 hours from now; when Google still calls a subscription entitled after its expiry has passed (around a renewal), the pass lasts one hour. Signatures are compared in constant time. Without `PASS_SECRET` no pass is ever minted: entitlement answers 503.

### The content gate

`CONTENT_GATE` is `off` by default. When it is `on`, every request under `/feed/` and `/papers/` needs a valid, unexpired pass in the `x-paperboy-pass` header or the `pb_pass` cookie (either one is enough). Otherwise the answer is 401 `{"error":"pass_required"}` (missing, malformed, or wrongly signed) or 401 `{"error":"pass_expired"}` (a correctly signed pass past its `exp`), and the content repo is not asked. Gated responses are served with `cache-control: private` in place of `public`, with the same max-age rules, and without `access-control-allow-origin`: the app reads the feed natively and its pages same-origin, so no other origin needs to read a subscriber's copy. `/`, the site, `/kit/`, and `/v1/active-fields` stay public. With the gate on and no `PASS_SECRET` the gated paths answer 503 `not_configured`.

### The owner's numbers page

`GET /owner/numbers` is the one place income and API cost show side by side, built to the board `design/canvas/project/Owner-Numbers.dc.html` and rendered by the worker with no JavaScript (`src/owner.ts`). It asks for HTTP Basic authentication: any username, and the password in the secret `OWNER_PASSWORD`, compared in constant time. Without that secret, or on the worker without the subscriber database, every `/owner/` path is 404. Answers carry `cache-control: no-store`, `x-robots-tag: noindex`, and a content security policy that allows only same-origin fonts and the kit's font stylesheet and the page's one style element (by its hash): no scripts, images, frames, or forms.

What it counts:

- Subscribers: rows that pay now, `active`, `grace`, and `canceled` before its expiry. Trials are counted apart as "Trials not yet paying". On hold, paused, expired, and pending count as neither.
- Income after Google's cut: subscribers times `LIST_PRICE_USD` times (1 minus `GOOGLE_FEE_PERCENT` / 100). An estimate, and the page says so: real payouts come from Google's reports. With no price set it shows "not set", and so does left over.
- API cost and pages made: from the content repo's `state/cost/<YYYY-MM>.jsonl` (written by the pipeline's `record-cost`), read through the bucket the same way feed files are, but never served: `/state/` stays 404. A complete run counts its `total_cost_usd`; an incomplete run the larger of that and its `budget_cap_usd`, the same rule as `spend_usd` and `budget-gate`. `../schema/fixtures/cost/` holds records both test suites check. A month with no file is $0; a file that cannot be read shows "cannot be read".
- API cost by field: the records have no cost per field, so each run's cost is split evenly over the papers it was handed (`taken`). A run handed nothing counts in the month's total and on no field.
- Status: "Making pages" when the field is in `GET /v1/active-fields` now.
- By month: this month from live counts; a past month from its last daily snapshot (the `snapshots` table, written by the Cron Trigger at 23:55 UTC each day, `55 23 * * *`). A past month with no snapshot shows "not recorded". Up to 24 months, back to the first snapshot or subscriber.

### Variables and secrets

Variables are in `wrangler.jsonc` (repeated for the `paid` environment, because environments do not inherit them). Secrets are set with `wrangler secret put` and never committed.

| Name | Kind | What it holds |
| --- | --- | --- |
| `DB` | D1 binding (`paid` only) | The `paperboy-subscribers` database. |
| `CONTENT_GATE` | variable | `off` (default) or `on`. |
| `COUNT_TRIALS` | variable | `true` (default) counts trials in the active fields; `false` leaves them out. |
| `PLAY_PACKAGE_NAME` | variable (`paid`) | The app's package name, `io.github.ntrpydev.paperboy`. |
| `RTDN_AUDIENCE` | variable (`paid`) | The audience on the Pub/Sub push subscription. Set to `https://paperboy.ntrpydev.workers.dev/v1/rtdn`, which is what Pub/Sub uses when no audience is set. |
| `RTDN_SERVICE_ACCOUNT` | variable (`paid`) | The service account email on the push subscription. Empty until the owner sets it, so every push is 401. |
| `LIST_PRICE_USD` | variable (`paid`) | The subscription's listed monthly price in US dollars, for example `4.99`. Empty until the price is set; the numbers page then shows income as "not set". |
| `GOOGLE_FEE_PERCENT` | variable (`paid`) | Google's fee on subscriptions in percent, `15` ("10% + 5% billing fee" for US auto-renewing subscriptions, https://support.google.com/googleplay/android-developer/answer/112622). |
| `OWNER_PASSWORD` | secret | The numbers page's password. Unset means the page is 404. |
| `PASS_SECRET` | secret | A random string that signs passes. Changing it ends every pass at once; apps get a new one on their next entitlement call. |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | secret | The whole JSON key file of the service account that calls the Play Developer API (`client_email`, `private_key`, `private_key_id` are read). |

### Going live

One-time steps, in order. The Google steps follow the pages linked in each.

1. Create the database: `npx wrangler d1 create paperboy-subscribers`. Paste the id it prints into `env.paid.d1_databases[0].database_id` in `wrangler.jsonc`, in place of the all-zero placeholder.
2. Apply the migrations (`migrations/0001_subscribers.sql` and `0002_snapshots.sql`): `npx wrangler d1 migrations apply paperboy-subscribers --env paid --remote`.
3. Set the pass secret: `npx wrangler secret put PASS_SECRET --env paid`, and enter a long random string at the prompt (for example the output of `openssl rand -base64 48`).
4. In Google Cloud: create a project, enable the Google Play Android Developer API and the Pub/Sub API, create a service account, and create a JSON key for it (https://developers.google.com/android-publisher/getting_started, https://docs.cloud.google.com/iam/docs/keys-create-delete).
5. In Play Console, Users and permissions: invite the service account's email and grant "View financial data, orders, and cancellation survey responses" and "Manage orders and subscriptions".
6. Store the key: `npx wrangler secret put GOOGLE_SERVICE_ACCOUNT_JSON --env paid < path/to/key.json`.
7. In Pub/Sub: create a topic, and grant `google-play-developer-notifications@system.gserviceaccount.com` the Pub/Sub Publisher role on it (https://developer.android.com/google/play/billing/getting-ready).
8. Choose the service account Pub/Sub signs pushes as (a new one, or the one from step 4). Create a push subscription on the topic with endpoint `https://paperboy.ntrpydev.workers.dev/v1/rtdn`, authentication enabled with that service account, and audience left empty or set to the same URL (https://docs.cloud.google.com/pubsub/docs/create-push-subscription). Per that page, the person creating the subscription needs `iam.serviceAccounts.actAs` on that service account, and `iam.serviceAccounts.getOpenIdToken` (in the Service Account Token Creator role) must be granted so Pub/Sub can create tokens for it.
9. Put that service account's email in `env.paid.vars.RTDN_SERVICE_ACCOUNT` in `wrangler.jsonc` (and `RTDN_AUDIENCE` if the subscription uses another audience).
10. Deploy the paid worker: `npm run deploy -- --env paid`. Check `GET /v1/active-fields` answers `{"v":1,"fields":[],...}`.
11. In Play Console, Monetize, Monetization setup, Real-time developer notifications: enable them, enter the topic as `projects/<project_id>/topics/<topic>`, choose "Get notifications for subscriptions and all voided purchases", and click Send Test Message. The worker answers a verified test message 204; `npx wrangler tail --env paid` shows the request. A 401 means the email or audience does not match; no request at all may mean Cloudflare's Browser Integrity Check on `workers.dev` stopped it (unverified: neither Google nor Cloudflare says whether Pub/Sub pushes pass it; https://developers.cloudflare.com/workers/configuration/routing/workers-dev/).
12. Once paid builds of the app send passes, set `CONTENT_GATE` to `on` in `env.paid.vars` and deploy again.
13. For the numbers page: `npx wrangler secret put OWNER_PASSWORD --env paid`, set `LIST_PRICE_USD` in `env.paid.vars` once the price is chosen, and deploy. The daily snapshot starts with the deploy; Cloudflare says new Cron Triggers can take up to 15 minutes to take effect.
