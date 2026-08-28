import { useEffect, useMemo, useState } from "react";
import { AgenticInfluenceChart } from "./components/AgenticInfluenceChart";
import { EvidenceMap } from "./components/EvidenceMap";
import { FrontierTimeline } from "./components/FrontierTimeline";
import { LiteratureReview } from "./components/LiteratureReview";
import { LongitudinalChart } from "./components/LongitudinalChart";
import { MaskChart } from "./components/MaskChart";
import { ModelPanel } from "./components/ModelPanel";
import {
  AttemptRateGraphic,
  CdeTopology,
  ElectionEvidenceMatrix,
  EvidenceRiftVisual,
  MechanismGallery,
  OnePageBriefPreview,
  PartIEvidenceArchitecture,
  PolicyPortfolio,
  PosterPreview,
} from "./components/ProgrammeVisuals";
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
import {
  artifactById,
  electionCases,
  explainers,
  outputs,
  paperAbstract,
  paperSections,
  partById,
  policyPriorities,
  programmeManifest,
  programmeUpdates,
} from "./programme";
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
const ELECTION_INDEX_URL = "https://huggingface.co/datasets/apol/ai-election-manipulation-cases";
const POLICY_ATLAS_URL = "https://huggingface.co/datasets/apol/agency-transfer-policy-atlas";
const LAB_URL = "https://agency-transfer-lab.miguelguerrero.eu";

type PageKey =
  | "home"
  | "research"
  | "part-i"
  | "part-ii"
  | "part-ii-evidence"
  | "part-ii-testing"
  | "part-iii"
  | "part-iv"
  | "paper"
  | "outputs"
  | "explainers"
  | "updates"
  | "about";

type DataKey =
  | "frontierModels"
  | "frontierObservations"
  | "testingNotes"
  | "diselect"
  | "agentic"
  | "mask"
  | "manifest"
  | "benchmarks";

const route = (path = "") => `${import.meta.env.BASE_URL}${path.replace(/^\/+/, "")}`;
const external = (href: string) => /^https?:\/\//.test(href);
const errorMessage = (reason: unknown) =>
  reason instanceof Error ? reason.message : "Unknown data-loading error";

const pageFromPath = (): PageKey => {
  const base = import.meta.env.BASE_URL.replace(/\/$/, "");
  let path = window.location.pathname;
  if (base && path.startsWith(base)) path = path.slice(base.length);
  path = path.replace(/index\.html$/, "").replace(/^\/+|\/+$/g, "");

  if (path === "research") return "research";
  if (path === "research/part-i") return "part-i";
  if (path === "research/part-ii") return "part-ii";
  if (path === "research/part-ii/evidence" || path === "evidence") return "part-ii-evidence";
  if (path === "research/part-ii/testing" || path === "testing") return "part-ii-testing";
  if (path === "research/part-iii") return "part-iii";
  if (path === "research/part-iv") return "part-iv";
  if (path === "paper") return "paper";
  if (path === "outputs") return "outputs";
  if (path === "explainers") return "explainers";
  if (path === "updates") return "updates";
  if (path === "about") return "about";
  return "home";
};

const pageMetadata: Record<PageKey, { title: string; description: string; canonical: string }> = {
  home: {
    title: "Agency Transfer · Frontier AI, harmful manipulation, and democratic power",
    description: "A maintained research programme on frontier AI, harmful manipulation, election security, agency transfer, and concentrated democratic power.",
    canonical: "",
  },
  research: {
    title: "Research programme · Agency Transfer",
    description: "Four connected research parts examine operationalisation, capability measurement, election evidence, and policy intervention.",
    canonical: "research/",
  },
  "part-i": {
    title: "Part I · From output to operationalisation · Agency Transfer",
    description: "Served-system evidence, red-team objectives, forensic traces, research tools, and the boundary between planning output and real action.",
    canonical: "research/part-i/",
  },
  "part-ii": {
    title: "Part II · Capability and measurement · Agency Transfer",
    description: "The Frontier Evaluation Registry and recovered APE-120 audit preserve benchmark-native outcomes, route evidence, missingness, and claim ceilings.",
    canonical: "research/part-ii/",
  },
  "part-ii-evidence": {
    title: "Part II evidence · Agency Transfer",
    description: "What each manipulation-relevant evaluation instrument can and cannot establish.",
    canonical: "research/part-ii/evidence/",
  },
  "part-ii-testing": {
    title: "Part II testing · Agency Transfer",
    description: "Direct tests, route integrity, exclusions, validation status, and the confirmatory publication gate.",
    canonical: "research/part-ii/testing/",
  },
  "part-iii": {
    title: "Part III · Election evidence · Agency Transfer",
    description: "A claim-level evidence index showing where public election records are strong and where exposure and effect remain unresolved.",
    canonical: "research/part-iii/",
  },
  "part-iv": {
    title: "Part IV · Policy evidence · Agency Transfer",
    description: "A causal policy atlas mapping interventions, authority, mechanism evidence, effect evidence, maturity, rights risks, and research gaps.",
    canonical: "research/part-iv/",
  },
  paper: {
    title: "Harmful Manipulation and Election Security · Working paper",
    description: "Current web working edition of the Capability–Deployment–Effect Gap flagship paper.",
    canonical: "paper/",
  },
  outputs: {
    title: "Research outputs · Agency Transfer",
    description: "The flagship paper, white paper, brief, poster, datasets, research tools, methods, and code.",
    canonical: "outputs/",
  },
  explainers: {
    title: "Explainers · Agency Transfer",
    description: "Synthetic scenarios and visual explainers of AI-mediated influence mechanisms and their evidentiary limits.",
    canonical: "explainers/",
  },
  updates: {
    title: "Programme updates · Agency Transfer",
    description: "Dated changes to the evidence, methods, datasets, publications, and claim ceilings.",
    canonical: "updates/",
  },
  about: {
    title: "About the programme · Agency Transfer",
    description: "Programme scope, author, fellowship context, evidence policy, citation, and responsible release.",
    canonical: "about/",
  },
};

function usePageMetadata(page: PageKey) {
  useEffect(() => {
    const metadata = pageMetadata[page];
    document.title = metadata.title;
    const description = document.querySelector<HTMLMetaElement>('meta[name="description"]');
    if (description) description.content = metadata.description;
    const canonical = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
    if (canonical) canonical.href = `https://miguelguerrero.eu/agencytransfer/${metadata.canonical}`;
    const ogTitle = document.querySelector<HTMLMetaElement>('meta[property="og:title"]');
    if (ogTitle) ogTitle.content = metadata.title;
    const ogDescription = document.querySelector<HTMLMetaElement>('meta[property="og:description"]');
    if (ogDescription) ogDescription.content = metadata.description;
    const ogUrl = document.querySelector<HTMLMetaElement>('meta[property="og:url"]');
    if (ogUrl) ogUrl.content = `https://miguelguerrero.eu/agencytransfer/${metadata.canonical}`;
  }, [page]);
}

