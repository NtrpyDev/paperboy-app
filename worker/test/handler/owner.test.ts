import { createScheduledController } from "cloudflare:test";
import { env } from "cloudflare:workers";
import { afterEach, describe, expect, it } from "vitest";
import { createHandler, ORIGIN, type WorkerEnv } from "../../src/handler";
import { parseMonth } from "../../src/cost";
import { sha256Hex } from "../../src/encoding";
import { PAGE_STYLE } from "../../src/owner";
// The cost records pipeline/tests/test_cost_fixture.py checks budget-gate against.
import october from "../../../schema/fixtures/cost/2026-10.jsonl?raw";
import november from "../../../schema/fixtures/cost/2026-11.jsonl?raw";
import expectedJson from "../../../schema/fixtures/cost/expected.json?raw";

const EXPECTED = JSON.parse(expectedJson).months as Record<string, { spend_usd: number; runs: number; pages: Record<string, number> }>;
const NOW = Date.UTC(2026, 10, 12, 12, 0, 0);
const DAY = 86_400_000;
const PASSWORD = "correct horse battery staple";
const db = (env as unknown as { DB: D1Database }).DB;

afterEach(async () => {
  await db.batch([db.prepare("DELETE FROM subscribers"), db.prepare("DELETE FROM snapshots")]);
  const listed = await env.CONTENT.list();
  if (listed.objects.length) await env.CONTENT.delete(listed.objects.map((o) => o.key));
});

function setup(vars: Partial<WorkerEnv> = {}, files: Record<string, string> = { "state/cost/2026-10.jsonl": october, "state/cost/2026-11.jsonl": november }) {
  const calls: string[] = [];
  let down = false;
  const fetch = async (input: RequestInfo | URL): Promise<Response> => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    calls.push(url);
    if (down) return new Response("unavailable", { status: 503 });
    const path = url.startsWith(ORIGIN) ? url.slice(ORIGIN.length) : null;
    if (path === null || !(path in files)) return new Response("404: Not Found", { status: 404 });
    return new Response(files[path]);
  };
  let t = NOW;
  const handler = createHandler({ fetch, now: () => t });
  const testEnv = { ...env, OWNER_PASSWORD: PASSWORD, LIST_PRICE_USD: "5", ...vars } as WorkerEnv;
  const get = (path: string, init: RequestInit = {}) => handler.fetch(new Request(`https://paperboy.example${path}`, init), testEnv);
  const page = async (user = "owner", password = PASSWORD) => {
    const res = await get("/owner/numbers", { headers: { authorization: `Basic ${btoa(`${user}:${password}`)}` } });
    return { res, html: await res.text() };
  };
  return {
    calls,
    get,
    page,
    handler,
    testEnv,
    takeDown() {
      down = true;
    },
    at(ms: number) {
      t = ms;
    },
  };
}

let n = 0;
async function subscriber(state: string, fields: string[], expiresAt: number | null = NOW + 10 * DAY, createdAt = NOW - DAY) {
  const token = `tok-${state}-${n++}`;
  await db
    .prepare("INSERT INTO subscribers VALUES (?1, ?2, 'paperboy_monthly', ?3, ?4, ?5, ?6, ?6)")
    .bind(await sha256Hex(token), token, state, expiresAt, JSON.stringify(fields), createdAt)
    .run();
}

// Every state once: four pay now (two active, grace, canceled before expiry), two are trials,
// and the rest count as neither.
async function seedEveryState() {
  await subscriber("active", ["physics", "math"]);
  await subscriber("active", ["physics"]);
  await subscriber("grace", ["cs"]);
  await subscriber("canceled", ["earth"], NOW + DAY);
  await subscriber("canceled", ["medicine"], NOW - 1);
  await subscriber("trial", ["space"]);
  await subscriber("trial", ["physics"]);
  await subscriber("on_hold", ["chemistry"], NOW - DAY);
  await subscriber("paused", ["chemistry"]);
  await subscriber("expired", ["neuroscience"], NOW - DAY);
  await subscriber("pending", ["engineering"], null);
}

const text = (html: string) => html.replace(/<[^>]+>/g, " ").replace(/&amp;/g, "&").replace(/\s+/g, " ").trim();

function figures(html: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const m of html.matchAll(/<div class="fig"><div class="lab">(.*?)<\/div><div class="num">(.*?)<\/div>(.*?)<\/div>(?=<div class="fig">|<\/div>\n)/g)) {
    out[m[1]] = m[2];
    out[`${m[1]} note`] = text(m[3]);
  }
  return out;
}

