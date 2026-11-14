// The Google Play Developer API, called as a service account. Every request goes through the
// injected fetch, so tests run against a fake Google.
//
// Service account flow (JWT signed with RS256, exchanged for an access token):
//   https://developers.google.com/identity/protocols/oauth2/service-account
// Key file fields (client_email, private_key as PKCS#8 PEM, private_key_id):
//   https://docs.cloud.google.com/iam/docs/keys-create-delete
// purchases.subscriptionsv2.get:
//   https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptionsv2/get
// The SubscriptionPurchaseV2 resource:
//   https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptionsv2
// purchases.subscriptions.acknowledge (there is no subscriptionsv2 acknowledge):
//   https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptions/acknowledge
// RSASSA-PKCS1-v1_5 in Workers: https://developers.cloudflare.com/workers/runtime-apis/web-crypto/

import { base64Decode, base64UrlEncode, isObject, utf8 } from "./encoding";

export const TOKEN_URL = "https://oauth2.googleapis.com/token";
export const PUBLISHER_SCOPE = "https://www.googleapis.com/auth/androidpublisher";
export const PUBLISHER_BASE = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/";

// An access token is used until this long before Google says it expires.
const TOKEN_MARGIN_MS = 5 * 60_000;
// Google allows an assertion at most one hour after its issue time.
const ASSERTION_LIFETIME_S = 3600;

// The parts of SubscriptionPurchaseV2 the worker reads.
export interface SubscriptionV2 {
  subscriptionState?: string;
  acknowledgementState?: string;
  linkedPurchaseToken?: string;
  canceledStateContext?: { replacementCancellation?: object };
  outOfAppPurchaseContext?: { expiredPurchaseToken?: string };
  lineItems?: LineItem[];
}

export interface LineItem {
  productId?: string;
  expiryTime?: string;
  autoRenewingPlan?: { autoRenewEnabled?: boolean };
  offerPhase?: { freeTrial?: object; introductoryPrice?: object; basePrice?: object; prorationPeriod?: object };
}

export type Lookup = { kind: "found"; subscription: SubscriptionV2 } | { kind: "unknown" } | { kind: "unreachable" };

// Thrown when the service account secret or the package name is missing or unusable.
export class ConfigError extends Error {}

interface ServiceAccount {
  client_email: string;
  private_key: string;
  private_key_id?: string;
}

export interface GoogleDeps {
  fetch: typeof fetch;
  now: () => number;
}

export interface GoogleConfig {
  serviceAccountJson: string | undefined;
  packageName: string | undefined;
}

