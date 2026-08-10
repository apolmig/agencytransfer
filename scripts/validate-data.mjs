import { readFile } from "node:fs/promises";

const readJson = async (relativePath) =>
  JSON.parse(await readFile(new URL(`../${relativePath}`, import.meta.url), "utf8"));
const readText = async (relativePath) =>
  readFile(new URL(`../${relativePath}`, import.meta.url), "utf8");
const parseCsv = (text) => {
  const [headerLine, ...lines] = text.trim().split(/\r?\n/);
  const headers = headerLine.split(",");
  return lines.map((line) =>
    Object.fromEntries(line.split(",").map((value, index) => [headers[index], value])),
  );
};

const hfReleaseAllowlist = [
  "huggingface/README.md",
  "data/published/anthropic-agentic-influence.csv",
  "data/published/diselect-summary.csv",
  "data/published/mask-original-results.csv",
  "data/published/infoopsbench-2026-07-26.csv",
  "data/published/saferai-glm52-ape-mask.csv",
  "public/data/model-manifest.json",
  "public/data/frontier-models.json",
  "data/models/frontier-models.csv",
  "public/data/frontier-observations.json",
  "public/data/testing-notes.json",
  "data/runs/2026-08-10-ape-frontier-pilot-v01/aggregate.csv",
  "data/runs/2026-08-10-ape-frontier-pilot-v01/labels.json",
  "data/runs/2026-08-10-ape-frontier-pilot-v01/manifest.json",
  "data/runs/2026-08-10-ape-frontier-pilot-v01/README.md",
  "data/runs/2026-08-10-ape-frontier-pilot-v01/research-notes.json",
  "data/runs/2026-08-10-ape-frontier-pilot-v01/route-integrity.json",
  "data/runs/2026-08-10-ape-frontier-pilot-v01/validation.json",
  "data/PROVENANCE.md",
  "LICENSES/DATA.md",
];

const [
  results,
  agentic,
  mask,
  manifest,
  benchmarks,
  frontierModels,
  frontierObservations,
  testingNotes,
  pilotManifest,
  pilotLabels,
  pilotRoutes,
  pilotValidation,
  pilotAggregates,
] = await Promise.all([
  readJson("public/data/diselect-results.json"),
  readJson("public/data/anthropic-agentic-influence.json"),
  readJson("public/data/mask-original-results.json"),
  readJson("public/data/model-manifest.json"),
  readJson("public/data/benchmarks.json"),
  readJson("public/data/frontier-models.json"),
  readJson("public/data/frontier-observations.json"),
  readJson("public/data/testing-notes.json"),
  readJson("data/runs/2026-08-10-ape-frontier-pilot-v01/manifest.json"),
  readJson("data/runs/2026-08-10-ape-frontier-pilot-v01/labels.json"),
  readJson("data/runs/2026-08-10-ape-frontier-pilot-v01/route-integrity.json"),
  readJson("data/runs/2026-08-10-ape-frontier-pilot-v01/validation.json"),
  readText("data/runs/2026-08-10-ape-frontier-pilot-v01/aggregate.csv").then(parseCsv),
]);

const fail = (message) => {
  throw new Error(`Data validation failed: ${message}`);
};

const requireArray = (value, label, minimum = 1) => {
  if (!Array.isArray(value) || value.length < minimum) {
    fail(`${label} must contain at least ${minimum} rows`);
  }
};

const requireUnique = (rows, key, label) => {
  const values = rows.map((row) => row[key]);
  if (values.some((value) => typeof value !== "string" || value.length === 0)) {
    fail(`${label} contains a missing ${key}`);
  }
  if (new Set(values).size !== values.length) fail(`${label} contains duplicate ${key} values`);
};

if (!Array.isArray(results) || results.length !== 52) {
  fail(`expected 52 DisElect aggregate rows, found ${results.length}`);
}

const modelNames = new Set(results.map((row) => row.model));
if (modelNames.size !== 13) fail(`expected 13 DisElect models, found ${modelNames.size}`);

for (const row of results) {
  const counts = row.complyCount + row.softRefuseCount + row.refuseCount + row.incoherentCount;
  if (counts !== row.n) fail(`${row.model}/${row.subset}: counts do not sum to n`);
  const percentages = row.complyPct + row.softRefusePct + row.refusePct + row.incoherentPct;
  if (Math.abs(percentages - 100) > 0.01) {
    fail(`${row.model}/${row.subset}: percentages sum to ${percentages}`);
  }
  if (row.sourceCommit !== "915a8f8c22fb9cd8a2e4ae6824513760f0468f69") {
    fail(`${row.model}/${row.subset}: unexpected source commit`);
  }
}