function rows(html: string, table: "fields" | "months"): string[][] {
  const body = new RegExp(`<table class="${table}">.*?<tbody>(.*?)</tbody>`, "s").exec(html)![1];
  return [...body.matchAll(/<tr[^>]*>(.*?)<\/tr>/g)].map((r) => [...r[1].matchAll(/<t[hd][^>]*>(.*?)<\/t[hd]>/g)].map((c) => text(c[1])));
}

describe("the owner's numbers page", () => {
  it("shows subscribers, income after Google's cut, API cost, and left over for this month, with the paid-for-itself sentence", async () => {
    await seedEveryState();
    const s = setup();

    const { res, html } = await s.page();
    const figs = figures(html);

    expect(res.status).toBe(200);
    expect(html).toContain("<h1>Paperboy numbers</h1>");
    expect(figs["Subscribers"]).toBe("4");
    // 4 x $5 x (1 - 15 / 100).
    expect(figs["Income after Google's cut"]).toBe("$17.00");
    expect(figs["Income after Google's cut note"]).toBe("Estimate from today's subscriber count.");
    expect(figs["API cost"]).toBe("$11.50");
    expect(figs["Left over"]).toBe("$5.50");
    expect(figs["Left over note"]).toBe("The app paid for itself this month.");
    expect(text(html)).toContain("This month November 2026");
  });

  it("says what the app cost when the API cost more than the income", async () => {
    await seedEveryState();
    const s = setup({ LIST_PRICE_USD: "2" });

    const figs = figures((await s.page()).html);

    expect(figs["Income after Google's cut"]).toBe("$6.80");
    expect(figs["Left over"]).toBe("-$4.70");
    expect(figs["Left over note"]).toBe("The app cost you $4.70 this month.");
  });

  it("counts trials apart from subscribers, and on hold, paused, expired, pending, and lapsed cancellations as neither", async () => {
    await seedEveryState();
    const s = setup();

    const { html } = await s.page();

    expect(figures(html)["Subscribers"]).toBe("4");
    expect(text(html)).toContain("Trials not yet paying: 2");
  });

  it("uses GOOGLE_FEE_PERCENT when set", async () => {
    await subscriber("active", ["math"]);
    const s = setup({ LIST_PRICE_USD: "10", GOOGLE_FEE_PERCENT: "30" });

    expect(figures((await s.page()).html)["Income after Google's cut"]).toBe("$7.00");
  });

  it.each(["", "free", "0", "-3"])("shows income and left over as not set when LIST_PRICE_USD is %j, with no sentence", async (price) => {
    await subscriber("active", ["math"]);
    const s = setup({ LIST_PRICE_USD: price });

    const figs = figures((await s.page()).html);

    expect(figs["Income after Google's cut"]).toBe("not set");
    expect(figs["Income after Google's cut note"]).toBe("");
    expect(figs["Left over"]).toBe("not set");
    expect(figs["Left over note"]).toBe("");
    expect(figs["API cost"]).toBe("$11.50");
  });

  it("lists every field in the app's order with subscribers who picked it, pages and API cost this month, and its status", async () => {
    await seedEveryState();
    const s = setup();

    const { html } = await s.page();
    const table = rows(html, "fields");

    expect(html).toContain(
      '</table></div>\n<p class="note muted">A run\'s cost is split evenly across the papers it worked on, so a field\'s cost is an estimate.</p>\n</section>',
    );
    // Pages and cost from the November fixture: run 1 ($3.10) was handed cs twice and biology
    // once; run 2 ($0.40) was handed nothing; run 3 is incomplete and counts its $8 cap, all earth.
    expect(table).toEqual([
      ["Physics", "2", "0", "$0", "Making pages"],
      ["Space", "0", "0", "$0", "Making pages"],
      ["Math", "1", "0", "$0", "Making pages"],
      ["Computer science", "1", "2", "$2.07", "Making pages"],
      ["Biology", "0", "1", "$1.03", "No subscribers, no pages"],
      ["Neuroscience", "0", "0", "$0", "No subscribers, no pages"],
      ["Medicine", "0", "0", "$0", "No subscribers, no pages"],
      ["Chemistry", "0", "0", "$0", "No subscribers, no pages"],
      ["Earth", "1", "1", "$8.00", "Making pages"],
      ["Engineering", "0", "0", "$0", "No subscribers, no pages"],
      ["Social science", "0", "0", "$0", "No subscribers, no pages"],
    ]);
  });

  it("marks a field picked only by trials as not making pages when COUNT_TRIALS is false", async () => {
    await subscriber("trial", ["space"]);
    const s = setup({ COUNT_TRIALS: "false" });

    const space = rows((await s.page()).html, "fields")[1];

    expect(space).toEqual(["Space", "0", "0", "$0", "No subscribers, no pages"]);
  });

  it("dims the row of a field with no subscribers, as the board does", async () => {
    const s = setup();

    const { html } = await s.page();

    expect(html.match(/<tr class="off">/g)).toHaveLength(11);
  });
});

