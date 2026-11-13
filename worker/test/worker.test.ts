import { reset } from "cloudflare:test";
import { env } from "cloudflare:workers";
import { afterEach, describe, expect, it } from "vitest";
import { createHandler } from "../src/handler";

const ORIGIN = "https://raw.githubusercontent.com/NtrpyDev/paperboy-content/main/";

// A stand-in for the content repo's raw file host. Files can be changed or the
// whole origin taken down between requests, and every call is recorded.
function fakeOrigin(files: Record<string, string>) {
  const calls: string[] = [];
  let down = false;
  const fetch = async (input: RequestInfo | URL): Promise<Response> => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    calls.push(url);
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
    takeDown() {
      down = true;
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

afterEach(async () => {
  await reset();
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
});
