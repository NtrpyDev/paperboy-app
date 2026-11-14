import { describe, expect, it } from "vitest";
import { base64UrlDecode, base64UrlEncode, sha256Hex, utf8 } from "../../src/encoding";
import { mintPass, passSubject, verifyPass } from "../../src/pass";

const SECRET = "test-pass-secret";
const NOW = Date.UTC(2026, 10, 12, 12, 0, 0);
const EXP = NOW / 1000 + 3600;
const SUB = "0123456789abcdef";

describe("the pass", () => {
  it("has the v1.<P>.<S> form, with P the JSON exp and sub and S the HMAC-SHA256 of v1.<P>", async () => {
    const pass = await mintPass(SECRET, SUB, EXP);
    const [version, payload, signature] = pass.split(".");

    expect(version).toBe("v1");
    expect(new TextDecoder().decode(base64UrlDecode(payload)!)).toBe(`{"exp":${EXP},"sub":"${SUB}"}`);
    expect(pass).not.toContain("=");
    const key = await crypto.subtle.importKey("raw", utf8(SECRET), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    const expected = base64UrlEncode(await crypto.subtle.sign("HMAC", key, utf8(`v1.${payload}`)));
    expect(signature).toBe(expected);
  });

  it("takes its subject from the first 16 hex characters of the purchase token's SHA-256", async () => {
    expect(await passSubject("tok")).toBe((await sha256Hex("tok")).slice(0, 16));
    expect(await passSubject("tok")).toMatch(/^[0-9a-f]{16}$/);
  });

  it("verifies after a round trip", async () => {
    const pass = await mintPass(SECRET, SUB, EXP);

    expect(await verifyPass(SECRET, pass, NOW)).toEqual({ ok: true, exp: EXP, sub: SUB });
  });

  it("is expired from its exp second on", async () => {
    const pass = await mintPass(SECRET, SUB, EXP);

    expect((await verifyPass(SECRET, pass, EXP * 1000 - 1)).ok).toBe(true);
    expect(await verifyPass(SECRET, pass, EXP * 1000)).toEqual({ ok: false, reason: "expired" });
  });

  it("is refused when made with another secret", async () => {
    const pass = await mintPass("another-secret", SUB, EXP);

    expect(await verifyPass(SECRET, pass, NOW)).toEqual({ ok: false, reason: "malformed" });
  });

  it("is refused when its payload is changed, even to a later expiry", async () => {
    const [, , signature] = (await mintPass(SECRET, SUB, EXP)).split(".");
    const longer = base64UrlEncode(utf8(JSON.stringify({ exp: EXP + 86400 * 365, sub: SUB })));

    expect(await verifyPass(SECRET, `v1.${longer}.${signature}`, NOW)).toEqual({ ok: false, reason: "malformed" });
  });

  it("is refused when an expired pass is altered, rather than reported as expired", async () => {
    const [, payload, signature] = (await mintPass(SECRET, SUB, EXP)).split(".");
    const flipped = (signature[0] === "A" ? "B" : "A") + signature.slice(1);

    expect(await verifyPass(SECRET, `v1.${payload}.${flipped}`, EXP * 1000 + 1)).toEqual({ ok: false, reason: "malformed" });
  });

  it.each(["", "v1", "v1..", "v2.abc.def", "v1.abc", "v1.a.b.c", "v1.e30.!!!", "not a pass"])("refuses the malformed pass %j", async (pass) => {
    expect(await verifyPass(SECRET, pass, NOW)).toEqual({ ok: false, reason: "malformed" });
  });

  it("refuses a correctly signed payload that is not the pass JSON", async () => {
    const payload = base64UrlEncode(utf8(JSON.stringify({ exp: "soon", sub: SUB })));
    const key = await crypto.subtle.importKey("raw", utf8(SECRET), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    const signature = base64UrlEncode(await crypto.subtle.sign("HMAC", key, utf8(`v1.${payload}`)));

    expect(await verifyPass(SECRET, `v1.${payload}.${signature}`, NOW)).toEqual({ ok: false, reason: "malformed" });
  });

  it("is never minted without a secret", async () => {
    await expect(mintPass(undefined, SUB, EXP)).rejects.toThrow("PASS_SECRET");
    await expect(mintPass("", SUB, EXP)).rejects.toThrow("PASS_SECRET");
  });
});
