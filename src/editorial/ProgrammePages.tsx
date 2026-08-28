import { LAB_URL, REGISTRY_DATA_URL, REPOSITORY_URL, RIFT_ANIMATION, DraftBoundary, PageLead, TextLink, route } from "./EditorialShell";
import { BenchmarkArchipelagoVisual, EditorialRiftVisual, MechanismStrip } from "./EditorialVisuals";

function PartNavigation() {
  return (
    <section className="v2-parts" aria-label="Four research parts">
      <article className="v2-part-card">
        <p>Part I</p><h2>Operations</h2><h3>Access is not control.</h3>
        <p>What a served system can produce, what an operator can operationalise, and where the chain stopped.</p>
        <TextLink href={route("research/part-i/")}>Explore operations</TextLink>
      </article>
      <article className="v2-part-card v2-part-card--featured">
        <div className="v2-feature-label">Featured artifact</div>
        <p>Part II</p><h2>Evaluation</h2><h3>Measurement is part of the object.</h3>
        <BenchmarkArchipelagoVisual compact />
        <p>The complete public registry, evidence review, testing record, and benchmark-native results.</p>
        <div className="v2-card-links">
          <TextLink href={route("research/part-ii/")}>Registry</TextLink>
          <TextLink href={route("research/part-ii/evidence/")}>Evidence</TextLink>
          <TextLink href={route("research/part-ii/testing/")}>Testing</TextLink>
        </div>
      </article>
      <article className="v2-part-card">
        <p>Part III</p><h2>Field evidence</h2><h3>Evidence thins downstream.</h3>
        <p>What public election records establish about operations, exposure, response, and electoral consequence.</p>
        <TextLink href={route("research/part-iii/")}>Explore field evidence</TextLink>
      </article>
      <article className="v2-part-card">
        <p>Part IV</p><h2>Policy</h2><h3>Adoption is not effectiveness.</h3>
        <p>Where controls act, who holds the evidence, and what the strongest defensible policy claim is.</p>
        <TextLink href={route("research/part-iv/")}>Explore policy evidence</TextLink>
      </article>
    </section>
  );
}

function Hero() {
  return (
    <section className="v2-hero">
      <div className="v2-hero-copy">
        <p className="v2-eyebrow">Frontier AI · harmful manipulation · election security</p>
        <h1>Harmful manipulation<br />and election security</h1>
        <h2>The capability–deployment–effect gap</h2>
        <p className="v2-deck">This programme studies how frontier AI capability can become deployed influence infrastructure, where evidence weakens between capability and effect, and what that means for democratic self-correction.</p>
        <p className="v2-plain-boundary">It does not show that frontier AI changed an election.</p>
        <div className="v2-actions">
          <a className="v2-button v2-button--dark" href={route("research/")}>Explore the programme</a>
          <a className="v2-button" href={route("paper/")}>Read the working paper</a>
        </div>
      </div>
      <div className="v2-hero-art">
        <EditorialRiftVisual />
        <p className="v2-figure-caption">Evidence is stronger upstream and progressively weaker across authentic exposure, human response, and aggregate consequence.</p>
      </div>
    </section>
  );
}

function AnimationFeature() {
  return (
    <section className="v2-animation-section">
      <div className="v2-section-lead">
        <div><p className="v2-eyebrow">Animated overview</p><h2>The CDE Rift, in motion</h2></div>
        <p>The animation explains the whole research problem: capability is observable; deployment is conditional; effect requires new evidence at every bridge.</p>
      </div>
      <div className="v2-animation-frame">
        <iframe title="Animated presentation of the Capability–Deployment–Effect Rift" src={RIFT_ANIMATION} loading="lazy" allowFullScreen />
      </div>
      <div className="v2-inline-note"><span>Working draft</span><p>The animation is an explanatory artifact, not evidence of a completed causal chain.</p><TextLink href={RIFT_ANIMATION}>Open full screen</TextLink></div>
    </section>
  );
}

function KeyResources() {
  const items = [
    { label: "Paper", detail: "Current v1.0 working draft reflected in the web edition", href: route("paper/") },
    { label: "Poster", detail: "Draft visual overview; final asset pending", href: route("outputs/#poster") },
    { label: "White paper", detail: "Accessible policy synthesis; draft", href: route("outputs/#white-paper") },
    { label: "Explainers", detail: "The CDE animation and synthetic scenarios", href: route("explainers/") },
    { label: "Agency Transfer Lab", detail: "Research harness and open tools", href: LAB_URL, external: true },
  ];
  return (
    <section className="v2-resources">
      <div className="v2-section-lead"><div><p className="v2-eyebrow">Resources</p><h2>Key artifacts</h2></div><TextLink href={route("outputs/")}>View all resources</TextLink></div>
      <div className="v2-resource-grid">
        {items.map((item) => <article key={item.label}><span aria-hidden="true">↗</span><h3>{item.label}</h3><p>{item.detail}</p><TextLink href={item.href} external={item.external}>{item.external ? "Open" : "View"}</TextLink></article>)}
      </div>
    </section>
  );
}

