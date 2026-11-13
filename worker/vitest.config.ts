import { cloudflareTest } from "@cloudflare/vitest-plugin";
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    projects: [
      {
        // The HTTP handler inside the Workers runtime, with a real local bucket.
        plugins: [cloudflareTest({ wrangler: { configPath: "./wrangler.jsonc" } })],
        test: { name: "handler", include: ["test/handler/**/*.test.ts"] },
      },
      {
        // The whole worker with its static assets, run the way wrangler dev runs it.
        test: { name: "assets", environment: "node", include: ["test/assets/**/*.test.ts"] },
      },
    ],
  },
});
