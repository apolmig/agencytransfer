import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";

const VERSION = "atb-stitching-readiness-v0.1";
const OBSERVATIONS_PATH = "public/data/frontier-observations.json";
const CONSTRUCTS_PATH = "research/methods/benchmark-constructs-v0.1.json";
const OUTPUT_PATH = "data/diagnostics/stitching-readiness-v0.1.json";

const readBytes = (path) => readFile(new URL(`../${path}`, import.meta.url));
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
const unique = (values) => [...new Set(values)].sort();

const [observationBytes, constructBytes] = await Promise.all([
  readBytes(OBSERVATIONS_PATH),
  readBytes(CONSTRUCTS_PATH),
]);
const observations = JSON.parse(observationBytes.toString("utf8"));
const constructMap = JSON.parse(constructBytes.toString("utf8"));

if (!Array.isArray(observations) || observations.length === 0) {
  throw new Error("frontier observations must be a non-empty array");
}
if (!Array.isArray(constructMap.constructs) || constructMap.constructs.length === 0) {
  throw new Error("construct map must contain at least one construct");
}

const instruments = unique(observations.map((row) => row.benchmarkId));
const modelIds = unique(observations.map((row) => row.modelId));
const observationsByModel = new Map(
  modelIds.map((modelId) => [
    modelId,
    unique(observations.filter((row) => row.modelId === modelId).map((row) => row.benchmarkId)),
  ]),
);

const instrumentModels = new Map(
  instruments.map((instrument) => [
    instrument,
    new Set(observations.filter((row) => row.benchmarkId === instrument).map((row) => row.modelId)),
  ]),
);

const pairwiseOverlap = [];
for (let first = 0; first < instruments.length; first += 1) {
  for (let second = first + 1; second < instruments.length; second += 1) {
    const left = instruments[first];
    const right = instruments[second];
    const sharedModels = [...instrumentModels.get(left)]
      .filter((modelId) => instrumentModels.get(right).has(modelId))
      .sort();
    pairwiseOverlap.push({ left, right, sharedModelCount: sharedModels.length, sharedModels });
  }
}

const constructCoverage = constructMap.constructs.map((construct) => {
  const unknown = construct.instruments.filter((instrument) => !instrumentModels.has(instrument));
  if (unknown.length > 0) {
    throw new Error(`${construct.id} refers to unknown instruments: ${unknown.join(", ")}`);
  }
  const withinConstructPairs = pairwiseOverlap.filter(
    (pair) => construct.instruments.includes(pair.left) && construct.instruments.includes(pair.right),
  );
  const anchorModels = unique(withinConstructPairs.flatMap((pair) => pair.sharedModels));
  return {
    constructId: construct.id,
    evidenceLayer: construct.evidenceLayer,
    instruments: construct.instruments,
    instrumentCount: construct.instruments.length,
    anchorModelCount: anchorModels.length,
    anchorModels,
    pairwiseOverlap: withinConstructPairs,
    fitTogetherNow: construct.fitTogetherNow,
  };
});

const minimumInstruments = constructMap.paperOverlapAnalogue.minimumDistinctInstrumentsPerModel;
const modelsMeetingPaperOverlapAnalogue = [...observationsByModel.entries()]
  .filter(([, modelInstruments]) => modelInstruments.length >= minimumInstruments)
  .map(([modelId, modelInstruments]) => ({ modelId, instruments: modelInstruments }))
  .sort((left, right) => left.modelId.localeCompare(right.modelId));
const multiInstrumentModels = [...observationsByModel.entries()]
  .filter(([, modelInstruments]) => modelInstruments.length > 1)
  .map(([modelId, modelInstruments]) => ({ modelId, instruments: modelInstruments }))
  .sort((left, right) => left.modelId.localeCompare(right.modelId));

const multiInstrumentConstructs = constructCoverage.filter((row) => row.instrumentCount > 1);
const sameConstructAnchorOverlapPass = multiInstrumentConstructs.length > 0
  && multiInstrumentConstructs.every((row) => row.anchorModelCount > 0 && row.fitTogetherNow);
const criteria = [
  {
    id: "paper-overlap-analogue",
    pass: modelsMeetingPaperOverlapAnalogue.length > 0,
    actual: `${modelsMeetingPaperOverlapAnalogue.length} models appear in at least ${minimumInstruments} instruments`,
    boundary: "This follows the paper's >3-benchmark filter as a diagnostic; it is necessary here, not sufficient.",
  },
  {
    id: "same-construct-anchor-overlap",
    pass: sameConstructAnchorOverlapPass,
    actual: multiInstrumentConstructs.map((row) => ({
      constructId: row.constructId,
      anchorModelCount: row.anchorModelCount,
      fitTogetherNow: row.fitTogetherNow,
    })),
    boundary: "Anchor overlap is necessary but does not override construct review; cross-construct overlap cannot identify a one-dimensional harmful-manipulation scale.",
  },
  {
    id: "protocol-invariance",
    pass: constructMap.fitRequirements.protocolInvarianceEstablished,
    actual: "not established",
    boundary: "Prompt, scaffold, judge, serving condition, and metric direction must be harmonised or modelled.",
  },
  {
    id: "item-level-or-split-invariant-weighting",
    pass: constructMap.fitRequirements.itemLevelOrSplitInvariantWeightingEstablished,
    actual: "not established",
    boundary: "Aggregate-score stitching can overweight a benchmark merely because it was split into several aggregates.",
  },
];
const ready = criteria.every((criterion) => criterion.pass);

const report = {
  schemaVersion: VERSION,
  asOf: constructMap.asOf,
  status: ready ? "eligible-for-exploratory-fit" : "not-ready",
  fittingPerformed: false,
  publicationBoundary: ready
    ? "Eligibility permits an exploratory fit only; it does not validate a public capability index."
    : "No latent capability or benchmark-difficulty scores may be produced from this report.",
  conceptualSource: constructMap.conceptualSource,
  inputs: {
    frontierObservations: {
      path: OBSERVATIONS_PATH,
      sha256: digest(observationBytes),
    },
    constructMap: {
      path: CONSTRUCTS_PATH,
      sha256: digest(constructBytes),
    },
  },
  coverage: {
    observationCount: observations.length,
    modelCount: modelIds.length,
    instrumentCount: instruments.length,
    instruments,
    multiInstrumentModels,
    minimumDistinctInstrumentsPerModel: minimumInstruments,
    modelsMeetingPaperOverlapAnalogue,
    pairwiseInstrumentOverlap: pairwiseOverlap,
    constructCoverage,
  },
  criteria,
  limitations: [
    "The public observations mix author-reported and project-curated protocols.",
    "Release date, evaluation date, checkpoint, endpoint, scaffold, and safeguards are not interchangeable.",
    "APE, MASK, DisElect, InfoOpsBench, and agentic influence do not measure one demonstrated latent construct.",
    "A readiness pass would justify model fitting and sensitivity analysis, not a claim of persuasion, agency transfer, or democratic harm.",
  ],
};

const outputUrl = new URL(`../${OUTPUT_PATH}`, import.meta.url);
await mkdir(new URL("../data/diagnostics/", import.meta.url), { recursive: true });
await writeFile(outputUrl, `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log(
  `Stitching readiness: ${report.status}; ${observations.length} observations, `
  + `${modelIds.length} models, ${instruments.length} instruments.`,
);
