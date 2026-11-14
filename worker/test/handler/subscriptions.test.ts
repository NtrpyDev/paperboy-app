import { env } from "cloudflare:workers";
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { createHandler, type WorkerEnv } from "../../src/handler";
import { sha256Hex } from "../../src/encoding";
import { verifyPass } from "../../src/pass";
import { UNKNOWN_TTL_MS } from "../../src/subscriptions";
import { fakeGoogle, PACKAGE, PRODUCT, PUSH_EMAIL, pushJwt, serviceAccountJson, subscription } from "./fake-google";

const START = Date.UTC(2026, 10, 12, 12, 0, 0);
const HOUR = 3_600_000;
const DAY = 24 * HOUR;
const SECRET = "test-pass-secret";
const db = (env as unknown as { DB: D1Database }).DB;
const ALL_FIELDS = ["physics", "space", "math", "cs", "biology", "neuroscience", "medicine", "chemistry", "earth", "engineering", "social"];

let saJson: string;
beforeAll(async () => {
  saJson = await serviceAccountJson();
});

afterEach(async () => {
  // The database is shared by every test in this file, so empty it after each.
  await db.batch([db.prepare("DELETE FROM subscribers"), db.prepare("DELETE FROM unknown_purchases")]);
});

function setup(vars: Partial<WorkerEnv> = {}) {
  const google = fakeGoogle();
  let t = START;
  const handler = createHandler({ fetch: google.fetch, now: () => t });
  const testEnv = {
    ...env,
    PASS_SECRET: SECRET,
    GOOGLE_SERVICE_ACCOUNT_JSON: saJson,
    RTDN_SERVICE_ACCOUNT: PUSH_EMAIL,
    ...vars,
  } as WorkerEnv;
  const call = (path: string, init?: RequestInit) => handler.fetch(new Request(`https://paperboy.example${path}`, init), testEnv);
  const entitle = (body: unknown) =>
    call("/v1/entitlement", { method: "POST", headers: { "content-type": "application/json" }, body: typeof body === "string" ? body : JSON.stringify(body) });
  const ask = (token: string, fields: string[] = ["math"]) => entitle({ purchase_token: token, product_id: PRODUCT, fields });
  const push = async (notification: object, jwt?: string) =>
    call("/v1/rtdn", {
      method: "POST",
      headers: { authorization: `Bearer ${jwt ?? (await pushJwt(t))}`, "content-type": "application/json" },
      body: JSON.stringify({
        message: { data: btoa(JSON.stringify(notification)), messageId: "136969346945", publishTime: new Date(t).toISOString() },
        subscription: "projects/paperboy-test/subscriptions/rtdn",
      }),
    });
  const notify = (token: string, type = 2) =>
    push({ version: "1.0", packageName: PACKAGE, eventTimeMillis: String(t), subscriptionNotification: { version: "1.0", notificationType: type, purchaseToken: token } });
  const activeFields = async () => (await call("/v1/active-fields")).json<{ v: number; fields: string[]; updated_at: string }>();
  return {
    google,
    call,
    entitle,
    ask,
    push,
    notify,
    activeFields,
    advance(ms: number) {
      t += ms;
    },
    now: () => t,
  };
}

async function row(token: string) {
  return db.prepare("SELECT * FROM subscribers WHERE token_hash = ?1").bind(await sha256Hex(token)).first<Record<string, unknown>>();
}

type Entitlement = { entitled: boolean; state: string; expires_at: string | null; pass: string | null; pass_expires_at: string | null };

