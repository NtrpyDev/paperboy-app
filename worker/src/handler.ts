import { COST_KEY } from "./cost";
import { createOwner, type OwnerEnv } from "./owner";
import { verifyPass } from "./pass";
import { createApi, type ApiEnv } from "./subscriptions";

export const ORIGIN = "https://raw.githubusercontent.com/NtrpyDev/paperboy-content/main/";

// How long a stored copy of a changing file is served before it is fetched again.
const REFRESH_MS = 60_000;

// Each feed version has its own folder, feed/v<N>/, with its own head and chunks. A chunk is
// judged open or closed by the head in its own folder.
const HEAD = /^feed\/v\d+\/head\.json$/;
const CHUNK = /^(feed\/v\d+)\/chunks\/(\d{6})\.json$/;
const LONG_CACHE = "public, max-age=31536000, immutable";
const SHORT_CACHE = "public, max-age=60";

// The raw host labels every file text/plain, so types come from the file name.
const TYPES: Record<string, string> = {
  html: "text/html; charset=utf-8",
  json: "application/json; charset=utf-8",
  webp: "image/webp",
  png: "image/png",
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  svg: "image/svg+xml",
};

// Explainers may load only same-origin scripts, styles, images, and fonts, plus
// inline page code and data: images, and may make no network calls.
const EXPLAINER_POLICY = [
  "default-src 'none'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:",
  "font-src 'self'",
  "connect-src 'none'",
].join("; ");

// Every closed chunk holds exactly this many items (chunk_size in schema/head.schema.json).
const CHUNK_SIZE = 40;

export interface Deps {
  fetch: typeof fetch;
  now: () => number;
}

// Secrets are set with `wrangler secret put` and do not appear in the generated Env.
export interface Secrets {
  PASS_SECRET?: string;
  GOOGLE_SERVICE_ACCOUNT_JSON?: string;
  OWNER_PASSWORD?: string;
}

export type WorkerEnv = Env & ApiEnv & OwnerEnv & Secrets;

