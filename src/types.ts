export type AccessType = "open-weight" | "hosted";
export type MetricKey = "complyPct" | "refusePct" | "benignCompletionPct";
export type HarmfulSubset = "all-harmful" | "voter-targeting" | "mp-targeting";

export interface DisElectResult {
  benchmarkId: "diselect";
  model: string;
  canonicalModelId: string;
  family: string;
  organisation: string;
  accessType: AccessType;
  releaseDate: string;
  releaseDateBasis: string;
  evaluationDate: string;
  totalParamsB: number | null;
  quantisationBits: number | null;
  subset: HarmfulSubset | "benign";
  n: number;
  complyCount: number;
  softRefuseCount: number;
  refuseCount: number;
  incoherentCount: number;
  complyPct: number;
  softRefusePct: number;
  refusePct: number;
  incoherentPct: number;
  sourceType: string;
  sourceUrl: string;
  sourceCommit: string;
  judgeModel: string;
}

export interface AgenticInfluenceResult {
  benchmarkId: "anthropic-agentic-influence";
  model: string;
  releaseDate: string;
  scenario: "voter-suppression" | "domestic-polarization";
  scorePct: number;
  runs: number;
  frictionLevels: number;
  successCriteria: number;
  deploymentCondition: "helpful-only";
  sourceType: "author-reported";
  sourceUrl: string;
  sourceSection: string;
}

export interface MaskResult {
  benchmarkId: "mask";
  model: string;
  canonicalModelId: string;
  releaseDate: string;
  totalParamsB: number;
  activeParamsB: number;
  honestPct: number;
  liePct: number;
  accuracyPct: number;
  n: number;
  protocolId: string;
  sourceType: "author-reported";
  sourceUrl: string;
  sourceLocator: string;
}

export interface WaveModel {
  model: string;
  canonicalModelId: string;
  organisation: string;
  family: string;
  releaseDate: string;
  totalParamsB: number;
  activeParamsB: number | null;
  accessType: AccessType;
  licence: string;
  openRouterId: string;
  openRouterStatus: "available" | "unavailable" | "verify";
  wave: "historical-anchor" | "wave-1" | "wave-2";
  sourceUrl: string;
  note: string;
}

export interface BenchmarkRecord {
  id: string;
  name: string;
  construct: string;
  metric: string;
  observes: string;
  doesNotObserve: string;
  evidenceLayer: "capability" | "safeguard" | "efficacy" | "access";
  status: "live" | "ingestion" | "planned" | "external";
  publicationDate: string;
  modelPeriod: string;
  sourceUrl: string;
}
