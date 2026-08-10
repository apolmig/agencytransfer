import { useEffect, useMemo, useState } from "react";
import { AgenticInfluenceChart } from "./components/AgenticInfluenceChart";
import { EvidenceMap } from "./components/EvidenceMap";
import { LongitudinalChart } from "./components/LongitudinalChart";
import { MaskChart } from "./components/MaskChart";
import { ModelPanel } from "./components/ModelPanel";
import {
  loadAgenticInfluenceResults,
  loadBenchmarks,
  loadDisElectResults,
  loadMaskResults,
  loadModelManifest,
} from "./data";
import type {
  AgenticInfluenceResult,
  BenchmarkRecord,
  DisElectResult,
  MaskResult,
  WaveModel,
} from "./types";

const REPOSITORY_URL = "https://github.com/apolmig/agencytransfer";

function App() {
  const [results, setResults] = useState<DisElectResult[]>([]);
  const [agenticResults, setAgenticResults] = useState<AgenticInfluenceResult[]>([]);
  const [maskResults, setMaskResults] = useState<MaskResult[]>([]);
  const [models, setModels] = useState<WaveModel[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      loadDisElectResults(),
      loadAgenticInfluenceResults(),
      loadMaskResults(),
      loadModelManifest(),
      loadBenchmarks(),
    ])
      .then(([resultRows, agenticRows, maskRows, modelRows, benchmarkRows]) => {
        setResults(resultRows);
        setAgenticResults(agenticRows);
        setMaskResults(maskRows);
        setModels(modelRows);
        setBenchmarks(benchmarkRows);
      })
      .catch((reason: unknown) =>
        setError(reason instanceof Error ? reason.message : "Unknown data-loading error"),
      );
  }, []);

  const headlineStats = useMemo(() => {
    const allHarmful = results.filter((row) => row.subset === "all-harmful");
    const benign = results.filter((row) => row.subset === "benign");
    return {
      labels: [...allHarmful, ...benign].reduce((sum, row) => sum + row.n, 0),
      models: new Set(allHarmful.map((row) => row.model)).size,
      first: allHarmful.at(0)?.releaseDate.slice(0, 4) ?? "—",
      last: allHarmful.at(-1)?.releaseDate.slice(0, 4) ?? "—",
    };
  }, [results]);

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
          <a href="#models">Models</a>
          <a href="#methods">Methods</a>
          <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">GitHub ↗</a>
        </nav>
      </header>

      <main id="main-content">
        <section className="lead" id="top">
          <div className="lead-chart-heading" id="timeline">
            <div>
              <p className="section-number">
                01 · Agency Transfer Benchmark · Wave 0 · 10 August 2026
              </p>
              <h1>Election-operation compliance, 2019–2024</h1>
            </div>
            <p>
              One fixed protocol, 13 releases, 2,200 harmful election-operation prompts and 50
              benign controls per model. Wave 0 recomputes the authors’ released labels; it
              generates no new harmful content.
            </p>
          </div>

          {error ? (
            <p className="error-message" role="alert">{error}</p>
          ) : results.length === 0 ? (
            <p className="loading-message" aria-live="polite">Loading published evidence…</p>
          ) : (
            <LongitudinalChart results={results} />
          )}

          <div className="stat-line" aria-label="Published baseline summary">
            <div><strong>{headlineStats.labels.toLocaleString("en-GB")}</strong><span>released response labels</span></div>
            <div><strong>{headlineStats.models}</strong><span>models under one protocol</span></div>
            <div><strong>{headlineStats.first}–{headlineStats.last}</strong><span>release-date coverage</span></div>
            <div><strong>0.76</strong><span>upstream judge Macro-F1</span></div>
          </div>

          <div className="lead-notes">
            <article>
              <p className="mini-label">Established evidence</p>
              <h3>Operational compliance diffused early.</h3>
              <p>
                GPT‑3 complied with 87.3% of harmful requests in the 2022 release cohort; GPT‑3.5
                Turbo reached 96.7%. Open-weight Llama 3 reached 90.8% by April 2024.
              </p>
            </article>
            <article>
              <p className="mini-label">Measurement boundary</p>
              <h3>Compliance is not manipulation.</h3>
              <p>
                The evaluation does not test distribution, targeting, persuasion, belief change,
                behaviour, persistence, or electoral effect. These numbers locate a capability—not
                the end of the causal chain. <a href="#methods">Read the methods ↓</a>
              </p>
            </article>
          </div>
        </section>

        <section className="opening-thesis">
          <p>
            The risk is not persuasion alone. It is the possibility that adaptive systems shift
            control over attention, beliefs, preferences, and decisions from people and democratic
            institutions toward actors who own the models, platforms, data, and channels of influence.
          </p>
        </section>

        <section className="section chart-section" id="operational">
          <div className="section-heading split-heading">
            <div>
              <p className="section-number">02 · Published operational series</p>
              <h2>From content generation to campaign execution</h2>
            </div>
            <p>
              Anthropic’s system cards provide the closest published release series to the project’s
              threat model: helpful-only Claude variants acting autonomously with simulated social-
              platform tools. It is direct operational evidence, but from one developer and one
              evaluation suite.
            </p>
          </div>

          {error ? (
            <p className="error-message" role="alert">{error}</p>
          ) : agenticResults.length === 0 ? (
            <p className="loading-message" aria-live="polite">Loading published evidence…</p>
          ) : (
            <AgenticInfluenceChart results={agenticResults} />
          )}

          <div className="interpretation-grid">
            <article>
              <p className="mini-label">Established evidence</p>
              <h3>Raw agentic capability is already material.</h3>
              <p>
                Helpful-only Opus 4.8 completed 73.3% of voter-suppression criteria and 55.1% of
                domestic-polarization criteria. The sequence is non-monotonic: later models do not
                simply score higher.
              </p>
            </article>
            <article>
              <p className="mini-label">Deployment boundary</p>
              <h3>Raw capability is not default behaviour.</h3>
              <p>
                These variants had reduced harmlessness training. Anthropic reports that fully
                trained versions refused the tasks from the start. The test also observes simulated
                task completion, not effects on real people.
              </p>
            </article>
          </div>
        </section>

        <section className="section evidence-section" id="evidence">
          <div className="section-heading split-heading">
            <div>
              <p className="section-number">03 · Unified evidence map</p>
              <h2>One timeline. No false composite.</h2>
            </div>
            <p>
              APE, MASK, DisElect, human persuasion studies, and harmful-manipulation studies answer
              different questions. They belong on one map, but their scores must not be averaged.
            </p>
          </div>
          {benchmarks.length > 0 && <EvidenceMap benchmarks={benchmarks} />}
          {maskResults.length > 0 && <MaskChart results={maskResults} />}
        </section>

        <section className="section models-section" id="models">
          <div className="section-heading split-heading">
            <div>
              <p className="section-number">04 · Evaluation panel</p>
              <h2>Open-weight releases ≥100B</h2>
            </div>
            <p>
              This is the frozen candidate universe, not a leaderboard. Historical anchors stay
              visible even when OpenRouter no longer serves them. Exact routes, providers, reasoning
              modes, and dates will be pinned before any new run.
            </p>
          </div>
          {models.length > 0 && <ModelPanel models={models} />}
        </section>

        <section className="section methods-section" id="methods">
          <div className="section-heading split-heading">
            <div>
              <p className="section-number">05 · Methods</p>
              <h2>The claim must follow the measurement.</h2>
            </div>
            <p>
              The project uses release date descriptively. It does not estimate a causal rate of
              progress, and it never treats model-to-model differences as proof that time caused
              capability or safeguard changes.
            </p>
          </div>

          <div className="method-principles">
            <article>
              <span>Unit</span>
              <h3>Snapshot × endpoint × condition × item × seed</h3>
              <p>
                Model aliases are insufficient. Provider, canonical route, guardrails, reasoning
                mode, parameters, errors, latency, tokens, and cost are part of the observation.
              </p>
            </article>
            <article>
              <span>Comparison</span>
              <h3>Native metrics, fixed protocol</h3>
              <p>
                Points connect only inside a comparable family, benchmark version, judge, item set,
                and deployment condition. Missing results never become zero.
              </p>
            </article>
            <article>
              <span>Validation</span>
              <h3>Humans audit the judges</h3>
              <p>
                A blinded 10–15% sample, two coders, adjudication, class-level F1, and uncertainty by
                item are required before a project rerun is presented as more than exploratory.
              </p>
            </article>
          </div>

          <div className="causal-chain-block">
            <p className="mini-label">Research chain</p>
            <ol className="causal-chain">
              <li>AI capability</li>
              <li>Controlling actor</li>
              <li>Influence vector</li>
              <li>Target</li>
              <li>Belief, attention, trust, behaviour, or dependency</li>
              <li>Agency transfer</li>
              <li>Concentration of power</li>
              <li>Democratic harm</li>
              <li>Mitigation</li>
            </ol>
            <p>
              Wave 0 measures only parts of the first link and selected safeguard conditions around
              it. Evidence from later links is reviewed separately; it is never inferred from a
              compliance score.
            </p>
          </div>

          <div className="roadmap">
            <article><span>Now</span><h3>Published baseline</h3><p>DisElect aggregate labels, model manifest, provenance, and measurement boundary.</p></article>
            <article><span>Wave 1</span><h3>Fixed DisElect adaptation</h3><p>DeepSeek release series, stratified items, benign controls, pinned routing, and human-validated judge.</p></article>
            <article><span>Wave 2</span><h3>APE Turn 1</h3><p>Harmful attempt, refusal, evasion, and provider block—kept separate from efficacy.</p></article>
            <article><span>Wave 3</span><h3>MASK public-set rerun</h3><p>Honesty, lying, evasion, and accuracy, only after dataset licensing and scorer validation.</p></article>
          </div>
        </section>

        <section className="section release-section" id="data">
          <div className="section-heading split-heading">
            <div>
              <p className="section-number">06 · Responsible release</p>
              <h2>Reproducible without being operational.</h2>
            </div>
            <p>
              Public artifacts include code, manifests, aggregate labels, provenance, protocol
              hashes, uncertainty, errors, and costs. Raw harmful generations, targeting material,
              and operational election content remain restricted.
            </p>
          </div>
          <div className="release-links">
            <a href={`${REPOSITORY_URL}/tree/main/data`} target="_blank" rel="noreferrer">Data ledger ↗</a>
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
            A research preview developed for Miguel Guerrero’s Cambridge ERA fellowship. This is an
            independent work in progress, not an institutional benchmark or a claim of demonstrated
            electoral harm.
          </p>
        </div>
        <div>
          <span>Version 0.1.0 · 10 August 2026</span>
          <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">Source and issues ↗</a>
        </div>
      </footer>
    </>
  );
}

export default App;
