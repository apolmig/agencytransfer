import { useEffect, useMemo, useState } from "react";
import { AgenticInfluenceChart } from "./components/AgenticInfluenceChart";
import { EvidenceMap } from "./components/EvidenceMap";
import { FrontierTimeline } from "./components/FrontierTimeline";
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

function App() {
  const [frontierModels, setFrontierModels] = useState<FrontierModel[]>([]);
  const [frontierObservations, setFrontierObservations] = useState<FrontierObservation[]>([]);
  const [testingNotes, setTestingNotes] = useState<TestingNote[]>([]);
  const [results, setResults] = useState<DisElectResult[]>([]);
  const [agenticResults, setAgenticResults] = useState<AgenticInfluenceResult[]>([]);
  const [maskResults, setMaskResults] = useState<MaskResult[]>([]);
  const [models, setModels] = useState<WaveModel[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkRecord[]>([]);
  const [errors, setErrors] = useState<Partial<Record<DataKey, string>>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const tasks: Promise<void>[] = [];

    const queue = <T,>(key: DataKey, loader: () => Promise<T>, commit: (value: T) => void) => {
      tasks.push(
        loader()
          .then((value) => {
            if (!cancelled) commit(value);
          })
          .catch((reason: unknown) => {
            if (!cancelled) {
              setErrors((current) => ({ ...current, [key]: errorMessage(reason) }));
            }
          }),
      );
    };

    queue("frontierModels", loadFrontierModels, setFrontierModels);
    queue("frontierObservations", loadFrontierObservations, setFrontierObservations);
    queue("testingNotes", loadTestingNotes, setTestingNotes);
    queue("diselect", loadDisElectResults, setResults);
    queue("agentic", loadAgenticInfluenceResults, setAgenticResults);
    queue("mask", loadMaskResults, setMaskResults);
    queue("manifest", loadModelManifest, setModels);
    queue("benchmarks", loadBenchmarks, setBenchmarks);

    void Promise.all(tasks).finally(() => {
      if (!cancelled) setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const frontierStats = useMemo(
    () => ({
      releases: frontierModels.length,
      observations: frontierObservations.length,
      measures: new Set(
        frontierObservations.map((row) => `${row.benchmarkId}::${row.metricKey}`),
      ).size,
    }),
    [frontierModels, frontierObservations],
  );

  const historicalStats = useMemo(() => {
    const allHarmful = results
      .filter((row) => row.subset === "all-harmful")
      .sort((a, b) => a.releaseDate.localeCompare(b.releaseDate));
    const benign = results.filter((row) => row.subset === "benign");
    return {
      labels: [...allHarmful, ...benign].reduce((sum, row) => sum + row.n, 0),
      models: new Set(allHarmful.map((row) => row.model)).size,
      first: allHarmful.at(0)?.releaseDate.slice(0, 4) ?? "—",
      last: allHarmful.at(-1)?.releaseDate.slice(0, 4) ?? "—",
    };
  }, [results]);

  const frontierError = [errors.frontierModels, errors.frontierObservations]
    .filter(Boolean)
    .join(" · ");

  return (
    <>
      <header className="site-header">
        <a className="wordmark" href="#top" aria-label="Agency Transfer Benchmark home">
          <span aria-hidden="true">AT</span>
          <strong>Agency Transfer Benchmark</strong>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#timeline">Chart</a>
          <a href="#evidence">Evidence</a>
          <a href="#testing">Testing</a>
          <a href="#systems">Systems</a>
          <a href="#methods">Methods</a>
          <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">GitHub ↗</a>
        </nav>
      </header>

      <main id="main-content">
        <aside className="draft-banner" aria-label="Publication status">
          <strong>DRAFT IN PROGRESS</strong>
          <span>
            Part of Miguel Guerrero’s Cambridge:ERA research on Frontier AI, Harmful Manipulation,
            and Election Security. Independent research; not an official ERA benchmark.
          </span>
        </aside>

        <section className="lead" id="top">
          <div className="lead-chart-heading" id="timeline">
            <div>
              <p className="section-number">01 · Frontier longitudinal view · 2024–2026</p>
              <h1>Frontier harmful-influence evidence, through 2026</h1>
            </div>
            <p>
              The primary rail is restricted to frontier-scale releases: open-weight models with at
              least 100 billion total parameters, plus separately labelled hosted frontier and
              requested comparison APIs. A release without a comparable result remains visible as
              missing—not zero.
            </p>
          </div>

          {frontierError ? <p className="inline-data-error" role="alert">Some frontier data could not load: {frontierError}</p> : null}
          {frontierModels.length > 0 ? (
            <FrontierTimeline models={frontierModels} observations={frontierObservations} />
          ) : loading ? (
            <p className="loading-message" aria-live="polite">Loading frontier evidence…</p>
          ) : (
            <p className="empty-message">No verified frontier release manifest is available in this build.</p>
          )}

          {frontierModels.length > 0 ? (
            <div className="stat-line frontier-stat-line" aria-label="Frontier evidence coverage">
              <div><strong>{frontierStats.releases}</strong><span>frontier and requested comparison releases</span></div>
              <div><strong>{frontierStats.observations}</strong><span>source-linked observations</span></div>
              <div><strong>{frontierStats.measures}</strong><span>native benchmark measures</span></div>
              <div><strong>2024–2026</strong><span>fixed release-date window</span></div>
            </div>
          ) : null}

          <div className="lead-notes">
            <article>
              <p className="mini-label">Frozen 26 July 2026 snapshot</p>
              <h3>One protocol, a 71-point spread.</h3>
              <p>
                InfoOpsBench reported 5.5% compliance for Claude Sonnet 5 and 76.5% for GLM-5.2.
                That contrast is evidence of endpoint behaviour under one rubric—not proof of why
                the endpoints differ or what they would do in another deployment.
              </p>
            </article>
            <article>
              <p className="mini-label">What it cannot establish</p>
              <h3>A model score is not manipulation.</h3>
              <p>
                These evaluations do not by themselves demonstrate human persuasion, durable belief
                change, agency transfer, vote change, or democratic harm.
              </p>
            </article>
          </div>
        </section>

        <section className="opening-thesis">
          <p>
            Frontier behaviour is only the first link. Safeguards and access shape who can use it;
            applications, memory, tools, and repeated exposure determine how model capability can
            become infrastructure for influence and agency transfer.
          </p>
        </section>

        {errors.testingNotes ? (
          <section className="section testing-section" id="testing">
            <div className="section-heading split-heading">
              <div><p className="section-number">02 · Testing</p><h2>Runs, results, and failures</h2></div>
              <p className="inline-data-error" role="alert">Testing notes could not load: {errors.testingNotes}</p>
            </div>
          </section>
        ) : loading && testingNotes.length === 0 ? (
          <section className="section testing-section" id="testing">
            <div className="section-heading split-heading">
              <div><p className="section-number">02 · Testing</p><h2>Runs, results, and failures</h2></div>
              <p className="loading-message" aria-live="polite">Loading project research notes…</p>
            </div>
          </section>
        ) : (
          <TestingSection notes={testingNotes} />
        )}

        <section className="section chart-section" id="operational">
          <div className="section-heading split-heading">
            <div>
              <p className="section-number">03 · Published operational evidence</p>
              <h2>From response generation to campaign execution</h2>
            </div>
            <p>
              Anthropic’s system cards provide a single-developer release series of helpful-only
              Claude variants using simulated social-platform tools. It observes operational task
              completion, not effects on real people or default deployed behaviour.
            </p>
          </div>

          {errors.agentic ? <p className="inline-data-error" role="alert">Agentic evidence could not load: {errors.agentic}</p> : null}
          {agenticResults.length > 0 ? (
            <AgenticInfluenceChart results={agenticResults} />
          ) : loading ? (
            <p className="loading-message" aria-live="polite">Loading published operational evidence…</p>
          ) : null}

          <div className="interpretation-grid">
            <article>
              <p className="mini-label">Established evidence</p>
              <h3>Models can be tested as operators, not only writers.</h3>
              <p>
                This protocol measures completion of criteria across simulated influence workflows.
                The interactive chart preserves the author-reported values and conditions.
              </p>
            </article>
            <article>
              <p className="mini-label">Deployment boundary</p>
              <h3>Raw capability is not default behaviour.</h3>
              <p>
                The evaluated helpful-only variants had reduced harmlessness training. The results
                neither describe default product behaviour nor establish real-world efficacy.
              </p>
            </article>
          </div>
        </section>

        <SystemsResearchSection />

        <section className="section evidence-section" id="evidence">
          <div className="section-heading split-heading">
            <div>
              <p className="section-number">04 · Safeguards, access, and efficacy</p>
              <h2>Related evidence. No false composite.</h2>
            </div>
            <p>
              APE, MASK, DisElect, agentic evaluations, and human studies answer different questions.
              They belong in one evidence architecture, but their scores must not be averaged into an
              “Agency Transfer Score.”
            </p>
          </div>
          {errors.benchmarks ? <p className="inline-data-error" role="alert">The evidence registry could not load: {errors.benchmarks}</p> : null}
          {benchmarks.length > 0 ? <EvidenceMap benchmarks={benchmarks} /> : null}
          {errors.mask ? <p className="inline-data-error" role="alert">MASK evidence could not load: {errors.mask}</p> : null}
          {maskResults.length > 0 ? <MaskChart results={maskResults} /> : null}
        </section>

        <section className="section models-section" id="models">
          <div className="section-heading split-heading">
            <div>
              <p className="section-number">05 · Practical access</p>
              <h2>Frontier capability can diffuse through open weights</h2>
            </div>
            <p>
              Parameter count is an inclusion rule, not a capability score. This secondary view
              records large open-weight releases and serving availability; hosted frontier systems
              remain a separately labelled population.
            </p>
          </div>
          {errors.manifest ? <p className="inline-data-error" role="alert">The legacy model manifest could not load: {errors.manifest}</p> : null}
          {models.length > 0 ? <ModelPanel models={models} /> : null}
        </section>

        <section className="section historical-section" id="historical">
          <div className="section-heading split-heading">
            <div>
              <p className="section-number">06 · Historical context · not the frontier cohort</p>
              <h2>The published baseline begins before frontier scale</h2>
            </div>
            <p>
              DisElect supplies a fixed election-operation protocol across older and smaller models.
              It remains useful context, but its mixed-size 2019–2024 cohort is deliberately excluded
              from the primary frontier-only claim.
            </p>
          </div>
          {errors.diselect ? <p className="inline-data-error" role="alert">DisElect evidence could not load: {errors.diselect}</p> : null}
          {results.length > 0 ? <LongitudinalChart results={results} /> : null}
          {results.length > 0 ? (
            <div className="stat-line" aria-label="Historical published baseline summary">
              <div><strong>{historicalStats.labels.toLocaleString("en-GB")}</strong><span>released response labels</span></div>
              <div><strong>{historicalStats.models}</strong><span>models under one protocol</span></div>
              <div><strong>{historicalStats.first}–{historicalStats.last}</strong><span>release-date coverage</span></div>
              <div><strong>Context</strong><span>not the primary frontier series</span></div>
            </div>
          ) : null}
        </section>

        <section className="section methods-section" id="methods">
          <div className="section-heading split-heading">
            <div>
              <p className="section-number">Methods</p>
              <h2>The claim must follow the measurement</h2>
            </div>
            <p>
              Release date is descriptive. The project does not estimate a causal rate of progress,
              and it does not treat differences between models as proof that time, scale, or openness
              caused a capability or safeguard change.
            </p>
          </div>

          <div className="method-principles">
            <article>
              <span>Unit</span>
              <h3>Snapshot × endpoint × condition × item × seed</h3>
              <p>Aliases are insufficient. Route, provider, guardrails, reasoning mode, errors, tokens, latency, and cost are part of the observation.</p>
            </article>
            <article>
              <span>Comparison</span>
              <h3>Native metrics, fixed protocols</h3>
              <p>Lines require the same benchmark, item set, judge, deployment condition, and comparability identifier. Missing results never become zero.</p>
            </article>
            <article>
              <span>Validation</span>
              <h3>Humans audit automated judges</h3>
              <p>Project-generated comparisons require blinded human review and visible uncertainty before they are treated as more than exploratory.</p>
            </article>
          </div>

          <div className="causal-chain-block">
            <p className="mini-label">Research chain</p>
            <ol className="causal-chain">
              <li>AI capability</li><li>Controlling actor</li><li>Influence vector</li><li>Target</li>
              <li>Belief, attention, trust, behaviour, or dependency</li><li>Agency transfer</li>
              <li>Concentration of power</li><li>Democratic harm</li><li>Mitigation</li>
            </ol>
            <p>
              Current model evaluations observe parts of the first link and selected safeguard
              conditions. Evidence from later links is reviewed separately; it is never inferred
              from a compliance, persuasion-attempt, or honesty score.
            </p>
          </div>
        </section>

        <section className="section release-section" id="data">
          <div className="section-heading split-heading">
            <div>
              <p className="section-number">Responsible release</p>
              <h2>Reproducible without becoming operational</h2>
            </div>
            <p>
              Public artifacts include manifests, aggregate labels, provenance, protocol hashes,
              uncertainty, failures, and costs. Raw harmful generations, targeting material, and
              current-election operational content remain restricted.
            </p>
          </div>
          <div className="release-links">
            <a href={`${REPOSITORY_URL}/tree/main/data`} target="_blank" rel="noreferrer">Data ledger ↗</a>
            <a href={HUGGING_FACE_URL} target="_blank" rel="noreferrer">Hugging Face ↗</a>
            <a href={`${REPOSITORY_URL}/blob/main/METHODS.md`} target="_blank" rel="noreferrer">Methods ↗</a>
            <a href={`${REPOSITORY_URL}/blob/main/RESPONSIBLE_RELEASE.md`} target="_blank" rel="noreferrer">Release policy ↗</a>
            <a href={`${REPOSITORY_URL}/blob/main/CITATION.cff`} target="_blank" rel="noreferrer">Citation ↗</a>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div>
          <strong>Agency Transfer Benchmark</strong>
          <p>
            Part of Miguel Guerrero’s Cambridge:ERA research on Frontier AI, Harmful Manipulation,
            and Election Security. Independent research; not an official ERA benchmark.
          </p>
        </div>
        <div>
          <span>Draft · 10 August 2026</span>
          <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">Source and issues ↗</a>
        </div>
      </footer>
    </>
  );
}

export default App;
