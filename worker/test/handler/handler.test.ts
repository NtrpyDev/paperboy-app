import { env } from "cloudflare:workers";
import { afterEach, describe, expect, it } from "vitest";
import { createHandler } from "../../src/handler";

const ORIGIN = "https://raw.githubusercontent.com/NtrpyDev/paperboy-content/main/";

// A stand-in for the content repo's raw file host. Files can be changed or the
// whole origin taken down between requests, and every call is recorded.
function fakeOrigin(files: Record<string, string>) {
  const calls: string[] = [];
  let down: false | "error" | "throw" = false;
  const fetch = async (input: RequestInfo | URL): Promise<Response> => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    calls.push(url);
    if (down === "throw") throw new TypeError("Network connection lost.");
    if (down) return new Response("unavailable", { status: 503 });
    const path = url.startsWith(ORIGIN) ? url.slice(ORIGIN.length) : null;
    if (path === null || !(path in files)) return new Response("404: Not Found", { status: 404 });
    // The real host labels every file text/plain, so the worker must not trust it.
    return new Response(files[path], { headers: { "content-type": "text/plain; charset=utf-8" } });
  };
  return {
    fetch,
    calls,
    files,
    // "error" answers 503; "throw" fails the way fetch does when the host is unreachable.
    takeDown(how: "error" | "throw" = "error") {
      down = how;
    },
  };
}

function clock(start = Date.UTC(2026, 10, 12, 12, 0, 0)) {
  let t = start;
  return {
    now: () => t,
    advance(seconds: number) {
      t += seconds * 1000;
    },
  };
}

function setup(files: Record<string, string>) {
  const origin = fakeOrigin(files);
  const time = clock();
  const handler = createHandler({ fetch: origin.fetch, now: time.now });
  const get = (path: string, init?: RequestInit) =>
    handler.fetch(new Request(`https://paperboy.example${path}`, init), env);
  return { origin, time, get };
}

function head(chunkCount: number) {
  return JSON.stringify({
    v: 1,
    updated_at: "2026-11-12T12:00:00Z",
    chunk_count: chunkCount,
    total_items: chunkCount * 40 - 39,
    chunk_size: 40,
    kit: 1,
    min_app: 1,
  });
}

afterEach(async () => {
  // Storage is shared by every test in this file, so empty the bucket after each.
  const listed = await env.CONTENT.list();
  if (listed.objects.length) await env.CONTENT.delete(listed.objects.map((o) => o.key));
});

describe("paper files", () => {
  it("fetches a missing file from the content repo, stores it in the bucket, and serves it", async () => {
    const { origin, get } = setup({ "papers/arxiv-1/meta.json": '{"id":"arxiv-1"}' });

    const res = await get("/papers/arxiv-1/meta.json");

    expect(res.status).toBe(200);
    expect(await res.text()).toBe('{"id":"arxiv-1"}');
    expect(origin.calls).toEqual([`${ORIGIN}papers/arxiv-1/meta.json`]);
    const stored = await env.CONTENT.get("papers/arxiv-1/meta.json");
    expect(await stored?.text()).toBe('{"id":"arxiv-1"}');
  });

  it("serves a stored file from the bucket without calling the content repo", async () => {
    const { origin, time, get } = setup({ "papers/arxiv-1/meta.json": '{"id":"arxiv-1"}' });
    await get("/papers/arxiv-1/meta.json");
    origin.files["papers/arxiv-1/meta.json"] = '{"id":"changed"}';
    time.advance(86400);

    const res = await get("/papers/arxiv-1/meta.json");

    expect(res.status).toBe(200);
    expect(await res.text()).toBe('{"id":"arxiv-1"}');
    expect(origin.calls).toHaveLength(1);
  });
});