export function HomePage() {
  return <main id="main-content" className="v2-main"><Hero /><PartNavigation /><AnimationFeature /><KeyResources /><aside className="v2-draft-notice"><strong>All material is draft.</strong><p>Findings, figures, artifact status, and public links will continue to change. No page represents a final policy position or a completed causal claim.</p><TextLink href={route("about/")}>About this draft</TextLink></aside></main>;
}

export function ResearchPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Research programme" title="Four audits of one influence system" deck="The programme does not collapse technical traces, model evaluations, election records, and policy adoption into one score. Each part observes a different node and stops at its own claim boundary." />
      <div className="v2-wide-figure"><EditorialRiftVisual /><p className="v2-figure-caption">The CDE Gap is an organising frame, not a universal linear ladder. Institutional harm does not always require voter persuasion.</p></div>
      <PartNavigation />
      <blockquote className="v2-rule-quote">Measure the node an intervention changes. Preserve evidence for the next node. Do not promote one into the other.</blockquote>
    </main>
  );
}

export function PartIPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Part I · Operations" title="Access is not control" deck="A model name hides the served system around it: route, safeguards, context, memory, tools, permissions, retries, and operator interaction. Deployment adds an actor, objective, data, authority, distribution, feedback, and persistence.">
        <DraftBoundary>No successful intervention, autonomous execution, authentic audience contact, persuasion, durable agency transfer, or electoral effect.</DraftBoundary>
      </PageLead>
      <div className="v2-wide-figure v2-wide-figure--mechanism"><MechanismStrip /><p className="v2-figure-caption">Editorialised from the supplied anatomy illustration. It shows the joins an operator could attempt to control; it does not show that a real operation completed them.</p></div>
      <section className="v2-three-column">
        <article><p className="v2-eyebrow">Observed</p><h2>Planning assistance and conversion constraints</h2><p>One recorded served route produced recognisable campaign-planning elements after some tactical refusals. A separate intervention study did not create a durable package that could be independently reloaded.</p></article>
        <article><p className="v2-eyebrow">Not observed</p><h2>No live operation</h2><p>The work did not research voters, contact real people, distribute content, run a feedback loop, or produce a behavioural estimate. Locally tamper-evident records are not provider attestation.</p></article>
        <article><p className="v2-eyebrow">Next study</p><h2>Observe action, not prose</h2><p>Use exact routes, a closed synthetic election environment, reversible state, matched controls, permission boundaries, clean reload, and a human-only baseline.</p></article>
      </section>
      <section className="v2-simple-section">
        <div className="v2-section-lead"><div><p className="v2-eyebrow">Artifacts</p><h2>Methods and bounded demonstrations</h2></div></div>
        <div className="v2-resource-grid v2-resource-grid--three">
          <article><h3>Agency Transfer Lab</h3><p>Tests harness behaviour, replay, persistence, migration, export integrity, and tamper detection. It does not measure persuasion or effect.</p><TextLink href={LAB_URL} external>Open the Lab</TextLink></article>
          <article><h3>Access-to-control record</h3><p>Public methods for the distance between formal model access and a durable, reloadable intervention.</p><TextLink href={`${REPOSITORY_URL}/tree/main/part1b`} external>Inspect methods</TextLink></article>
          <article><h3>Synthetic explainers</h3><p>Manuel/Miami and Brazil make possible mechanisms legible without presenting them as observed campaigns.</p><TextLink href={route("explainers/")}>View explainers</TextLink></article>
        </div>
      </section>
    </main>
  );
}

export function PartIILead() {
  return (
    <section className="v2-partii-lead">
      <div>
        <p className="v2-eyebrow">Part II · Featured artifact</p>
        <h1>Frontier Evaluation Registry</h1>
        <h2>Measurement is part of the object.</h2>
        <p className="v2-deck">The registry preserves benchmark-native outcomes across different constructs. The recovered APE-120 audit shows why route identity, parser behaviour, evaluator validity, and missingness cannot be treated as neutral plumbing.</p>
        <DraftBoundary>No pooled manipulation score, no model ranking, no longitudinal frontier trend, no human persuasion estimate, and no election effect.</DraftBoundary>
        <div className="v2-tab-links"><a aria-current="page" href={route("research/part-ii/")}>Registry</a><a href={route("research/part-ii/evidence/")}>Evidence</a><a href={route("research/part-ii/testing/")}>Testing</a><a href={REGISTRY_DATA_URL} target="_blank" rel="noreferrer">Data ↗</a></div>
      </div>
      <BenchmarkArchipelagoVisual />
    </section>
  );
}