function ProgrammeStatus({ concise = false }: { concise?: boolean }) {
  return (
    <div className={`programme-status${concise ? " programme-status--concise" : ""}`} aria-label="Publication status">
      <strong>WORKING RESEARCH PROGRAMME</strong>
      <span>Evidence freeze · 28 August 2026</span>
      {!concise ? <span>Independent research · sole author · not peer reviewed</span> : null}
    </div>
  );
}

const navForPage = (page: PageKey) => {
  if (page === "home") return "programme";
  if (["research", "part-i", "part-ii", "part-ii-evidence", "part-ii-testing", "part-iii", "part-iv"].includes(page)) return "research";
  return page;
};

function SiteHeader({ page }: { page: PageKey }) {
  const active = navForPage(page);
  const navigation = [
    { id: "programme", label: "Programme", href: route() },
    { id: "research", label: "Research", href: route("research/") },
    { id: "paper", label: "Paper", href: route("paper/") },
    { id: "outputs", label: "Outputs", href: route("outputs/") },
    { id: "explainers", label: "Explainers", href: route("explainers/") },
    { id: "about", label: "About", href: route("about/") },
  ];

  return (
    <header className="programme-header">
      <a className="programme-wordmark" href={route()} aria-label="Agency Transfer Research Programme home">
        <span aria-hidden="true">AT</span>
        <span><strong>Agency Transfer</strong><small>Research Programme</small></span>
      </a>
      <nav aria-label="Primary navigation">
        {navigation.map((item) => (
          <a key={item.id} href={item.href} aria-current={active === item.id ? "page" : undefined}>{item.label}</a>
        ))}
      </nav>
    </header>
  );
}

function SiteFooter() {
  return (
    <footer className="programme-footer">
      <div className="programme-footer__lead">
        <strong>Agency Transfer Research Programme</strong>
        <p>Frontier AI, harmful manipulation, election security, and concentrated democratic power.</p>
        <span>Miguel Guerrero · ERA:AI Summer Research Fellowship · Cambridge · 2026</span>
      </div>
      <div className="programme-footer__links">
        <a href={route("paper/")}>Working paper</a>
        <a href={route("research/")}>Research parts</a>
        <a href={route("updates/")}>Updates</a>
        <a href={`${REPOSITORY_URL}/blob/main/RESPONSIBLE_RELEASE.md`} target="_blank" rel="noreferrer">Responsible release ↗</a>
        <a href={`${REPOSITORY_URL}/blob/main/CITATION.cff`} target="_blank" rel="noreferrer">Citation ↗</a>
        <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">Source ↗</a>
      </div>
      <div className="programme-footer__boundary">
        The programme does not establish a closed adaptive influence loop, authentic audience exposure, durable agency erosion, a prevalence estimate, or an AI-attributable electoral effect.
      </div>
    </footer>
  );
}

function PageIntro({
  eyebrow,
  title,
  standfirst,
  children,
}: {
  eyebrow: string;
  title: string;
  standfirst: string;
  children?: React.ReactNode;
}) {
  return (
    <section className="programme-page-intro">
      <ProgrammeStatus />
      <p className="programme-eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      <p className="programme-standfirst">{standfirst}</p>
      {children}
    </section>
  );
}

function ClaimCeiling({ children }: { children: React.ReactNode }) {
  return (
    <aside className="claim-ceiling">
      <strong>Claim ceiling</strong>
      <p>{children}</p>
    </aside>
  );
}

function SectionHeading({ number, title, note }: { number: string; title: string; note?: string }) {
  return (
    <div className="programme-section-heading">
      <div><span>{number}</span><h2>{title}</h2></div>
      {note ? <p>{note}</p> : null}
    </div>
  );
}

function ArrowLink({ href, children, externalLink = false }: { href: string; children: React.ReactNode; externalLink?: boolean }) {
  return (
    <a className="arrow-link" href={externalLink ? href : route(href)} target={externalLink ? "_blank" : undefined} rel={externalLink ? "noreferrer" : undefined}>
      {children}<span aria-hidden="true">↗</span>
    </a>
  );
}

function OutputCard({ output, compact = false }: { output: (typeof outputs)[number]; compact?: boolean }) {
  const isExternal = "external" in output && output.external;
  return (
    <article className={`output-card${compact ? " output-card--compact" : ""}`}>
      <div className="output-card__meta"><span>{output.type}</span><span>{output.date}</span></div>
      <h3>{output.title}</h3>
      <p className="output-card__subtitle">{output.subtitle}</p>
      <p>{output.description}</p>
      <div className="output-card__footer">
        <span>{output.status}</span>
        <a href={isExternal ? output.href : route(output.href)} target={isExternal ? "_blank" : undefined} rel={isExternal ? "noreferrer" : undefined}>
          Open <span aria-hidden="true">↗</span>
        </a>
      </div>
    </article>
  );
}

function PartCard({ id }: { id: "part-i" | "part-ii" | "part-iii" | "part-iv" }) {
  const part = partById(id);
  const slug = id.replace("part-", "part-");
  return (
    <article className={`part-card part-card--${id}`}>
      <div className="part-card__number">{part.number}</div>
      <p>PART {part.number}</p>
      <h3>{part.title}</h3>
      <dl>
        <div><dt>Question</dt><dd>{part.question}</dd></div>
        <div><dt>Strongest current finding</dt><dd>{part.strongest_supported_claim}</dd></div>
        <div><dt>Boundary</dt><dd>{part.claim_ceiling}</dd></div>
      </dl>
      <a href={route(`research/${slug}/`)}>Read Part {part.number} <span aria-hidden="true">→</span></a>
    </article>
  );
}

