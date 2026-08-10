import { readFile } from "node:fs/promises";

const results = JSON.parse(
  await readFile(new URL("../public/data/diselect-results.json", import.meta.url), "utf8"),
);
const agentic = JSON.parse(
  await readFile(
    new URL("../public/data/anthropic-agentic-influence.json", import.meta.url),
    "utf8",
  ),
);
const mask = JSON.parse(
  await readFile(new URL("../public/data/mask-original-results.json", import.meta.url), "utf8"),
);
const manifest = JSON.parse(
  await readFile(new URL("../public/data/model-manifest.json", import.meta.url), "utf8"),
);
const benchmarks = JSON.parse(
  await readFile(new URL("../public/data/benchmarks.json", import.meta.url), "utf8"),
);

const fail = (message) => {
  throw new Error(`Data validation failed: ${message}`);
};

if (!Array.isArray(results) || results.length !== 52) {
  fail(`expected 52 DisElect aggregate rows, found ${results.length}`);
}

const modelNames = new Set(results.map((row) => row.model));
if (modelNames.size !== 13) fail(`expected 13 DisElect models, found ${modelNames.size}`);

for (const row of results) {
  const counts =
    row.complyCount + row.softRefuseCount + row.refuseCount + row.incoherentCount;
  if (counts !== row.n) fail(`${row.model}/${row.subset}: counts do not sum to n`);
  const percentages = row.complyPct + row.softRefusePct + row.refusePct + row.incoherentPct;
  if (Math.abs(percentages - 100) > 0.01) {
    fail(`${row.model}/${row.subset}: percentages sum to ${percentages}`);
  }
  if (row.sourceCommit !== "915a8f8c22fb9cd8a2e4ae6824513760f0468f69") {
    fail(`${row.model}/${row.subset}: unexpected source commit`);
  }
}

if (!Array.isArray(manifest) || manifest.length < 8) fail("model manifest is too small");
if (!manifest.every((row) => row.totalParamsB >= 100)) {
  fail("Wave manifest must contain only models with at least 100B total parameters");
}
if (!Array.isArray(benchmarks) || benchmarks.length < 5) {
  fail("benchmark registry must contain at least five evidence sources");
}
if (!Array.isArray(agentic) || agentic.length !== 14) {
  fail(`expected 14 Anthropic agentic-influence rows, found ${agentic.length}`);
}
if (new Set(agentic.map((row) => row.model)).size !== 7) {
  fail("expected seven Claude releases in the agentic-influence series");
}
if (!agentic.every((row) => row.deploymentCondition === "helpful-only")) {
  fail("agentic-influence series must remain explicitly helpful-only");
}
if (!Array.isArray(mask) || mask.length !== 4) {
  fail(`expected four original MASK rows, found ${mask.length}`);
}
if (!mask.every((row) => row.n === 1500 && row.totalParamsB >= 100)) {
  fail("MASK subset must remain the reported 1,500-item, >=100B open-weight cohort");
}

console.log(
  `Validated ${results.length} DisElect rows, ${agentic.length} agentic-influence rows, ${mask.length} MASK rows, ${manifest.length} wave models, and ${benchmarks.length} evidence sources.`,
);