export function createHandler(deps: Deps) {
  const api = createApi(deps);
  const owner = createOwner({ now: deps.now, read: (env, key) => readInternal(env as WorkerEnv, key) });

  // Fetches a file from the content repo and stores it, noting whether it was still
  // changing when fetched. Says "missing" when the repo answers 404 and
  // "unreachable" for any other failure.
  async function fill(env: Env, key: string, changing: boolean): Promise<Filled | Failure> {
    let res: Response;
    try {
      res = await deps.fetch(ORIGIN + key);
    } catch {
      return "unreachable";
    }
    if (res.status === 404) return "missing";
    if (!res.ok) return "unreachable";
    const body = await res.arrayBuffer();
    // The raw host caches for up to five minutes, so a chunk that just closed can
    // still arrive short. It counts as changing until it comes back full.
    if (!changing && CHUNK.test(key) && !isFullChunk(body)) changing = true;
    try {
      await env.CONTENT.put(key, body, {
        customMetadata: { fetched_at: String(deps.now()), changing: String(changing) },
      });
    } catch {
      // R2 allows one write per second to a key, so two requests refreshing the same
      // file at once can collide. The file is still served; the next request stores it.
    }
    return { body, changing };
  }

  // The highest chunk number in the stored head at headKey, filling the head first if
  // the bucket does not have it. Null when no head can be read.
  async function openChunk(env: Env, headKey: string): Promise<number | null> {
    const stored = await env.CONTENT.get(headKey);
    let text: string;
    if (stored) {
      text = await stored.text();
    } else {
      const filled = await fill(env, headKey, true);
      if (typeof filled === "string") return null;
      text = new TextDecoder().decode(filled.body);
    }
    try {
      const n = JSON.parse(text).chunk_count;
      return Number.isInteger(n) ? n : null;
    } catch {
      return null;
    }
  }

  // A changing file is refreshed after REFRESH_MS: a head, and any chunk that is
  // not known to be closed. A chunk is closed only when the stored head in its own
  // feed folder names a higher chunk, so a missing or stale head can only make a
  // chunk look open.
  async function isChanging(env: Env, key: string): Promise<boolean> {
    if (HEAD.test(key)) return true;
    // A month's cost records change until the month ends (UTC).
    const cost = COST_KEY.exec(key);
    if (cost) return cost[1] >= new Date(deps.now()).toISOString().slice(0, 7);
    const chunk = CHUNK.exec(key);
    if (!chunk) return false;
    const open = await openChunk(env, `${chunk[1]}/head.json`);
    return open === null || Number(chunk[2]) >= open;
  }

  return {
    async fetch(request: Request, env: WorkerEnv): Promise<Response> {
      const pathname = new URL(request.url).pathname;
      if (pathname.startsWith("/v1/")) return api(request, env);
      if (pathname.startsWith("/owner/")) return owner.fetch(request, env);
      if (request.method !== "GET" && request.method !== "HEAD") {
        return new Response("Method not allowed\n", { status: 405, headers: { allow: "GET, HEAD" } });
      }
      const res = await respond(request, env);
      if (request.method !== "HEAD") return res;
      await res.body?.cancel();
      return new Response(null, res);
    },

    // The daily Cron Trigger: a snapshot of today's subscriber counts for the numbers page.
    async scheduled(controller: ScheduledController, env: WorkerEnv): Promise<void> {
      await owner.snapshot(env, controller.scheduledTime);
    },
  };

  async function respond(request: Request, env: WorkerEnv): Promise<Response> {
    const pathname = new URL(request.url).pathname;
    // With the content gate on, everything under /feed/ and /papers/ needs a valid pass.
    const gated = env.CONTENT_GATE === "on" && (pathname.startsWith("/feed/") || pathname.startsWith("/papers/"));
    if (gated) {
      const refused = await checkPass(request, env, deps.now());
      if (refused) return refused;
    }
    let key = pathname.slice(1);
    if (key.startsWith("papers/") && key.endsWith("/")) key += "index.html";
    if (!isContentKey(key)) return notFound();
    const loaded = await load(env, key);
    if (loaded === "missing") return notFound();
    if (loaded === "unreachable") return new Response("Content repo unreachable\n", { status: 502 });
    return serve(key, loaded.body, loaded.changing, loaded.source, gated);
  }

  // A file from the bucket, filled or refreshed from the content repo as its kind requires.
  // "missing" when the content repo does not have it, "unreachable" when the content repo
  // fails and the bucket has no copy.
  async function load(env: Env, key: string): Promise<Loaded | Failure> {
    const changing = await isChanging(env, key);

    const stored = await env.CONTENT.get(key);
    if (stored) {
      const age = deps.now() - Number(stored.customMetadata?.fetched_at ?? 0);
      // A copy fetched while the file was still changing may be missing its last
      // edits, so it keeps being refreshed until a copy is fetched after it stopped.
      const storedChanging = stored.customMetadata?.changing === "true";
      const due = (changing || storedChanging) && age > REFRESH_MS;
      if (!due) return { body: stored.body, changing: changing || storedChanging, source: "bucket" };
      const fresh = await fill(env, key, changing);
      if (fresh === "missing") {
        // The content repo no longer has the file, as with feed/v1's chunks after the
        // feed restarted in feed/v2, so the stored copy goes too.
        await stored.body.cancel();
        await forget(env, key);
        return "missing";
      }
      if (fresh === "unreachable") return { body: stored.body, changing: true, source: "bucket" };
      await stored.body.cancel();
      return { body: fresh.body, changing: fresh.changing, source: "origin" };
    }

    const filled = await fill(env, key, changing);
    if (typeof filled === "string") return filled;
    return { body: filled.body, changing: filled.changing, source: "origin" };
  }

  // The text of a content repo file for the worker's own use, never served: the owner's
  // numbers page reads the cost records under state/ this way.
  async function readInternal(env: Env, key: string): Promise<string | Failure> {
    const loaded = await load(env, key);
    if (typeof loaded === "string") return loaded;
    return new Response(loaded.body).text();
  }
}

