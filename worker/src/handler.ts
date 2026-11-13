export const ORIGIN = "https://raw.githubusercontent.com/NtrpyDev/paperboy-content/main/";

export interface Deps {
  fetch: typeof fetch;
  now: () => number;
}

export function createHandler(deps: Deps) {
  return {
    async fetch(request: Request, env: Env): Promise<Response> {
      const key = new URL(request.url).pathname.slice(1);
      if (!key.startsWith("papers/")) return notFound();

      const stored = await env.CONTENT.get(key);
      if (stored) return new Response(stored.body);

      const res = await deps.fetch(ORIGIN + key);
      if (!res.ok) return notFound();
      const body = await res.arrayBuffer();
      await env.CONTENT.put(key, body);
      return new Response(body);
    },
  };
}

function notFound(): Response {
  return new Response("Not found\n", { status: 404 });
}
