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
  testingNotes,
  pilotManifest,
  pilotLabels,
  pilotRoutes,
  pilotValidation,
  stitchingConstructs,
  stitchingReadiness,
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
  readJson("research/methods/benchmark-constructs-v0.1.json"),
  readJson("data/diagnostics/stitching-readiness-v0.1.json"),
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

const [stitchingObservationBytes, stitchingConstructBytes] = await Promise.all([
  readFile(new URL("../public/data/frontier-observations.json", import.meta.url)),
  readFile(new URL("../research/methods/benchmark-constructs-v0.1.json", import.meta.url)),
]);
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
if (
  stitchingConstructs.schemaVersion !== "atb-benchmark-construct-map-v0.1" ||
  stitchingConstructs.conceptualSource?.arxiv !== "2512.00193v1" ||
  stitchingConstructs.conceptualSource?.codeUrl !== "https://github.com/epoch-research/benchmark-stitching"
) {
  fail("unexpected benchmark-stitching construct map or conceptual source");
}
if (
  stitchingReadiness.schemaVersion !== "atb-stitching-readiness-v0.1" ||
  stitchingReadiness.status !== "not-ready" ||
  stitchingReadiness.fittingPerformed !== false
) {
  fail("current stitching diagnostic must remain an explicit no-fit result");
}
if (
  stitchingReadiness.inputs?.frontierObservations?.sha256 !== sha256(stitchingObservationBytes) ||
  stitchingReadiness.inputs?.constructMap?.sha256 !== sha256(stitchingConstructBytes)
) {
  fail("stitching diagnostic input hashes are stale");
}
const stitchingInstrumentIds = new Set(frontierObservations.map((row) => row.benchmarkId));
const stitchingModelIds = new Set(frontierObservations.map((row) => row.modelId));
if (
  stitchingReadiness.coverage?.observationCount !== frontierObservations.length ||
  stitchingReadiness.coverage?.modelCount !== stitchingModelIds.size ||
  stitchingReadiness.coverage?.instrumentCount !== stitchingInstrumentIds.size
) {
  fail("stitching diagnostic coverage does not match the public observation ledger");
}
const expectedStitchingCriterionIds = [
  "paper-overlap-analogue",
  "same-construct-anchor-overlap",
  "protocol-invariance",
  "item-level-or-split-invariant-weighting",
  "design-frozen-before-fitting",
];
const stitchingCriterionIds = Array.isArray(stitchingReadiness.criteria)
  ? stitchingReadiness.criteria.map((criterion) => criterion.id)
  : [];
if (
  stitchingCriterionIds.length !== expectedStitchingCriterionIds.length ||
  new Set(stitchingCriterionIds).size !== expectedStitchingCriterionIds.length ||
  expectedStitchingCriterionIds.some((id) => !stitchingCriterionIds.includes(id)) ||
  stitchingReadiness.criteria.every((criterion) => criterion.pass)
) {
  fail("stitching diagnostic must expose the five preregistered readiness failures");
}
const forbiddenStitchingKeys = new Set([
  "benchmarkDifficulty",
  "benchmarkDifficulties",
  "capabilityScore",
  "capabilityScores",
  "latentScores",
  "ranking",
  "forecast",
]);
const containsForbiddenStitchingOutput = (value) => {
  if (Array.isArray(value)) return value.some(containsForbiddenStitchingOutput);
  if (!value || typeof value !== "object") return false;
  return Object.entries(value).some(([key, nested]) =>
    forbiddenStitchingKeys.has(key) || containsForbiddenStitchingOutput(nested));
};
if (containsForbiddenStitchingOutput(stitchingReadiness)) {
  fail("stitching readiness diagnostic contains a prohibited fitted output");
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
  `Validated ${frontierModels.length} frontier releases, ${frontierObservations.length} source-linked observations, ${testingNotes.length} testing notes, ${pilotLabels.length} pilot labels, and all legacy evidence tables.`,
);