describe("the head", () => {
  it("is served from the bucket for 60 seconds, then refreshed from the content repo", async () => {
    const { origin, time, get } = setup({ "feed/v1/head.json": head(1) });
    await get("/feed/v1/head.json");
    origin.files["feed/v1/head.json"] = head(2);

    time.advance(60);
    const early = await get("/feed/v1/head.json");
    expect(JSON.parse(await early.text()).chunk_count).toBe(1);
    expect(origin.calls).toHaveLength(1);

    time.advance(1);
    const late = await get("/feed/v1/head.json");
    expect(JSON.parse(await late.text()).chunk_count).toBe(2);
    expect(origin.calls).toHaveLength(2);
  });

  it.each(["error", "throw"] as const)(
    "is served from the stored copy when the content repo fails during a refresh (%s)",
    async (how) => {
      const { origin, time, get } = setup({ "feed/v1/head.json": head(1) });
      await get("/feed/v1/head.json");
      origin.takeDown(how);
      time.advance(120);

      const res = await get("/feed/v1/head.json");

      expect(res.status).toBe(200);
      expect(JSON.parse(await res.text()).chunk_count).toBe(1);
      expect(origin.calls).toHaveLength(2);
    },
  );
});

describe("chunks", () => {
  const chunk = (n: number, items: number) => JSON.stringify({ v: 1, number: n, items: Array(items).fill({}) });

  it("refreshes the open chunk, the highest numbered one in the stored head, after 60 seconds", async () => {
    const { origin, time, get } = setup({
      "feed/v1/head.json": head(2),
      "feed/v1/chunks/000002.json": chunk(2, 1),
    });
    await get("/feed/v1/head.json");
    await get("/feed/v1/chunks/000002.json");
    origin.files["feed/v1/chunks/000002.json"] = chunk(2, 2);

    time.advance(30);
    expect(JSON.parse(await (await get("/feed/v1/chunks/000002.json")).text()).items).toHaveLength(1);
    time.advance(31);
    expect(JSON.parse(await (await get("/feed/v1/chunks/000002.json")).text()).items).toHaveLength(2);
  });

  it("never refreshes a closed chunk", async () => {
    const { origin, time, get } = setup({
      "feed/v1/head.json": head(2),
      "feed/v1/chunks/000001.json": chunk(1, 40),
    });
    await get("/feed/v1/head.json");
    await get("/feed/v1/chunks/000001.json");
    const callsAfterFill = origin.calls.length;
    time.advance(86400);

    const res = await get("/feed/v1/chunks/000001.json");

    expect(JSON.parse(await res.text()).items).toHaveLength(40);
    expect(origin.calls).toHaveLength(callsAfterFill);
  });

  it("fetches a chunk once more after it closes, so its last items are not lost, then keeps it", async () => {
    const { origin, time, get } = setup({
      "feed/v1/head.json": head(1),
      "feed/v1/chunks/000001.json": chunk(1, 39),
    });
    await get("/feed/v1/head.json");
    await get("/feed/v1/chunks/000001.json");
    origin.files["feed/v1/chunks/000001.json"] = chunk(1, 40);
    origin.files["feed/v1/head.json"] = head(2);
    time.advance(61);
    await get("/feed/v1/head.json");

    const closed = await get("/feed/v1/chunks/000001.json");
    expect(JSON.parse(await closed.text()).items).toHaveLength(40);

    const callsAfterClose = origin.calls.length;
    time.advance(86400);
    await get("/feed/v1/chunks/000001.json");
    expect(origin.calls).toHaveLength(callsAfterClose);
  });

  // The content repo's raw host caches files for up to five minutes, so right after
  // a chunk closes it can still hand out the copy from before its last items.
  it("keeps refreshing a closed chunk until it holds the full 40 items", async () => {
    const { origin, time, get } = setup({
      "feed/v1/head.json": head(2),
      "feed/v1/chunks/000001.json": chunk(1, 39),
    });
    await get("/feed/v1/head.json");
    await get("/feed/v1/chunks/000001.json");
    origin.files["feed/v1/chunks/000001.json"] = chunk(1, 40);

    time.advance(61);
    const res = await get("/feed/v1/chunks/000001.json");
    expect(JSON.parse(await res.text()).items).toHaveLength(40);

    const callsWhenFull = origin.calls.length;
    time.advance(86400);
    await get("/feed/v1/chunks/000001.json");
    expect(origin.calls).toHaveLength(callsWhenFull);
  });
});

