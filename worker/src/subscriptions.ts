// The subscription API under /v1/ (Contract 1 in the paid app spec):
//   POST /v1/entitlement   the app asks whether its purchase token is entitled and gets a pass
//   POST /v1/rtdn          Pub/Sub push of Play Real-time Developer Notifications
//   GET  /v1/active-fields the fields picked by at least one subscriber whose state counts
//
// RTDN message format: https://developer.android.com/google/play/billing/rtdn-reference
// Subscription lifecycle (states, grace, hold, acknowledgement, linkedPurchaseToken):
//   https://developer.android.com/google/play/billing/lifecycle/subscriptions

import { base64Decode, decodeUtf8, isObject, parseJson, readBody, sha256Hex } from "./encoding";
import { ConfigError, createGoogle, type GoogleConfig, type LineItem, type SubscriptionV2 } from "./google";
import { mintPass, PASS_LIFETIME_S } from "./pass";
import { createPushVerifier } from "./push";
import {
  countingFields,
  deleteSubscriber,
  getSubscriber,
  isKnownUnknown,
  rememberUnknown,
  saveSubscriber,
  type State,
} from "./store";

// Wire values in order, from the enum in schema/feed-item.schema.json.
export const FIELDS = [
  "physics",
  "space",
  "math",
  "cs",
  "biology",
  "neuroscience",
  "medicine",
  "chemistry",
  "earth",
  "engineering",
  "social",
] as const;
const KNOWN_FIELDS = new Set<string>(FIELDS);

// Request size caps. An entitlement body is a token, a product id, and at most 11 fields.
const ENTITLEMENT_MAX_BYTES = 8 * 1024;
const RTDN_MAX_BYTES = 64 * 1024;
// Play documents no format for purchase tokens, so only the length and the characters are
// limited: printable ASCII with no spaces.
const TOKEN_SHAPE = /^[\x21-\x7e]{1,2048}$/;
// Product IDs "must start with a number or lowercase letter" and may hold numbers, lowercase
// letters, underscores, and periods, up to 40 characters:
//   https://support.google.com/googleplay/android-developer/answer/140504
const PRODUCT_SHAPE = /^[a-z0-9][a-z0-9._]{0,39}$/;
// How long a token Google did not know is answered 404 without asking Google again.
export const UNKNOWN_TTL_MS = 5 * 60_000;
// A pass for an entitled subscription whose expiry is already past (Google still calling it
// active, as around a renewal) lasts this long, so the app checks again soon.
const SHORT_PASS_S = 3600;

export interface ApiEnv {
  DB?: D1Database;
  PASS_SECRET?: string;
  GOOGLE_SERVICE_ACCOUNT_JSON?: string;
  PLAY_PACKAGE_NAME?: string;
  RTDN_AUDIENCE?: string;
  RTDN_SERVICE_ACCOUNT?: string;
  COUNT_TRIALS?: string;
}

export interface ApiDeps {
  fetch: typeof fetch;
  now: () => number;
}

// Google's state mapped to the spec's state.
export interface Snapshot {
  state: State;
  expiresAt: number | null;
  productId: string | null;
  needsAck: boolean;
  // Tokens this purchase replaces: linkedPurchaseToken, and for a resubscribe from the Play
  // Store after expiry, outOfAppPurchaseContext.expiredPurchaseToken.
  replaces: string[];
}

// The docs settle this: "The offerPhase field in the SubscriptionPurchaseLineItem provides
// details about the current phase of the subscription, such as free trial or introductory
// price", and OfferPhase.freeTrial is "Set when the offer phase is a free trial". A line item
// with no offerPhase is read as paid.
export function isFreeTrial(item: LineItem | undefined): boolean {
  return isObject(item?.offerPhase?.freeTrial);
}

// The line item that decides the expiry: the one that runs longest.
function mainItem(items: LineItem[]): LineItem | undefined {
  let best: LineItem | undefined;
  let bestTime = -Infinity;
  for (const item of items) {
    const time = Date.parse(item.expiryTime ?? "");
    if (Number.isFinite(time) && time > bestTime) {
      best = item;
      bestTime = time;
    }
  }
  return best ?? items[0];
}