describe("POST /v1/entitlement", () => {
  it("grants a free trial, with a pass that lasts 48 hours when the trial runs longer", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-trial", subscription("SUBSCRIPTION_STATE_ACTIVE", { trial: true, expiry: START + 7 * DAY }));

    const res = await s.ask("tok-trial");
    const body = await res.json<Entitlement>();

    expect(res.status).toBe(200);
    expect(res.headers.get("cache-control")).toBe("no-store");
    expect(body).toMatchObject({ entitled: true, state: "trial", expires_at: new Date(START + 7 * DAY).toISOString() });
    expect(body.pass_expires_at).toBe(new Date(START + 48 * HOUR).toISOString());
    const check = await verifyPass(SECRET, body.pass!, START);
    expect(check).toEqual({ ok: true, exp: (START + 48 * HOUR) / 1000, sub: (await sha256Hex("tok-trial")).slice(0, 16) });
  });

  it("grants an active subscription, with a pass that ends at the subscription's expiry when that is sooner", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_ACTIVE", { expiry: START + 10 * HOUR }));

    const body = await (await s.ask("tok-active")).json<Entitlement>();

    expect(body).toMatchObject({ entitled: true, state: "active", pass_expires_at: new Date(START + 10 * HOUR).toISOString() });
  });

  it.each([
    ["SUBSCRIPTION_STATE_IN_GRACE_PERIOD", "grace", true],
    ["SUBSCRIPTION_STATE_ON_HOLD", "on_hold", false],
    ["SUBSCRIPTION_STATE_PAUSED", "paused", false],
    ["SUBSCRIPTION_STATE_EXPIRED", "expired", false],
    ["SUBSCRIPTION_STATE_PENDING_PURCHASE_CANCELED", "expired", false],
    ["SUBSCRIPTION_STATE_UNSPECIFIED", "expired", false],
  ])("maps %s to %s (entitled %s)", async (google, state, entitled) => {
    const s = setup();
    s.google.subscriptions.set("tok", subscription(google, { expiry: google === "SUBSCRIPTION_STATE_IN_GRACE_PERIOD" ? START + 3 * DAY : START - DAY }));

    const body = await (await s.ask("tok")).json<Entitlement>();

    expect(body.state).toBe(state);
    expect(body.entitled).toBe(entitled);
    expect(body.pass === null).toBe(!entitled);
    expect(body.pass_expires_at === null).toBe(!entitled);
  });

  it("maps a pending purchase to pending, with no expiry and no pass", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-pending", subscription("SUBSCRIPTION_STATE_PENDING", { expiry: null, acknowledged: false }));

    const body = await (await s.ask("tok-pending")).json<Entitlement>();

    expect(body).toEqual({ entitled: false, state: "pending", expires_at: null, pass: null, pass_expires_at: null });
    expect(s.google.count("ack")).toBe(0);
  });

  it("keeps a canceled subscription entitled until its expiry, then not", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-canceled", subscription("SUBSCRIPTION_STATE_CANCELED", { expiry: START + 2 * HOUR }));

    const before = await (await s.ask("tok-canceled")).json<Entitlement>();
    expect(before).toMatchObject({ entitled: true, state: "canceled", pass_expires_at: new Date(START + 2 * HOUR).toISOString() });

    s.advance(2 * HOUR);
    const after = await (await s.ask("tok-canceled")).json<Entitlement>();
    expect(after).toMatchObject({ entitled: false, state: "canceled", pass: null });
  });

  it("does not entitle a subscription canceled because another purchase replaced it", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-old", subscription("SUBSCRIPTION_STATE_CANCELED", { expiry: START + DAY, replaced: true }));

    const body = await (await s.ask("tok-old")).json<Entitlement>();

    expect(body).toMatchObject({ entitled: false, state: "expired", pass: null });
  });

  it("gives an entitled subscription whose expiry already passed a one hour pass", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-renewing", subscription("SUBSCRIPTION_STATE_ACTIVE", { expiry: START - 60_000 }));

    const body = await (await s.ask("tok-renewing")).json<Entitlement>();

    expect(body).toMatchObject({ entitled: true, pass_expires_at: new Date(START + HOUR).toISOString() });
  });

  it("answers 404 unknown_purchase for a token Google does not know, and does not ask Google again for a while", async () => {
    const s = setup();

    const first = await s.ask("tok-made-up");
    expect(first.status).toBe(404);
    expect(await first.json()).toEqual({ error: "unknown_purchase" });
    expect(s.google.count("get")).toBe(1);

    const repeat = await s.ask("tok-made-up");
    expect(repeat.status).toBe(404);
    expect(s.google.count("get")).toBe(1);

    s.advance(UNKNOWN_TTL_MS);
    await s.ask("tok-made-up");
    expect(s.google.count("get")).toBe(2);
    expect(await row("tok-made-up")).toBeNull();
  });

  it.each([410, 400])("reads Google's %s as an unknown purchase", async (status) => {
    const s = setup();
    s.google.subscriptions.set("tok-gone", status);

    expect((await s.ask("tok-gone")).status).toBe(404);
  });

  it.each([["throw"], [503], [500], [429], [403]] as const)("answers 502 store_unreachable when Google fails (%s)", async (how) => {
    const s = setup();
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_ACTIVE"));
    s.google.takeDown(how);

    const res = await s.ask("tok-active");

    expect(res.status).toBe(502);
    expect(await res.json()).toEqual({ error: "store_unreachable" });
    expect(await row("tok-active")).toBeNull();
  });

  it("answers 502 when Google's token endpoint fails", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_ACTIVE"));
    s.google.takeDownTokenEndpoint();

    expect((await s.ask("tok-active")).status).toBe(502);
    expect(s.google.count("get")).toBe(0);
  });

  it("acknowledges a new purchase once, and never one Google already shows acknowledged", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-new", subscription("SUBSCRIPTION_STATE_ACTIVE", { trial: true, acknowledged: false }));
    s.google.subscriptions.set("tok-renewed", subscription("SUBSCRIPTION_STATE_ACTIVE"));

    await s.ask("tok-new");
    await s.ask("tok-new");
    await s.ask("tok-renewed");

    expect(s.google.calls.filter((c) => c.kind === "ack")).toEqual([{ kind: "ack", token: "tok-new", productId: PRODUCT }]);
  });

  it("does not acknowledge an expired purchase", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-lapsed", subscription("SUBSCRIPTION_STATE_EXPIRED", { acknowledged: false, expiry: START - DAY }));

    await s.ask("tok-lapsed");

    expect(s.google.count("ack")).toBe(0);
  });

  it("reuses one access token until shortly before it expires", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_ACTIVE"));

    await s.ask("tok-active");
    s.advance(54 * 60_000);
    await s.ask("tok-active");
    expect(s.google.count("token")).toBe(1);

    s.advance(2 * 60_000);
    await s.ask("tok-active");
    expect(s.google.count("token")).toBe(2);
  });

  it("gets a fresh access token and retries once when Google rejects the cached one", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_ACTIVE"));
    await s.ask("tok-active");
    s.google.revokeAccessTokens();

    const res = await s.ask("tok-active");

    expect(res.status).toBe(200);
    expect(s.google.count("token")).toBe(2);
  });

  it("stores the token, product id, state, expiry, fields, and timestamps, and nothing else", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_ACTIVE", { expiry: START + DAY }));

    await s.ask("tok-active", ["space", "math"]);

    expect(await row("tok-active")).toEqual({
      token_hash: await sha256Hex("tok-active"),
      purchase_token: "tok-active",
      product_id: PRODUCT,
      state: "active",
      expires_at: START + DAY,
      fields: '["space","math"]',
      created_at: START,
      updated_at: START,
    });
  });

  it("replaces the fields when the person changes them", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_ACTIVE"));
    await s.ask("tok-active", ["physics", "space"]);
    s.advance(60_000);

    await s.ask("tok-active", ["biology"]);

    expect(await row("tok-active")).toMatchObject({ fields: '["biology"]', created_at: START, updated_at: START + 60_000 });
    expect((await s.activeFields()).fields).toEqual(["biology"]);
  });

  it("moves a replaced token's row to the new token, keeping the new token's own fields when it sent them", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-a", subscription("SUBSCRIPTION_STATE_ACTIVE"));
    await s.ask("tok-a", ["physics"]);
    s.google.subscriptions.set("tok-a", subscription("SUBSCRIPTION_STATE_CANCELED", { replaced: true }));
    s.google.subscriptions.set("tok-b", subscription("SUBSCRIPTION_STATE_ACTIVE", { linked: "tok-a" }));

    await s.ask("tok-b", ["chemistry"]);

    expect(await row("tok-a")).toBeNull();
    expect(await row("tok-b")).toMatchObject({ fields: '["chemistry"]' });
  });

  describe("bad bodies", () => {
    const good = { purchase_token: "tok", product_id: PRODUCT, fields: ["math"] };
    it.each([
      ["not JSON", "{"],
      ["an array", "[]"],
      ["no token", JSON.stringify({ product_id: PRODUCT, fields: ["math"] })],
      ["a number token", JSON.stringify({ ...good, purchase_token: 5 })],
      ["an empty token", JSON.stringify({ ...good, purchase_token: "" })],
      ["a token with a space", JSON.stringify({ ...good, purchase_token: "a b" })],
      ["a token that is too long", JSON.stringify({ ...good, purchase_token: "a".repeat(2049) })],
      ["no product id", JSON.stringify({ purchase_token: "tok", fields: ["math"] })],
      ["a product id with capitals", JSON.stringify({ ...good, product_id: "Monthly" })],
      ["no fields", JSON.stringify({ purchase_token: "tok", product_id: PRODUCT })],
      ["empty fields", JSON.stringify({ ...good, fields: [] })],
      ["fields that are not a list", JSON.stringify({ ...good, fields: "math" })],
      ["an unknown field", JSON.stringify({ ...good, fields: ["math", "astrology"] })],
      ["a field label instead of its wire value", JSON.stringify({ ...good, fields: ["Computer science"] })],
      ["a repeated field", JSON.stringify({ ...good, fields: ["math", "math"] })],
      ["12 fields", JSON.stringify({ ...good, fields: [...ALL_FIELDS, "math"] })],
      ["an extra key", JSON.stringify({ ...good, device: "pixel" })],
      ["a body over 8 KiB", JSON.stringify({ ...good, pad: "x".repeat(9000) })],
    ])("answers 400 bad_request for %s without asking Google", async (_name, body) => {
      const s = setup();

      const res = await s.entitle(body);

      expect(res.status).toBe(400);
      expect(await res.json()).toEqual({ error: "bad_request" });
      expect(s.google.calls).toEqual([]);
    });

    it("accepts all 11 fields", async () => {
      const s = setup();
      s.google.subscriptions.set("tok", subscription("SUBSCRIPTION_STATE_ACTIVE"));
      expect((await s.ask("tok", ALL_FIELDS)).status).toBe(200);
    });
  });

  it("fails loudly with 503 not_configured when PASS_SECRET is missing, and never asks Google or mints a pass", async () => {
    const s = setup({ PASS_SECRET: undefined });
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_ACTIVE"));

    const res = await s.ask("tok-active");

    expect(res.status).toBe(503);
    expect(await res.json()).toEqual({ error: "not_configured" });
    expect(s.google.calls).toEqual([]);
  });

  it("answers 503 not_configured when the service account secret is not usable", async () => {
    const s = setup({ GOOGLE_SERVICE_ACCOUNT_JSON: '{"client_email":"x@example.com","private_key":"not a key"}' });

    const res = await s.ask("tok-active");

    expect(res.status).toBe(503);
  });

  it("answers 405 to anything but POST", async () => {
    const s = setup();

    const res = await s.call("/v1/entitlement");

    expect(res.status).toBe(405);
    expect(res.headers.get("allow")).toBe("POST");
  });
});