function HomePage() {
  return (
    <main id="main-content" className="programme-main">
      <section className="programme-hero">
        <ProgrammeStatus />
        <div className="programme-hero__grid">
          <div>
            <p className="programme-eyebrow">Frontier AI · Harmful manipulation · Democratic power</p>
            <h1>The next Cambridge Analytica will be a system.</h1>
            <p className="programme-hero__dek">
              Frontier AI can join generation, personal context, action, distribution, and feedback into influence infrastructure before institutions can independently measure or govern its downstream effects.
            </p>
            <p className="programme-hero__boundary">
              The risk is not only false content. It is concentrated control over the systems that shape attention, trust, participation, dependency, and choice—and over the evidence needed to contest that influence.
            </p>
            <div className="programme-actions">
              <a className="programme-button programme-button--primary" href={route("paper/")}>Read the working paper</a>
              <a className="programme-button" href={route("research/")}>Explore the research</a>
            </div>
          </div>
          <EvidenceRiftVisual />
        </div>
      </section>

      <section className="programme-section programme-thesis">
        <SectionHeading number="01" title="The risk is in the joins" note="Capability is not deployment. Deployment is not exposure. Exposure is not effect." />
        <div className="programme-prose programme-prose--two-column">
          <p>
            Cambridge Analytica’s durable warning was architectural. Data, political purpose, targeting, content, distribution, and measurement could be joined under private control before citizens or institutions could inspect the influence process or estimate its final effect.
          </p>
          <p>
            Frontier AI may add persistent context, natural conversation, synthetic identities, planning, tool use, and feedback. The present research does not observe a closed adaptive system operating against real people. It identifies the missing bridges and the conditions under which influence capacity could become more integrated and concentrated.
          </p>
        </div>
        <CdeTopology />
      </section>

      <section className="programme-section">
        <SectionHeading number="02" title="Four connected research parts" note="Different evidence streams. One causal topology. No synthetic score." />
        <div className="part-grid">
          <PartCard id="part-i" />
          <PartCard id="part-ii" />
          <PartCard id="part-iii" />
          <PartCard id="part-iv" />
        </div>
      </section>

      <section className="programme-section programme-evidence-state">
        <SectionHeading number="03" title="What is known. What is inferred. What remains open." />
        <div className="evidence-grade-grid">
          {programmeManifest.evidence_grades.map((grade) => (
            <article key={grade.id} className={`evidence-grade evidence-grade--${grade.id}`}>
              <span>{grade.label}</span>
              <p>{grade.definition}</p>
            </article>
          ))}
        </div>
        <p className="programme-note">These categories describe epistemic status, not severity.</p>
      </section>

      <section className="programme-section">
        <SectionHeading number="04" title="Selected outputs" note="One programme, several forms. Each output answers a different reading need." />
        <div className="output-grid">
          {outputs.slice(0, 8).map((output) => <OutputCard output={output} key={output.id} compact />)}
        </div>
        <div className="programme-section-link"><ArrowLink href="outputs/">View all outputs</ArrowLink></div>
      </section>

      <section className="programme-section programme-explainer-strip">
        <SectionHeading number="05" title="Explain the mechanism, not the spectacle" note="Synthetic scenarios illustrate possible joins. They are not observations of real campaigns or effects." />
        <div className="explainer-strip">
          {explainers.map((item) => (
            <article key={item.id}>
              <span>{item.type}</span>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
              <a href={route(`explainers/#${item.id}`)}>View explainer <span aria-hidden="true">→</span></a>
            </article>
          ))}
        </div>
      </section>

      <section className="programme-section programme-current-state">
        <SectionHeading number="06" title="A programme, not a finished claim" />
        <blockquote>
          The flagship’s contribution is to hold four research streams together without allowing one to borrow the strongest result of another.
        </blockquote>
        <div className="programme-update-list programme-update-list--compact">
          {programmeUpdates.slice(0, 3).map((update) => (
            <article key={`${update.date}-${update.title}`}>
              <time>{update.date}</time><h3>{update.title}</h3><p>{update.body}</p>
            </article>
          ))}
        </div>
        <div className="programme-section-link"><ArrowLink href="updates/">View the programme log</ArrowLink></div>
      </section>
    </main>
  );
}

function ResearchPage() {
  return (
    <main id="main-content" className="programme-main">
      <PageIntro
        eyebrow="Research programme"
        title="Four parts. Different evidence. One systems problem."
        standfirst="The programme does not force capability tests, field incidents, and policy records into one metric. It uses them to locate where evidence accumulates, where it thins, and which missing bridge defines the next study."
      />
      <section className="programme-section programme-section--first">
        <CdeTopology />
      </section>
      <section className="programme-section">
        <div className="part-grid part-grid--research">
          <PartCard id="part-i" />
          <PartCard id="part-ii" />
          <PartCard id="part-iii" />
          <PartCard id="part-iv" />
        </div>
      </section>
      <section className="programme-section programme-claim-rule">
        <SectionHeading number="Method" title="Claim ceilings keep the parts honest" />
        <div className="programme-prose programme-prose--two-column">
          <p>A claim ceiling records the strongest conclusion the evidence can support: the observed node, unit, configuration, provenance, comparator, licensed inference, missing bridge, and claims expressly not supported.</p>
          <p>Claim ceilings constrain what an institution may say. They do not automatically determine what it may do. A mechanism-matched, lawful, proportionate, reviewable, and reversible response may precede proof of changed votes.</p>
        </div>
      </section>
    </main>
  );
}

