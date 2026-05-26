#!/usr/bin/env node
// Regenerates dev-blog/posts/posts.json from all .md files in posts/
// Uses Node.js built-in modules only.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const postsDir = path.resolve(__dirname, "..", "posts");
const outFile = path.join(postsDir, "posts.json");

let entries;
try {
  entries = fs.readdirSync(postsDir);
} catch (err) {
  console.error(`Error reading posts directory (${postsDir}):`, err.message);
  process.exit(1);
}

const posts = entries
  .filter((f) => f.endsWith(".md") && f !== "posts.json")
  .sort();

fs.writeFileSync(outFile, JSON.stringify(posts, null, 2) + "\n");

console.log(`Generated posts.json with ${posts.length} post(s).`);
