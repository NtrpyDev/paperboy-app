// A stand-in for every Google endpoint the worker calls: the OAuth token endpoint (which checks
// the worker's RS256 assertion against the service account's public key), the Play Developer
// API's subscriptionsv2.get and acknowledge, and Google's signing keys for Pub/Sub push JWTs.
// The keys are generated per test run; none of them are real.

import { PUBLISHER_BASE, PUBLISHER_SCOPE, TOKEN_URL } from "../../src/google";
import { GOOGLE_CERTS_URL } from "../../src/push";
import { base64UrlDecode, base64UrlEncode, utf8 } from "../../src/encoding";

export const PACKAGE = "io.github.ntrpydev.paperboy";
export const PRODUCT = "paperboy_monthly";
export const SERVICE_ACCOUNT_EMAIL = "worker@paperboy-test.iam.gserviceaccount.com";
export const PUSH_EMAIL = "pusher@paperboy-test.iam.gserviceaccount.com";
export const AUDIENCE = "https://paperboy.ntrpydev.workers.dev/v1/rtdn";
export const PUSH_KID = "push-key-1";

const RSA = { name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" };

async function rsaPair(): Promise<CryptoKeyPair> {
  return (await crypto.subtle.generateKey(RSA, true, ["sign", "verify"])) as CryptoKeyPair;
}

function pem(der: ArrayBuffer): string {
  const b64 = btoa(String.fromCharCode(...new Uint8Array(der)));
  return `-----BEGIN PRIVATE KEY-----\n${b64.match(/.{1,64}/g)!.join("\n")}\n-----END PRIVATE KEY-----\n`;
}

// Generated once per test file: RSA key generation is slow.
const serviceKeys = rsaPair();
const pushKeys = rsaPair();
const strangerKeys = rsaPair();

export async function serviceAccountJson(): Promise<string> {
  const keys = await serviceKeys;
  return JSON.stringify({
    type: "service_account",
    project_id: "paperboy-test",
    private_key_id: "sa-key-1",
    private_key: pem((await crypto.subtle.exportKey("pkcs8", keys.privateKey)) as ArrayBuffer),
    client_email: SERVICE_ACCOUNT_EMAIL,
    client_id: "1",
    token_uri: TOKEN_URL,
  });
}

// A Pub/Sub push JWT. Claims can be overridden or removed (undefined), and the token can be
// signed with a key Google never published.
export async function pushJwt(
  now: number,
  overrides: Record<string, unknown> = {},
  options: { stranger?: boolean; kid?: string } = {},
): Promise<string> {
  const header = { alg: "RS256", kid: options.kid ?? PUSH_KID, typ: "JWT" };
  const claims: Record<string, unknown> = {
    aud: AUDIENCE,
    azp: "1234",
    email: PUSH_EMAIL,
    email_verified: true,
    exp: Math.floor(now / 1000) + 3600,
    iat: Math.floor(now / 1000),
    iss: "https://accounts.google.com",
    sub: "1234",
    ...overrides,
  };
  for (const [k, v] of Object.entries(claims)) if (v === undefined) delete claims[k];
  const unsigned = `${base64UrlEncode(utf8(JSON.stringify(header)))}.${base64UrlEncode(utf8(JSON.stringify(claims)))}`;
  const key = (await (options.stranger ? strangerKeys : pushKeys)).privateKey;
  const signature = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, utf8(unsigned));
  return `${unsigned}.${base64UrlEncode(signature)}`;
}

export interface FakeSubscription {
  subscriptionState: string;
  acknowledgementState?: string;
  linkedPurchaseToken?: string;
  canceledStateContext?: object;
  outOfAppPurchaseContext?: object;
  lineItems?: object[];
}

export interface Call {
  kind: "token" | "get" | "ack" | "certs";
  token?: string;
  productId?: string;
}

