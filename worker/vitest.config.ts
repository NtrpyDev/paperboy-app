import { cloudflareTest, readD1Migrations } from "@cloudflare/vitest-plugin";
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    projects: [
      {
        // The HTTP handler inside the Workers runtime, with a real local bucket and a local
        // subscriber database, using the paid environment's bindings. The migrations are handed
        // to the setup file as a test-only binding, the way the Workers Vitest docs show:
        // https://developers.cloudflare.com/workers/testing/vitest-integration/configuration/
        // Paths are relative to this folder, where npm test runs.
        plugins: [
          cloudflareTest(async () => ({
            wrangler: { configPath: "./wrangler.jsonc", environment: "paid" },
            miniflare: {
              bindings: { TEST_MIGRATIONS: await readD1Migrations("./migrations") },
            },
          })),
        ],
        test: {
          name: "handler",
          include: ["test/handler/**/*.test.ts"],
          setupFiles: ["./test/handler/apply-migrations.ts"],
        },
      },
      {
        // The whole worker with its static assets, run the way wrangler dev runs it.
        test: { name: "assets", environment: "node", include: ["test/assets/**/*.test.ts"] },
      },
    ],
  },
});