describe("the daily snapshot", () => {
  it("is written by the scheduled handler for the UTC day, replacing an earlier one that day", async () => {
    await seedEveryState();
    const s = setup();

    await s.handler.scheduled(createScheduledController({ scheduledTime: new Date(NOW - 60_000), cron: "55 23 * * *" }), s.testEnv);
    await subscriber("active", ["social"]);
    await s.handler.scheduled(createScheduledController({ scheduledTime: new Date(NOW), cron: "55 23 * * *" }), s.testEnv);

    const { results } = await db.prepare("SELECT day, paying, trials, fields FROM snapshots").all<{ fields: string }>();
    expect(results.map((r) => ({ ...r, fields: JSON.parse(r.fields) }))).toEqual([
      { day: "2026-11-12", paying: 5, trials: 2, fields: { physics: 2, math: 1, cs: 1, earth: 1, social: 1 } },
    ]);
  });

  it("does nothing without a database", async () => {
    const s = setup({ DB: undefined });

    await s.handler.scheduled(createScheduledController({ scheduledTime: new Date(NOW) }), s.testEnv);
  });

  it("gives each past month its last snapshot's subscribers and income, with that month's API cost, newest first", async () => {
    const s = setup();
    // September: two snapshots, the later one counts. October: one, at month end.
    await subscriber("active", ["math"], NOW + DAY, Date.UTC(2026, 8, 1));
    s.at(Date.UTC(2026, 8, 10, 23, 55));
    await s.handler.scheduled(createScheduledController({ scheduledTime: new Date(Date.UTC(2026, 8, 10, 23, 55)) }), s.testEnv);
    await subscriber("active", ["math"]);
    await s.handler.scheduled(createScheduledController({ scheduledTime: new Date(Date.UTC(2026, 8, 30, 23, 55)) }), s.testEnv);
    await subscriber("active", ["math"]);
    await subscriber("active", ["math"]);
    await s.handler.scheduled(createScheduledController({ scheduledTime: new Date(Date.UTC(2026, 9, 31, 23, 55)) }), s.testEnv);
    await subscriber("trial", ["math"]);
    s.at(NOW);

    const table = rows((await s.page()).html, "months");

    expect(table).toEqual([
      // November: live counts (four paying) and the November fixture.
      ["November 2026", "4", "$17.00", "$11.50", "$5.50"],
      // October: 4 x $5 x 0.85, and the October fixture's $24.75 (two incomplete runs).
      ["October 2026", "4", "$17.00", "$24.75", "-$7.75"],
      // September: the 30th's snapshot, and no cost file: $0.
      ["September 2026", "2", "$8.50", "$0", "$8.50"],
    ]);
  });

  it("says not recorded for a month with no snapshot", async () => {
    await subscriber("active", ["math"], NOW + DAY, Date.UTC(2026, 9, 5));
    const s = setup();

    const table = rows((await s.page()).html, "months");

    expect(table[1]).toEqual(["October 2026", "not recorded", "not recorded", "$24.75", "not recorded"]);
  });
});