describe("cache lifetimes", () => {
  const LONG = "public, max-age=31536000, immutable";
  const SHORT = "public, max-age=60";
  const files = {
    "feed/v1/head.json": head(2),
    "feed/v1/chunks/000001.json": JSON.stringify({ v: 1, number: 1, items: Array(40).fill({}) }),
    "feed/v1/chunks/000002.json": JSON.stringify({ v: 1, number: 2, items: [{}] }),
    "papers/arxiv-1/index.html": "<!doctype html><title>x</title>",
    "papers/arxiv-1/meta.json": "{}",
  };

  it.each([
    ["/feed/v1/head.json", SHORT],
    ["/feed/v1/chunks/000002.json", SHORT],
    ["/feed/v1/chunks/000001.json", LONG],
    ["/papers/arxiv-1/index.html", LONG],
    ["/papers/arxiv-1/meta.json", LONG],
  ])("%s is served with cache-control %s, on a miss and on a hit", async (path, expected) => {
    const { get } = setup({ ...files });
    await get("/feed/v1/head.json");

    const miss = await get(path);
    const hit = await get(path);

    expect(miss.headers.get("cache-control")).toBe(expected);
    expect(hit.headers.get("cache-control")).toBe(expected);
  });
});

describe("content types", () => {
  it.each([
    ["/feed/v1/head.json", "application/json; charset=utf-8"],
    ["/papers/arxiv-1/index.html", "text/html; charset=utf-8"],
    ["/papers/arxiv-1/meta.json", "application/json; charset=utf-8"],
    ["/papers/arxiv-1/hero.webp", "image/webp"],
    ["/papers/arxiv-1/figure.png", "image/png"],
    ["/papers/arxiv-1/figure.jpg", "image/jpeg"],
    ["/papers/arxiv-1/figure.svg", "image/svg+xml"],
  ])("%s is served as %s, on a miss and on a hit", async (path, expected) => {
    const { get } = setup({ [path.slice(1)]: "content" });

    const miss = await get(path);
    const hit = await get(path);

    expect(miss.headers.get("content-type")).toBe(expected);
    expect(hit.headers.get("content-type")).toBe(expected);
  });
});

describe("explainer security policy", () => {
  const POLICY =
    "default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data:; font-src 'self'; connect-src 'none'";

  it("is sent with explainer pages, on a miss and on a hit", async () => {
    const { get } = setup({ "papers/arxiv-1/index.html": "<!doctype html><title>x</title>" });

    const miss = await get("/papers/arxiv-1/index.html");
    const hit = await get("/papers/arxiv-1/index.html");

    expect(miss.headers.get("content-security-policy")).toBe(POLICY);
    expect(hit.headers.get("content-security-policy")).toBe(POLICY);
  });

  it("is not sent with feed files", async () => {
    const { get } = setup({ "feed/v1/head.json": head(1) });

    const res = await get("/feed/v1/head.json");

    expect(res.headers.get("content-security-policy")).toBeNull();
  });
});

describe("explainer address", () => {
  it("serves a paper folder's index.html for the folder path", async () => {
    const { origin, get } = setup({ "papers/arxiv-1/index.html": "<!doctype html><title>x</title>" });

    const res = await get("/papers/arxiv-1/");

    expect(res.status).toBe(200);
    expect(await res.text()).toBe("<!doctype html><title>x</title>");
    expect(res.headers.get("content-type")).toBe("text/html; charset=utf-8");
    expect(res.headers.get("content-security-policy")).toContain("default-src 'none'");
    expect(origin.calls).toEqual([`${ORIGIN}papers/arxiv-1/index.html`]);
  });
});