describe("POST /v1/rtdn", () => {
  it("reads the token's state from Google on a verified subscription notification and updates the row", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_ACTIVE", { expiry: START + DAY }));
    await s.ask("tok-active", ["earth"]);
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_CANCELED", { expiry: START + DAY }));

    const res = await s.notify("tok-active", 3);

    expect(res.status).toBe(204);
    expect(await row("tok-active")).toMatchObject({ state: "canceled", fields: '["earth"]' });
  });

  it("acknowledges a purchase it hears about before the app calls", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-new", subscription("SUBSCRIPTION_STATE_ACTIVE", { acknowledged: false }));

    expect((await s.notify("tok-new", 4)).status).toBe(204);

    expect(s.google.count("ack")).toBe(1);
    expect(await row("tok-new")).toMatchObject({ state: "active", fields: "[]" });
  });

  it("gives a replacement token the fields of the token it replaces when it sent none", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-a", subscription("SUBSCRIPTION_STATE_ACTIVE"));
    await s.ask("tok-a", ["neuroscience", "medicine"]);
    s.google.subscriptions.set("tok-b", subscription("SUBSCRIPTION_STATE_ACTIVE", { linked: "tok-a" }));

    await s.notify("tok-b", 4);

    expect(await row("tok-b")).toMatchObject({ fields: '["neuroscience","medicine"]' });
    expect(await row("tok-a")).toBeNull();
    expect((await s.activeFields()).fields).toEqual(["medicine", "neuroscience"]);
  });

  it("gives a resubscription from the Play Store the fields of the expired token it names", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-a", subscription("SUBSCRIPTION_STATE_ACTIVE"));
    await s.ask("tok-a", ["social"]);
    s.google.subscriptions.set("tok-c", subscription("SUBSCRIPTION_STATE_ACTIVE", { expiredToken: "tok-a", acknowledged: false }));

    await s.notify("tok-c", 4);

    expect(await row("tok-c")).toMatchObject({ fields: '["social"]' });
  });

  it("answers 204 for a notification about a token Google does not know", async () => {
    const s = setup();

    expect((await s.notify("tok-unknown")).status).toBe(204);
    expect(await row("tok-unknown")).toBeNull();
  });

  it("answers 204 to a test notification and to another app's notification without asking Google", async () => {
    const s = setup();

    const test = await s.push({ version: "1.0", packageName: PACKAGE, eventTimeMillis: "1", testNotification: { version: "1.0" } });
    const other = await s.push({
      version: "1.0",
      packageName: "com.other.app",
      eventTimeMillis: "1",
      subscriptionNotification: { version: "1.0", notificationType: 4, purchaseToken: "tok" },
    });

    expect(test.status).toBe(204);
    expect(other.status).toBe(204);
    expect(s.google.count("get")).toBe(0);
  });

  it("reads the state again on a voided subscription purchase", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_ACTIVE"));
    await s.ask("tok-active");
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_EXPIRED", { expiry: START }));

    await s.push({
      version: "1.0",
      packageName: PACKAGE,
      eventTimeMillis: "1",
      voidedPurchaseNotification: { purchaseToken: "tok-active", orderId: "GPA.1", productType: 1, refundType: 1 },
    });

    expect(await row("tok-active")).toMatchObject({ state: "expired" });
  });

  it("answers 502 so Pub/Sub resends when Google cannot be asked", async () => {
    const s = setup();
    s.google.takeDown(503);

    expect((await s.notify("tok-active")).status).toBe(502);
  });

  it.each([
    ["a token signed with a key Google never published", { stranger: true }, {}],
    ["a key id Google does not list", { kid: "other-kid" }, {}],
    ["the wrong audience", {}, { aud: "https://elsewhere.example/v1/rtdn" }],
    ["the wrong email", {}, { email: "someone@evil.example" }],
    ["an unverified email", {}, { email_verified: false }],
    ["no email_verified claim", {}, { email_verified: undefined }],
    ["the wrong issuer", {}, { iss: "https://evil.example" }],
    ["an expired token", {}, { exp: Math.floor(START / 1000) - 1 }],
  ])("answers 401 to a push with %s, without asking Google about the token", async (_name, options, claims) => {
    const s = setup();
    const jwt = await pushJwt(START, claims, options);

    const res = await s.push({ packageName: PACKAGE, subscriptionNotification: { notificationType: 4, purchaseToken: "tok" } }, jwt);

    expect(res.status).toBe(401);
    expect(s.google.count("get")).toBe(0);
  });

  it("answers 401 to a push with a tampered payload", async () => {
    const s = setup();
    const [h, , sig] = (await pushJwt(START)).split(".");
    const forged = btoa(JSON.stringify({ aud: "x" })).replace(/=+$/, "");

    expect((await s.push({ packageName: PACKAGE }, `${h}.${forged}.${sig}`)).status).toBe(401);
  });

  it("answers 401 to a push with no authorization header, or when no service account is configured", async () => {
    const s = setup();
    const bare = await s.call("/v1/rtdn", { method: "POST", body: "{}" });
    const unconfigured = await setup({ RTDN_SERVICE_ACCOUNT: "" }).notify("tok");

    expect(bare.status).toBe(401);
    expect(unconfigured.status).toBe(401);
  });

  it("answers 502 when Google's signing keys cannot be fetched, and caches them once fetched", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_ACTIVE"));
    s.google.takeDownCerts();
    expect((await s.notify("tok-active")).status).toBe(502);

    s.google.bringUp();
    await s.notify("tok-active");
    await s.notify("tok-active");
    expect(s.google.count("certs")).toBe(2);
  });

  it("answers 405 to anything but POST", async () => {
    const s = setup();

    expect((await s.call("/v1/rtdn")).status).toBe(405);
  });
});