function PartIPage() {
  const part = partById("part-i");
  return (
    <main id="main-content" className="programme-main">
      <PageIntro
        eyebrow="Part I · From output to operationalisation"
        title="Planning output crossed a tactical-refusal boundary. It never became deployment."
        standfirst="Part I records a broader paired red-team programme, protocol-generating probes, a deeply instrumented forensic subset, and a separate access-to-control methods study. These units answer different questions and are not added into one sample size."
      >
        <ClaimCeiling>{part.claim_ceiling}</ClaimCeiling>
      </PageIntro>

      <section className="programme-section programme-section--first">
        <SectionHeading number="01" title="Part I is broader than the forensic subset" note="Breadth, protocol development, and forensic depth are complementary views—not additive counts." />
        <PartIEvidenceArchitecture />
      </section>

      <section className="programme-section">
        <SectionHeading number="02" title="What the trace record supports" />
        <div className="finding-grid">
          <article><span>Established</span><h3>Operationally structured text</h3><p>Completed outputs named possible audiences, channels, sequencing, mobilisation or demobilisation objectives, measurement, and proposed adaptation under the recorded conditions.</p></article>
          <article><span>Mixed result</span><h3>Tactical constraint, broader assistance</h3><p>In one session, the route refused or redirected some explicitly deceptive tactics while continuing to provide broader campaign-planning material. A refusal rate alone would miss that trajectory.</p></article>
          <article><span>Not established</span><h3>Action, reach, or effect</h3><p>The route did not research audiences, segment voters, run feedback, distribute content, or expose a real person. Tools were disabled and no live action occurred.</p></article>
        </div>
        <div className="route-contrast">
          <div><strong>10 / 10</strong><span>official hosted objectives refused in the paired record</span></div>
          <div aria-hidden="true">≠</div>
          <div><strong>0 / 10</strong><span>safeguard-reduced objectives refused in the paired record</span></div>
          <p>This contrast is descriptive. The public record does not provide same-checkpoint route equivalence, complete matched traces, blinded scoring, or a causal estimate of safeguard removal.</p>
        </div>
      </section>

      <section className="programme-section programme-mechanisms">
        <SectionHeading number="03" title="The principal mechanisms" note="Conceptual illustrations. They show where control can join; they do not claim that a real operation completed the chain." />
        <MechanismGallery />
      </section>

      <section className="programme-section">
        <SectionHeading number="04" title="Research artifacts" />
        <div className="artifact-list">
          <article>
            <p>Research tool</p><h3>Agency Transfer Lab</h3>
            <p>Validates control semantics, replay, persistence, migration, export integrity, and tamper detection. It does not measure persuasion, behaviour change, agency transfer, actor uplift, or electoral impact.</p>
            <ArrowLink href={LAB_URL} externalLink>Open the Lab</ArrowLink>
          </article>
          <article>
            <p>Methods record</p><h3>From open weights to reproducible intervention</h3>
            <p>The access-to-control work documents technical conversion, failed and incomplete attempts, evidence custody, and the distance between compute access and a reloadable behavioural artifact.</p>
            <ArrowLink href={`${REPOSITORY_URL}/tree/main/part1b`} externalLink>Inspect public methods</ArrowLink>
          </article>
          <article>
            <p>Controlled evidence</p><h3>Private validation record</h3>
            <p>Raw outputs, grader traces, reviewer mappings, credentials, and controlled evidence remain private. The public site reports bounded aggregates and responsible-release decisions, not offensive material.</p>
            <ArrowLink href={`${REPOSITORY_URL}/blob/main/RESPONSIBLE_RELEASE.md`} externalLink>Read release boundary</ArrowLink>
          </article>
        </div>
      </section>

      <section className="programme-section">
        <SectionHeading number="05" title="Synthetic explainers" note="The films make the mechanism legible. They do not extend the evidence." />
        <div className="explainer-strip">
          {explainers.map((item) => (
            <article key={item.id}>
              <span>{item.subtitle}</span><h3>{item.title}</h3><p>{item.description}</p>
              <a href={route(`explainers/#${item.id}`)}>Open explainer <span aria-hidden="true">→</span></a>
            </article>
          ))}
        </div>
      </section>

      <section className="programme-section programme-next-study">
        <SectionHeading number="Next study" title="Observe action rather than prose" />
        <p>Use named systems, frozen routes, synthetic tools, permission boundaries, state changes, resistance, revocation, rollback, and a non-AI operator baseline. Only then can the programme test whether frontier AI reduces the expertise, time, cost, or coordination required for an influence operation.</p>
      </section>
    </main>
  );
}

interface PartIIProps {
  models: FrontierModel[];
  observations: FrontierObservation[];
  loading: boolean;
  error: string;
}