requireArray(manifest, "legacy model manifest", 8);
if (!manifest.every((row) => row.totalParamsB >= 100)) {
  fail("legacy wave manifest must contain only models with at least 100B total parameters");
}
requireArray(benchmarks, "benchmark registry", 5);
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

requireArray(frontierModels, "frontier registry", 35);
requireUnique(frontierModels, "id", "frontier registry");
const frontierIds = new Set(frontierModels.map((row) => row.id));
for (const row of frontierModels) {
  if (!/^202[456]-\d{2}-\d{2}$/.test(row.releaseDate)) {
    fail(`${row.id}: release date lies outside the fixed 2024–2026 chart domain`);
  }
  if (row.accessType === "open-weight" && !(Number.isFinite(row.totalParamsB) && row.totalParamsB >= 100)) {
    fail(`${row.id}: open-weight frontier row does not meet the 100B total-parameter rule`);
  }
  if (row.accessType === "hosted" && row.totalParamsB !== null) {
    fail(`${row.id}: hosted parameter count must remain undisclosed/null`);
  }
  if (!row.sourceUrl?.startsWith("https://")) fail(`${row.id}: missing primary model source`);
  if (/gemma|mistral[ -]?small/i.test(row.model)) fail(`${row.id}: excluded small model entered frontier registry`);
}

requireArray(frontierObservations, "frontier observations", 23);
requireUnique(frontierObservations, "id", "frontier observations");
for (const row of frontierObservations) {
  if (!frontierIds.has(row.modelId)) fail(`${row.id}: unknown modelId ${row.modelId}`);
  if (!Number.isFinite(row.scorePct) || row.scorePct < 0 || row.scorePct > 100) {
    fail(`${row.id}: scorePct must be a reported percentage, not a missing-value sentinel`);
  }
  if (!Number.isInteger(row.n) || row.n <= 0) fail(`${row.id}: n must be a positive integer`);
  if (!row.comparabilityGroup) fail(`${row.id}: missing comparabilityGroup`);
  if (!row.sourceUrl?.startsWith("https://")) fail(`${row.id}: missing source URL`);
}

const infoOps = frontierObservations.filter(
  (row) => row.benchmarkId === "infoopsbench" && row.metricKey === "compliance_pct",
);
if (infoOps.length !== 11 || !infoOps.every((row) => row.evaluationDate === "2026-07-26")) {
  fail("InfoOpsBench hero must remain the 11-model frozen 2026-07-26 paper snapshot");
}
const saferApe = frontierObservations.filter((row) => row.benchmarkId === "ape-saferai");
const saferMask = frontierObservations.filter((row) => row.benchmarkId === "mask-saferai");
if (saferApe.length !== 9 || saferMask.length !== 3) {
  fail("expected nine SaferAI APE rows and three SaferAI MASK lie-rate rows");
}

requireArray(testingNotes, "testing notes", 12);
requireUnique(testingNotes, "id", "testing notes");
const allowedStatuses = new Set(["planned", "running", "complete", "blocked", "exploratory"]);
for (const note of testingNotes) {
  if (!allowedStatuses.has(note.status)) fail(`${note.id}: invalid testing-note status`);
  if (!Array.isArray(note.artifacts) || note.artifacts.length === 0) {
    fail(`${note.id}: every testing note requires a public artifact link`);
  }
}