export function snapshot(sub: SubscriptionV2): Snapshot {
  const items = Array.isArray(sub.lineItems) ? sub.lineItems : [];
  const item = mainItem(items);
  const expiry = Date.parse(item?.expiryTime ?? "");
  const google = sub.subscriptionState;
  let state: State;
  switch (google) {
    case "SUBSCRIPTION_STATE_PENDING":
      state = "pending";
      break;
    case "SUBSCRIPTION_STATE_ACTIVE":
      state = isFreeTrial(item) ? "trial" : "active";
      break;
    case "SUBSCRIPTION_STATE_PAUSED":
      state = "paused";
      break;
    case "SUBSCRIPTION_STATE_IN_GRACE_PERIOD":
      state = "grace";
      break;
    case "SUBSCRIPTION_STATE_ON_HOLD":
      state = "on_hold";
      break;
    case "SUBSCRIPTION_STATE_CANCELED":
      // A subscription canceled because another purchase replaced it (an upgrade, downgrade,
      // or resubscribe) gives no access: the new token holds it.
      state = isObject(sub.canceledStateContext?.replacementCancellation) ? "expired" : "canceled";
      break;
    default:
      // SUBSCRIPTION_STATE_EXPIRED, SUBSCRIPTION_STATE_PENDING_PURCHASE_CANCELED (a pending
      // purchase that was never paid), and anything new or unspecified.
      state = "expired";
  }
  const purchased = google !== "SUBSCRIPTION_STATE_PENDING" && google !== "SUBSCRIPTION_STATE_PENDING_PURCHASE_CANCELED" && google !== "SUBSCRIPTION_STATE_EXPIRED";
  const replaces = [sub.linkedPurchaseToken, sub.outOfAppPurchaseContext?.expiredPurchaseToken].filter(
    (t): t is string => typeof t === "string" && t.length > 0,
  );
  return {
    state,
    expiresAt: Number.isFinite(expiry) ? expiry : null,
    productId: typeof item?.productId === "string" ? item.productId : null,
    // "If you don't acknowledge a new subscription purchase within three days, the user
    // automatically receives a refund", and the window starts once the purchase leaves PENDING.
    needsAck: sub.acknowledgementState === "ACKNOWLEDGEMENT_STATE_PENDING" && purchased,
    replaces,
  };
}

export function isEntitled(state: State, expiresAt: number | null, now: number): boolean {
  if (state === "trial" || state === "active" || state === "grace") return true;
  if (state === "canceled") return expiresAt !== null && expiresAt > now;
  return false;
}

function json(status: number, body: unknown, extra: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra },
  });
}

const badRequest = () => json(400, { error: "bad_request" });
const notConfigured = () => json(503, { error: "not_configured" });
const unreachable = () => json(502, { error: "store_unreachable" });

function rfc3339(ms: number | null): string | null {
  return ms === null ? null : new Date(ms).toISOString();
}

interface EntitlementRequest {
  purchaseToken: string;
  productId: string;
  fields: string[];
}

function parseEntitlement(text: string): EntitlementRequest | null {
  const body = parseJson(text);
  if (!isObject(body)) return null;
  const keys = Object.keys(body);
  if (keys.length !== 3 || !keys.every((k) => k === "purchase_token" || k === "product_id" || k === "fields")) return null;
  const { purchase_token, product_id, fields } = body;
  if (typeof purchase_token !== "string" || !TOKEN_SHAPE.test(purchase_token)) return null;
  if (typeof product_id !== "string" || !PRODUCT_SHAPE.test(product_id)) return null;
  if (!Array.isArray(fields) || fields.length < 1 || fields.length > FIELDS.length) return null;
  if (!fields.every((f) => typeof f === "string" && KNOWN_FIELDS.has(f))) return null;
  if (new Set(fields).size !== fields.length) return null;
  return { purchaseToken: purchase_token, productId: product_id, fields: fields as string[] };
}

