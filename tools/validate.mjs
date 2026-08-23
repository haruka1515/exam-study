#!/usr/bin/env node
// CLI wrapper around js/validate-core.js. Runs in GitHub Actions on every push
// (their runners have Node preinstalled), or locally if you install Node.
//
//   node tools/validate.mjs                      # every set under data/
//   node tools/validate.mjs data/ch03/s02.json
//   node tools/validate.mjs --expect 25 data/ch03/s02.json
//
// If you don't have Node, open validate.html in the browser instead — same checks.

import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, dirname, resolve, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { validateSet } from "../js/validate-core.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const RED = "[31m";
const YEL = "[33m";
const GRN = "[32m";
const OFF = "[0m";

const args = process.argv.slice(2);
let expected = 50;
const targets = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--expect") expected = Number(args[++i]);
  else targets.push(args[i]);
}

const profiles = readJson(join(ROOT, "prompts", "profiles.json")) ?? {};
const files = targets.length ? targets.map((t) => resolve(t)) : discover(join(ROOT, "data"));

if (!files.length) {
  console.log("No question sets found under data/ yet. Nothing to validate.");
  process.exit(0);
}

let totalErrors = 0;
let totalWarnings = 0;

for (const file of files) {
  const rel = relative(ROOT, file).split(sep).join("/");
  let errors = [];
  let warnings = [];

  if (!existsSync(file)) {
    errors = ["file does not exist"];
  } else {
    try {
      ({ errors, warnings } = validateSet(JSON.parse(readFileSync(file, "utf8")), {
        profiles,
        expected,
      }));
    } catch (e) {
      errors = [`not valid JSON — ${e.message}`];
    }
  }

  totalErrors += errors.length;
  totalWarnings += warnings.length;

  if (!errors.length && !warnings.length) {
    console.log(`${GRN}✓${OFF} ${rel}`);
    continue;
  }
  console.log(`${errors.length ? `${RED}✗${OFF}` : `${YEL}!${OFF}`} ${rel}`);
  for (const e of errors) console.log(`    ${RED}✗${OFF} ${e}`);
  for (const w of warnings) console.log(`    ${YEL}!${OFF} ${w}`);
}

console.log(`\n${files.length} set(s) checked — ${totalErrors} error(s), ${totalWarnings} warning(s).`);
process.exit(totalErrors ? 1 : 0);

function discover(dir) {
  if (!existsSync(dir)) return [];
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...discover(p));
    else if (name.endsWith(".json") && name !== "manifest.json") out.push(p);
  }
  return out.sort();
}

function readJson(p) {
  try {
    return JSON.parse(readFileSync(p, "utf8"));
  } catch {
    return null;
  }
}
