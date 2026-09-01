import { useEffect, useState } from "react";
import { MeasurementGap } from "./components/ResearchStatus";
import { AgenticInfluenceChart } from "./components/AgenticInfluenceChart";
import { EvidenceMap } from "./components/EvidenceMap";
import { FrontierTimeline } from "./components/FrontierTimeline";
import { LiteratureReview } from "./components/LiteratureReview";
import { LongitudinalChart } from "./components/LongitudinalChart";
import { MaskChart } from "./components/MaskChart";
import { ModelPanel } from "./components/ModelPanel";
import { SystemsResearchSection } from "./components/SystemsResearchSection";
import { TestingSection } from "./components/TestingSection";
import {
  loadAgenticInfluenceResults,
  loadBenchmarks,
  loadDisElectResults,
  loadFrontierModels,
  loadFrontierObservations,
  loadMaskResults,
  loadModelManifest,
  loadTestingNotes,
} from "./data";
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

const REPOSITORY_URL = "https://github.com/apolmig/agencytransfer";
const HUGGING_FACE_URL = "https://huggingface.co/datasets/apol/agency-transfer-benchmark";
const REGISTRY_BASE = `${import.meta.env.BASE_URL}registry/`;

type PageKey = "home" | "evidence" | "testing";
type DataKey =
  | "frontierModels"
  | "frontierObservations"
  | "testingNotes"
  | "diselect"
  | "agentic"
  | "mask"
  | "manifest"
  | "benchmarks";

const errorMessage = (reason: unknown) =>
  reason instanceof Error ? reason.message : "Unknown data-loading error";

const currentPage = (): PageKey => {
  const path = window.location.pathname.replace(/\/+$/, "");
  if (/\/(?:registry\/|research\/part-ii\/)?evidence(?:\.html)?$/.test(path)) return "evidence";
  if (/\/(?:registry\/|research\/part-ii\/)?testing(?:\.html)?$/.test(path)) return "testing";
  return "home";
};

function useRegistryMetadata(page: PageKey) {
  useEffect(() => {
    const title = page === "home"
      ? "Agency Transfer Benchmark"
      : page === "evidence"
        ? "Evidence · Agency Transfer Benchmark"
        : "Testing · Agency Transfer Benchmark";
    const suffix = page === "home" ? "" : `${page}/`;
    document.title = `${title} · Draft / work in progress`;
    const description = document.querySelector<HTMLMetaElement>('meta[name="description"]');
    if (description) description.content = "Draft evaluation registry and research in progress. Native measures remain useful; a common validated system-level harmful-manipulation instrument remains unresolved.";
    const canonical = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
    if (canonical) canonical.href = `https://miguelguerrero.eu/agencytransfer/registry/${suffix}`;
    document.body.classList.remove("editorial-v2-active");
    document.body.classList.add("registry-legacy-active");
    return () => document.body.classList.remove("registry-legacy-active");
  }, [page]);
}

function DraftMark() {
  return (
    <div className="draft-mark" aria-label="Publication status">
      <strong>DRAFT · IN PROGRESS</strong>
      <span>Provisional programme results · not peer reviewed · not an official ERA benchmark</span>
    </div>
  );
}

function SiteHeader({ page }: { page: PageKey }) {
  return (
    <header className="site-header">
      <a className="wordmark" href={REGISTRY_BASE} aria-label="Agency Transfer Benchmark home">
        <span aria-hidden="true">AT</span>
        <strong>Agency Transfer Benchmark</strong>
      </a>
      <nav aria-label="Primary navigation">
        <a href={REGISTRY_BASE} aria-current={page === "home" ? "page" : undefined}>Chart</a>
        <a href={`${REGISTRY_BASE}evidence/`} aria-current={page === "evidence" ? "page" : undefined}>Evidence</a>
        <a href={`${REGISTRY_BASE}testing/`} aria-current={page === "testing" ? "page" : undefined}>Testing</a>
      </nav>
    </header>
  );
}

function SiteFooter() {
  return (
    <footer className="site-footer">
      <div>
        <strong>Agency Transfer Benchmark</strong>
        <p>Frontier AI, harmful manipulation, and election security. Independent research; draft and in progress.</p>
      </div>
      <div>
        <span>Draft / work in progress · presentation revised 1 September 2026 · source dates vary</span>
        <a href={`${REPOSITORY_URL}/blob/main/METHODS.md`} target="_blank" rel="noreferrer">Method ↗</a>
        <a href={HUGGING_FACE_URL} target="_blank" rel="noreferrer">Data ↗</a>
        <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">Source and issues ↗</a>
      </div>
    </footer>
  );
}