export function createApi(deps: ApiDeps) {
  const google = createGoogle(deps);
  const verifyPush = createPushVerifier(deps);

  function googleConfig(env: ApiEnv): GoogleConfig {
    return { serviceAccountJson: env.GOOGLE_SERVICE_ACCOUNT_JSON, packageName: env.PLAY_PACKAGE_NAME };
  }

  // Asks Google for the token's state and writes the row. sentFields is null when the caller
  // sent none (a notification), and then the row keeps its fields, or takes over the fields of
  // the token it replaces.
  async function refresh(
    db: D1Database,
    env: ApiEnv,
    purchaseToken: string,
    sentFields: string[] | null,
    fallbackProduct: string,
  ): Promise<{ kind: "unknown" } | { kind: "unreachable" } | { kind: "ok"; snap: Snapshot }> {
    const lookup = await google.subscription(googleConfig(env), purchaseToken);
    const tokenHash = await sha256Hex(purchaseToken);
    if (lookup.kind === "unknown") {
      // Google no longer knows the token (for example 60 days after expiry), so its row goes.
      await deleteSubscriber(db, tokenHash);
      return lookup;
    }
    if (lookup.kind === "unreachable") return lookup;

    const snap = snapshot(lookup.subscription);
    const now = deps.now();
    const replacedHashes = await Promise.all(snap.replaces.map((t) => sha256Hex(t)));
    let fields = sentFields;
    if (fields === null) {
      const existing = await getSubscriber(db, tokenHash);
      fields = existing?.fields.length ? existing.fields : null;
      for (const hash of replacedHashes) {
        if (fields) break;
        const old = await getSubscriber(db, hash);
        if (old?.fields.length) fields = old.fields;
      }
      fields ??= existing?.fields ?? [];
    }
    const productId = snap.productId ?? fallbackProduct;
    await saveSubscriber(
      db,
      { tokenHash, purchaseToken, productId, state: snap.state, expiresAt: snap.expiresAt, fields },
      replacedHashes,
      now,
    );
    if (snap.needsAck && productId) {
      // A failed acknowledgement is retried on the next call or notification, while Google
      // still reports it pending.
      await google.acknowledge(googleConfig(env), productId, purchaseToken);
    }
    return { kind: "ok", snap };
  }

  async function entitlement(request: Request, env: ApiEnv): Promise<Response> {
    const text = await readBody(request, ENTITLEMENT_MAX_BYTES);
    const req = text === null ? null : parseEntitlement(text);
    if (!req) return badRequest();
    const db = env.DB;
    if (!db || !env.PASS_SECRET || !env.GOOGLE_SERVICE_ACCOUNT_JSON || !env.PLAY_PACKAGE_NAME) {
      console.error("entitlement: DB, PASS_SECRET, GOOGLE_SERVICE_ACCOUNT_JSON, or PLAY_PACKAGE_NAME is not set");
      return notConfigured();
    }

    const tokenHash = await sha256Hex(req.purchaseToken);
    if (await isKnownUnknown(db, tokenHash, deps.now())) return json(404, { error: "unknown_purchase" });

    const result = await refresh(db, env, req.purchaseToken, req.fields, req.productId);
    if (result.kind === "unknown") {
      const now = deps.now();
      await rememberUnknown(db, tokenHash, now + UNKNOWN_TTL_MS, now);
      return json(404, { error: "unknown_purchase" });
    }
    if (result.kind === "unreachable") return unreachable();

    const { state, expiresAt } = result.snap;
    const now = deps.now();
    const entitled = isEntitled(state, expiresAt, now);
    let pass: string | null = null;
    let passExp: number | null = null;
    if (entitled) {
      const nowS = Math.floor(now / 1000);
      passExp = nowS + PASS_LIFETIME_S;
      if (expiresAt !== null) passExp = Math.min(passExp, Math.floor(expiresAt / 1000));
      if (passExp <= nowS) passExp = nowS + SHORT_PASS_S;
      pass = await mintPass(env.PASS_SECRET, tokenHash.slice(0, 16), passExp);
    }
    return json(200, {
      entitled,
      state,
      expires_at: rfc3339(expiresAt),
      pass,
      pass_expires_at: passExp === null ? null : rfc3339(passExp * 1000),
    });
  }

  async function rtdn(request: Request, env: ApiEnv): Promise<Response> {
    const check = await verifyPush(request.headers.get("authorization"), {
      audience: env.RTDN_AUDIENCE,
      serviceAccount: env.RTDN_SERVICE_ACCOUNT,
    });
    if (check === "keys_unreachable") {
      await request.body?.cancel();
      // Not a verdict on the message: Pub/Sub resends it once Google's keys can be read.
      return json(502, { error: "keys_unreachable" });
    }
    if (check !== "ok") {
      await request.body?.cancel();
      return json(401, { error: "unauthorized" });
    }
    const db = env.DB;
    if (!db || !env.GOOGLE_SERVICE_ACCOUNT_JSON || !env.PLAY_PACKAGE_NAME) {
      await request.body?.cancel();
      console.error("rtdn: DB, GOOGLE_SERVICE_ACCOUNT_JSON, or PLAY_PACKAGE_NAME is not set");
      return notConfigured();
    }

    const token = notificationToken(await readBody(request, RTDN_MAX_BYTES), env.PLAY_PACKAGE_NAME);
    // Anything verified that is not about one of this app's subscriptions (a test
    // notification, a one-time product, a malformed body) is acknowledged and dropped,
    // since resending it would not change it.
    if (!token) return new Response(null, { status: 204 });
    const result = await refresh(db, env, token, null, "");
    // Google could not be asked, so the update would be lost: Pub/Sub resends on a non-success.
    if (result.kind === "unreachable") return unreachable();
    return new Response(null, { status: 204 });
  }

  async function activeFields(env: ApiEnv): Promise<Response> {
    const db = env.DB;
    if (!db) return notConfigured();
    const now = deps.now();
    const lists = await countingFields(db, env.COUNT_TRIALS !== "false", now);
    const picked = new Set(lists.flat().filter((f) => KNOWN_FIELDS.has(f)));
    return json(200, { v: 1, fields: [...picked].sort(), updated_at: rfc3339(now) }, { "cache-control": "public, max-age=60" });
  }

  const routes: Record<string, { methods: string[]; run: (request: Request, env: ApiEnv) => Promise<Response> }> = {
    "/v1/entitlement": { methods: ["POST"], run: entitlement },
    "/v1/rtdn": { methods: ["POST"], run: rtdn },
    "/v1/active-fields": { methods: ["GET", "HEAD"], run: (_request, env) => activeFields(env) },
  };

  return async function api(request: Request, env: ApiEnv): Promise<Response> {
    const path = new URL(request.url).pathname;
    const route = routes[path];
    if (!route) {
      await request.body?.cancel();
      return json(404, { error: "not_found" });
    }
    if (!route.methods.includes(request.method)) {
      await request.body?.cancel();
      return json(405, { error: "method_not_allowed" }, { allow: route.methods.join(", ") });
    }
    let res: Response;
    try {
      res = await route.run(request, env);
    } catch (error) {
      if (error instanceof ConfigError) {
        console.error(`config: ${error.message}`);
        return notConfigured();
      }
      // Only the error class and message are logged; neither carries a token or a pass.
      console.error(`${path} failed: ${error instanceof Error ? error.name : "unknown error"}`);
      return json(500, { error: "internal" });
    }
    if (request.method !== "HEAD") return res;
    await res.body?.cancel();
    return new Response(null, res);
  };
}

// The purchase token of a subscription notification for this app, or null.
function notificationToken(body: string | null, packageName: string): string | null {
  const envelope = body === null ? undefined : parseJson(body);
  if (!isObject(envelope) || !isObject(envelope.message) || typeof envelope.message.data !== "string") return null;
  const bytes = base64Decode(envelope.message.data);
  const text = bytes && decodeUtf8(bytes);
  const note = typeof text === "string" ? parseJson(text) : undefined;
  if (!isObject(note) || note.packageName !== packageName) return null;
  const sub = note.subscriptionNotification;
  if (isObject(sub) && typeof sub.purchaseToken === "string" && TOKEN_SHAPE.test(sub.purchaseToken)) return sub.purchaseToken;
  // A voided subscription purchase (a refund or chargeback) also changes what the token is
  // entitled to, so its state is read again too.
  const voided = note.voidedPurchaseNotification;
  if (isObject(voided) && voided.productType === 1 && typeof voided.purchaseToken === "string" && TOKEN_SHAPE.test(voided.purchaseToken)) {
    return voided.purchaseToken;
  }
  return null;
}
