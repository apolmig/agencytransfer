import { useEffect, useState } from "react";
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
  loadHmcEstimates,
  loadHmcFrontier,
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
  HmcEstimate,
  HmcFrontierPoint,
  MaskResult,
  TestingNote,
  WaveModel,
} from "./types";

const REPOSITORY_URL = "https://github.com/apolmig/agencytransfer";
const HUGGING_FACE_URL = "https://huggingface.co/datasets/apol/agency-transfer-benchmark";

type PageKey = "home" | "evidence" | "testing";
type DataKey =
  | "frontierModels"
  | "frontierObservations"
  | "hmcEstimates"
  | "hmcFrontier"
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
  if (/\/evidence(?:\.html)?$/.test(path)) return "evidence";
  if (/\/testing(?:\.html)?$/.test(path)) return "testing";
  return "home";
};

function DraftMark() {
  return (
    <div className="draft-mark" aria-label="Publication status">
      <strong>DRAFT · IN PROGRESS</strong>
      <span>Independent Cambridge:ERA research · not an official ERA benchmark</span>
    </div>
  );
}

function SiteHeader({ page }: { page: PageKey }) {
  const base = import.meta.env.BASE_URL;
  return (
    <header className="site-header">
      <a className="wordmark" href={base} aria-label="Agency Transfer Benchmark home">
        <span aria-hidden="true">AT</span>
        <strong>Agency Transfer Benchmark</strong>
      </a>
      <nav aria-label="Primary navigation">
        <a href={base} aria-current={page === "home" ? "page" : undefined}>Chart</a>
        <a href={`${base}evidence/`} aria-current={page === "evidence" ? "page" : undefined}>Evidence</a>
        <a href={`${base}testing/`} aria-current={page === "testing" ? "page" : undefined}>Testing</a>
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
        <span>Draft · 12 August 2026</span>
        <a href={`${REPOSITORY_URL}/blob/main/ESTIMATED_SCORE.md`} target="_blank" rel="noreferrer">Method ↗</a>
        <a href={HUGGING_FACE_URL} target="_blank" rel="noreferrer">Data ↗</a>
        <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">Source and issues ↗</a>
      </div>
    </footer>
  );
}

interface HomeProps {
  models: FrontierModel[];
  observations: FrontierObservation[];
  estimates: HmcEstimate[];
  frontier: HmcFrontierPoint[];
  loading: boolean;
  error: string;
}

function HomePage({ models, observations, estimates, frontier, loading, error }: HomeProps) {
  const eligible = estimates.filter((estimate) => estimate.evidenceStatus === "estimated").length;
  return (
    <main id="main-content">
      <section className="lead home-lead" id="top">
        <DraftMark />
        <div className="home-title">
          <h1>Manipulation-relevant model behaviour</h1>
          <p>Frontier releases · 2022–2026 · Native instruments first</p>
        </div>

        {error ? <p className="inline-data-error" role="alert">Some chart data could not load: {error}</p> : null}
        {models.length > 0 && (observations.length > 0 || estimates.length > 0) ? (
          <FrontierTimeline models={models} observations={observations} estimates={estimates} frontier={frontier} />
        ) : loading ? (
          <p className="loading-message" aria-live="polite">Loading the release series…</p>
        ) : (
          <p className="empty-message">No verified release series is available in this build.</p>
        )}

        <details className="hero-method-note">
          <summary>Why the synthesis remains experimental</summary>
          <div>
            <p>
              The default view preserves one benchmark-native outcome. A separate selectable proxy combines
              operational harmful support (40%), agentic campaign execution (30%), harmful persuasion attempts
              (20%), and deception under pressure (10%). It is a visual synthesis, not a validated latent
              capability scale.
            </p>
            <p>
              {eligible} of {models.length} releases currently meet the proxy's minimum coverage rule. All other releases
              remain visible as hollow marks—missing, never zero.
            </p>
            <a href={`${REPOSITORY_URL}/blob/main/ESTIMATED_SCORE.md`} target="_blank" rel="noreferrer">Weights, uncertainty, sensitivity, and limits ↗</a>
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
          No source measures harmful manipulation capability end to end. The literature separately observes
          willingness, safeguards, task execution, persuasive effect, deception, or access. The chart is an
          ATB-authored synthesis—not a score or conclusion reported by any cited paper.
        </p>
      </section>

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
          <p>Native benchmark outcomes remain selectable on the Home chart and retain their own protocols, denominators, and directions.</p>
        </div>
        {errors.benchmarks ? <p className="inline-data-error" role="alert">The evidence registry could not load: {errors.benchmarks}</p> : null}
        {benchmarks.length > 0 ? <EvidenceMap benchmarks={benchmarks} /> : null}
      </section>

      <section className="section chart-section" id="agentic">
        <div className="section-heading split-heading">
          <div><p className="section-number">03 · Agentic execution</p><h2>Campaign workflows, not human effects</h2></div>
          <p>Anthropic’s helpful-only variants were tested in simulated social-platform workflows. These results measure task completion, not default safeguards or real-world persuasion.</p>
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

function App() {
  const [frontierModels, setFrontierModels] = useState<FrontierModel[]>([]);
  const [frontierObservations, setFrontierObservations] = useState<FrontierObservation[]>([]);
  const [hmcEstimates, setHmcEstimates] = useState<HmcEstimate[]>([]);
  const [hmcFrontier, setHmcFrontier] = useState<HmcFrontierPoint[]>([]);
  const [testingNotes, setTestingNotes] = useState<TestingNote[]>([]);
  const [diselectResults, setDisElectResults] = useState<DisElectResult[]>([]);
  const [agenticResults, setAgenticResults] = useState<AgenticInfluenceResult[]>([]);
  const [maskResults, setMaskResults] = useState<MaskResult[]>([]);
  const [models, setModels] = useState<WaveModel[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkRecord[]>([]);
  const [errors, setErrors] = useState<Partial<Record<DataKey, string>>>({});
  const [loading, setLoading] = useState(true);
  const page = currentPage();

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
    queue("hmcEstimates", loadHmcEstimates, setHmcEstimates);
    queue("hmcFrontier", loadHmcFrontier, setHmcFrontier);
    queue("testingNotes", loadTestingNotes, setTestingNotes);
    queue("diselect", loadDisElectResults, setDisElectResults);
    queue("agentic", loadAgenticInfluenceResults, setAgenticResults);
    queue("mask", loadMaskResults, setMaskResults);
    queue("manifest", loadModelManifest, setModels);
    queue("benchmarks", loadBenchmarks, setBenchmarks);

    void Promise.all(tasks).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const frontierError = [errors.frontierModels, errors.frontierObservations, errors.hmcEstimates, errors.hmcFrontier]
    .filter(Boolean)
    .join(" · ");

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <SiteHeader page={page} />
      {page === "home" ? (
        <HomePage
          models={frontierModels}
          observations={frontierObservations}
          estimates={hmcEstimates}
          frontier={hmcFrontier}
          loading={loading}
          error={frontierError}
        />
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
            <h1>Confirmatory results only</h1>
            <p>Exploratory runs stay in the audit trail. A comparison appears here only after route integrity, a frozen protocol, blinded human validation, and uncertainty checks pass.</p>
          </section>
          {errors.testingNotes ? <p className="inline-data-error standalone-error" role="alert">Testing notes could not load: {errors.testingNotes}</p> : null}
          <TestingSection notes={testingNotes} />
        </main>
      )}
      <SiteFooter />
    </>
  );
}

export default App;