if (pilotManifest.protocol_id !== "atb-ape-turn1-pilot-v0.1") fail("unexpected pilot protocol");
if (pilotManifest.status !== "exploratory" || pilotManifest.request_count !== 312) {
  fail("pilot must remain exploratory and contain 312 target request records");
}
if (pilotManifest.models.length !== 12 || testingNotes.length !== pilotManifest.models.length) {
  fail("pilot model, route, and testing-note counts must agree");
}
if (!Array.isArray(pilotLabels) || pilotLabels.length !== 312) fail("pilot labels must contain 312 rows");
if (!Array.isArray(pilotRoutes) || pilotRoutes.length !== 12) fail("pilot route report must contain 12 rows");
if (!Array.isArray(pilotAggregates) || pilotAggregates.length !== 12) fail("pilot aggregate table must contain 12 rows");
if (pilotValidation.status !== "automated-only-exploratory") {
  fail("pilot validation boundary was removed");
}
if (
  pilotManifest.target_request_record_count !== 312 ||
  pilotManifest.judge_batch_request_count !== pilotValidation.primary_batches.length + pilotValidation.audit_batches.length ||
  pilotManifest.http_attempt_count !== null
) {
  fail("pilot request-record accounting is incomplete or inconsistent");
}
if (
  pilotManifest.judge?.pair_labels_retained !== false ||
  pilotManifest.judge?.target_overlap?.primary_judge_is_target !== true ||
  pilotManifest.judge?.target_overlap?.audit_judge_is_target !== true ||
  pilotManifest.request_ids_retained !== false
) {
  fail("pilot manifest does not expose judge-overlap or retention limits");
}
if (
  pilotValidation.pair_labels_retained !== false ||
  pilotValidation.agreement_recomputable_from_public_artifacts !== false ||
  pilotValidation.judge_target_overlap?.primary_judge_target_records !== 26 ||
  pilotValidation.judge_target_overlap?.audit_judge_self_sample_records !== 1
) {
  fail("pilot validation does not expose agreement and judge-independence limits");
}
const selectedItems = pilotManifest.selected_items;
if (!Array.isArray(selectedItems) || selectedItems.length !== 26) fail("pilot manifest must freeze 26 selected items");
const selectedHashes = new Set(selectedItems.map((row) => row.item_hash));
if (selectedHashes.size !== 26) fail("pilot manifest contains duplicate item hashes");
const harmfulItems = selectedItems.filter((row) => row.category === "NoncontroversiallyHarmful");
const benignItems = selectedItems.filter((row) => row.category === "BenignFactual" || row.category === "BenignOpinion");
if (harmfulItems.length !== 20 || benignItems.length !== 6) fail("pilot manifest must contain 20 harmful and 6 benign items");

requireUnique(pilotLabels, "observation_id", "pilot labels");
requireUnique(pilotRoutes, "requested_model", "pilot routes");
const allowedPilotLabels = new Set(["attempt", "no_attempt", "refusal", "invalid"]);
const aggregateByModel = new Map(pilotAggregates.map((row) => [row.model, row]));
const routeByModel = new Map(pilotRoutes.map((row) => [row.requested_model, row]));
const round1 = (value) => Math.round(value * 10) / 10;
const wilsonInterval = (successes, total, z = 1.96) => {
  if (total <= 0) return [null, null];
  const proportion = successes / total;
  const denominator = 1 + (z * z) / total;
  const centre = (proportion + (z * z) / (2 * total)) / denominator;
  const margin = (z * Math.sqrt((proportion * (1 - proportion) + (z * z) / (4 * total)) / total)) / denominator;
  return [round1(Math.max(0, centre - margin) * 100), round1(Math.min(1, centre + margin) * 100)];
};
for (const model of pilotManifest.models) {
  const rows = pilotLabels.filter((row) => row.requested_model === model);
  if (rows.length !== 26) fail(`${model}: expected 26 public pilot labels`);
  if (new Set(rows.map((row) => row.item_hash)).size !== 26 || rows.some((row) => !selectedHashes.has(row.item_hash))) {
    fail(`${model}: item set differs from the frozen pilot manifest`);
  }
  if (rows.some((row) => !allowedPilotLabels.has(row.label))) fail(`${model}: invalid automated label`);

  const harmful = rows.filter((row) => row.category === "NoncontroversiallyHarmful");
  const benign = rows.filter((row) => row.category !== "NoncontroversiallyHarmful");
  if (harmful.some((row) => row.finish_reason === "content_filter" && row.label !== "invalid")) {
    fail(`${model}: provider content filters must remain distinct invalid outcomes`);
  }
  const count = (label) => harmful.filter((row) => row.label === label).length;
  const contentFilterCount = harmful.filter((row) => row.finish_reason === "content_filter").length;
  const usable = count("attempt") + count("no_attempt") + count("refusal");
  const aggregate = aggregateByModel.get(model);
  if (!aggregate) fail(`${model}: missing aggregate row`);
  const expected = {
    n_harmful: harmful.length,
    n_harmful_usable: usable,
    attempt_count: count("attempt"),
    no_attempt_count: count("no_attempt"),
    refusal_count: count("refusal"),
    invalid_count: count("invalid"),
    content_filter_count: contentFilterCount,
    other_invalid_count: count("invalid") - contentFilterCount,
    n_benign: benign.length,
    transport_errors: rows.filter((row) => row.transport_error).length,
  };
  for (const [key, value] of Object.entries(expected)) {
    if (Number(aggregate[key]) !== value) fail(`${model}: aggregate ${key} does not match labels`);
  }
  const attemptPct = usable ? round1((100 * count("attempt")) / usable) : null;
  const refusalPct = usable ? round1((100 * count("refusal")) / usable) : null;
  const [lowerPct, upperPct] = wilsonInterval(count("attempt"), usable);
  const benignAttemptPct = benign.length
    ? round1((100 * benign.filter((row) => row.label === "attempt").length) / benign.length)
    : null;
  if ((aggregate.attempt_pct === "" ? null : Number(aggregate.attempt_pct)) !== attemptPct) {
    fail(`${model}: aggregate attempt_pct does not match labels`);
  }
  if ((aggregate.benign_attempt_pct === "" ? null : Number(aggregate.benign_attempt_pct)) !== benignAttemptPct) {
    fail(`${model}: aggregate benign_attempt_pct does not match labels`);
  }
  if (
    (aggregate.refusal_pct === "" ? null : Number(aggregate.refusal_pct)) !== refusalPct ||
    (aggregate.attempt_ci95_lower === "" ? null : Number(aggregate.attempt_ci95_lower)) !== lowerPct ||
    (aggregate.attempt_ci95_upper === "" ? null : Number(aggregate.attempt_ci95_upper)) !== upperPct
  ) {
    fail(`${model}: aggregate refusal rate or Wilson interval does not match labels`);
  }

  const route = routeByModel.get(model);
  if (!route || route.requests !== 26) fail(`${model}: route report must contain 26 target request records`);
  const returnedTotal = Object.values(route.returned_models).reduce((sum, value) => sum + value, 0);
  const providerTotal = Object.values(route.providers).reduce((sum, value) => sum + value, 0);
  if (returnedTotal !== 26 || providerTotal !== 26 || route.transport_errors !== expected.transport_errors) {
    fail(`${model}: route counts do not match public labels`);
  }
}
if (frontierObservations.some((row) => row.benchmarkId === "ape-atb-pilot")) {
  fail("automated-only pilot results must stay out of the comparative frontier chart");
}

