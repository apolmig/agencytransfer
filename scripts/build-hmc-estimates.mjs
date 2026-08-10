import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const VERSION = "hmc-proxy-v0.1";
const SEED = 20260810;
const DRAW_COUNT = 20_000;
const WEIGHTS = { operational: 0.4, agentic: 0.3, persuasion: 0.2, deception: 0.1 };
const EQUAL_WEIGHTS = { operational: 0.25, agentic: 0.25, persuasion: 0.25, deception: 0.25 };
const CAPABILITY_WEIGHTS = { operational: 0.5, agentic: 0.5, persuasion: 0, deception: 0 };

const PATHS = {
  models: "public/data/frontier-models.json",
  modelsCsv: "data/models/frontier-models.csv",
  observations: "public/data/frontier-observations.json",
  legacyManifest: "public/data/model-manifest.json",
  diselect: "public/data/diselect-results.json",
  mask: "public/data/mask-original-results.json",
  agentic: "public/data/anthropic-agentic-influence.json",
  estimates: "public/data/hmc-estimates.json",
  frontier: "public/data/hmc-frontier.json",
  csv: "data/estimated/hmc-proxy-v0.1.csv",
  manifest: "data/estimated/hmc-proxy-v0.1-manifest.json",
};

const readJson = async (path) => JSON.parse(await readFile(resolve(ROOT, path), "utf8"));
const writeJson = async (path, value) => {
  const destination = resolve(ROOT, path);
  await mkdir(dirname(destination), { recursive: true });
  await writeFile(destination, `${JSON.stringify(value, null, 2)}\n`);
};

const hashFile = async (path) =>
  createHash("sha256").update(await readFile(resolve(ROOT, path))).digest("hex");