describe("cross-origin reads", () => {
  it("are allowed from any origin on feed files", async () => {
    const { get } = setup({ "feed/v1/head.json": head(1) });

    const res = await get("/feed/v1/head.json", { headers: { origin: "https://elsewhere.example" } });

    expect(res.headers.get("access-control-allow-origin")).toBe("*");
  });

  it("are not opened up on paper files", async () => {
    const { get } = setup({ "papers/arxiv-1/meta.json": "{}" });

    const res = await get("/papers/arxiv-1/meta.json", { headers: { origin: "https://elsewhere.example" } });

    expect(res.headers.get("access-control-allow-origin")).toBeNull();
  });
});

describe("unknown paths", () => {
  it.each(["/nothing-here", "/state/seen.txt", "/feed", "/papers"])(
    "%s is 404 without asking the content repo",
    async (path) => {
      const { origin, get } = setup({ "state/seen.txt": "secret-ish" });

      const res = await get(path);

      expect(res.status).toBe(404);
      expect(origin.calls).toEqual([]);
    },
  );

  it.each(["/feed/v1/%2e%2e%2fstate/seen.txt", "/papers/a%2Fb/index.html", "/papers//index.html"])(
    "%s, a path outside the plain file name characters, is 404 without asking the content repo",
    async (path) => {
      const { origin, get } = setup({});

      const res = await get(path);

      expect(res.status).toBe(404);
      expect(origin.calls).toEqual([]);
    },
  );

  it("is 404 when the content repo does not have the file, and nothing is stored", async () => {
    const { get } = setup({});

    const res = await get("/papers/arxiv-1/missing.json");

    expect(res.status).toBe(404);
    expect(await env.CONTENT.get("papers/arxiv-1/missing.json")).toBeNull();
  });
});

describe("content repo outage", () => {
  it.each(["error", "throw"] as const)(
    "a file the bucket does not have yet is a 502, not a 404, and nothing is stored (%s)",
    async (how) => {
      const { origin, get } = setup({ "papers/arxiv-1/meta.json": "{}" });
      origin.takeDown(how);

      const res = await get("/papers/arxiv-1/meta.json");

      expect(res.status).toBe(502);
      expect(await env.CONTENT.get("papers/arxiv-1/meta.json")).toBeNull();
    },
  );
});

describe("request methods", () => {
  it("answers HEAD with the headers of GET and no body", async () => {
    const { get } = setup({ "feed/v1/head.json": head(1) });

    const res = await get("/feed/v1/head.json", { method: "HEAD" });

    expect(res.status).toBe(200);
    expect(res.headers.get("content-type")).toBe("application/json; charset=utf-8");
    expect(await res.text()).toBe("");
  });

  it("refuses anything other than GET and HEAD without asking the content repo", async () => {
    const { origin, get } = setup({ "feed/v1/head.json": head(1) });

    const res = await get("/feed/v1/head.json", { method: "POST", body: "x" });

    expect(res.status).toBe(405);
    expect(res.headers.get("allow")).toBe("GET, HEAD");
    expect(origin.calls).toEqual([]);
  });
});

describe("where a response came from", () => {
  it("says origin when the file was just fetched from the content repo and bucket when it was stored", async () => {
    const { origin, time, get } = setup({ "feed/v1/head.json": head(1) });

    const first = await get("/feed/v1/head.json");
    const second = await get("/feed/v1/head.json");
    time.advance(61);
    const refreshed = await get("/feed/v1/head.json");
    origin.takeDown();
    time.advance(61);
    const fallback = await get("/feed/v1/head.json");

    expect(first.headers.get("x-paperboy-source")).toBe("origin");
    expect(second.headers.get("x-paperboy-source")).toBe("bucket");
    expect(refreshed.headers.get("x-paperboy-source")).toBe("origin");
    expect(fallback.headers.get("x-paperboy-source")).toBe("bucket");
  });
});