export function fakeGoogle() {
  const subscriptions = new Map<string, FakeSubscription | number>();
  const calls: Call[] = [];
  let down: false | "throw" | number = false;
  let tokenDown = false;
  let certsDown = false;
  let issued = 0;
  const validTokens = new Set<string>();

  const fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const request = new Request(input, init);
    const url = request.url;

    if (url === GOOGLE_CERTS_URL) {
      calls.push({ kind: "certs" });
      if (certsDown) throw new TypeError("Network connection lost.");
      const jwk = await crypto.subtle.exportKey("jwk", (await pushKeys).publicKey);
      return Response.json(
        { keys: [{ ...(jwk as object), kid: PUSH_KID, alg: "RS256", use: "sig" }] },
        { headers: { "cache-control": "public, max-age=21600" } },
      );
    }

    if (url === TOKEN_URL) {
      calls.push({ kind: "token" });
      if (tokenDown) return new Response("unavailable", { status: 503 });
      const form = new URLSearchParams(await request.text());
      if (form.get("grant_type") !== "urn:ietf:params:oauth:grant-type:jwt-bearer") return Response.json({ error: "unsupported_grant_type" }, { status: 400 });
      const [h, p, s] = (form.get("assertion") ?? "").split(".");
      const valid = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", (await serviceKeys).publicKey, base64UrlDecode(s)!, utf8(`${h}.${p}`));
      const claims = JSON.parse(new TextDecoder().decode(base64UrlDecode(p)!));
      const header = JSON.parse(new TextDecoder().decode(base64UrlDecode(h)!));
      if (
        !valid ||
        header.alg !== "RS256" ||
        claims.iss !== SERVICE_ACCOUNT_EMAIL ||
        claims.aud !== TOKEN_URL ||
        claims.scope !== PUBLISHER_SCOPE ||
        claims.exp - claims.iat > 3600
      ) {
        return Response.json({ error: "invalid_grant" }, { status: 400 });
      }
      const token = `access-${++issued}`;
      validTokens.add(token);
      return Response.json({ access_token: token, token_type: "Bearer", expires_in: 3600 });
    }

    const prefix = `${PUBLISHER_BASE}${PACKAGE}/purchases/`;
    if (url.startsWith(prefix)) {
      const bearer = request.headers.get("authorization")?.replace(/^Bearer /, "") ?? "";
      const rest = url.slice(prefix.length);
      const get = /^subscriptionsv2\/tokens\/([^/]+)$/.exec(rest);
      const ack = /^subscriptions\/([^/]+)\/tokens\/([^/]+):acknowledge$/.exec(rest);
      if (get && request.method === "GET") {
        const token = decodeURIComponent(get[1]);
        calls.push({ kind: "get", token });
        if (down === "throw") throw new TypeError("Network connection lost.");
        if (down) return new Response("unavailable", { status: down });
        if (!validTokens.has(bearer)) return Response.json({ error: { code: 401 } }, { status: 401 });
        const found = subscriptions.get(token);
        if (found === undefined) return Response.json({ error: { code: 404, message: "Not found" } }, { status: 404 });
        if (typeof found === "number") return Response.json({ error: { code: found } }, { status: found });
        return Response.json({ kind: "androidpublisher#subscriptionPurchaseV2", ...found });
      }
      if (ack && request.method === "POST") {
        const token = decodeURIComponent(ack[2]);
        calls.push({ kind: "ack", token, productId: decodeURIComponent(ack[1]) });
        if (!validTokens.has(bearer)) return Response.json({ error: { code: 401 } }, { status: 401 });
        const found = subscriptions.get(token);
        if (typeof found === "object") found.acknowledgementState = "ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED";
        return new Response(null, { status: 200 });
      }
    }
    return new Response("not a fake Google endpoint", { status: 599 });
  };

  return {
    fetch,
    calls,
    subscriptions,
    count: (kind: Call["kind"]) => calls.filter((c) => c.kind === kind).length,
    takeDown(how: "throw" | number = 503) {
      down = how;
    },
    bringUp() {
      down = false;
      tokenDown = false;
      certsDown = false;
    },
    takeDownTokenEndpoint() {
      tokenDown = true;
    },
    takeDownCerts() {
      certsDown = true;
    },
    revokeAccessTokens() {
      validTokens.clear();
    },
  };
}

const DAY = 86_400_000;

// A SubscriptionPurchaseV2 body in one of Google's states.
export function subscription(
  state: string,
  options: {
    expiry?: number | null;
    trial?: boolean;
    acknowledged?: boolean;
    linked?: string;
    replaced?: boolean;
    expiredToken?: string;
    product?: string;
  } = {},
): FakeSubscription {
  const item: Record<string, unknown> = {
    productId: options.product ?? PRODUCT,
    autoRenewingPlan: { autoRenewEnabled: true },
    offerDetails: { basePlanId: "monthly", ...(options.trial ? { offerId: "free-trial" } : {}) },
    offerPhase: options.trial ? { freeTrial: {} } : { basePrice: {} },
  };
  if (options.expiry !== null) item.expiryTime = new Date(options.expiry ?? Date.UTC(2026, 10, 12, 12) + 30 * DAY).toISOString();
  return {
    subscriptionState: state,
    acknowledgementState: options.acknowledged === false ? "ACKNOWLEDGEMENT_STATE_PENDING" : "ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED",
    ...(options.linked ? { linkedPurchaseToken: options.linked } : {}),
    ...(options.replaced ? { canceledStateContext: { replacementCancellation: {} } } : {}),
    ...(options.expiredToken ? { outOfAppPurchaseContext: { expiredPurchaseToken: options.expiredToken } } : {}),
    lineItems: [item],
  };
}