function PartIIPage({ models, observations, loading, error }: PartIIProps) {
  return (
    <main id="main-content" className="programme-main">
      <PageIntro
        eyebrow="Part II · Capability and measurement"
        title="The attempt rate is high. The measurement stack is not confirmatory."
        standfirst="Part II combines a six-instrument Evaluation Registry with a recovered APE-120 audit. Its strongest result is not a leaderboard. It is a record of broad descriptive activity, route-conditioned observability, missingness, and a prespecified gate that no served condition reached."
      >
        <ClaimCeiling>No pooled manipulation score, no human persuasion estimate, no model safety ranking, and no defensible longitudinal frontier trend.</ClaimCeiling>
      </PageIntro>

      <section className="programme-section programme-section--first">
        <SectionHeading number="01" title="Recovered primary-research audit" note="The headline number and the failed confirmatory gate belong together." />
        <AttemptRateGraphic />
      </section>

      <section className="programme-section programme-registry" id="registry">
        <SectionHeading number="02" title="Frontier Evaluation Registry" note="One release map. Separate constructs. Missing is never zero." />
        {error ? <p className="inline-data-error" role="alert">Some registry data could not load: {error}</p> : null}
        {models.length > 0 && observations.length > 0 ? (
          <FrontierTimeline models={models} observations={observations} />
        ) : loading ? (
          <p className="loading-message" aria-live="polite">Loading the release registry…</p>
        ) : (
          <p className="empty-message">No verified release series is available in this build.</p>
        )}
        <details className="hero-method-note">
          <summary>How to read the registry</summary>
          <div>
            <p>Each view shows one instrument’s native outcome. Measures with different protocols, prompts, judges, denominators, or constructs are not combined.</p>
            <p>Hollow release marks mean that no comparable observation is available in the selected view—missing, never zero.</p>
            <a href={`${REPOSITORY_URL}/blob/main/METHODS.md`} target="_blank" rel="noreferrer">Methods and comparability limits ↗</a>
          </div>
        </details>
      </section>

      <section className="programme-section part-ii-links">
        <article><p>Evidence</p><h3>What each instrument can—and cannot—claim</h3><p>Literature, construct map, agentic execution, deception, election-operation compliance, and access conditions remain separate.</p><a href={route("research/part-ii/evidence/")}>Open evidence <span aria-hidden="true">→</span></a></article>
        <article><p>Testing</p><h3>Confirmatory results only</h3><p>Exploratory runs stay in the audit trail. A comparison appears publicly only after route integrity, frozen protocol, human validation, and uncertainty checks pass.</p><a href={route("research/part-ii/testing/")}>Open testing <span aria-hidden="true">→</span></a></article>
        <article><p>Data</p><h3>Aggregate and provenance mirror</h3><p>The public dataset contains aggregate results and source metadata. Raw harmful generations are excluded.</p><a href={HUGGING_FACE_URL} target="_blank" rel="noreferrer">Open Hugging Face <span aria-hidden="true">↗</span></a></article>
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

function PartIIEvidencePage({ benchmarks, agenticResults, maskResults, diselectResults, models, errors }: EvidenceProps) {
  return (
    <main id="main-content">
      <section className="page-intro">
        <ProgrammeStatus />
        <p className="section-number">Part II · Evidence</p>
        <h1>What each instrument can—and cannot—claim</h1>
        <p>No source measures harmful manipulation end to end. The literature separately observes attempted persuasion, safeguards, task execution, persuasive effect, deception, access, or deployment conditions. The registry preserves those native outcomes rather than collapsing them into one score.</p>
      </section>

      <section className="section literature-section" id="literature">
        <div className="section-heading split-heading"><div><p className="section-number">01 · Literature review</p><h2>Papers behind the measurement model</h2></div><p>Primary sources are grouped by the construct they actually observe. Human-efficacy studies inform interpretation but are not converted into model scores.</p></div>
        <LiteratureReview />
      </section>

      <section className="section evidence-section" id="map">
        <div className="section-heading split-heading"><div><p className="section-number">02 · Evidence map</p><h2>One timeline, separate constructs</h2></div><p>Native benchmark outcomes retain their own protocols, denominators, and directions.</p></div>
        {errors.benchmarks ? <p className="inline-data-error" role="alert">The evidence registry could not load: {errors.benchmarks}</p> : null}
        {benchmarks.length > 0 ? <EvidenceMap benchmarks={benchmarks} /> : null}
      </section>

      <section className="section chart-section" id="agentic">
        <div className="section-heading split-heading"><div><p className="section-number">03 · Agentic execution</p><h2>Campaign workflows, not human effects</h2></div><p>Controlled simulated social-platform workflows measure task completion, not authentic exposure, default safeguards, or real-world persuasion.</p></div>
        {errors.agentic ? <p className="inline-data-error" role="alert">Agentic evidence could not load: {errors.agentic}</p> : null}
        {agenticResults.length > 0 ? <AgenticInfluenceChart results={agenticResults} /> : null}
      </section>

      <section className="section chart-section" id="deception">
        <div className="section-heading split-heading"><div><p className="section-number">04 · Deception</p><h2>Honesty under pressure</h2></div><p>MASK concerns the model’s own output under belief conflict. It is manipulation-relevant, but it does not observe a target’s beliefs, choices, or agency.</p></div>
        {errors.mask ? <p className="inline-data-error" role="alert">MASK evidence could not load: {errors.mask}</p> : null}
        {maskResults.length > 0 ? <MaskChart results={maskResults} /> : null}
      </section>

      <section className="section historical-section" id="diselect">
        <div className="section-heading split-heading"><div><p className="section-number">05 · Election operations</p><h2>Historical harmful compliance</h2></div><p>DisElect measures response generation under one protocol—not campaign success, vote change, or democratic harm.</p></div>
        {errors.diselect ? <p className="inline-data-error" role="alert">DisElect evidence could not load: {errors.diselect}</p> : null}
        {diselectResults.length > 0 ? <LongitudinalChart results={diselectResults} /> : null}
      </section>

      <SystemsResearchSection />

      <section className="section models-section" id="access">
        <div className="section-heading split-heading"><div><p className="section-number">06 · Access</p><h2>Capability can diffuse through weights and APIs</h2></div><p>Parameter count is an inclusion rule, not a capability score. Open-weight and hosted frontier releases remain distinct populations.</p></div>
        {errors.manifest ? <p className="inline-data-error" role="alert">The access manifest could not load: {errors.manifest}</p> : null}
        {models.length > 0 ? <ModelPanel models={models} /> : null}
      </section>
    </main>
  );
}

function PartIITestingPage({ notes, error }: { notes: TestingNote[]; error?: string }) {
  return (
    <main id="main-content">
      <section className="page-intro testing-page-intro">
        <ProgrammeStatus />
        <p className="section-number">Part II · Testing</p>
        <h1>Confirmatory results only</h1>
        <p>Exploratory runs stay in the audit trail. A comparison appears here only after route integrity, a frozen protocol, blinded human validation, uncertainty checks, and the public-release gate pass.</p>
      </section>
      {error ? <p className="inline-data-error standalone-error" role="alert">Testing notes could not load: {error}</p> : null}
      <TestingSection notes={notes} />
    </main>
  );
}

function PartIIIPage() {
  const part = partById("part-iii");
  const metrics = part.headline_metrics;
  return (
    <main id="main-content" className="programme-main">
      <PageIntro
        eyebrow="Part III · Election evidence and the effect gap"
        title="Public records document operations more readily than effects."
        standfirst="The Election Evidence Index separates occurrence, mechanism, attribution, distribution, authentic exposure, human effect, electoral effect, and institutional response. It is a purposive evidence corpus—not a prevalence estimate or census."
      >
        <ClaimCeiling>{part.claim_ceiling}</ClaimCeiling>
      </PageIntro>

      <section className="programme-section programme-section--first">
        <SectionHeading number="01" title="Read the counts in the right order" />
        <div className="evidence-funnel" aria-label="Election Evidence Index count layers">
          <div><strong>{metrics.relational_rows.toLocaleString()}</strong><span>relational rows</span></div>
          <i aria-hidden="true">→</i>
          <div><strong>{metrics.catalogue_entries}</strong><span>catalogue entries</span></div>
          <i aria-hidden="true">→</i>
          <div><strong>{metrics.core_records}</strong><span>core records</span></div>
          <i aria-hidden="true">→</i>
          <div><strong>{metrics.incident_eligible_records}</strong><span>incident-eligible</span></div>
          <i aria-hidden="true">→</i>
          <div><strong>{metrics.documented_manipulation_records}</strong><span>documented manipulation</span></div>
        </div>
        <p className="programme-note">Relational rows and catalogue entries are not incident counts. The public release contains six documented-manipulation records.</p>
      </section>

      <section className="programme-section">
        <SectionHeading number="02" title="The record narrows before authentic exposure and effect" note="Engagement is not belief. Views are not unique voters. Institutional response is not a voter-level effect estimate." />
        <ElectionEvidenceMatrix />
      </section>

      <section className="programme-section">
        <SectionHeading number="03" title="Selected cases" />
        <div className="case-note-grid">
          {electionCases.map((item) => (
            <article key={item.case}><h3>{item.case}</h3><p>{item.note}</p></article>
          ))}
        </div>
      </section>

      <section className="programme-section programme-field-lessons">
        <SectionHeading number="04" title="What the field record changes" />
        <div className="finding-grid">
          <article><span>Noisy operations</span><h3>Visibility can exceed materiality</h3><p>Floods of synthetic content, contradictory narratives, and coordinated amplification may leave many traces while their authentic exposure and effect remain difficult to identify.</p></article>
          <article><span>Quiet operations</span><h3>Low visibility can hide strategic reach</h3><p>Narrow targeting through private messaging, local communities, or trusted identities may avoid public detection. The Index cannot estimate how common or consequential those operations are.</p></article>
          <article><span>Decision windows</span><h3>Timing changes correctability</h3><p>False procedural information released in the final hours may exploit a period in which meaningful correction is impossible, even when durable belief change is not measured.</p></article>
        </div>
      </section>

      <section className="programme-section programme-data-cta">
        <div><p>Public dataset</p><h2>AI, Elections and Agency Transfer Evidence Index</h2><p>Release v0.4.4 · research cutoff 12 August 2026 · claim-level, source-linked records.</p></div>
        <ArrowLink href={ELECTION_INDEX_URL} externalLink>Open the dataset</ArrowLink>
      </section>
    </main>
  );
}

function PartIVPage() {
  const part = partById("part-iv");
  return (
    <main id="main-content" className="programme-main">
      <PageIntro
        eyebrow="Part IV · Policy evidence and intervention"
        title="Policy supply is abundant. Credible effect evidence is scarce."
        standfirst="The Policy Atlas asks where an intervention could interrupt the pathway, who can implement it, what authority exists, which endpoint has actually been measured, and what rights, displacement, or concentration risks the control itself creates."
      >
        <ClaimCeiling>{part.claim_ceiling}</ClaimCeiling>
      </PageIntro>

      <section className="programme-section programme-section--first">
        <SectionHeading number="01" title="A broad portfolio, mostly upstream" />
        <PolicyPortfolio />
      </section>

      <section className="programme-section">
        <SectionHeading number="02" title="Govern the mechanism already visible" />
        <div className="policy-priority-grid">
          {policyPriorities.map((priority) => (
            <article key={priority.number}><span>{priority.number}</span><h3>{priority.title}</h3><p>{priority.body}</p></article>
          ))}
        </div>
      </section>

      <section className="programme-section policy-baseline">
        <SectionHeading number="03" title="Three manipulation baselines should not be conflated" />
        <div className="baseline-grid">
          <article><p>Programme analytic test</p><h3>Reflective and contestable choice</h3><p>Influence becomes manipulation when opacity, deception, vulnerability exploitation, asymmetry, dependency, or control of the decision environment degrades reflective and contestable choice.</p><span>Normative analytic definition; not proof of occurrence, harm, liability, or effect.</span></article>
          <article><p>EU AI Act Article 5</p><h3>A binding, conjunctive prohibition</h3><p>Specified subliminal, purposefully manipulative or deceptive techniques, and exploitation of listed vulnerabilities are prohibited only where the cumulative statutory conditions are met.</p><span>Not a general ban on persuasion or political manipulation.</span></article>
          <article><p>GPAI Code Appendix 1.4(4)</p><h3>A systemic-risk baseline</h3><p>The Code frames harmful manipulation around strategic distortion of behaviour or beliefs through persuasion, deception, or personalised targeting—especially multi-turn or difficult-to-detect influence at scale or against high-stakes decision-makers.</p><span>Voluntary Article 55 compliance route; not a standalone prohibition or proof that mitigation works.</span></article>
        </div>
      </section>

      <section className="programme-section programme-design-test">
        <SectionHeading number="04" title="Design for democratic observability" />
        <div className="design-test-line">
          {['Visible', 'Divisible', 'Auditable', 'Interruptible', 'Reversible', 'Contestable'].map((item, index) => (
            <div key={item}><span>{String(index + 1).padStart(2, '0')}</span><strong>{item}</strong></div>
          ))}
        </div>
        <p>These are governance objectives, not findings that one design has proved effective. Evidence custody, audit, and interruption also create privacy, security, proportionality, cost, and intellectual-property burdens that must be designed in rather than ignored.</p>
      </section>

      <section className="programme-section programme-data-cta">
        <div><p>Public beta dataset</p><h2>Agency Transfer Policy Atlas</h2><p>68 control families · 118 implementations · source-integrated register v0.3.1 · public release v0.1.0-beta.2.</p></div>
        <div className="programme-actions programme-actions--small">
          <ArrowLink href={POLICY_ATLAS_URL} externalLink>Open the dataset</ArrowLink>
          <ArrowLink href={`${REPOSITORY_URL}/tree/main/policy-atlas`} externalLink>Inspect methods</ArrowLink>
        </div>
      </section>
    </main>
  );
}

function PaperPage() {
  return (
    <main id="main-content" className="paper-web">
      <article>
        <header className="paper-web__header">
          <ProgrammeStatus />
          <p>ERA:AI Summer Research Fellowship 2026 · Flagship working paper</p>
          <h1>Harmful Manipulation<br />and Election Security</h1>
          <h2>The Capability–Deployment–Effect Gap</h2>
          <h3>Frontier AI, influence infrastructure, and democratic self-correction</h3>
          <div className="paper-web__byline">Miguel Guerrero · ERA:AI Summer Research Fellowship, Cambridge</div>
          <div className="paper-web__metadata">
            <span>Current web working edition</span><span>Evidence freeze · 28 August 2026</span><span>Sole author · not peer reviewed</span>
          </div>
          <ClaimCeiling>
            The paper reports an exploratory red-team programme, a deeply instrumented forensic subset, an upstream access-to-intervention methods study, a direct model-evaluation audit, a claim-level election evidence index, and a policy evidence atlas. It does not report a successful model intervention, authentic audience exposure, a prevalence estimate, durable agency erosion, or an AI-attributable electoral effect.
          </ClaimCeiling>
        </header>

        <section className="paper-web__abstract" id="abstract">
          <p>Abstract</p>
          {paperAbstract.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
        </section>

        <nav className="paper-web__toc" aria-label="Paper contents">
          <strong>Contents</strong>
          <ol>{paperSections.map((section) => <li key={section.id}><a href={`#${section.id}`}><span>{section.number}</span>{section.title}</a></li>)}</ol>
        </nav>

        <section className="paper-web__figure" id="gap-figure">
          <CdeTopology />
        </section>

        {paperSections.map((section) => (
          <section className="paper-web__section" id={section.id} key={section.id}>
            <p>{section.number}</p>
            <h2>{section.title}</h2>
            <p>{section.summary}</p>
            {section.id === "influence" ? (
              <div className="paper-web__contrast">
                <article><strong>Persuasion</strong><p>Source and purpose are reasonably visible; claims can be examined; alternatives remain accessible; rejection is practical.</p></article>
                <article><strong>Manipulation</strong><p>Opacity, deception, impersonation, vulnerability exploitation, asymmetry, coercion, dependency, or control of the decision environment weaken reflective and contestable choice.</p></article>
              </div>
            ) : null}
            {section.id === "programme" ? (
              <div className="paper-web__part-summary"><PartCard id="part-i" /><PartCard id="part-ii" /><PartCard id="part-iii" /><PartCard id="part-iv" /></div>
            ) : null}
            {section.id === "joins" ? (
              <div className="condition-table">
                <div><strong>Sustained capability</strong><span>Repeated adaptive interaction remains effective.</span><em>Test exact routes; limit memory, tools, and consequential actions.</em></div>
                <div><strong>Trusted access</strong><span>Assistants, identity channels, workflows, or dominant platforms provide access.</span><em>Authentication, disclosure, plural channels, and procurement diversity.</em></div>
                <div><strong>Joined control</strong><span>One actor controls several CDE links.</span><em>Separate permissions and require independent approval at consequential transitions.</em></div>
                <div><strong>Weak observability</strong><span>The controller sees response data while outsiders lack route, delivery, or audit evidence.</span><em>Preserve or escrow records and enable qualified independent review.</em></div>
                <div><strong>Persistent dependency</strong><span>People or institutions cannot function or decide without the system.</span><em>Exit, interoperability, human override, and institutional redundancy.</em></div>
              </div>
            ) : null}
            {section.id === "governance" ? (
              <blockquote>Do not promote upstream evidence into downstream claims. Do not wait for a downstream claim before acting on an evidenced upstream mechanism.</blockquote>
            ) : null}
          </section>
        ))}

        <section className="paper-web__citation" id="citation">
          <p>Citation</p>
          <blockquote>Guerrero, Miguel. 2026. <em>Harmful Manipulation and Election Security: The Capability–Deployment–Effect Gap.</em> ERA:AI Summer Research Fellowship working paper. Current web edition; evidence freeze 28 August 2026.</blockquote>
          <div className="programme-actions programme-actions--small">
            <ArrowLink href={`${REPOSITORY_URL}/blob/main/CITATION.cff`} externalLink>Citation metadata</ArrowLink>
            <ArrowLink href={`${REPOSITORY_URL}/blob/main/RESPONSIBLE_RELEASE.md`} externalLink>Responsible release</ArrowLink>
          </div>
        </section>
      </article>
    </main>
  );
}

function OutputsPage() {
  return (
    <main id="main-content" className="programme-main">
      <PageIntro
        eyebrow="Research outputs"
        title="One programme, several forms."
        standfirst="The flagship paper provides the narrative spine. Briefs, posters, datasets, tools, methods, and explainers serve different reading needs without silently upgrading the evidence."
      />

      <section className="programme-section programme-section--first">
        <SectionHeading number="Core" title="Publications and briefings" />
        <div className="output-grid output-grid--full">
          {outputs.slice(0, 4).map((output) => <OutputCard output={output} key={output.id} />)}
        </div>
      </section>

      <section className="programme-section" id="one-page-brief">
        <SectionHeading number="01" title="One-page brief" note="Latest working web facsimile; the final downloadable asset can replace it without changing the route." />
        <OnePageBriefPreview />
      </section>

      <section className="programme-section" id="research-poster">
        <SectionHeading number="02" title="Research poster" note="Provisional web facsimile until the final canonical poster is supplied." />
        <PosterPreview />
      </section>

      <section className="programme-section white-paper-block" id="white-paper">
        <SectionHeading number="03" title="The Persuasion Machines" note="White paper · tenth edition · 27 August 2026" />
        <div className="white-paper-block__grid">
          <div><p className="programme-eyebrow">Frontier AI, persuasion, and the risk of harmful manipulation</p><h3>The system—not the isolated sentence—is the relevant unit.</h3></div>
          <div><p>The white paper translates the programme for policy and general audiences. It explains why democratic persuasion is not the enemy, why manipulation depends on process and control, and why persistent systems with data, tools, distribution, and feedback raise a different governance problem from cheaper misinformation alone.</p><p>A standalone canonical file will replace this web summary when supplied.</p></div>
        </div>
      </section>

      <section className="programme-section">
        <SectionHeading number="Evidence" title="Datasets, evaluations, and tools" />
        <div className="output-grid output-grid--full">
          {outputs.slice(4).map((output) => <OutputCard output={output} key={output.id} />)}
        </div>
      </section>

      <section className="programme-section programme-repository-map">
        <SectionHeading number="Code" title="Public research record" />
        <div className="repository-map">
          <a href={REPOSITORY_URL} target="_blank" rel="noreferrer"><strong>apolmig/agencytransfer</strong><span>Programme site, evaluation registry, public methods, datasets, and validation.</span></a>
          <a href={`${REPOSITORY_URL}/tree/main/part1b`} target="_blank" rel="noreferrer"><strong>part1b/</strong><span>Access-to-control methods and fail-closed public contracts.</span></a>
          <a href={`${REPOSITORY_URL}/tree/main/evals`} target="_blank" rel="noreferrer"><strong>evals/</strong><span>Inspect harness, manifests, fixtures, gates, and audit trail.</span></a>
          <a href={`${REPOSITORY_URL}/tree/main/policy-atlas`} target="_blank" rel="noreferrer"><strong>policy-atlas/</strong><span>Source register, schema, validation, and versioned policy releases.</span></a>
        </div>
      </section>
    </main>
  );
}

function ExplainersPage() {
  return (
    <main id="main-content" className="programme-main">
      <PageIntro
        eyebrow="Explainers"
        title="Mechanisms made visible—without turning illustration into evidence."
        standfirst="These films and diagrams explain how capability, targeting, identity, distribution, repetition, feedback, and observability might be joined. Synthetic scenarios are not records of real campaigns or effects."
      />

      <section className="programme-section programme-section--first explainer-feature" id="manuel-miami">
        <div className="explainer-feature__copy">
          <span>Synthetic scenario · US midterms · Miami</span>
          <h2>Manuel: an agentic influence scenario</h2>
          <p>{explainers[0].description}</p>
          <ClaimCeiling>{explainers[0].claim}</ClaimCeiling>
          <a href={explainers[0].watchUrl ?? "#"} target="_blank" rel="noreferrer">Watch on YouTube <span aria-hidden="true">↗</span></a>
        </div>
        <div className="explainer-video">
          <iframe
            src={explainers[0].embedUrl ?? undefined}
            title="Manuel: agentic AI manipulation and election security explainer"
            loading="lazy"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
          />
        </div>
      </section>

      <section className="programme-section explainer-feature explainer-feature--reverse" id="brazil-2026">
        <div className="explainer-feature__copy">
          <span>Synthetic scenario · Brazil 2026 · Recife</span>
          <h2>Brazil 2026: the final-hour voice</h2>
          <p>{explainers[1].description}</p>
          <ClaimCeiling>{explainers[1].claim}</ClaimCeiling>
          <p className="programme-note">Status: {explainers[1].status}. The temporary-host link is deliberately not published.</p>
        </div>
        <div className="brazil-storyboard" aria-label="Brazil 2026 explainer storyboard">
          <article><span>00:04</span><h3>Ana intends to vote</h3><p>A fictional nursing assistant in Recife has a prior political preference.</p></article>
          <article><span>00:17</span><h3>A trusted voice appears</h3><p>WhatsApp delivers audio that sounds authentic but was cloned by AI.</p></article>
          <article><span>00:35</span><h3>The attempt scales</h3><p>The scenario multiplies attempted targeting while preserving the unmeasured gap between delivery, response, and aggregate effect.</p></article>
        </div>
      </section>

      <section className="programme-section">
        <SectionHeading number="Visual grammar" title="Six mechanisms recur across the programme" />
        <MechanismGallery />
      </section>

      <section className="programme-section explainer-rules">
        <SectionHeading number="Release rule" title="Every explainer carries its boundary" />
        <div className="programme-prose programme-prose--two-column"><p>A public video needs a durable host, preserved master, poster frame, captions, transcript, date, duration, source version, rights review, and visible classification as synthetic scenario, methods demonstration, evidence explainer, or talk.</p><p>No autoplay with sound. No synthetic campaign content as generic decoration. No temporary file hosts as canonical links. A film can clarify a mechanism; it cannot create evidence that the underlying operation or effect occurred.</p></div>
      </section>
    </main>
  );
}

function UpdatesPage() {
  return (
    <main id="main-content" className="programme-main">
      <PageIntro
        eyebrow="Programme log"
        title="What changed, why it changed, and whether the conclusion moved."
        standfirst="This is a material-change record, not a blog. Updates document revisions to evidence, methods, datasets, public outputs, and claim ceilings."
      />
      <section className="programme-section programme-section--first">
        <div className="programme-update-list">
          {programmeUpdates.map((update) => (
            <article key={`${update.date}-${update.title}`}><time>{update.date}</time><div><h2>{update.title}</h2><p>{update.body}</p></div></article>
          ))}
        </div>
      </section>
    </main>
  );
}

function AboutPage() {
  return (
    <main id="main-content" className="programme-main">
      <PageIntro
        eyebrow="About"
        title="A maintained research record of an unfinished systems problem."
        standfirst={programmeManifest.programme.scope_statement}
      />
      <section className="programme-section programme-section--first about-grid">
        <div><SectionHeading number="Programme" title="Research question" /><p>The project asks what frontier AI systems can do that is relevant to harmful manipulation; when those capabilities become operational systems; who controls the systems; what effects follow; and when that control threatens democratic self-government.</p><p>Its wider concern is manipulation as a mechanism through which political and epistemic power may become extremely concentrated.</p></div>
        <div><SectionHeading number="Author" title="Miguel Guerrero" /><p>Research Fellow at Cambridge ERA. Senior AI adviser and programme director in government, founder of Saturdays.AI, engineer, educator, and researcher working across AI adoption, governance, safety, and democratic resilience.</p><p>The programme is independent research. It is not an official position of ERA, Cambridge, or any institution with which the author is affiliated.</p></div>
      </section>
      <section className="programme-section about-grid">
        <div><SectionHeading number="Evidence" title="Primary records are not independent replication" /><p>Project-produced traces, recovered evaluations, coding decisions, and curated datasets document protocols and observations within the same programme. They do not constitute peer review or independent corroboration of downstream effects.</p></div>
        <div><SectionHeading number="Release" title="Responsible publication" /><p>The public record publishes concepts, aggregates, source-linked claims, defensive methods, and synthetic explainers. It withholds campaign-ready outputs, targetable profiles, evasion instructions, credentials, raw harmful traces, and private validation material.</p></div>
      </section>
      <section className="programme-section citation-panel">
        <SectionHeading number="Citation" title="Programme citation" />
        <blockquote>Guerrero, Miguel. 2026. <em>Agency Transfer Research Programme: Frontier AI, Harmful Manipulation, and Democratic Power.</em> ERA:AI Summer Research Fellowship, Cambridge. Working programme, evidence freeze 28 August 2026.</blockquote>
        <div className="programme-actions programme-actions--small"><ArrowLink href={`${REPOSITORY_URL}/blob/main/CITATION.cff`} externalLink>Citation metadata</ArrowLink><ArrowLink href={REPOSITORY_URL} externalLink>Source repository</ArrowLink></div>
      </section>
    </main>
  );
}

function App() {
  const page = pageFromPath();
  usePageMetadata(page);

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

  const needsPartIIData = useMemo(
    () => ["part-ii", "part-ii-evidence", "part-ii-testing"].includes(page),
    [page],
  );

  useEffect(() => {
    if (!needsPartIIData) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
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
  }, [needsPartIIData]);

  const frontierError = [errors.frontierModels, errors.frontierObservations].filter(Boolean).join(" · ");

  let content: React.ReactNode;
  switch (page) {
    case "research": content = <ResearchPage />; break;
    case "part-i": content = <PartIPage />; break;
    case "part-ii": content = <PartIIPage models={frontierModels} observations={frontierObservations} loading={loading} error={frontierError} />; break;
    case "part-ii-evidence": content = <PartIIEvidencePage benchmarks={benchmarks} agenticResults={agenticResults} maskResults={maskResults} diselectResults={diselectResults} models={models} errors={errors} />; break;
    case "part-ii-testing": content = <PartIITestingPage notes={testingNotes} error={errors.testingNotes} />; break;
    case "part-iii": content = <PartIIIPage />; break;
    case "part-iv": content = <PartIVPage />; break;
    case "paper": content = <PaperPage />; break;
    case "outputs": content = <OutputsPage />; break;
    case "explainers": content = <ExplainersPage />; break;
    case "updates": content = <UpdatesPage />; break;
    case "about": content = <AboutPage />; break;
    default: content = <HomePage />;
  }

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <SiteHeader page={page} />
      {content}
      <SiteFooter />
    </>
  );
}

export default App;