describe("API cost from the cost records", () => {
  it("counts each fixture month the way budget-gate does, incomplete runs at the larger of cost and cap", () => {
    for (const [month, raw] of [["2026-10", october], ["2026-11", november]] as const) {
      const parsed = parseMonth(raw)!;
      expect(parsed.spend).toBeCloseTo(EXPECTED[month].spend_usd, 6);
      expect(parsed.runs).toBe(EXPECTED[month].runs);
      expect(parsed.pages).toEqual(EXPECTED[month].pages);
    }
  });

  it("is $0 with no pages for a month with no cost file", async () => {
    await subscriber("active", ["math"]);
    const s = setup({}, {});

    const { html } = await s.page();

    expect(figures(html)["API cost"]).toBe("$0");
    expect(rows(html, "fields")[2]).toEqual(["Math", "1", "0", "$0", "Making pages"]);
  });

  it("says the cost cannot be read when a record is not valid, and when the content repo cannot be reached", async () => {
    await subscriber("active", ["math"]);
    const broken = setup({}, { "state/cost/2026-11.jsonl": `${november}{"v":1,"complete":"yes"}\n` });
    expect(figures((await broken.page()).html)["API cost"]).toBe("cannot be read");

    const down = setup();
    down.takeDown();
    const figs = figures((await down.page()).html);
    expect(figs["API cost"]).toBe("cannot be read");
    expect(figs["Left over"]).toBe("cannot be read");
  });

  it("reads the cost records through the bucket and never serves them", async () => {
    await subscriber("active", ["math"]);
    const s = setup();
    await s.page();

    expect(await env.CONTENT.get("state/cost/2026-11.jsonl")).not.toBeNull();
    for (const path of ["/state/cost/2026-11.jsonl", "/state/cost/2026-10.jsonl", "/state/seen.txt", "/owner/state/cost/2026-11.jsonl"]) {
      const res = await s.get(path, { headers: { authorization: `Basic ${btoa(`owner:${PASSWORD}`)}` } });
      expect(res.status, path).toBe(404);
      expect(await res.text(), path).not.toContain("run-nov");
    }
  });
});

describe("who can open it", () => {
  it("asks for a password with no credentials", async () => {
    const s = setup();

    const res = await s.get("/owner/numbers");

    expect(res.status).toBe(401);
    expect(res.headers.get("www-authenticate")).toBe('Basic realm="Paperboy numbers", charset="UTF-8"');
    expect(res.headers.get("cache-control")).toBe("no-store");
    expect(await res.text()).not.toContain("Paperboy numbers</h1>");
  });

  it.each([
    ["the wrong password", "owner", "wrong"],
    ["an empty password", "owner", ""],
    ["the password with a different case", "owner", PASSWORD.toUpperCase()],
  ])("refuses %s", async (_name, user, password) => {
    const s = setup();

    expect((await s.page(user, password)).res.status).toBe(401);
  });

  it("refuses a header that is not Basic credentials", async () => {
    const s = setup();

    for (const authorization of [`Bearer ${PASSWORD}`, "Basic !!!", `Basic ${btoa(PASSWORD)}`]) {
      expect((await s.get("/owner/numbers", { headers: { authorization } })).status, authorization).toBe(401);
    }
  });

  it("opens with the right password and any username, private, unindexed, and under a strict policy", async () => {
    const s = setup();

    for (const user of ["owner", "", "anyone"]) {
      const { res } = await s.page(user);
      expect(res.status).toBe(200);
      expect(res.headers.get("content-type")).toBe("text/html; charset=utf-8");
      expect(res.headers.get("cache-control")).toBe("no-store");
      expect(res.headers.get("x-robots-tag")).toBe("noindex");
    }
    const policy = (await s.page()).res.headers.get("content-security-policy")!;
    const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(PAGE_STYLE));
    const hash = btoa(String.fromCharCode(...new Uint8Array(digest)));
    expect(policy).toBe(`default-src 'none'; style-src 'self' 'sha256-${hash}'; font-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`);
    const { html } = await s.page();
    expect(html).not.toContain("<script");
    expect(html).not.toContain("style=");
  });

  it("is 404, never open, when OWNER_PASSWORD is not set", async () => {
    const s = setup({ OWNER_PASSWORD: undefined });

    expect((await s.get("/owner/numbers")).status).toBe(404);
    expect((await s.page("owner", "")).res.status).toBe(404);
  });

  it("is 404 on the worker deployed today, which has no subscriber database", async () => {
    const s = setup({ DB: undefined });

    expect((await s.page()).res.status).toBe(404);
  });

  it("is 404 for any other /owner/ path and 405 for other methods", async () => {
    const s = setup();

    expect((await s.get("/owner/")).status).toBe(404);
    expect((await s.get("/owner/numbers/")).status).toBe(404);
    const post = await s.get("/owner/numbers", { method: "POST", body: "x" });
    expect(post.status).toBe(405);
    expect(post.headers.get("allow")).toBe("GET, HEAD");
  });
});
