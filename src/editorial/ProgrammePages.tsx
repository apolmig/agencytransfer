import { LAB_URL, REPOSITORY_URL, RIFT_ANIMATION, DraftBoundary, PageLead, TextLink, route } from "./EditorialShell";
import { MechanismStrip } from "./EditorialVisuals";
import { BudgetBoundary } from "../components/ResearchStatus";

const researchParts = [
  {
    label: "Part I",
    title: "Capability and operations",
    line: "How far can an adversarial actor go with $10?",
    body: "Pretty far, actually—for exploratory planning and synthetic prototypes. An author-reported service budget, not a verified full-cost operation.",
    href: route("research/part-i/"),
    action: "Open Part I",
    featured: false,
  },
  {
    label: "Part II",
    title: "Frontier Evaluation Registry",
    line: "Useful evaluations. No shared system-level yardstick.",
    body: "Useful model and system studies exist. Our review has not identified an accepted cross-system standard for harmful manipulation as framed by the EU GPAI Code.",
    href: route("registry/"),
    action: "Open the Registry",
    featured: true,
  },
  {
    label: "Part III",
    title: "Field evidence",
    line: "Real operations. Unresolved electoral effects.",
    body: "Documented influence attempts and harms, including harassment and confusion. Individual and election-wide effects remain bounded or unresolved; proliferation is a hypothesis, not our estimate.",
    href: route("research/part-iii/"),
    action: "Open Part III",
    featured: false,
  },
  {
    label: "Part IV",
    title: "Policy interventions",
    line: "What works—and for whom?",
    body: "Concrete legal and research examples, from AI-origin marking and ChatGPT’s DSA designation to tested sharing interventions. Recommendations remain provisional; adoption is not effectiveness.",
    href: route("research/part-iv/"),
    action: "Open Part IV",
    featured: false,
  },
] as const;

function PartNavigation() {
  return (
    <section className="v2-parts v2-parts--simple" aria-label="Four research parts">
      {researchParts.map((part) => (
        <article className={`v2-part-card${part.featured ? " v2-part-card--featured" : ""}`} key={part.label}>
          {part.featured ? <div className="v2-feature-label">Featured draft artifact</div> : null}
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
        <p className="v2-deck">A research programme in progress on how frontier AI could become influence infrastructure, who controls it, and when practical agency shifts away from citizens and democratic institutions.</p>
        <p className="v2-plain-boundary">All programme results and recommendations are provisional and not peer reviewed. Documented harms do not establish that AI changed an election.</p>
        <div className="v2-actions">
          <a className="v2-button v2-button--dark" href={route("research/")}>Explore the research</a>
          <a className="v2-button" href={route("paper/")}>Read the working paper</a>
        </div>
      </div>
      <figure className="v2-hero-art v2-hero-art--supplied">
        <img
  src={route("media/cde-gap3-hero-1672.webp")}
  srcSet={`${route("media/cde-gap3-hero-824.webp")} 824w, ${route("media/cde-gap3-hero-1672.webp")} 1672w`}
  sizes="(max-width: 1050px) calc(100vw - 48px), 55vw"
  width={1672}
  height={941}
  loading="eager"
  fetchPriority="high"
  decoding="async"
  style={{ height: "auto" }}
  alt="The Capability–Deployment–Effect Gap: AI capability and deployment are separated from electoral consequences by uncertain links through exposure, attention, beliefs, and intentions."
/>
        <figcaption>Conceptual illustration, not a measured universal law. The reviewed records establish operations more readily than authentic exposure, durable human response or electoral consequence.</figcaption>
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
    { label: "Working paper", detail: "v1.3 working draft · full PDF", href: route("paper/") },
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
      <p className="v2-draft-line"><strong>Working draft.</strong> All programme findings, coding, interpretations and recommendations are work in progress, subject to correction and not independently replicated.</p>
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
      <PageLead eyebrow="Part I · Capability and operations · Draft / work in progress" title="How far can an adversarial actor go with $10?" deck="Pretty far, actually—for planning and synthetic prototypes. This is an author-reported exploratory pilot, not a verified $10 influence campaign.">
        <DraftBoundary>Planning assistance and synthetic prototypes are not a demonstrated live operation. No autonomous execution, authentic audience contact, human persuasion, durable agency transfer or electoral effect was established by these tests.</DraftBoundary>
      </PageLead>
      <BudgetBoundary />
      <div className="v2-wide-figure v2-wide-figure--mechanism"><MechanismStrip /><p className="v2-figure-caption">A conceptual account of the joins an operator could attempt to control. It does not show that a real operation completed them.</p></div>
      <section className="v2-three-column">
        <article><p className="v2-eyebrow">Provisional programme record</p><h2>Planning assistance, not demonstrated execution</h2><p>The author-reported pilot describes multi-step, multimodal prototyping. In a closer-inspected subset, one served route produced campaign-planning elements after some tactical refusals. These records do not establish a reliable success rate or retained capability. A separate model-intervention study failed to produce an independently reloadable package.</p></article>
        <article><p className="v2-eyebrow">Not observed</p><h2>No live operation</h2><p>The work did not research voters, contact real people, distribute content, run a feedback loop, or produce a behavioural estimate.</p></article>
        <article><p className="v2-eyebrow">Next study</p><h2>Observe action, not prose</h2><p>Reconcile the full budget and evidence units. Compare exact system versions with a human-only baseline in a closed synthetic environment. Record time, quality, missing outputs and permission failures, with blinded review and independent replication.</p></article>
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
