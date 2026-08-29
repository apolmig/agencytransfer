import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const partsDir = path.join(root, "assets", "cde-rift");
const outputPath = path.join(root, "public", "media", "cde-rift-hero.webp");
const expectedParts = ["00.b64", "01.b64", "02.b64", "03.b64", "04.b64"];
const expectedBytes = 14_904;
const expectedSha256 = "a2f16213657d2ee7fda0fcf86fc930efac9c5b7c2854959cadfd6379fa230f3c";

const availableParts = fs
  .readdirSync(partsDir)
  .filter((name) => name.endsWith(".b64"))
  .sort();

if (JSON.stringify(availableParts) !== JSON.stringify(expectedParts)) {
  throw new Error(
    `CDE Rift source parts differ from the frozen manifest: ${availableParts.join(", ")}`,
  );
}

const encoded = expectedParts
  .map((name) => fs.readFileSync(path.join(partsDir, name), "utf8").trim())
  .join("");
const bytes = Buffer.from(encoded, "base64");
const digest = crypto.createHash("sha256").update(bytes).digest("hex");

if (bytes.length !== expectedBytes || digest !== expectedSha256) {
  throw new Error(
    `CDE Rift asset integrity check failed: ${bytes.length} bytes, sha256 ${digest}`,
  );
}

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, bytes);
console.log(`Prepared ${path.relative(root, outputPath)} (${bytes.length} bytes).`);