// Removes a stored file. A failed delete is left for the next request, which asks the
// content repo again and tries once more.
async function forget(env: Env, key: string): Promise<void> {
  try {
    await env.CONTENT.delete(key);
  } catch {
    // Nothing to do here; the response is a 404 either way.
  }
}

type Failure = "missing" | "unreachable";

interface Filled {
  body: ArrayBuffer;
  changing: boolean;
}

interface Loaded {
  body: ReadableStream | ArrayBuffer;
  changing: boolean;
  source: "origin" | "bucket";
}

// The source header says whether this response was fetched from the content repo
// just now or read from the bucket, so a deployed worker can be checked from outside.
// A gated response may be kept only by the device that asked (private, same max-age), and
// carries no access-control-allow-origin: the app reads the feed natively and its pages
// same-origin, so no other origin has a reason to read a subscriber's copy.
function serve(key: string, body: BodyInit, changing: boolean, source: "origin" | "bucket", gated: boolean): Response {
  const extension = key.slice(key.lastIndexOf(".") + 1).toLowerCase();
  const cache = changing ? SHORT_CACHE : LONG_CACHE;
  const headers = new Headers({
    "content-type": TYPES[extension] ?? "application/octet-stream",
    "cache-control": gated ? cache.replace(/^public/, "private") : cache,
    "x-paperboy-source": source,
  });
  if (extension === "html") headers.set("content-security-policy", EXPLAINER_POLICY);
  if (key.startsWith("feed/") && !gated) headers.set("access-control-allow-origin", "*");
  return new Response(body, { headers });
}

// Null when the request carries a valid, unexpired pass in the x-paperboy-pass header or the
// pb_pass cookie; otherwise the 401 to send. Any one valid pass is enough. The answer is
// pass_expired only when a pass with a good signature has expired.
async function checkPass(request: Request, env: WorkerEnv, now: number): Promise<Response | null> {
  if (!env.PASS_SECRET) {
    console.error("CONTENT_GATE is on but PASS_SECRET is not set");
    return gateRefusal(503, "not_configured");
  }
  const candidates = [request.headers.get("x-paperboy-pass"), cookie(request, "pb_pass")].filter(
    (p): p is string => typeof p === "string" && p.length > 0 && p.length <= 1024,
  );
  let expired = false;
  for (const pass of candidates) {
    const check = await verifyPass(env.PASS_SECRET, pass, now);
    if (check.ok) return null;
    if (check.reason === "expired") expired = true;
  }
  return gateRefusal(401, expired ? "pass_expired" : "pass_required");
}

function gateRefusal(status: number, error: string): Response {
  return new Response(JSON.stringify({ error }), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

function cookie(request: Request, name: string): string | null {
  for (const part of (request.headers.get("cookie") ?? "").split(";")) {
    const eq = part.indexOf("=");
    if (eq > 0 && part.slice(0, eq).trim() === name) return part.slice(eq + 1).trim();
  }
  return null;
}

// Only plain file paths under feed/ and papers/ are passed on to the content repo.
const CONTENT_KEY = /^(feed|papers)(\/[A-Za-z0-9._-]+)+$/;

function isContentKey(key: string): boolean {
  return CONTENT_KEY.test(key) && !key.split("/").some((part) => part === "." || part === "..");
}

function isFullChunk(body: ArrayBuffer): boolean {
  try {
    const items = JSON.parse(new TextDecoder().decode(body)).items;
    return Array.isArray(items) && items.length >= CHUNK_SIZE;
  } catch {
    return false;
  }
}

function notFound(): Response {
  return new Response("Not found\n", { status: 404 });
}