interface HomeProps {
  models: FrontierModel[];
  observations: FrontierObservation[];
  loading: boolean;
  error: string;
}

function HomePage({ models, observations, loading, error }: HomeProps) {
  return (
    <main id="main-content">
      <section className="lead home-lead" id="top">
        <DraftMark />
        <div className="home-title">
          <h1>Manipulation-relevant model behaviour</h1>
          <p>Frontier releases · 2022–2026 · Native instruments first</p>
        </div>

        <MeasurementGap compact />
        {error ? <p className="inline-data-error" role="alert">Some chart data could not load: {error}</p> : null}
        {models.length > 0 && observations.length > 0 ? (
          <FrontierTimeline models={models} observations={observations} />
        ) : loading ? (
          <p className="loading-message" aria-live="polite">Loading the release series…</p>
        ) : (
          <p className="empty-message">No verified release series is available in this build.</p>
        )}

        <details className="hero-method-note">
          <summary>How to read the chart</summary>
          <div>
            <p>
              Each view shows one benchmark's native outcome. Measures with different protocols, prompts,
              judges, denominators, or constructs are not combined into a single score.
            </p>
            <p>
              Hollow release marks mean that no comparable observation is available in the selected view—missing,
              never zero.
            </p>
            <a href={`${REPOSITORY_URL}/blob/main/METHODS.md`} target="_blank" rel="noreferrer">Methods and comparability limits ↗</a>
          </div>
        </details>
      </section>
    </main>
  );
}

interface EvidenceProps {
  benchmarks: BenchmarkRecord[];
  agenticResults: AgenticInfluenceResult[];
  maskResults: MaskResult[];
  diselectResults: DisElectResult[];
  models: WaveModel[];
  errors: Partial<Record<DataKey, string>>;
}

function EvidencePage({ benchmarks, agenticResults, maskResults, diselectResults, models, errors }: EvidenceProps) {
  return (
    <main id="main-content">
      <section className="page-intro">
        <DraftMark />
        <p className="section-number">Evidence</p>
        <h1>What each instrument can—and cannot—claim</h1>
        <p>
          In the sources reviewed, no single accepted instrument covers harmful manipulation across deployed systems. The literature separately observes
          willingness, safeguards, task execution, persuasive effect, deception, or access. ATB preserves those
          native outcomes rather than collapsing them into a cross-benchmark score.
        </p>
      </section>

      <MeasurementGap />
      <section className="section literature-section" id="literature">
        <div className="section-heading split-heading">
          <div><p className="section-number">01 · Literature review</p><h2>Papers behind the measurement model</h2></div>
          <p>Primary sources are grouped by the construct they actually observe. Human-efficacy studies inform interpretation but are not converted into model scores.</p>
        </div>
        <LiteratureReview />
      </section>

      <section className="section evidence-section" id="map">
        <div className="section-heading split-heading">
          <div><p className="section-number">02 · Evidence map</p><h2>One timeline, separate constructs</h2></div>
          <p>Native benchmark outcomes remain selectable on the Chart and retain their own protocols, denominators, and directions.</p>
        </div>
        {errors.benchmarks ? <p className="inline-data-error" role="alert">The evidence registry could not load: {errors.benchmarks}</p> : null}
        {benchmarks.length > 0 ? <EvidenceMap benchmarks={benchmarks} /> : null}
      </section>

      <section className="section chart-section" id="agentic">
        <div className="section-heading split-heading">
          <div><p className="section-number">03 · Agentic execution</p><h2>Campaign workflows, not human effects</h2></div>
          <p>Controlled simulated social-platform workflows measure task completion, not default safeguards or real-world persuasion.</p>
        </div>
        {errors.agentic ? <p className="inline-data-error" role="alert">Agentic evidence could not load: {errors.agentic}</p> : null}
        {agenticResults.length > 0 ? <AgenticInfluenceChart results={agenticResults} /> : null}
      </section>

      <section className="section chart-section" id="deception">
        <div className="section-heading split-heading">
          <div><p className="section-number">04 · Deception</p><h2>Lying under pressure</h2></div>
          <p>MASK tests honesty under belief conflict. It is relevant to manipulation risk, but it does not observe a target’s beliefs, choices, or agency.</p>
        </div>
        {errors.mask ? <p className="inline-data-error" role="alert">MASK evidence could not load: {errors.mask}</p> : null}
        {maskResults.length > 0 ? <MaskChart results={maskResults} /> : null}
      </section>

      <section className="section historical-section" id="diselect">
        <div className="section-heading split-heading">
          <div><p className="section-number">05 · Election operations</p><h2>Historical harmful compliance</h2></div>
          <p>DisElect provides a fixed election-operation protocol across older models. It measures response generation—not campaign success, vote change, or democratic harm.</p>
        </div>
        {errors.diselect ? <p className="inline-data-error" role="alert">DisElect evidence could not load: {errors.diselect}</p> : null}
        {diselectResults.length > 0 ? <LongitudinalChart results={diselectResults} /> : null}
      </section>

      <SystemsResearchSection />

      <section className="section models-section" id="access">
        <div className="section-heading split-heading">
          <div><p className="section-number">06 · Access</p><h2>Capability can diffuse through weights and APIs</h2></div>
          <p>Parameter count is an inclusion rule, not a capability score. Open-weight and hosted frontier releases remain distinct populations.</p>
        </div>
        {errors.manifest ? <p className="inline-data-error" role="alert">The access manifest could not load: {errors.manifest}</p> : null}
        {models.length > 0 ? <ModelPanel models={models} /> : null}
      </section>
    </main>
  );
}

