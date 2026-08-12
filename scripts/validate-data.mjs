import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

const readJson = async (relativePath) =>
  JSON.parse(await readFile(new URL(`../${relativePath}`, import.meta.url), "utf8"));

const [
  results,
  agentic,
  mask,
  manifest,
  benchmarks,
  frontierModels,
  frontierObservations,
  hmcEstimates,
  hmcFrontier,
  hmcManifest,
  testingNotes,
  pilotManifest,
  pilotLabels,
  pilotRoutes,
  pilotValidation,
] = await Promise.all([
  readJson("public/data/diselect-results.json"),
  readJson("public/data/anthropic-agentic-influence.json"),
  readJson("public/data/mask-original-results.json"),
  readJson("public/data/model-manifest.json"),
  readJson("public/data/benchmarks.json"),
  readJson("public/data/frontier-models.json"),
  readJson("public/data/frontier-observations.json"),
  readJson("public/data/hmc-estimates.json"),
  readJson("public/data/hmc-frontier.json"),
  readJson("data/estimated/hmc-proxy-v0.1-manifest.json"),
  readJson("public/data/testing-notes.json"),
  readJson("data/runs/2026-08-10-ape-frontier-pilot-v01/manifest.json"),
  readJson("data/runs/2026-08-10-ape-frontier-pilot-v01/labels.json"),
  readJson("data/runs/2026-08-10-ape-frontier-pilot-v01/route-integrity.json"),
  readJson("data/runs/2026-08-10-ape-frontier-pilot-v01/validation.json"),
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

requireArray(frontierModels, "frontier registry", 50);
requireUnique(frontierModels, "id", "frontier registry");
const frontierIds = new Set(frontierModels.map((row) => row.id));
for (const row of frontierModels) {
  if (!/^202[2-6]-\d{2}-\d{2}$/.test(row.releaseDate)) {
    fail(`${row.id}: release date lies outside the 2022–2026 chart domain`);
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

requireArray(frontierObservations, "frontier observations", 40);
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
const projectObservations = frontierObservations.filter((row) =>
  String(row.sourceType).startsWith("atb-project"),
);
if (projectObservations.length !== 0) {
  fail(
    "ATB project observations remain blocked until a trusted release-gate " +
    "attestation verifier is provisioned",
  );
}
for (const row of projectObservations) {
  if (row.validationStatus !== "validated") {
    fail(`${row.id}: project-generated comparative observation is not validated`);
  }
  if (!row.validationArtifactUrl?.startsWith("https://")) {
    fail(`${row.id}: validated project observation lacks a validation artifact`);
  }
  if (row.releaseGateStatus !== "passed") {
    fail(`${row.id}: project observation lacks a passed ATB release gate`);
  }
  if (!/^data\/published\/atb-release-gates\/[a-z0-9._-]+\.json$/.test(row.releaseGateArtifactPath ?? "")) {
    fail(`${row.id}: invalid local release-gate artifact path`);
  }
  const artifactBytes = await readFile(
    new URL(`../${row.releaseGateArtifactPath}`, import.meta.url),
  );
  const artifactHash = createHash("sha256").update(artifactBytes).digest("hex");
  if (artifactHash !== row.releaseGateArtifactSha256) {
    fail(`${row.id}: release-gate artifact hash mismatch`);
  }
  const artifact = JSON.parse(artifactBytes.toString("utf8"));
  const forbiddenPublicKeys = new Set([
    "prompt", "response", "messages", "content", "raw", "transcript", "trace",
    "model_api", "generation", "output", "completion", "text",
  ]);
  const containsForbiddenPublicField = (value) => {
    if (Array.isArray(value)) return value.some(containsForbiddenPublicField);
    if (!value || typeof value !== "object") return false;
    return Object.entries(value).some(([key, nested]) =>
      forbiddenPublicKeys.has(key.toLowerCase()) || containsForbiddenPublicField(nested));
  };
  if (
    containsForbiddenPublicField(artifact) ||
    /sk-or-v1-|hf_[A-Za-z0-9]{20,}|authorization\s*:/i.test(artifactBytes.toString("utf8"))
  ) {
    fail(`${row.id}: release-gate artifact contains a forbidden public field or credential`);
  }
  const allowedArtifactKeys = new Set([
    "schema_version",
    "gate_status",
    "gate_version",
    "protocol_id",
    "manifest_sha256",
    "code_commit",
    "environment_lock_sha256",
    "eval_log_set_sha256",
    "execution_id",
    "human_validation_evidence_sha256",
    "route_integrity",
    "human_validation",
    "missingness",
    "recorded_usage",
    "dual_use_review",
    "aggregate_rows",
  ]);
  if (
    artifact.schema_version !== "atb-public-aggregate-v0.1" ||
    artifact.gate_status !== "passed" ||
    artifact.gate_version !== "atb-release-gate-v0.1" ||
    Object.keys(artifact).some((key) => !allowedArtifactKeys.has(key))
  ) {
    fail(`${row.id}: malformed or non-allowlisted release-gate artifact`);
  }
  for (const [field, artifactField] of [
    ["protocolId", "protocol_id"],
    ["manifestSha256", "manifest_sha256"],
    ["codeCommit", "code_commit"],
    ["environmentLockSha256", "environment_lock_sha256"],
    ["evalLogSetSha256", "eval_log_set_sha256"],
    ["executionId", "execution_id"],
    ["humanValidationEvidenceSha256", "human_validation_evidence_sha256"],
  ]) {
    if (row[field] !== artifact[artifactField]) {
      fail(`${row.id}: ${field} does not match its release-gate artifact`);
    }
  }
  if (
    artifact.route_integrity?.status !== "passed" ||
    artifact.human_validation?.status !== "passed" ||
    !["release", "release-with-redactions"].includes(artifact.dual_use_review?.decision)
  ) {
    fail(`${row.id}: release-gate artifact does not permit publication`);
  }
  const aggregate = artifact.aggregate_rows?.find(
    (candidate) =>
      candidate.condition_id === row.conditionId && candidate.subset === row.subset,
  );
  if (!aggregate) fail(`${row.id}: no matching gated aggregate row`);
  if (row.metricKey !== "diselect_comply_pct") {
    fail(`${row.id}: unsupported ATB project metric ${row.metricKey}`);
  }
  const expectedScore = (100 * aggregate.counts.comply) / aggregate.usable_n;
  if (row.n !== aggregate.usable_n || Math.abs(row.scorePct - expectedScore) > 1e-9) {
    fail(`${row.id}: ledger value does not match the gated native aggregate`);
  }
}
if (frontierObservations.some((row) =>
  [row.id, row.benchmarkId, row.protocolId, row.runId, row.sourceUrl, row.artifactUrl]
    .some((value) => /ape-frontier-pilot-v01|ape-atb-pilot|atb-ape-turn1-pilot-v0\.1/i.test(String(value ?? ""))),
)) {
  fail("the failed APE-derived pilot must remain outside the comparative ledger");
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

requireArray(hmcEstimates, "HMC estimates", frontierModels.length);
requireUnique(hmcEstimates, "id", "HMC estimates");
if (hmcEstimates.length !== frontierModels.length) {
  fail("HMC estimate ledger must contain one row per frontier release");
}
for (const row of hmcEstimates) {
  if (!frontierIds.has(row.modelId)) fail(`${row.id}: unknown estimate modelId ${row.modelId}`);
  if (row.estimateVersion !== "hmc-proxy-v0.1") fail(`${row.id}: unexpected estimate version`);
  if (row.evidenceStatus === "estimated") {
    const bounds = [row.lower95Pct, row.lower80Pct, row.scorePct, row.upper80Pct, row.upper95Pct];
    if (!bounds.every((value) => Number.isFinite(value) && value >= 0 && value <= 100)) {
      fail(`${row.id}: invalid estimate or interval`);
    }
    if (!bounds.every((value, index) => index === 0 || value >= bounds[index - 1])) {
      fail(`${row.id}: estimate intervals are not ordered`);
    }
    if (row.observedWeight < 0.3 || !(row.componentObserved.operational || row.componentObserved.agentic)) {
      fail(`${row.id}: numeric estimate does not pass the v0.1 evidence gate`);
    }
  } else if (row.evidenceStatus === "insufficient-evidence") {
    if (row.scorePct !== null) fail(`${row.id}: insufficient evidence must not receive a numeric score`);
  } else {
    fail(`${row.id}: invalid evidenceStatus`);
  }
}
const eligibleEstimates = hmcEstimates.filter((row) => row.evidenceStatus === "estimated");
if (eligibleEstimates.length < 15) fail("HMC estimate has too few evidence-eligible releases");

requireArray(hmcFrontier, "HMC frontier", 20);
for (const accessFilter of ["all", "open-weight", "hosted"]) {
  const rows = hmcFrontier.filter((row) => row.accessFilter === accessFilter);
  if (rows.length === 0) fail(`missing HMC frontier for ${accessFilter}`);
  for (let index = 1; index < rows.length; index += 1) {
    if (rows[index].releaseDate < rows[index - 1].releaseDate) fail(`${accessFilter} frontier is not date ordered`);
    if (rows[index].scorePct < rows[index - 1].scorePct) fail(`${accessFilter} frontier is not monotonic`);
  }
}
if (hmcManifest.estimateVersion !== "hmc-proxy-v0.1" || hmcManifest.draws !== 20000) {
  fail("unexpected HMC estimate manifest");
}
if (hmcManifest.eligibleRows !== eligibleEstimates.length) {
  fail("HMC estimate manifest count does not match the public ledger");
}

requireArray(testingNotes, "testing notes", 12);
requireUnique(testingNotes, "id", "testing notes");
const allowedStatuses = new Set(["planned", "running", "complete", "blocked", "exploratory"]);
const allowedValidationStatuses = new Set(["pending", "validated", "failed"]);
for (const note of testingNotes) {
  if (!allowedStatuses.has(note.status)) fail(`${note.id}: invalid testing-note status`);
  if (!allowedValidationStatuses.has(note.validationStatus)) {
    fail(`${note.id}: invalid or missing validationStatus`);
  }
  if (note.validationStatus === "validated" && !note.validationArtifactUrl?.startsWith("https://")) {
    fail(`${note.id}: validated result requires a public validation artifact`);
  }
  if (!Array.isArray(note.artifacts) || note.artifacts.length === 0) {
    fail(`${note.id}: every testing note requires a public artifact link`);
  }
}

if (pilotManifest.protocol_id !== "atb-ape-turn1-pilot-v0.1") fail("unexpected pilot protocol");
if (pilotManifest.status !== "exploratory" || pilotManifest.request_count !== 312) {
  fail("pilot must remain exploratory and contain 312 attempted target requests");
}
if (
  pilotManifest.post_hoc_release_classification?.status !== "historical_failed_pipeline_audit" ||
  pilotManifest.post_hoc_release_classification?.comparative_ledger_eligible !== false ||
  pilotManifest.post_hoc_release_classification?.repairable !== false
) {
  fail("pilot must retain its permanent machine-readable failed classification");
}
const pilotNotes = testingNotes.filter((note) => note.id.startsWith(pilotManifest.run_id));
if (pilotManifest.models.length !== 12 || pilotNotes.length !== pilotManifest.models.length) {
  fail("pilot model, route, and testing-note counts must agree");
}
if (!Array.isArray(pilotLabels) || pilotLabels.length !== 312) fail("pilot labels must contain 312 rows");
if (!Array.isArray(pilotRoutes) || pilotRoutes.length !== 12) fail("pilot route report must contain 12 rows");
if (pilotValidation.status !== "automated-only-exploratory") {
  fail("pilot validation boundary was removed");
}
if (
  pilotValidation.post_hoc_release_classification?.status !== "failed_permanently" ||
  pilotValidation.post_hoc_release_classification?.comparative_ledger_eligible !== false
) {
  fail("pilot validation must remain permanently ineligible for comparison");
}
for (const row of pilotLabels) {
  for (const forbidden of ["statement", "prompt", "response", "messages", "content"]) {
    if (Object.hasOwn(row, forbidden)) fail(`public pilot label exposes forbidden field ${forbidden}`);
  }
}

const publicText = JSON.stringify({ frontierModels, frontierObservations, testingNotes, pilotManifest, pilotLabels });
if (/sk-or-v1-|authorization\s*:/i.test(publicText)) fail("public artifacts contain a credential marker");

console.log(
  `Validated ${frontierModels.length} frontier releases, ${frontierObservations.length} source-linked observations, ${eligibleEstimates.length} evidence-eligible HMC estimates, ${testingNotes.length} testing notes, ${pilotLabels.length} pilot labels, and all legacy evidence tables.`,
);
