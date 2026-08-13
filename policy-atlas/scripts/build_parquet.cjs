#!/usr/bin/env node
"use strict";

/** Build typed Parquet companions for every public CSV and refresh manifests. */

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const parquet = require("parquetjs-lite");
const { parse } = require("csv-parse/sync");

const ROOT = path.resolve(__dirname, "..");
const VERSION = "v0.1.0-beta.1";
const RELEASE = path.join(ROOT, "release", VERSION);
const DATA = path.join(RELEASE, "data");
const MANIFEST_PATH = path.join(RELEASE, "manifests", "release.json");
const CHECKSUM_PATH = path.join(RELEASE, "manifests", "checksums.sha256");

const LIST_COLUMNS = new Set([
  "legacy_ids",
  "implementation_ids",
  "linked_source_ids",
  "merged_relation_ids",
  "mechanism_ids",
  "context_entity_ids",
  "research_gap_ids",
  "claim_ids",
  "effect_claim_ids",
  "source_ids",
  "policy_package_ids",
  "priority_effect_review_outcomes",
  "priority_effect_publication_actions"
]);

const BOOLEAN_COLUMNS = new Set(["effect_claim_checked", "effect_claim_reviewed"]);
const INTEGER_COLUMNS = new Set(["implementation_count"]);

function walk(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const candidate = path.join(directory, entry.name);
    return entry.isDirectory() ? walk(candidate) : [candidate];
  });
}

function sha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function parquetField(column) {
  if (LIST_COLUMNS.has(column)) return { type: "UTF8", repeated: true };
  if (BOOLEAN_COLUMNS.has(column)) return { type: "BOOLEAN", optional: true };
  if (INTEGER_COLUMNS.has(column)) return { type: "INT64", optional: true };
  return { type: "UTF8", optional: true };
}

function valueFor(column, value) {
  if (LIST_COLUMNS.has(column)) {
    return value ? value.split(";").map((item) => item.trim()).filter(Boolean) : [];
  }
  if (BOOLEAN_COLUMNS.has(column)) return value === "true";
  if (INTEGER_COLUMNS.has(column)) return value === "" ? null : Number.parseInt(value, 10);
  return value === "" ? null : value;
}

async function convert(csvPath) {
  const rows = parse(fs.readFileSync(csvPath, "utf8"), {
    columns: true,
    bom: true,
    skip_empty_lines: true
  });
  if (rows.length === 0) throw new Error(`Cannot infer schema for empty CSV: ${csvPath}`);
  const columns = Object.keys(rows[0]);
  const schema = new parquet.ParquetSchema(
    Object.fromEntries(columns.map((column) => [column, parquetField(column)]))
  );
  const parquetPath = csvPath.replace(/\.csv$/, ".parquet");
  const writer = await parquet.ParquetWriter.openFile(schema, parquetPath);
  try {
    for (const row of rows) {
      await writer.appendRow(
        Object.fromEntries(columns.map((column) => [column, valueFor(column, row[column])]))
      );
    }
  } finally {
    await writer.close();
  }

  const reader = await parquet.ParquetReader.openFile(parquetPath);
  let count = 0;
  try {
    const cursor = reader.getCursor();
    while (await cursor.next()) count += 1;
  } finally {
    await reader.close();
  }
  if (count !== rows.length) {
    throw new Error(`${parquetPath}: expected ${rows.length} rows, read ${count}`);
  }
  return { parquetPath, rows: count };
}

async function main() {
  const csvFiles = walk(DATA).filter((filePath) => filePath.endsWith(".csv")).sort();
  const results = [];
  for (const csvPath of csvFiles) results.push(await convert(csvPath));

  const manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, "utf8"));
  manifest.formats = ["csv", "parquet"];
  manifest.files = {};
  for (const filePath of walk(DATA).sort()) {
    const relative = path.relative(RELEASE, filePath).split(path.sep).join("/");
    manifest.files[relative] = {
      sha256: sha256(filePath),
      bytes: fs.statSync(filePath).size
    };
  }
  fs.writeFileSync(MANIFEST_PATH, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");

  const checksumLines = Object.entries(manifest.files)
    .map(([relative, metadata]) => `${metadata.sha256}  ${relative}`)
    .concat(`${sha256(MANIFEST_PATH)}  manifests/release.json`)
    .join("\n");
  fs.writeFileSync(CHECKSUM_PATH, `${checksumLines}\n`, "utf8");

  console.log(
    JSON.stringify(
      {
        parquet_files: results.length,
        rows: Object.fromEntries(
          results.map(({ parquetPath, rows }) => [
            path.relative(RELEASE, parquetPath).split(path.sep).join("/"),
            rows
          ])
        )
      },
      null,
      2
    )
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
