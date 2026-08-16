import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const PATHS = {
  models: "public/data/frontier-models.json",
  modelsCsv: "data/models/frontier-models.csv",
  observations: "public/data/frontier-observations.json",
  legacyManifest: "public/data/model-manifest.json",
  diselect: "public/data/diselect-results.json",
  mask: "public/data/mask-original-results.json",
  agentic: "public/data/anthropic-agentic-influence.json",
};

const readJson = async (path) => JSON.parse(await readFile(resolve(ROOT, path), "utf8"));
const writeJson = async (path, value) => {
  const destination = resolve(ROOT, path);
  await mkdir(dirname(destination), { recursive: true });
  await writeFile(destination, `${JSON.stringify(value, null, 2)}\n`);
};

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

const csvEscape = (value) => {
  if (value === null || value === undefined) return "";
  const string = typeof value === "object" ? JSON.stringify(value) : String(value);
  return /[",\n]/.test(string) ? `"${string.replaceAll('"', '""')}"` : string;
};

const main = async () => {
  const [existingModels, existingObservations, legacyManifest, diselect, mask, agentic] =
    await Promise.all([
      readJson(PATHS.models),
      readJson(PATHS.observations),
      readJson(PATHS.legacyManifest),
      readJson(PATHS.diselect),
      readJson(PATHS.mask),
      readJson(PATHS.agentic),
    ]);

  const models = mergeUnique(existingModels, makeHistoricalModels(legacyManifest), "id").sort(
    modelByDateThenId,
  );
  const observations = mergeUnique(
    existingObservations,
    normaliseObservations(diselect, mask, agentic),
    "id",
  ).sort((first, second) => first.id.localeCompare(second.id));

  await writeJson(PATHS.models, models);
  await writeJson(PATHS.observations, observations);

  const modelColumns = [
    "id",
    "model",
    "organisation",
    "family",
    "accessType",
    "releaseDate",
    "totalParamsB",
    "openRouterId",
    "eligibilityBasis",
    "sourceUrl",
  ];
  const csv = [
    modelColumns.join(","),
    ...models.map((row) => modelColumns.map((column) => csvEscape(row[column])).join(",")),
  ].join("\n");
  const csvPath = resolve(ROOT, PATHS.modelsCsv);
  await mkdir(dirname(csvPath), { recursive: true });
  await writeFile(csvPath, `${csv}\n`);

  console.log(
    `Generated ${models.length} frontier releases and ${observations.length} source-linked observations.`,
  );
};

await main();
