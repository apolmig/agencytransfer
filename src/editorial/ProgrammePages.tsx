import { LAB_URL, REPOSITORY_URL, RIFT_ANIMATION, RIFT_IMAGE, DraftBoundary, PageLead, TextLink, route } from "./EditorialShell";
import { MechanismStrip } from "./EditorialVisuals";

const researchParts = [
  {
    label: "Part I",
    title: "Operations",
    line: "Access is not control.",
    body: "What a served system can produce, what an operator can operationalise, and where the chain stopped.",
    href: route("research/part-i/"),
    action: "Open Part I",
  },
  {
    label: "Part II",
    title: "Frontier Evaluation Registry",
    line: "Measurement is part of the object.",
    body: "The original chart, evidence review, testing record, and benchmark-native results—restored as one complete artifact.",
    href: route("registry/"),
    action: "Open the Registry",
    featured: true,
  },
  {
    label: "Part III",
    title: "Field evidence",
    line: "Evidence thins downstream.",
    body: "What public election records establish about operations, exposure, response, and electoral consequence.",
    href: route("research/part-iii/"),
    action: "Open Part III",
  },
  {
    label: "Part IV",
    title: "Policy evidence",
    line: "Adoption is not effectiveness.",
    body: "Where controls act, who holds the evidence, and what the strongest defensible policy claim is.",
    href: route("research/part-iv/"),
    action: "Open Part IV",
  },
] as const;

function PartNavigation() {
  return (
    <section className="v2-parts v2-parts--simple" aria-label="Four research parts">
      {researchParts.map((part) => (
        <article className={`v2-part-card${part.featured ? " v2-part-card--featured" : ""}`} key={part.label}>
          {part.featured ? <div className="v2-feature-label">Featured artifact</div> : null}
          <p>{part.label}</p>
          <h2>{part.title}</h2>
          <h3>{part.line}</h3>
          <p>{part.body}</p>
          <TextLink href={part.href}>{part.action}</TextLink>
        </article>
      ))}
    </section>
  );
}

function Hero() {
  return (
    <section className="v2-hero v2-hero--repository">
      <div className="v2-hero-copy">
        <p className="v2-eyebrow">Frontier AI · harmful manipulation · election security</p>
        <h1>Harmful manipulation<br />and election security</h1>
        <h2>The capability–deployment–effect gap</h2>
        <p className="v2-deck">A draft research programme on how frontier AI capability becomes deployed influence infrastructure, where evidence weakens between capability and effect, and what that means for democratic self-correction.</p>
        <p className="v2-plain-boundary">It does not show that frontier AI changed an election.</p>
        <div className="v2-actions">
          <a className="v2-button v2-button--dark" href={route("research/")}>Explore the research</a>
          <a className="v2-button" href={route("paper/")}>Read the working paper</a>
        </div>
      </div>
      <figure className="v2-hero-art v2-hero-art--supplied">
        <img src={RIFT_IMAGE} alt="Illustration of the Capability–Deployment–Effect Rift, from model capability and deployment to uncertain behavioural and electoral consequences." />
        <figcaption>Conceptual illustration. Evidence is stronger upstream and progressively weaker across authentic exposure, human response, and aggregate consequence.</figcaption>
      </figure>
    </section>
  );
}

export function AnimationFeature() {
  return (
    <section className="v2-animation-section">
      <div className="v2-section-lead">
        <div><p className="v2-eyebrow">Animated overview</p><h2>The CDE Rift, in motion</h2></div>
        <p>Capability is observable; deployment is conditional; effect requires new evidence at every bridge.</p>
      </div>
      <div className="v2-animation-frame">
        <iframe title="Animated presentation of the Capability–Deployment–Effect Rift" src={RIFT_ANIMATION} loading="lazy" allowFullScreen />
      </div>
      <div className="v2-inline-note"><span>Working draft</span><p>An explanatory artifact, not evidence of a completed causal chain.</p><TextLink href={RIFT_ANIMATION}>Open full screen</TextLink></div>
    </section>
  );
}

function KeyArtifacts() {
  const items: Array<{ label: string; detail: string; href: string; external?: boolean }> = [
    { label: "Working paper", detail: "Flagship v1.0 web draft", href: route("paper/") },
    { label: "Poster", detail: "Draft visual overview", href: route("outputs/#poster") },
    { label: "White paper", detail: "Accessible policy synthesis", href: route("outputs/#white-paper") },
    { label: "Explainers", detail: "Animation and synthetic scenarios", href: route("explainers/") },
    { label: "Agency Transfer Lab", detail: "Research harness and open tools", href: LAB_URL, external: true },
  ];

  return (
    <section className="v2-resources v2-resources--simple">
      <div className="v2-section-lead"><div><p className="v2-eyebrow">Artifacts</p><h2>Research outputs</h2></div><TextLink href={route("outputs/")}>View all artifacts</TextLink></div>
      <div className="v2-artifact-list">
        {items.map((item) => (
          <a key={item.label} href={item.href} target={item.external ? "_blank" : undefined} rel={item.external ? "noreferrer" : undefined}>
            <span><strong>{item.label}</strong><small>{item.detail}</small></span><i aria-hidden="true">→</i>
          </a>
        ))}
      </div>
    </section>
  );
}

export function HomePage() {
  return (
    <main id="main-content" className="v2-main">
      <Hero />
      <PartNavigation />
      <KeyArtifacts />
      <p className="v2-draft-line"><strong>Working draft.</strong> All findings and artifacts are provisional and subject to revision.</p>
    </main>
  );
}

export function ResearchPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Research" title="Four audits of one influence system" deck="The programme keeps technical traces, model evaluations, election records, and policy evidence separate. Each part observes a different node and stops at its own claim boundary." />
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
      <div className="v2-wide-figure v2-wide-figure--mechanism"><MechanismStrip /><p className="v2-figure-caption">A conceptual account of the joins an operator could attempt to control. It does not show that a real operation completed them.</p></div>
      <section className="v2-three-column">
        <article><p className="v2-eyebrow">Observed</p><h2>Planning assistance and conversion constraints</h2><p>One recorded served route produced recognisable campaign-planning elements after some tactical refusals. A separate intervention study did not create a durable package that could be independently reloaded.</p></article>
        <article><p className="v2-eyebrow">Not observed</p><h2>No live operation</h2><p>The work did not research voters, contact real people, distribute content, run a feedback loop, or produce a behavioural estimate.</p></article>
        <article><p className="v2-eyebrow">Next study</p><h2>Observe action, not prose</h2><p>Use exact routes, a closed synthetic election environment, reversible state, matched controls, permission boundaries, clean reload, and a human-only baseline.</p></article>
      </section>
      <section className="v2-simple-section">
        <div className="v2-section-lead"><div><p className="v2-eyebrow">Artifacts</p><h2>Methods and bounded demonstrations</h2></div></div>
        <div className="v2-artifact-list v2-artifact-list--three">
          <TextLink href={LAB_URL} external>Agency Transfer Lab</TextLink>
          <TextLink href={`${REPOSITORY_URL}/tree/main/part1b`} external>Access-to-control methods</TextLink>
          <TextLink href={route("explainers/")}>Synthetic explainers</TextLink>
        </div>
      </section>
    </main>
  );
}