const historicalModelConstants = [
  {
    id: "gpt-3-text-davinci-003",
    model: "GPT-3 · text-davinci-003",
    organisation: "OpenAI",
    family: "GPT-3",
    accessType: "hosted",
    releaseDate: "2022-11-28",
    totalParamsB: null,
    openRouterId: "",
    eligibilityBasis: "Hosted historical frontier comparison evaluated by DisElect; parameters are not used for hosted eligibility.",
    sourceUrl: "https://github.com/alan-turing-institute/election-ai-safety",
  },
  {
    id: "gpt-3-5-turbo-0613",
    model: "GPT-3.5 Turbo · 0613",
    organisation: "OpenAI",
    family: "GPT-3.5",
    accessType: "hosted",
    releaseDate: "2023-01-03",
    totalParamsB: null,
    openRouterId: "",
    eligibilityBasis: "Hosted historical frontier comparison evaluated by DisElect; family announcement date is used on the release axis.",
    sourceUrl: "https://github.com/alan-turing-institute/election-ai-safety",
  },
  {
    id: "gpt-4-0613",
    model: "GPT-4 · 0613",
    organisation: "OpenAI",
    family: "GPT-4",
    accessType: "hosted",
    releaseDate: "2023-03-14",
    totalParamsB: null,
    openRouterId: "",
    eligibilityBasis: "Hosted historical frontier comparison evaluated by DisElect; family announcement date is used on the release axis.",
    sourceUrl: "https://openai.com/index/gpt-4-research/",
  },
  {
    id: "gemini-1-0-pro-002",
    model: "Gemini 1.0 Pro · 002",
    organisation: "Google",
    family: "Gemini 1.0",
    accessType: "hosted",
    releaseDate: "2023-12-06",
    totalParamsB: null,
    openRouterId: "",
    eligibilityBasis: "Hosted historical frontier comparison evaluated by DisElect; parameters undisclosed.",
    sourceUrl: "https://blog.google/technology/ai/google-gemini-ai/",
  },
  {
    id: "qwen1-5-110b-chat",
    model: "Qwen1.5 110B Chat",
    organisation: "Alibaba",
    family: "Qwen 1.5",
    accessType: "open-weight",
    releaseDate: "2024-04-25",
    totalParamsB: 110,
    openRouterId: "",
    eligibilityBasis: "Open-weight historical checkpoint; 110B total parameters meets the >=100B rule.",
    sourceUrl: "https://huggingface.co/Qwen/Qwen1.5-110B-Chat",
  },
  {
    id: "claude-opus-4-6",
    model: "Claude Opus 4.6",
    organisation: "Anthropic",
    family: "Claude 4",
    accessType: "hosted",
    releaseDate: "2026-02-05",
    totalParamsB: null,
    openRouterId: "",
    eligibilityBasis: "Hosted historical comparison in Anthropic's helpful-only agentic influence evaluation.",
    sourceUrl: "https://cdn.sanity.io/files/4zrzovbb/website/037f06850df7fbe871e206dad004c3db5fd50340.pdf",
  },
  {
    id: "claude-sonnet-4-6",
    model: "Claude Sonnet 4.6",
    organisation: "Anthropic",
    family: "Claude 4",
    accessType: "hosted",
    releaseDate: "2026-02-17",
    totalParamsB: null,
    openRouterId: "",
    eligibilityBasis: "Hosted historical comparison in Anthropic's helpful-only agentic influence evaluation.",
    sourceUrl: "https://www-cdn.anthropic.com/9e6a1044980d8c4ed85669faf9c2a8342e2e9f1e/Claude%20Sonnet%205%20System%20Card.pdf",
  },
  {
    id: "claude-mythos-preview",
    model: "Claude Mythos Preview",
    organisation: "Anthropic",
    family: "Claude 5",
    accessType: "hosted",
    releaseDate: "2026-04-07",
    totalParamsB: null,
    openRouterId: "",
    eligibilityBasis: "Hosted historical comparison in Anthropic's helpful-only agentic influence evaluation.",
    sourceUrl: "https://www-cdn.anthropic.com/9e6a1044980d8c4ed85669faf9c2a8342e2e9f1e/Claude%20Sonnet%205%20System%20Card.pdf",
  },
  {
    id: "claude-opus-4-8",
    model: "Claude Opus 4.8",
    organisation: "Anthropic",
    family: "Claude 4",
    accessType: "hosted",
    releaseDate: "2026-05-28",
    totalParamsB: null,
    openRouterId: "",
    eligibilityBasis: "Hosted historical comparison in Anthropic's helpful-only agentic influence evaluation.",
    sourceUrl: "https://www-cdn.anthropic.com/9e6a1044980d8c4ed85669faf9c2a8342e2e9f1e/Claude%20Sonnet%205%20System%20Card.pdf",
  },
  {
    id: "claude-mythos-5",
    model: "Claude Mythos 5",
    organisation: "Anthropic",
    family: "Claude 5",
    accessType: "hosted",
    releaseDate: "2026-06-09",
    totalParamsB: null,
    openRouterId: "",
    eligibilityBasis: "Hosted historical comparison in Anthropic's helpful-only agentic influence evaluation; distinct from Claude Fable 5.",
    sourceUrl: "https://www-cdn.anthropic.com/9e6a1044980d8c4ed85669faf9c2a8342e2e9f1e/Claude%20Sonnet%205%20System%20Card.pdf",
  },
];

const legacyIdMap = new Map([
  ["bigscience/bloomz", "bloomz-176b"],
  ["tiiuae/falcon-180B-chat", "falcon-180b-chat"],
  ["mistralai/Mixtral-8x22B-Instruct-v0.1", "mixtral-8x22b-instruct"],
  ["meta-llama/Llama-3.1-405B-Instruct", "llama-3-1-405b-instruct"],
  ["deepseek-ai/DeepSeek-V3", "deepseek-v3"],
]);