describe("GET /v1/active-fields", () => {
  async function seed(s: ReturnType<typeof setup>) {
    const rows: [string, object, string[]][] = [
      ["tok-active", subscription("SUBSCRIPTION_STATE_ACTIVE"), ["physics"]],
      ["tok-trial", subscription("SUBSCRIPTION_STATE_ACTIVE", { trial: true }), ["space", "physics"]],
      ["tok-grace", subscription("SUBSCRIPTION_STATE_IN_GRACE_PERIOD"), ["math"]],
      ["tok-canceled", subscription("SUBSCRIPTION_STATE_CANCELED", { expiry: START + HOUR }), ["cs"]],
      ["tok-hold", subscription("SUBSCRIPTION_STATE_ON_HOLD", { expiry: START - DAY }), ["biology"]],
      ["tok-paused", subscription("SUBSCRIPTION_STATE_PAUSED"), ["chemistry"]],
      ["tok-pending", subscription("SUBSCRIPTION_STATE_PENDING", { expiry: null }), ["earth"]],
      ["tok-expired", subscription("SUBSCRIPTION_STATE_EXPIRED", { expiry: START - DAY }), ["social"]],
    ];
    for (const [token, sub, fields] of rows) {
      s.google.subscriptions.set(token, sub as never);
      await s.ask(token, fields);
    }
  }

  it("lists the sorted fields of subscribers who count, trials included by default", async () => {
    const s = setup();
    await seed(s);

    const res = await s.call("/v1/active-fields");

    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ v: 1, fields: ["cs", "math", "physics", "space"], updated_at: new Date(START).toISOString() });
  });

  it("leaves trials out when COUNT_TRIALS is false", async () => {
    const s = setup({ COUNT_TRIALS: "false" });
    await seed(s);

    expect((await s.activeFields()).fields).toEqual(["cs", "math", "physics"]);
  });

  it("drops a canceled subscriber's fields once the subscription expires", async () => {
    const s = setup();
    await seed(s);

    s.advance(HOUR);

    expect((await s.activeFields()).fields).toEqual(["math", "physics", "space"]);
  });

  it("drops a subscriber's fields when a notification says the subscription expired", async () => {
    const s = setup();
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_ACTIVE"));
    await s.ask("tok-active", ["engineering"]);
    expect((await s.activeFields()).fields).toEqual(["engineering"]);
    s.google.subscriptions.set("tok-active", subscription("SUBSCRIPTION_STATE_EXPIRED", { expiry: START }));

    await s.notify("tok-active", 13);

    expect((await s.activeFields()).fields).toEqual([]);
  });

  it("is an empty list with no subscribers, publishes no counts, and answers HEAD", async () => {
    const s = setup();

    const res = await s.call("/v1/active-fields");
    const head = await s.call("/v1/active-fields", { method: "HEAD" });

    expect(await res.json()).toEqual({ v: 1, fields: [], updated_at: new Date(START).toISOString() });
    expect(res.headers.get("cache-control")).toBe("public, max-age=60");
    expect(head.status).toBe(200);
    expect(await head.text()).toBe("");
  });

  it("answers 405 to POST", async () => {
    const s = setup();

    const res = await s.call("/v1/active-fields", { method: "POST", body: "{}" });

    expect(res.status).toBe(405);
    expect(res.headers.get("allow")).toBe("GET, HEAD");
  });
});

describe("other /v1/ paths", () => {
  it("are 404 JSON", async () => {
    const s = setup();

    const res = await s.call("/v1/nothing");

    expect(res.status).toBe(404);
    expect(await res.json()).toEqual({ error: "not_found" });
  });
});
