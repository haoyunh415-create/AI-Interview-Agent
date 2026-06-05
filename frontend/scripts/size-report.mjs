/**
 * Post-build size report — analyzes the `out/` directory
 * and prints file sizes per chunk category.
 */

import { readdirSync, statSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, "..", "out");

if (!existsSync(OUT)) {
  console.error("Build output not found at:", OUT);
  console.error("Run `npm run build` first.");
  process.exit(1);
}

const categories = { HTML: [], JS: [], CSS: [], SVG: [], Other: [] };

function collect(dir, prefix = "") {
  try {
    const entries = readdirSync(dir, { withFileTypes: true });
    for (const e of entries) {
      if (e.name === "_next" || e.name === "icons") continue;
      const full = join(dir, e.name);
      if (e.isDirectory()) {
        collect(full, `${prefix}/${e.name}`);
      } else {
        const stat = statSync(full);
        const ext = e.name.split(".").pop().toLowerCase();
        const entry = { name: `${prefix}/${e.name}`, size: stat.size };
        if (ext === "html") categories.HTML.push(entry);
        else if (ext === "js") categories.JS.push(entry);
        else if (ext === "css") categories.CSS.push(entry);
        else if (ext === "svg") categories.SVG.push(entry);
        else categories.Other.push(entry);
      }
    }
  } catch {
    // ignore
  }
}

// Also collect _next directory
function collectAll() {
  collect(OUT);
  const nextDir = join(OUT, "_next");
  if (existsSync(nextDir)) {
    collect(nextDir, "/_next");
  }
}

collectAll();

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function printCategory(title, files) {
  if (files.length === 0) return;
  const total = files.reduce((s, f) => s + f.size, 0);
  const sorted = files.sort((a, b) => b.size - a.size);
  console.log(`\n\u{1F4E6} ${title} (${files.length} files, ${formatBytes(total)})`);
  console.log("─".repeat(50));
  for (const f of sorted.slice(0, 10)) {
    console.log(`  ${formatBytes(f.size).padStart(8)}  ${f.name}`);
  }
  if (sorted.length > 10) {
    console.log(`  ... and ${sorted.length - 10} more`);
  }
}

console.log("\n╔══════════════════════════════════════════╗");
console.log("║  \u{1F4CA} Build Size Report                    ║");
console.log("╚══════════════════════════════════════════╝");

printCategory("JavaScript", categories.JS);
printCategory("CSS", categories.CSS);
printCategory("HTML", categories.HTML);
printCategory("SVG", categories.SVG);
printCategory("Other", categories.Other);

const grandTotal = [...categories.JS, ...categories.CSS, ...categories.HTML, ...categories.SVG, ...categories.Other].reduce(
  (s, f) => s + f.size,
  0,
);
console.log(`\n\u{1F4C8} Total: ${formatBytes(grandTotal)}`);
console.log("");
