// The pass: proof that a request comes from a person entitled to the feed, carried in the
// x-paperboy-pass header or the pb_pass cookie (Contract 1 in the paid app spec).
//
//   v1.<P>.<S>
//   P = base64url, no padding, of the JSON {"exp": <epoch seconds>, "sub": "<16 hex chars>"}
//   S = base64url, no padding, of HMAC-SHA256 over the ASCII string "v1.<P>" with PASS_SECRET
//
// HMAC and timingSafeEqual in Workers: https://developers.cloudflare.com/workers/runtime-apis/web-crypto/

import { base64UrlDecode, base64UrlEncode, decodeUtf8, isObject, parseJson, sha256Hex, utf8 } from "./encoding";

export const PASS_LIFETIME_S = 48 * 3600;

export type PassCheck = { ok: true; exp: number; sub: string } | { ok: false; reason: "malformed" | "expired" };

async function hmacKey(secret: string): Promise<CryptoKey> {
  return crypto.subtle.importKey("raw", utf8(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
}

// The pass subject: the first 16 hex characters of the SHA-256 of the purchase token.
export async function passSubject(purchaseToken: string): Promise<string> {
  return (await sha256Hex(purchaseToken)).slice(0, 16);
}

// Signs a pass. Throws when the secret is missing, so a pass is never minted unsigned.
export async function mintPass(secret: string | undefined, sub: string, exp: number): Promise<string> {
  if (!secret) throw new Error("PASS_SECRET is not set");
  const payload = base64UrlEncode(utf8(JSON.stringify({ exp, sub })));
  const signed = `v1.${payload}`;
  const signature = await crypto.subtle.sign("HMAC", await hmacKey(secret), utf8(signed));
  return `${signed}.${base64UrlEncode(signature)}`;
}

// Checks the signature first, then the expiry against nowMs. A pass with a bad signature is
// "malformed" whatever its expiry says, so an expired answer always means a real pass.
export async function verifyPass(secret: string, pass: string, nowMs: number): Promise<PassCheck> {
  const parts = pass.split(".");
  if (parts.length !== 3 || parts[0] !== "v1") return { ok: false, reason: "malformed" };
  const [, payload, signature] = parts;
  const given = base64UrlDecode(signature);
  if (!given || given.byteLength !== 32 || payload.length === 0) return { ok: false, reason: "malformed" };
  const expected = new Uint8Array(await crypto.subtle.sign("HMAC", await hmacKey(secret), utf8(`v1.${payload}`)));
  if (!crypto.subtle.timingSafeEqual(expected, given)) return { ok: false, reason: "malformed" };

  const bytes = base64UrlDecode(payload);
  const text = bytes && decodeUtf8(bytes);
  const claims = text === null || text === undefined ? undefined : parseJson(text);
  if (!isObject(claims)) return { ok: false, reason: "malformed" };
  const { exp, sub } = claims;
  if (!Number.isInteger(exp) || typeof sub !== "string" || !/^[0-9a-f]{16}$/.test(sub)) {
    return { ok: false, reason: "malformed" };
  }
  if ((exp as number) * 1000 <= nowMs) return { ok: false, reason: "expired" };
  return { ok: true, exp: exp as number, sub };
}