export default function LegacyRegistryApp() {
  const [frontierModels, setFrontierModels] = useState<FrontierModel[]>([]);
  const [frontierObservations, setFrontierObservations] = useState<FrontierObservation[]>([]);
  const [testingNotes, setTestingNotes] = useState<TestingNote[]>([]);
  const [diselectResults, setDisElectResults] = useState<DisElectResult[]>([]);
  const [agenticResults, setAgenticResults] = useState<AgenticInfluenceResult[]>([]);
  const [maskResults, setMaskResults] = useState<MaskResult[]>([]);
  const [models, setModels] = useState<WaveModel[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkRecord[]>([]);
  const [errors, setErrors] = useState<Partial<Record<DataKey, string>>>({});
  const [loading, setLoading] = useState(true);
  const page = currentPage();
  useRegistryMetadata(page);

  useEffect(() => {
    let cancelled = false;
    const tasks: Promise<void>[] = [];
    const queue = <T,>(key: DataKey, loader: () => Promise<T>, commit: (value: T) => void) => {
      tasks.push(loader().then((value) => {
        if (!cancelled) commit(value);
      }).catch((reason: unknown) => {
        if (!cancelled) setErrors((current) => ({ ...current, [key]: errorMessage(reason) }));
      }));
    };

    queue("frontierModels", loadFrontierModels, setFrontierModels);
    queue("frontierObservations", loadFrontierObservations, setFrontierObservations);
    queue("testingNotes", loadTestingNotes, setTestingNotes);
    queue("diselect", loadDisElectResults, setDisElectResults);
    queue("agentic", loadAgenticInfluenceResults, setAgenticResults);
    queue("mask", loadMaskResults, setMaskResults);
    queue("manifest", loadModelManifest, setModels);
    queue("benchmarks", loadBenchmarks, setBenchmarks);

    void Promise.all(tasks).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const frontierError = [errors.frontierModels, errors.frontierObservations]
    .filter(Boolean)
    .join(" · ");

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <SiteHeader page={page} />
      {page === "home" ? (
        <HomePage models={frontierModels} observations={frontierObservations} loading={loading} error={frontierError} />
      ) : page === "evidence" ? (
        <EvidencePage
          benchmarks={benchmarks}
          agenticResults={agenticResults}
          maskResults={maskResults}
          diselectResults={diselectResults}
          models={models}
          errors={errors}
        />
      ) : (
        <main id="main-content">
          <section className="page-intro testing-page-intro">
            <DraftMark />
            <p className="section-number">Testing</p>
            <h1>Testing in progress</h1>
            <p>These are provisional testing records, not automatically admitted findings. Confirmatory claims require route integrity, a frozen protocol, human-calibrated validation and uncertainty checks. The current non-confirmatory runs remain visible in the audit trail.</p>
          </section>
          {errors.testingNotes ? <p className="inline-data-error standalone-error" role="alert">Testing notes could not load: {errors.testingNotes}</p> : null}
          <TestingSection notes={testingNotes} />
        </main>
      )}
      <SiteFooter />
    </>
  );
}
