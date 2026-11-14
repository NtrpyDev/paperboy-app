import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { createTestHarness } from "wrangler";

// The worker as deployed today (the top level of wrangler.jsonc, without the paid
// environment's subscriber database), run the way wrangler dev runs it. No request here
// reaches Google or the content repo.
const server = createTestHarness({ workers: [{ configPath: "./wrangler.jsonc" }] });

beforeAll(async () => {
  await server.listen();
});

afterAll(async () => {
  await server.close();
});

describe("/v1/ on the worker deployed today", () => {
  it("reaches the worker rather than the static assets", async () => {
    const res = await server.fetch("/v1/active-fields");

    expect(res.headers.get("content-type")).toContain("application/json");
    expect(res.status).toBe(503);
    expect(await res.json()).toEqual({ error: "not_configured" });
  });

  it("answers a valid entitlement request with 503 not_configured, since it has no subscriber database", async () => {
    const res = await server.fetch("/v1/entitlement", {
      method: "POST",
      body: JSON.stringify({ purchase_token: "tok", product_id: "paperboy_monthly", fields: ["math"] }),
    });

    expect(res.status).toBe(503);
    expect(await res.json()).toEqual({ error: "not_configured" });
  });

  // A path the handler rejects before any fetch: 404, not the gate's 401.
  it("keeps the content gate off", async () => {
    const res = await server.fetch("/papers/a%2Fb/index.html");

    expect(res.status).toBe(404);
    await res.arrayBuffer();
  });
});
