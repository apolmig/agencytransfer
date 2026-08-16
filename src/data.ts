import type {
  AgenticInfluenceResult,
  BenchmarkRecord,
  DisElectResult,
  FrontierModel,
  FrontierObservation,
  MaskResult,
  TestingNote,
  WaveModel,
} from "./types";

async function loadJson<T>(filename: string): Promise<T> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/${filename}`);
  if (!response.ok) throw new Error(`Could not load ${filename}: ${response.status}`);
  return response.json() as Promise<T>;
}

export const loadDisElectResults = () =>
  loadJson<DisElectResult[]>("diselect-results.json");

export const loadAgenticInfluenceResults = () =>
  loadJson<AgenticInfluenceResult[]>("anthropic-agentic-influence.json");

export const loadMaskResults = () => loadJson<MaskResult[]>("mask-original-results.json");

export const loadModelManifest = () => loadJson<WaveModel[]>("model-manifest.json");

export const loadBenchmarks = () => loadJson<BenchmarkRecord[]>("benchmarks.json");

export const loadFrontierModels = () => loadJson<FrontierModel[]>("frontier-models.json");

export const loadFrontierObservations = () =>
  loadJson<FrontierObservation[]>("frontier-observations.json");

export const loadTestingNotes = () => loadJson<TestingNote[]>("testing-notes.json");