const diselectModelMap = new Map([
  ["tos_davinci3", "gpt-3-text-davinci-003"],
  ["gpt35t_0613", "gpt-3-5-turbo-0613"],
  ["gpt4_0613", "gpt-4-0613"],
  ["gemini-1.0-pro-002", "gemini-1-0-pro-002"],
]);

const maskModelMap = new Map([
  ["Qwen/Qwen1.5-110B-Chat", "qwen1-5-110b-chat"],
  ["meta-llama/Llama-3.1-405B-Instruct", "llama-3-1-405b-instruct"],
  ["deepseek-ai/DeepSeek-V3", "deepseek-v3"],
  ["deepseek-ai/DeepSeek-R1", "deepseek-r1"],
]);

const agenticModelMap = new Map([
  ["Claude Opus 4.6", "claude-opus-4-6"],
  ["Claude Sonnet 4.6", "claude-sonnet-4-6"],
  ["Claude Mythos Preview", "claude-mythos-preview"],
  ["Claude Opus 4.7", "claude-opus-4-7"],
  ["Claude Opus 4.8", "claude-opus-4-8"],
  ["Claude Mythos 5", "claude-mythos-5"],
  ["Claude Sonnet 5", "claude-sonnet-5"],
]);

const mulberry32 = (seed) => {
  let state = seed >>> 0;
  return () => {
    state += 0x6d2b79f5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
};

const random = mulberry32(SEED);
let spareNormal = null;
const normal = () => {
  if (spareNormal !== null) {
    const value = spareNormal;
    spareNormal = null;
    return value;
  }
  let u = 0;
  let v = 0;
  while (u === 0) u = random();
  while (v === 0) v = random();
  const magnitude = Math.sqrt(-2 * Math.log(u));
  spareNormal = magnitude * Math.sin(2 * Math.PI * v);
  return magnitude * Math.cos(2 * Math.PI * v);
};

const gamma = (shape) => {
  if (shape < 1) return gamma(shape + 1) * Math.pow(random(), 1 / shape);
  const d = shape - 1 / 3;
  const c = 1 / Math.sqrt(9 * d);
  for (;;) {
    let x;
    let v;
    do {
      x = normal();
      v = 1 + c * x;
    } while (v <= 0);
    v **= 3;
    const u = random();
    if (u < 1 - 0.0331 * x ** 4) return d * v;
    if (Math.log(u) < 0.5 * x ** 2 + d * (1 - v + Math.log(v))) return d * v;
  }
};

const beta = (alpha, betaShape) => {
  const first = gamma(alpha);
  return first / (first + gamma(betaShape));
};

const quantile = (values, probability) => {
  const sorted = [...values].sort((a, b) => a - b);
  const index = (sorted.length - 1) * probability;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  if (lower === upper) return sorted[lower];
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (index - lower);
};

const round = (value, digits = 1) => Number(value.toFixed(digits));
const median = (values) => quantile(values, 0.5);

const betaDraws = (scorePct, n) => {
  const successes = Math.round((scorePct / 100) * n);
  return Array.from({ length: DRAW_COUNT }, () => beta(successes + 0.5, n - successes + 0.5));
};

const sensitivityDraws = (scorePct) => {
  const probability = scorePct / 100;
  return Array.from({ length: DRAW_COUNT }, () => beta(0.5 + 9 * probability, 0.5 + 9 * (1 - probability)));
};

const uniformDraws = () => Array.from({ length: DRAW_COUNT }, () => random());
const averageDrawSets = (sets) =>
  Array.from({ length: DRAW_COUNT }, (_, index) =>
    sets.reduce((sum, values) => sum + values[index], 0) / sets.length,
  );

const weightedScore = (components, weights) =>
  Array.from({ length: DRAW_COUNT }, (_, index) =>
    100 * Object.entries(weights).reduce((sum, [key, weight]) => sum + components[key][index] * weight, 0),
  );

const summarise = (values) => ({
  scorePct: round(quantile(values, 0.5)),
  lower80Pct: round(quantile(values, 0.1)),
  upper80Pct: round(quantile(values, 0.9)),
  lower95Pct: round(quantile(values, 0.025)),
  upper95Pct: round(quantile(values, 0.975)),
});

const modelByDateThenId = (first, second) =>
  first.releaseDate.localeCompare(second.releaseDate) || first.id.localeCompare(second.id);

const makeHistoricalModels = (legacyManifest) => [
  ...legacyManifest.map((row) => ({
    id: legacyIdMap.get(row.canonicalModelId),
    model: row.model,
    organisation: row.organisation,
    family: row.family,
    accessType: row.accessType,
    releaseDate: row.releaseDate,
    totalParamsB: row.totalParamsB,
    openRouterId: row.openRouterId,
    eligibilityBasis: row.note,
    sourceUrl: row.sourceUrl,
  })),
  ...historicalModelConstants,
].filter((row) => row.id);

const mergeUnique = (rows, additions, key) => {
  const merged = new Map(rows.map((row) => [row[key], row]));
  for (const row of additions) merged.set(row[key], row);
  return [...merged.values()];
};

const normaliseObservations = (diselect, mask, agentic) => {
  const diselectRows = diselect
    .filter((row) => row.subset === "all-harmful" && diselectModelMap.has(row.canonicalModelId))
    .map((row) => ({
      id: `diselect-${diselectModelMap.get(row.canonicalModelId)}-harmful-compliance`,
      benchmarkId: "diselect",
      protocolId: `diselect-published-${row.sourceCommit.slice(0, 8)}`,
      modelId: diselectModelMap.get(row.canonicalModelId),
      metricKey: "harmful_compliance_pct",
      metricLabel: "Election-operation compliance",
      scorePct: row.complyPct,
      n: row.n,
      evaluationDate: "2025-03-17",
      sourceType: "recomputed-published-aggregates",
      sourceUrl: row.sourceUrl,
      sourceLocator: `Pinned aggregate labels at ${row.sourceCommit}; all-harmful subset`,
      comparabilityGroup: `diselect-all-harmful-${row.sourceCommit.slice(0, 8)}`,
      lowerPct: null,
      upperPct: null,
      artifactUrl: "https://doi.org/10.1371/journal.pone.0317421",
      note: "Publication date is used as the evaluation date because the upstream run date is not reported. This measures response compliance, not human persuasion or electoral impact.",
    }));

  const maskRows = mask.map((row) => ({
    id: `mask-original-${maskModelMap.get(row.canonicalModelId)}-lie-rate`,
    benchmarkId: "mask-original",
    protocolId: row.protocolId,
    modelId: maskModelMap.get(row.canonicalModelId),
    metricKey: "lie_pct",
    metricLabel: "Lies under pressure",
    scorePct: row.liePct,
    n: row.n,
    evaluationDate: "2025-03-05",
    sourceType: row.sourceType,
    sourceUrl: row.sourceUrl,
    sourceLocator: row.sourceLocator,
    comparabilityGroup: row.protocolId,
    lowerPct: null,
    upperPct: null,
    artifactUrl: null,
    note: "MASK measures lying under belief conflict and pressure; it is not a direct manipulation or persuasion evaluation.",
  }));

  const agenticRows = agentic.map((row) => ({
    id: `anthropic-agentic-${agenticModelMap.get(row.model)}-${row.scenario}`,
    benchmarkId: "anthropic-agentic-influence",
    protocolId: "anthropic-agentic-influence-helpful-only-v1",
    modelId: agenticModelMap.get(row.model),
    metricKey: `${row.scenario.replaceAll("-", "_")}_completion_pct`,
    metricLabel: `${row.scenario === "voter-suppression" ? "Voter-suppression" : "Polarisation"} task completion`,
    scorePct: row.scorePct,
    n: row.runs,
    evaluationDate: "2026-06-30",
    sourceType: row.sourceType,
    sourceUrl: row.sourceUrl,
    sourceLocator: row.sourceSection,
    comparabilityGroup: `anthropic-agentic-influence-${row.scenario}-helpful-only-v1`,
    lowerPct: null,
    upperPct: null,
    artifactUrl: null,
    note: "Helpful-only model variant in a simulated tool-use workflow; not default deployment behaviour or demonstrated human efficacy.",
  }));

  return [...diselectRows, ...maskRows, ...agenticRows].filter((row) => row.modelId);
};

const sourceIds = (rows) => [...new Set(rows.map((row) => row.id))].sort();

const buildEstimate = (model, observations) => {
  const modelRows = observations.filter((row) => row.modelId === model.id);
  const operationalRows = modelRows.filter((row) =>
    (row.benchmarkId === "infoopsbench" && row.metricKey === "compliance_pct") ||
    (row.benchmarkId === "diselect" && row.metricKey === "harmful_compliance_pct"),
  );
  const agenticRows = modelRows.filter((row) => row.benchmarkId === "anthropic-agentic-influence");
  const persuasionRows = modelRows.filter((row) => row.benchmarkId === "ape-saferai");
  const deceptionRows = modelRows.filter((row) =>
    (row.benchmarkId === "mask-original" || row.benchmarkId === "mask-saferai") && row.metricKey === "lie_pct",
  );

  const observed = {
    operational: operationalRows.length > 0,
    agentic: agenticRows.length > 0,
    persuasion: persuasionRows.length > 0,
    deception: deceptionRows.length > 0,
  };
  const observedWeight = Object.entries(WEIGHTS).reduce(
    (sum, [key, weight]) => sum + (observed[key] ? weight : 0),
    0,
  );
  const eligible = observedWeight >= 0.3 && (observed.operational || observed.agentic);

  const componentDraws = {
    operational: observed.operational
      ? averageDrawSets(operationalRows.map((row) => betaDraws(row.scorePct, row.n)))
      : uniformDraws(),
    agentic: observed.agentic
      ? averageDrawSets(agenticRows.map((row) => sensitivityDraws(row.scorePct)))
      : uniformDraws(),
    persuasion: observed.persuasion
      ? averageDrawSets(persuasionRows.map((row) => betaDraws(row.scorePct, row.n)))
      : uniformDraws(),
    deception: observed.deception
      ? averageDrawSets(deceptionRows.map((row) => betaDraws(row.scorePct, row.n)))
      : uniformDraws(),
  };

  const baselineDraws = weightedScore(componentDraws, WEIGHTS);
  const equalDraws = weightedScore(componentDraws, EQUAL_WEIGHTS);
  const capabilityDraws = weightedScore(componentDraws, CAPABILITY_WEIGHTS);
  const baseline = summarise(baselineDraws);
  const equalMedian = round(median(equalDraws));
  const capabilityMedian = round(median(capabilityDraws));
  const observedContribution = Object.entries(WEIGHTS).reduce((sum, [key, weight]) => {
    if (!observed[key]) return sum;
    return sum + weight * median(componentDraws[key]) * 100;
  }, 0);
  const grade = observedWeight >= 0.8 ? "A" : observedWeight >= 0.6 ? "B" : observedWeight >= 0.3 ? "C" : "D";

  return {
    row: {
      id: `${VERSION}-${model.id}`,
      modelId: model.id,
      estimateVersion: VERSION,
      evidenceStatus: eligible ? "estimated" : "insufficient-evidence",
      scorePct: eligible ? baseline.scorePct : null,
      lower80Pct: eligible ? baseline.lower80Pct : null,
      upper80Pct: eligible ? baseline.upper80Pct : null,
      lower95Pct: eligible ? baseline.lower95Pct : null,
      upper95Pct: eligible ? baseline.upper95Pct : null,
      observedWeight: round(observedWeight, 2),
      imputedWeight: round(1 - observedWeight, 2),
      evidenceGrade: grade,
      componentObserved: observed,
      componentPct: Object.fromEntries(
        Object.entries(componentDraws).map(([key, values]) => [key, observed[key] ? round(median(values) * 100) : null]),
      ),
      partialIdentificationLowerPct: round(observedContribution),
      partialIdentificationUpperPct: round(observedContribution + (1 - observedWeight) * 100),
      equalWeightsMedianPct: eligible ? equalMedian : null,
      capabilityOnlyMedianPct: eligible ? capabilityMedian : null,
      weightSensitive: eligible && (Math.abs(baseline.scorePct - equalMedian) > 10 || Math.abs(baseline.scorePct - capabilityMedian) > 10),
      basisBenchmarks: [...new Set(modelRows
        .filter((row) =>
          operationalRows.includes(row) || agenticRows.includes(row) || persuasionRows.includes(row) || deceptionRows.includes(row),
        )
        .map((row) => row.benchmarkId))].sort(),
      sourceObservationIds: sourceIds([...operationalRows, ...agenticRows, ...persuasionRows, ...deceptionRows]),
      methodUrl: "https://github.com/apolmig/agencytransfer/blob/main/ESTIMATED_SCORE.md",
      note: eligible
        ? "Modelled proxy with missing components drawn from Uniform(0,1); not observed manipulation, human efficacy, agency transfer, or real-world harm."
        : "No numeric proxy is shown because direct operational or agentic evidence is insufficient under v0.1 eligibility rules.",
    },
    baselineDraws,
    equalDraws,
    capabilityDraws,
  };
};

const frontierStatus = (models, estimates, key) => {
  const status = new Set();
  let best = -Infinity;
  for (const model of models) {
    const result = estimates.get(model.id);
    if (!result || result.row.evidenceStatus !== "estimated") continue;
    const value = median(result[key]);
    if (value > best) {
      best = value;
      status.add(model.id);
    }
  }
  return status;
};

const buildFrontier = (models, estimates, accessFilter) => {
  const eligibleModels = models
    .filter((model) => accessFilter === "all" || model.accessType === accessFilter)
    .filter((model) => estimates.get(model.id)?.row.evidenceStatus === "estimated")
    .sort(modelByDateThenId);
  let frontierDraws = Array.from({ length: DRAW_COUNT }, () => 0);
  let leader = null;
  let leaderMedian = -Infinity;
  return eligibleModels.map((model) => {
    const result = estimates.get(model.id);
    frontierDraws = frontierDraws.map((value, index) => Math.max(value, result.baselineDraws[index]));
    if (result.row.scorePct > leaderMedian) {
      leader = model.id;
      leaderMedian = result.row.scorePct;
    }
    return {
      accessFilter,
      releaseDate: model.releaseDate,
      modelId: model.id,
      leadingModelId: leader,
      ...summarise(frontierDraws),
    };
  });
};

const csvEscape = (value) => {
  if (value === null || value === undefined) return "";
  const string = typeof value === "object" ? JSON.stringify(value) : String(value);
  return /[",\n]/.test(string) ? `"${string.replaceAll('"', '""')}"` : string;
};

const csvColumns = [
  "modelId", "estimateVersion", "evidenceStatus", "scorePct", "lower80Pct", "upper80Pct",
  "lower95Pct", "upper95Pct", "observedWeight", "imputedWeight", "evidenceGrade",
  "partialIdentificationLowerPct", "partialIdentificationUpperPct", "equalWeightsMedianPct",
  "capabilityOnlyMedianPct", "weightSensitive", "componentObserved", "componentPct",
  "basisBenchmarks", "sourceObservationIds", "methodUrl", "note",
];

const main = async () => {
  const [existingModels, existingObservations, legacyManifest, diselect, mask, agentic] = await Promise.all([
    readJson(PATHS.models),
    readJson(PATHS.observations),
    readJson(PATHS.legacyManifest),
    readJson(PATHS.diselect),
    readJson(PATHS.mask),
    readJson(PATHS.agentic),
  ]);

  const models = mergeUnique(existingModels, makeHistoricalModels(legacyManifest), "id").sort(modelByDateThenId);
  const observations = mergeUnique(
    existingObservations,
    normaliseObservations(diselect, mask, agentic),
    "id",
  ).sort((first, second) => first.id.localeCompare(second.id));

  await writeJson(PATHS.models, models);
  await writeJson(PATHS.observations, observations);
  const modelColumns = ["id", "model", "organisation", "family", "accessType", "releaseDate", "totalParamsB", "openRouterId", "eligibilityBasis", "sourceUrl"];
  await writeFile(
    resolve(ROOT, PATHS.modelsCsv),
    `${modelColumns.join(",")}\n${models.map((row) => modelColumns.map((column) => csvEscape(row[column])).join(",")).join("\n")}\n`,
  );

  const estimates = new Map(models.map((model) => [model.id, buildEstimate(model, observations)]));
  const baselineFrontier = frontierStatus(models, estimates, "baselineDraws");
  const equalFrontier = frontierStatus(models, estimates, "equalDraws");
  const capabilityFrontier = frontierStatus(models, estimates, "capabilityDraws");

  for (const [modelId, result] of estimates) {
    if (result.row.evidenceStatus !== "estimated") continue;
    const statusChanged =
      baselineFrontier.has(modelId) !== equalFrontier.has(modelId) ||
      baselineFrontier.has(modelId) !== capabilityFrontier.has(modelId);
    result.row.weightSensitive = result.row.weightSensitive || statusChanged;
  }

  const estimateRows = models.map((model) => estimates.get(model.id).row);
  const frontierRows = ["all", "open-weight", "hosted"].flatMap((filter) =>
    buildFrontier(models, estimates, filter),
  );
  await writeJson(PATHS.estimates, estimateRows);
  await writeJson(PATHS.frontier, frontierRows);

  const csv = [
    csvColumns.join(","),
    ...estimateRows.map((row) => csvColumns.map((column) => csvEscape(row[column])).join(",")),
  ].join("\n");
  await mkdir(dirname(resolve(ROOT, PATHS.csv)), { recursive: true });
  await writeFile(resolve(ROOT, PATHS.csv), `${csv}\n`);

  const inputHashes = Object.fromEntries(
    await Promise.all(
      [PATHS.models, PATHS.observations, PATHS.diselect, PATHS.mask, PATHS.agentic].map(async (path) => [
        path,
        await hashFile(path),
      ]),
    ),
  );
  await writeJson(PATHS.manifest, {
    estimateVersion: VERSION,
    status: "experimental-modelled-proxy",
    generatedOn: "2026-08-10",
    seed: SEED,
    draws: DRAW_COUNT,
    weights: WEIGHTS,
    sensitivityWeights: { equal: EQUAL_WEIGHTS, capabilityOnly: CAPABILITY_WEIGHTS },
    eligibility: "observed weight >= 0.30 and operational or agentic component observed",
    plottedInterval: "80% modelled interval",
    detailInterval: "95% modelled interval",
    inputHashes,
    outputRows: estimateRows.length,
    eligibleRows: estimateRows.filter((row) => row.evidenceStatus === "estimated").length,
    limitations: [
      "This is not an observed benchmark score or a measure of real-world manipulation.",
      "The source protocols measure different constructs and deployment conditions.",
      "Missing components are represented by Uniform(0,1), creating wide modelled uncertainty.",
      "The frontier envelope is monotonic by construction and is vulnerable to winner's-curse bias.",
      "Release-date ordering is retrospective and does not estimate a causal rate of progress.",
    ],
  });

  console.log(`Generated ${estimateRows.length} ${VERSION} rows (${estimateRows.filter((row) => row.evidenceStatus === "estimated").length} eligible) and ${frontierRows.length} frontier steps.`);
};

await main();
