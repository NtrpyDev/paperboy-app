// Verifies that a Pub/Sub push came from Google, the way Google documents push authentication:
// the request carries "Authorization: Bearer <JWT>", an RS256 token signed by Google, whose
// email and aud claims must match the push subscription's service account and audience, with
// email_verified true.
//   https://docs.cloud.google.com/pubsub/docs/authenticate-push-subscriptions
// Issuer, expiry, and Google's signing keys (jwks_uri of the discovery document, cached by the
// response's cache directives):
//   https://developers.google.com/identity/openid-connect/openid-connect
//   https://accounts.google.com/.well-known/openid-configuration

import { base64UrlDecode, decodeUtf8, isObject, parseJson, utf8 } from "./encoding";

export const GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs";
const ISSUERS = new Set(["https://accounts.google.com", "accounts.google.com"]);
// Used when the keys response gives no max-age.
const DEFAULT_KEYS_TTL_MS = 3600_000;
// A key id Google does not list causes at most one refetch of the keys this often.
const REFETCH_MIN_MS = 60_000;

export interface PushConfig {
  audience: string | undefined;
  serviceAccount: string | undefined;
}

export type PushCheck = "ok" | "unverified" | "keys_unreachable";

export function createPushVerifier(deps: { fetch: typeof fetch; now: () => number }) {
  let keys: { byId: Map<string, JsonWebKey>; fetchedAt: number; expiresAt: number } | null = null;

  async function loadKeys(): Promise<boolean> {
    let res: Response;
    try {
      res = await deps.fetch(GOOGLE_CERTS_URL);
    } catch {
      return false;
    }
    if (!res.ok) {
      await res.body?.cancel();
      return false;
    }
    const body: unknown = await res.json().catch(() => null);
    if (!isObject(body) || !Array.isArray(body.keys)) return false;
    const byId = new Map<string, JsonWebKey>();
    for (const key of body.keys) {
      if (isObject(key) && typeof key.kid === "string" && key.kty === "RSA") byId.set(key.kid, key as unknown as JsonWebKey);
    }
    const maxAge = /max-age=(\d+)/.exec(res.headers.get("cache-control") ?? "");
    const ttl = maxAge ? Number(maxAge[1]) * 1000 : DEFAULT_KEYS_TTL_MS;
    keys = { byId, fetchedAt: deps.now(), expiresAt: deps.now() + ttl };
    return true;
  }

  async function keyFor(kid: string): Promise<JsonWebKey | null | "unreachable"> {
    const now = deps.now();
    if (!keys || now >= keys.expiresAt) {
      if (!(await loadKeys())) return "unreachable";
    } else if (!keys.byId.has(kid) && now - keys.fetchedAt >= REFETCH_MIN_MS) {
      // Google may have rotated in a new key since the last fetch.
      await loadKeys();
    }
    return keys?.byId.get(kid) ?? null;
  }

  return async function verify(authorization: string | null, config: PushConfig): Promise<PushCheck> {
    if (!config.audience || !config.serviceAccount || !authorization) return "unverified";
    const match = /^Bearer ([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)$/i.exec(authorization.trim());
    if (!match) return "unverified";
    const [, headerPart, payloadPart, signaturePart] = match;
    const header = decodePart(headerPart);
    const claims = decodePart(payloadPart);
    const signature = base64UrlDecode(signaturePart);
    if (!isObject(header) || !isObject(claims) || !signature) return "unverified";
    if (header.alg !== "RS256" || typeof header.kid !== "string") return "unverified";

    // Claims first, so a token that could never pass does not cost a key fetch.
    if (typeof claims.iss !== "string" || !ISSUERS.has(claims.iss)) return "unverified";
    // Pub/Sub calls the audience "a single, case-insensitive string".
    if (typeof claims.aud !== "string" || claims.aud.toLowerCase() !== config.audience.toLowerCase()) return "unverified";
    if (claims.email !== config.serviceAccount || claims.email_verified !== true) return "unverified";
    if (typeof claims.exp !== "number" || deps.now() >= claims.exp * 1000) return "unverified";

    const jwk = await keyFor(header.kid);
    if (jwk === "unreachable") return "keys_unreachable";
    if (!jwk) return "unverified";
    let key: CryptoKey;
    try {
      key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
    } catch {
      return "unverified";
    }
    const valid = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, signature, utf8(`${headerPart}.${payloadPart}`));
    return valid ? "ok" : "unverified";
  };
}

function decodePart(part: string): unknown {
  const bytes = base64UrlDecode(part);
  const text = bytes && decodeUtf8(bytes);
  return typeof text === "string" ? parseJson(text) : undefined;
}
