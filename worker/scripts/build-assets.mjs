// Assembles the static assets the worker serves: the site from ../site and a copy
// of every kit version from ../kit at /kit/<version>. The kit stays where it is in the repo.
import { cpSync, rmSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const worker = join(dirname(fileURLToPath(import.meta.url)), "..");
const repo = join(worker, "..");
const out = join(worker, "public");

rmSync(out, { recursive: true, force: true });
mkdirSync(out, { recursive: true });
cpSync(join(repo, "site"), out, { recursive: true });
cpSync(join(repo, "kit"), join(out, "kit"), { recursive: true });
console.log(`assets assembled in ${out}`);
