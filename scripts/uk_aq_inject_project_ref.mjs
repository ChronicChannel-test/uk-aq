#!/usr/bin/env node
// Trigger deploy 
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(SCRIPT_DIR, "..");
const ENV_PATH = path.join(REPO_ROOT, ".env");
const DEFAULT_TARGETS = [
  "uk_aq_hex_map.html",
  "index.html",
  "uk_aq_bristol.html",
];

const envText = await readFileIfExists(ENV_PATH);
if (envText) {
  loadEnvFromText(envText);
}

const projectRef = (process.env.SUPABASE_PROJECT_REF || "").trim();
const anonKey = (
  process.env.SB_ANON_JWT
  || process.env.SUPABASE_ANON_JWT
  || process.env.SUPABASE_PUBLISHABLE_DEFAULT_KEY
  || process.env.SUPABASE_ANON_KEY
  || ""
).trim();

if (!projectRef) {
  console.error("SUPABASE_PROJECT_REF is missing. Set it in .env or the environment.");
  process.exit(1);
}
if (!anonKey) {
  console.error("Anon key is missing. Set SB_ANON_JWT or SUPABASE_ANON_JWT in .env or the environment.");
  process.exit(1);
}

const cliTargets = process.argv.slice(2).filter(Boolean);
const targets = (cliTargets.length ? cliTargets : DEFAULT_TARGETS)
  .map((target) => (path.isAbsolute(target) ? target : path.join(REPO_ROOT, target)));
const refPattern = /const PROJECT_REF_PLACEHOLDER = "([^"]*)";/g;
const anonPattern = /const ANON_KEY_PLACEHOLDER = "([^"]*)";/g;

for (const targetPath of targets) {
  const html = await fs.readFile(targetPath, "utf8");
  let updated = html;
  updated = replacePlaceholder(
    updated,
    refPattern,
    `const PROJECT_REF_PLACEHOLDER = "${projectRef}";`,
    "PROJECT_REF_PLACEHOLDER",
    targetPath,
  );
  updated = replacePlaceholder(
    updated,
    anonPattern,
    `const ANON_KEY_PLACEHOLDER = "${anonKey}";`,
    "ANON_KEY_PLACEHOLDER",
    targetPath,
  );

  if (updated !== html) {
    await fs.writeFile(targetPath, updated);
    console.log(`Injected SUPABASE_PROJECT_REF and anon key into ${path.relative(REPO_ROOT, targetPath)}`);
  } else {
    console.log(`${path.relative(REPO_ROOT, targetPath)} already uses the configured SUPABASE project ref and anon key.`);
  }
}

function replacePlaceholder(text, pattern, replacement, label, targetPath) {
  const matches = text.match(pattern);
  if (!matches) {
    console.error(`Could not find ${label} in ${path.relative(REPO_ROOT, targetPath)}`);
    process.exit(1);
  }
  return text.replace(pattern, replacement);
}

function loadEnvFromText(text) {
  text.split(/\r?\n/).forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      return;
    }
    const separatorIndex = trimmed.indexOf("=");
    if (separatorIndex === -1) {
      return;
    }
    const key = trimmed.slice(0, separatorIndex).trim();
    let value = trimmed.slice(separatorIndex + 1).trim();
    if (!key) {
      return;
    }
    if ((value.startsWith("\"") && value.endsWith("\""))
      || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (!Object.prototype.hasOwnProperty.call(process.env, key)) {
      process.env[key] = value;
    }
  });
}

async function readFileIfExists(filePath) {
  try {
    return await fs.readFile(filePath, "utf8");
  } catch (error) {
    if (error && typeof error === "object" && "code" in error && error.code === "ENOENT") {
      return null;
    }
    throw error;
  }
}
