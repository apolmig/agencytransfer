import { useEffect, useRef, useState } from "react";
import { LAB_URL, REPOSITORY_URL, RIFT_ANIMATION, RIFT_PLAYER, DraftBoundary, PageLead, TextLink, route } from "./EditorialShell";
import { MechanismStrip } from "./EditorialVisuals";
import { BudgetBoundary } from "../components/ResearchStatus";

const researchParts = [
  {
    label: "Part I",
    title: "Capability and operations",
    line: "How far can an adversarial actor go with $10?",
    body: "Pretty far, actually. Explore the planning and prototyping pilot—and its limits.",
    href: route("research/part-i/"),
    action: "Open Part I",
    featured: false,
  },
  {
    label: "Part II",
    title: "Frontier Evaluation Registry",
    line: "Useful evaluations. No shared system-level yardstick.",
    body: "The complete Registry: benchmark-native results, evidence and testing. Opens as an independent artifact.",
    href: route("registry/"),
    action: "Open the Registry",
    featured: true,
  },
  {
    label: "Part III",
    title: "Field evidence",
    line: "Real operations. Unresolved electoral effects.",
    body: "Documented attempts and harms. What election records establish—and what remains unknown.",
    href: route("research/part-iii/"),
    action: "Open Part III",
    featured: false,
  },
  {
    label: "Part IV",
    title: "Policy interventions",
    line: "What works—and for whom?",
    body: "Concrete controls, evidence and limits. Adoption is not the same as effectiveness.",
    href: route("research/part-iv/"),
    action: "Open Part IV",
    featured: false,
  },
] as const;

function PartNavigation() {
  return (
    <section className="v2-parts v2-parts--simple" id="research" aria-label="Four research parts">
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
        <p className="v2-eyebrow">Frontier AI · harmful manipulation · epistemic risk</p>
        <h1>Harmful manipulation<br />and election security</h1>
        <h2>The capability–deployment–effect gap</h2>
        <p className="v2-deck">A research programme in progress on harmful manipulation and epistemic risk, with election security as its first focus.</p>
        <p className="v2-plain-boundary">Documented harms do not establish that AI changed an election.</p>
        <div className="v2-actions">
          <a className="v2-button v2-button--dark" href={route("paper/")}>Read the draft overview</a>
          <a className="v2-button" href={RIFT_ANIMATION}>The CDE Gap, explained</a>
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
        <figcaption>Conceptual illustration. Each transition needs evidence; the image does not show a completed operation.</figcaption>
      </figure>
    </section>
  );
}

export function AnimationFeature() {
  const frame = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState(780);
  useEffect(() => {
    const receive = (event: MessageEvent) => {
      if (event.origin !== location.origin || event.source !== frame.current?.contentWindow || event.data?.type !== "cde-explainer-height") return;
      const value = Number(event.data.height);
      if (Number.isFinite(value) && value >= 350 && value <= 4000) setHeight(Math.ceil(value));
    };
    addEventListener("message", receive);
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) frame.current?.contentWindow?.postMessage({ type: "cde-explainer-pause" }, location.origin);
    });
    if (frame.current) observer.observe(frame.current);
    return () => { removeEventListener("message", receive); observer.disconnect(); };
  }, []);
  return (
    <section className="v2-animation-section" id="cde-explainer" aria-label="Interactive CDE explainer">
      <div className="v2-animation-frame v2-animation-frame--readable">
        <iframe ref={frame} title="The CDE Gap: a user-controlled, captioned explainer" src={RIFT_PLAYER} loading="eager" allowFullScreen style={{ height }} />
      </div>
    </section>
  );
}

function KeyArtifacts() {
  const items: Array<{ label: string; detail: string; href: string; external?: boolean }> = [
    { label: "Working paper", detail: "Draft overview · full paper coming soon", href: route("paper/") },
    { label: "References", detail: "Flagship bibliography and wider reading", href: route("references/") },
    { label: "Explainers", detail: "Animation and synthetic scenarios", href: route("explainers/") },
    { label: "Agency Transfer Lab", detail: "Research harness and open tools", href: LAB_URL, external: true },
  ];

  return (
    <section className="v2-resources v2-resources--simple">
      <div className="v2-section-lead"><div><h2>Paper &amp; supporting artifacts</h2></div><TextLink href={route("outputs/")}>View all artifacts</TextLink></div>
      <div className="v2-artifact-list v2-artifact-list--available">
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
      <p className="home-research-label">First phase · Election security</p>
      <PartNavigation />
      <KeyArtifacts />
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
      <PageLead eyebrow="Part I · Capability and operations · Draft / work in progress" title="How far can an adversarial actor go with $10?" deck="Pretty far, actually. The exploratory pilot examines planning assistance and synthetic prototypes—not a live campaign.">
        <DraftBoundary>Planning assistance and synthetic prototypes are not a demonstrated live operation. No autonomous execution, authentic audience contact, human persuasion, durable agency transfer or electoral effect was established by these tests.</DraftBoundary>
      </PageLead>
      <div className="v2-wide-figure v2-wide-figure--mechanism"><MechanismStrip /><p className="v2-figure-caption">A conceptual account of the joins an operator could attempt to control. It does not show that a real operation completed them.</p></div>
      <section className="v2-three-column">
        <article><p className="v2-eyebrow">Provisional programme record</p><h2>Planning assistance, not demonstrated execution</h2><p>The author-reported pilot describes multi-step, multimodal prototyping. In a closer-inspected subset, one served route produced campaign-planning elements after some tactical refusals. These records do not establish a reliable success rate or retained capability. A separate model-intervention study failed to produce an independently reloadable package.</p></article>
        <article><p className="v2-eyebrow">Not observed</p><h2>No live operation</h2><p>The work did not research voters, contact real people, distribute content, run a feedback loop, or produce a behavioural estimate.</p></article>
        <article><p className="v2-eyebrow">Next study</p><h2>Observe action, not prose</h2><p>Reconcile the full budget and evidence units. Compare exact system versions with a human-only baseline in a closed synthetic environment. Record time, quality, missing outputs and permission failures, with blinded review and independent replication.</p></article>
      </section>
      <BudgetBoundary />
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
