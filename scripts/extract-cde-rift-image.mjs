import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const sourcePath = path.join(root, "public", "media", "cde-rift-animation", "index.html");
const outputPath = path.join(root, "public", "media", "cde-rift-hero.png");

const source = fs.readFileSync(sourcePath, "utf8");
const match = source.match(/const ART_DATA = 'data:image\/png;base64,([^']+)'/s);

if (!match) {
  throw new Error(`Could not find embedded CDE Rift artwork in ${sourcePath}`);
}

const bytes = Buffer.from(match[1], "base64");
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, bytes);

console.log(`Extracted CDE Rift artwork to ${path.relative(root, outputPath)} (${bytes.length} bytes).`);
