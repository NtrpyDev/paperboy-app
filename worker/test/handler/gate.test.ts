import { env } from "cloudflare:workers";
import { afterEach, describe, expect, it } from "vitest";
import { createHandler, ORIGIN, type WorkerEnv } from "../../src/handler";
import { mintPass } from "../../src/pass";

const NOW = Date.UTC(2026, 10, 12, 12, 0, 0);
const SECRET = "test-pass-secret";
const SUB = "0123456789abcdef";

const head = JSON.stringify({ v: 1, updated_at: "2026-11-12T12:00:00Z", chunk_count: 1, total_items: 1, chunk_size: 40, kit: 1, min_app: 2 });
const FILES: Record<string, string> = {
  "feed/v2/head.json": head,
  "papers/arxiv-1/index.html": "<!doctype html><title>x</title>",
  "papers/arxiv-1/hero.webp": "image",
};

function setup(vars: Partial<WorkerEnv> = {}) {
  const calls: string[] = [];
  const fetch = async (input: RequestInfo | URL): Promise<Response> => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    calls.push(url);
    const path = url.startsWith(ORIGIN) ? url.slice(ORIGIN.length) : null;
    if (path === null || !(path in FILES)) return new Response("404: Not Found", { status: 404 });
    return new Response(FILES[path]);
  };
  let t = NOW;
  const handler = createHandler({ fetch, now: () => t });
  const testEnv = { ...env, CONTENT_GATE: "on", PASS_SECRET: SECRET, ...vars } as WorkerEnv;
  const get = (path: string, headers: Record<string, string> = {}, method = "GET") =>
    handler.fetch(new Request(`https://paperboy.example${path}`, { headers, method }), testEnv);
  return {
    calls,
    get,
    advance(seconds: number) {
      t += seconds * 1000;
    },
  };
}

const valid = () => mintPass(SECRET, SUB, NOW / 1000 + 3600);

afterEach(async () => {
  const listed = await env.CONTENT.list();
  if (listed.objects.length) await env.CONTENT.delete(listed.objects.map((o) => o.key));
});

describe("the content gate", () => {
  it("is off by default: no pass is needed and responses stay public", async () => {
    const s = setup({ CONTENT_GATE: env.CONTENT_GATE });

    const res = await s.get("/feed/v2/head.json");

    expect(env.CONTENT_GATE).toBe("off");
    expect(res.status).toBe(200);
    expect(res.headers.get("cache-control")).toBe("public, max-age=60");
    expect(res.headers.get("access-control-allow-origin")).toBe("*");
  });

  it.each(["/feed/v2/head.json", "/papers/arxiv-1/index.html", "/papers/arxiv-1/", "/feed/v2/chunks/000001.json", "/papers/nothing/here.json"])(
    "answers 401 pass_required for %s with no pass, without asking the content repo",
    async (path) => {
      const s = setup();

      const res = await s.get(path);

      expect(res.status).toBe(401);
      expect(await res.json()).toEqual({ error: "pass_required" });
      expect(res.headers.get("cache-control")).toBe("no-store");
      expect(s.calls).toEqual([]);
    },
  );

  it("serves a request with a valid pass in the header, privately, with the same max-age rules and no open CORS", async () => {
    const s = setup();
    const pass = await valid();

    const headRes = await s.get("/feed/v2/head.json", { "x-paperboy-pass": pass });
    const page = await s.get("/papers/arxiv-1/index.html", { "x-paperboy-pass": pass });

    expect(headRes.status).toBe(200);
    expect(headRes.headers.get("cache-control")).toBe("private, max-age=60");
    expect(headRes.headers.get("access-control-allow-origin")).toBeNull();
    expect(page.status).toBe(200);
    expect(page.headers.get("cache-control")).toBe("private, max-age=31536000, immutable");
    expect(page.headers.get("content-security-policy")).toContain("default-src 'none'");
  });

  it("serves a request with a valid pass in the pb_pass cookie, as the WebView and its images send it", async () => {
    const s = setup();
    const pass = await valid();

    const res = await s.get("/papers/arxiv-1/hero.webp", { cookie: `theme=dark; pb_pass=${pass}; other=1` });

    expect(res.status).toBe(200);
    expect(res.headers.get("content-type")).toBe("image/webp");
    expect(res.headers.get("cache-control")).toBe("private, max-age=31536000, immutable");
  });

  it("answers 401 pass_expired once the pass has expired", async () => {
    const s = setup();
    const pass = await valid();
    s.advance(3600);

    const res = await s.get("/feed/v2/head.json", { "x-paperboy-pass": pass });

    expect(res.status).toBe(401);
    expect(await res.json()).toEqual({ error: "pass_expired" });
  });

  it.each([
    ["a malformed pass", "v1.nope"],
    ["a pass signed with another secret", "other"],
  ])("answers 401 pass_required for %s", async (_name, kind) => {
    const s = setup();
    const pass = kind === "other" ? await mintPass("another-secret", SUB, NOW / 1000 + 3600) : kind;

    const res = await s.get("/feed/v2/head.json", { "x-paperboy-pass": pass });

    expect(res.status).toBe(401);
    expect(await res.json()).toEqual({ error: "pass_required" });
  });

  it("accepts the cookie when the header holds a stale pass", async () => {
    const s = setup();

    const res = await s.get("/feed/v2/head.json", { "x-paperboy-pass": "v1.stale.x", cookie: `pb_pass=${await valid()}` });

    expect(res.status).toBe(200);
  });

  it("answers HEAD with a valid pass", async () => {
    const s = setup();

    const res = await s.get("/feed/v2/head.json", { "x-paperboy-pass": await valid() }, "HEAD");

    expect(res.status).toBe(200);
    expect(await res.text()).toBe("");
  });

  it.each(["/", "/kit/v1/paperboy.css", "/feed", "/v1/nothing"])("leaves %s outside the gate", async (path) => {
    const s = setup();

    const res = await s.get(path);

    expect(res.status).toBe(404);
    await res.arrayBuffer();
  });

  it("keeps the active fields list public", async () => {
    const s = setup();

    const res = await s.get("/v1/active-fields");

    expect(res.status).toBe(200);
  });

  it("fails closed with 503 not_configured when PASS_SECRET is missing", async () => {
    const s = setup({ PASS_SECRET: undefined });

    const res = await s.get("/feed/v2/head.json", { "x-paperboy-pass": await valid() });

    expect(res.status).toBe(503);
    expect(await res.json()).toEqual({ error: "not_configured" });
    expect(s.calls).toEqual([]);
  });
});
