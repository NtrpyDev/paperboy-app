import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { createTestHarness } from "wrangler";

// Static assets are not exposed to tests in the Workers pool, so these run the
// worker the way wrangler dev does. Only asset paths and paths the handler rejects
// without a fetch are used, so the real content repo is never called.
const server = createTestHarness({ workers: [{ configPath: "./wrangler.jsonc" }] });

beforeAll(async () => {
  await server.listen();
});

afterAll(async () => {
  await server.close();
});

describe("static assets", () => {
  it.each([
    ["/kit/v1/paperboy.css", "text/css"],
    ["/kit/v1/paperboy.js", "javascript"],
    ["/kit/v1/vendor/d3.min.js", "javascript"],
    ["/kit/v1/vendor/katex/katex.min.css", "text/css"],
    ["/kit/v1/vendor/katex/fonts/KaTeX_Main-Regular.woff2", "font/woff2"],
    ["/kit/v1/gallery.html", "text/html"],
  ])("serves the kit file %s as %s", async (path, type) => {
    const res = await server.fetch(path);

    expect(res.status).toBe(200);
    expect(res.headers.get("content-type")).toContain(type);
    await res.arrayBuffer();
  });

  it("serves the home page at /", async () => {
    const res = await server.fetch("/");

    expect(res.status).toBe(200);
    expect(res.headers.get("content-type")).toContain("text/html");
    expect(await res.text()).toContain("Paperboy is a free, open source Android app");
  });

  it("answers 404 for a kit file that does not exist", async () => {
    const res = await server.fetch("/kit/v1/missing.js");

    expect(res.status).toBe(404);
    await res.arrayBuffer();
  });
});
