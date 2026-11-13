export const ORIGIN = "https://raw.githubusercontent.com/NtrpyDev/paperboy-content/main/";

// How long a stored copy of a changing file is served before it is fetched again.
const REFRESH_MS = 60_000;

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

  return {
    async fetch(request: Request, env: Env): Promise<Response> {
      const key = new URL(request.url).pathname.slice(1);
      if (!key.startsWith("papers/") && !key.startsWith("feed/")) return notFound();
      const changing = key === "feed/v1/head.json";

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

function notFound(): Response {
  return new Response("Not found\n", { status: 404 });
}