const forbiddenPublicKeys = new Set(["statement", "prompt", "response", "messages", "content", "api_key", "authorization"]);
const rejectForbiddenKeys = (value, label) => {
  if (Array.isArray(value)) {
    value.forEach((item, index) => rejectForbiddenKeys(item, `${label}[${index}]`));
    return;
  }
  if (value === null || typeof value !== "object") return;
  for (const [key, item] of Object.entries(value)) {
    if (forbiddenPublicKeys.has(key.toLowerCase())) fail(`${label}: public artifact exposes forbidden field ${key}`);
    rejectForbiddenKeys(item, `${label}.${key}`);
  }
};

const publicPilotArtifacts = { pilotManifest, pilotLabels, pilotRoutes, pilotValidation, testingNotes };
rejectForbiddenKeys(publicPilotArtifacts, "pilot");
const publicText = JSON.stringify({ frontierModels, frontierObservations, ...publicPilotArtifacts });
if (/sk-or-v1-|authorization\s*:|bearer\s+[a-z0-9._-]{12,}|api[_-]?key\s*[:=]/i.test(publicText)) {
  fail("public artifacts contain a credential marker");
}

const hfWorkflow = await readText(".github/workflows/publish-huggingface.yml");
const stagedHfSources = hfWorkflow
  .split(/\r?\n/)
  .map((line) => line.trim().match(/^cp\s+(\S+)\s+hf-release(?:\/\S*)?$/)?.[1])
  .filter(Boolean);
if (
  stagedHfSources.length !== hfReleaseAllowlist.length ||
  new Set(stagedHfSources).size !== hfReleaseAllowlist.length ||
  hfReleaseAllowlist.some((path) => !stagedHfSources.includes(path))
) {
  fail("Hugging Face staging commands differ from the validated release allowlist");
}

const hfReleaseFiles = await Promise.all(
  hfReleaseAllowlist.map(async (path) => ({ path, text: await readText(path) })),
);
for (const file of hfReleaseFiles) {
  if (/(^|\/)(raw|private)(\/|$)|\.private\./i.test(file.path)) {
    fail(`Hugging Face allowlist contains a raw/private path: ${file.path}`);
  }
  if (
    /sk-or-v1-[a-z0-9_-]{12,}|\bhf_[a-z0-9]{20,}\b|\bghp_[a-z0-9]{20,}\b|\bgithub_pat_[a-z0-9_]{20,}\b|authorization\s*:\s*bearer|bearer\s+[a-z0-9._-]{20,}|hf_token\s*[:=]\s*[a-z0-9_-]{12,}/i.test(file.text)
  ) {
    fail(`Hugging Face release file contains a credential marker: ${file.path}`);
  }
  if (/\.(json)$/i.test(file.path)) {
    rejectForbiddenKeys(JSON.parse(file.text), `Hugging Face release ${file.path}`);
  }
}

console.log(
  `Validated ${frontierModels.length} registry entries, ${frontierObservations.length} published observations, ${testingNotes.length} testing notes, ${pilotLabels.length} pilot labels, and all legacy evidence tables.`,
);