export function createGoogle(deps: GoogleDeps) {
  // One access token per service account key, kept for the life of the isolate.
  let cached: { keyId: string; token: string; expiresAt: number } | null = null;
  let signingKey: { keyId: string; key: CryptoKey } | null = null;

  function parseAccount(json: string | undefined): ServiceAccount {
    if (!json) throw new ConfigError("GOOGLE_SERVICE_ACCOUNT_JSON is not set");
    let parsed: unknown;
    try {
      parsed = JSON.parse(json);
    } catch {
      throw new ConfigError("GOOGLE_SERVICE_ACCOUNT_JSON is not JSON");
    }
    if (!isObject(parsed) || typeof parsed.client_email !== "string" || typeof parsed.private_key !== "string") {
      throw new ConfigError("GOOGLE_SERVICE_ACCOUNT_JSON lacks client_email or private_key");
    }
    return {
      client_email: parsed.client_email,
      private_key: parsed.private_key,
      private_key_id: typeof parsed.private_key_id === "string" ? parsed.private_key_id : undefined,
    };
  }

  async function importSigningKey(account: ServiceAccount, keyId: string): Promise<CryptoKey> {
    if (signingKey?.keyId === keyId) return signingKey.key;
    const body = account.private_key
      .replace(/-----BEGIN PRIVATE KEY-----/, "")
      .replace(/-----END PRIVATE KEY-----/, "")
      .replace(/\s+/g, "");
    const der = base64Decode(body);
    if (!der) throw new ConfigError("private_key is not a PEM PKCS#8 key");
    let key: CryptoKey;
    try {
      key = await crypto.subtle.importKey("pkcs8", der, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["sign"]);
    } catch {
      throw new ConfigError("private_key could not be imported as an RSA key");
    }
    signingKey = { keyId, key };
    return key;
  }

  // An access token for the Publisher API, or null when Google's token endpoint fails.
  async function accessToken(config: GoogleConfig): Promise<string | null> {
    const account = parseAccount(config.serviceAccountJson);
    const keyId = `${account.client_email}/${account.private_key_id ?? ""}`;
    if (cached && cached.keyId === keyId && deps.now() < cached.expiresAt - TOKEN_MARGIN_MS) return cached.token;

    const iat = Math.floor(deps.now() / 1000);
    const header: Record<string, string> = { alg: "RS256", typ: "JWT" };
    if (account.private_key_id) header.kid = account.private_key_id;
    const claims = {
      iss: account.client_email,
      scope: PUBLISHER_SCOPE,
      aud: TOKEN_URL,
      iat,
      exp: iat + ASSERTION_LIFETIME_S,
    };
    const unsigned = `${base64UrlEncode(utf8(JSON.stringify(header)))}.${base64UrlEncode(utf8(JSON.stringify(claims)))}`;
    const key = await importSigningKey(account, keyId);
    const signature = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, utf8(unsigned));
    const assertion = `${unsigned}.${base64UrlEncode(signature)}`;

    let res: Response;
    try {
      res = await deps.fetch(TOKEN_URL, {
        method: "POST",
        headers: { "content-type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer", assertion }).toString(),
      });
    } catch {
      return null;
    }
    if (!res.ok) {
      console.error(`google token endpoint answered ${res.status}`);
      await res.body?.cancel();
      return null;
    }
    const body: unknown = await res.json().catch(() => null);
    if (!isObject(body) || typeof body.access_token !== "string") return null;
    const lifetime = typeof body.expires_in === "number" ? body.expires_in : 3600;
    cached = { keyId, token: body.access_token, expiresAt: deps.now() + lifetime * 1000 };
    return body.access_token;
  }

  function packageName(config: GoogleConfig): string {
    if (!config.packageName) throw new ConfigError("PLAY_PACKAGE_NAME is not set");
    return config.packageName;
  }

  // Calls the Publisher API once, and once more with a fresh access token if Google answers 401.
  async function publisher(config: GoogleConfig, url: string, init: RequestInit): Promise<Response | null> {
    for (let attempt = 0; attempt < 2; attempt++) {
      const token = await accessToken(config);
      if (!token) return null;
      let res: Response;
      try {
        res = await deps.fetch(url, { ...init, headers: { ...init.headers, authorization: `Bearer ${token}` } });
      } catch {
        return null;
      }
      if (res.status !== 401 || attempt === 1) return res;
      await res.body?.cancel();
      cached = null;
    }
    return null;
  }

  return {
    async subscription(config: GoogleConfig, purchaseToken: string): Promise<Lookup> {
      const url = `${PUBLISHER_BASE}${encodeURIComponent(packageName(config))}/purchases/subscriptionsv2/tokens/${encodeURIComponent(purchaseToken)}`;
      const res = await publisher(config, url, { method: "GET" });
      if (!res) return { kind: "unreachable" };
      // The reference does not list the error for a token Google does not know. 404 and 410
      // (a token more than 60 days past expiry) are read as unknown, and so is 400, since the
      // token is the only caller-supplied part of the request. Unverified until real
      // credentials exist.
      if (res.status === 400 || res.status === 404 || res.status === 410) {
        await res.body?.cancel();
        return { kind: "unknown" };
      }
      if (!res.ok) {
        console.error(`google subscriptionsv2.get answered ${res.status}`);
        await res.body?.cancel();
        return { kind: "unreachable" };
      }
      const body: unknown = await res.json().catch(() => null);
      if (!isObject(body)) return { kind: "unreachable" };
      return { kind: "found", subscription: body as SubscriptionV2 };
    },

    // True when Google accepted the acknowledgement.
    async acknowledge(config: GoogleConfig, productId: string, purchaseToken: string): Promise<boolean> {
      const url =
        `${PUBLISHER_BASE}${encodeURIComponent(packageName(config))}/purchases/subscriptions/` +
        `${encodeURIComponent(productId)}/tokens/${encodeURIComponent(purchaseToken)}:acknowledge`;
      const res = await publisher(config, url, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: "{}",
      });
      if (!res) return false;
      await res.body?.cancel();
      if (!res.ok) console.error(`google acknowledge answered ${res.status}`);
      return res.ok;
    },
  };
}

export type Google = ReturnType<typeof createGoogle>;
