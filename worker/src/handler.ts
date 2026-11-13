export const ORIGIN = "https://raw.githubusercontent.com/NtrpyDev/paperboy-content/main/";

// How long a stored copy of a changing file is served before it is fetched again.
const REFRESH_MS = 60_000;

const HEAD = "feed/v1/head.json";
const CHUNK = /^feed\/v1\/chunks\/(\d{6})\.json$/;

export interface Deps {
  fetch: typeof fetch;
  now: () => number;
}

export function createHandler(deps: Deps) {
  // Fetches a file from the content repo and stores it. Returns null when the repo
  // does not have it or cannot be reached.
  async function fill(env: Env, key: string): Promise<ArrayBuffer | null> {
    let res: Response;
    try {
      res = await deps.fetch(ORIGIN + key);
    } catch {
      return null;
    }
    if (!res.ok) return null;
    const body = await res.arrayBuffer();
    await env.CONTENT.put(key, body, {
      customMetadata: { fetched_at: String(deps.now()) },
    });
    return body;
  }

  // The highest chunk number in the stored head, filling the head first if the
  // bucket does not have it. Null when no head can be read.
  async function openChunk(env: Env): Promise<number | null> {
    const stored = await env.CONTENT.get(HEAD);
    const text = stored ? await stored.text() : await bodyText(await fill(env, HEAD));
    if (text === null) return null;
    try {
      const n = JSON.parse(text).chunk_count;
      return Number.isInteger(n) ? n : null;
    } catch {
      return null;
    }
  }

  // A changing file is refreshed after REFRESH_MS: the head, and any chunk that is
  // not known to be closed. A chunk is closed only when the stored head names a
  // higher chunk, so a missing or stale head can only make a chunk look open.
  async function isChanging(env: Env, key: string): Promise<boolean> {
    if (key === HEAD) return true;
    const chunk = CHUNK.exec(key);
    if (!chunk) return false;
    const open = await openChunk(env);
    return open === null || Number(chunk[1]) >= open;
  }

  return {
    async fetch(request: Request, env: Env): Promise<Response> {
      const key = new URL(request.url).pathname.slice(1);
      if (!key.startsWith("papers/") && !key.startsWith("feed/")) return notFound();
      const changing = await isChanging(env, key);

      const stored = await env.CONTENT.get(key);
      if (stored) {
        const age = deps.now() - Number(stored.customMetadata?.fetched_at ?? 0);
        if (!changing || age <= REFRESH_MS) return new Response(stored.body);
        const fresh = await fill(env, key);
        return new Response(fresh ?? stored.body);
      }

      const body = await fill(env, key);
      if (!body) return notFound();
      return new Response(body);
    },
  };
}

function bodyText(body: ArrayBuffer | null): string | null {
  return body === null ? null : new TextDecoder().decode(body);
}

function notFound(): Response {
  return new Response("Not found\n", { status: 404 });
}
