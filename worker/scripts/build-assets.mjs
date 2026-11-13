// Assembles the static assets the worker serves: the placeholder site from ../site
// and a copy of the kit from ../kit/v1 at /kit/v1. The kit stays where it is in the repo.
import { cpSync, rmSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const worker = join(dirname(fileURLToPath(import.meta.url)), "..");
const repo = join(worker, "..");
const out = join(worker, "public");

rmSync(out, { recursive: true, force: true });
mkdirSync(out, { recursive: true });
cpSync(join(repo, "site"), out, { recursive: true });
cpSync(join(repo, "kit", "v1"), join(out, "kit", "v1"), { recursive: true });
console.log(`assets assembled in ${out}`);
