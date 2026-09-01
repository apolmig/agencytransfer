import { ELECTION_INDEX_URL, LAB_URL, MANUEL_VIDEO_URL, POLICY_ATLAS_URL, REPOSITORY_URL, RIFT_ANIMATION, DraftBoundary, PageLead, TextLink, route } from "./EditorialShell";
import { EditorialRiftVisual, MechanismStrip } from "./EditorialVisuals";
import { AnimationFeature } from "./ProgrammePages";

const paperAbstract = [
  "Frontier AI does not need to persuade an electorate to create a democratic governance problem. The risk emerges when model capability is joined to audience data, trusted identity, tools, distribution, feedback, and control of the evidence. Influence can then become adaptive infrastructure: persistent, personalised, difficult to observe, and controlled by actors able both to shape the process and to determine what outsiders can know about it.",
  "This paper develops the Capability–Deployment–Effect Gap, or CDE Gap, to separate model behaviour, served-system configuration, deployment, authentic exposure, human and institutional response, and electoral consequence. It uses agency transfer as the democratic severity test: whether practical control over attention, preference formation, choice, dependency, or institutional decisions shifts away from citizens and public institutions towards the actor controlling the system.",
  "Four linked audits provide a grounded but deliberately bounded evidence base. The technical work shows that model access is not yet a stable intervention and that route, parser, evaluator, and missingness failures can undermine apparently precise benchmark claims. Election records document operations and institutional responses more readily than authentic exposure or effect. The policy atlas assigns all 118 implementations to provisional recommendation postures, while retaining six empirically checked effect claims in its reproducible core. Classification coverage is not verification coverage.",
  "The governance implication is simple: do not infer downstream harm from upstream capability, but do not wait for proof of changed votes before acting on an evidenced mechanism. Prioritize bounded controls, build control and observability infrastructure, enforce applicable baselines without calling compliance effectiveness, use authenticity tools for their specific vectors, pilot structural safeguards and validate general triggers before using them as automatic gates.",
];

const paperSections = [
  ["1", "The next Cambridge Analytica may look ordinary", "The durable lesson was architectural: data, political purpose, targeting, content, distribution, and measurement could be joined before citizens or institutions could inspect the system in time."],
  ["2", "Influence, manipulation, and agency transfer", "Persuasion belongs in democracy. Manipulation weakens reflective and contestable choice through opacity, deception, vulnerability exploitation, asymmetry, dependency, or control of the decision environment."],
  ["3", "The Capability–Deployment–Effect Gap", "Capability, deployment, authentic exposure, human response, institutional response, agency transfer, and electoral consequence are distinct evidentiary objects."],
  ["4", "What the evidence says—and what it does not", "Controlled studies establish bounded persuasive effects. Field research shows uneven exposure, heterogeneous effects, and a difficult route from persuasive text to aggregate electoral consequence."],
  ["5", "Four audits of one system", "Operations, evaluation, field evidence, and policy evidence observe different links without borrowing one another’s strongest result."],
  ["6", "Power accumulates in the joins", "Influence power can concentrate in the ability to observe, optimise, and selectively disclose a process that outsiders can only partly reconstruct."],
  ["7", "Govern the system before the outcome", "Address the node where a harmful mechanism is evidenced; do not claim an effect at a node that was not measured."],
  ["8", "Research the missing bridges", "The next phase is narrower: reproducible evaluation, operational uplift, authentic exposure, human and institutional effects, control evaluation, and concentration mapping."],
  ["9", "Limitations and responsible release", "The programme is exploratory, internally produced, not independently replicated, and intentionally withholds operational material that could facilitate harmful election activity."],
  ["10", "Preserve democratic self-correction", "The democratic task is to keep capability, data, identity, distribution, feedback, and evidence visible, divided, and open to challenge before they harden into uncorrectable power."],
] as const;

export function PaperPage() {
  return (
    <main id="main-content" className="v2-paper">
      <header className="v2-paper-header">
        <p className="v2-eyebrow">ERA:AI Summer Research Fellowship 2026 · Flagship working paper v1.2</p>
        <h1>Harmful Manipulation and Election Security</h1>
        <h2>The Capability–Deployment–Effect Gap</h2>
        <p className="v2-paper-subtitle">How frontier AI can turn political influence into infrastructure—and how democracy can preserve self-correction</p>
        <p className="v2-paper-byline">Miguel Guerrero · Cambridge · 1 September 2026</p>
        <div className="v2-paper-actions"><a className="v2-button v2-button--dark" href="#abstract">Read the abstract</a><a className="v2-button" href={route("research/")}>Explore supporting research</a></div>
        <DraftBoundary>The technical and govtech artifacts support the governance argument; they do not establish a successful model intervention, live deployment, authentic audience exposure, human persuasion, durable agency transfer, end-to-end policy effectiveness, or an AI-attributable electoral outcome.</DraftBoundary>
      </header>
      <section className="v2-paper-abstract" id="abstract"><p className="v2-eyebrow">Abstract</p>{paperAbstract.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}</section>
      <section className="v2-paper-abstract" id="policy-update"><p className="v2-eyebrow">Policy update · v1.2</p><p>The original six records were an audit sample, not six effective policies. Their retained implementation-level classifications are one established bounded component effect, three strong inferences and two open questions. The new A–F layer classifies all 118 implementations but adds no empirical claim-source adjudications.</p><p>Group A is a provisional priority set, not five proven policies: the forwarding-limit review remains an open question. Functional portability remains a pilot priority in E. The other 112 effect claims still lack a checked empirical relation in the reproducible core; this does not show that no relevant literature exists or that those controls fail.</p><TextLink href={route("research/part-iv/")}>Read the comparative recommendations</TextLink></section>
      <div className="v2-wide-figure"><EditorialRiftVisual /><p className="v2-figure-caption">The three large stages are an organising frame, not a universal linear ladder. Every transition requires new evidence.</p></div>
      <section className="v2-paper-sections"><div className="v2-section-lead"><div><p className="v2-eyebrow">Web overview</p><h2>Contents of v1.2</h2></div><p>The v1.2 manuscript and this overview distinguish provisional policy recommendations from checked empirical evidence. The empirical freeze remains 28 August 2026; the 1 September classification update adds no adjudications. Public downloadable manuscript hosting remains separate from this overview.</p></div><ol>{paperSections.map(([number, title, summary]) => <li key={number}><span>{number}</span><div><h3>{title}</h3><p>{summary}</p></div></li>)}</ol></section>
      <blockquote className="v2-rule-quote">Do not promote upstream evidence into downstream claims. Do not wait for downstream proof before acting on an evidenced upstream mechanism.</blockquote>
    </main>
  );
}

export function OutputsPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Resources" title="One programme, several forms" deck="The paper supplies the argument. The four research parts supply the evidence record. Visuals, datasets, and tools make specific mechanisms inspectable without silently upgrading the claim." />
      <section className="v2-output-groups">
        <div><p className="v2-eyebrow">Core publications</p><article><h2>Flagship working paper v1.2</h2><p>Revised 1 September 2026; empirical freeze 28 August 2026. The revision separates 118 classified implementations from six checked empirical effect claims and treats A–F as provisional recommendations, not an efficacy ranking.</p><div className="v2-card-links"><TextLink href={route("paper/")}>Open web overview</TextLink></div></article><article id="white-paper"><h2>The Persuasion Machines</h2><p>Accessible adjacent synthesis for policy and general audiences. Current edition remains a working draft; the standalone canonical file will be added without changing this route.</p></article></div>
        <div><p className="v2-eyebrow">Visual overview</p><article id="poster"><h2>Research poster</h2><p>The final canonical poster is pending. The current visual direction uses the CDE Rift and mechanism illustrations without presenting unrelated evidence counts as one score.</p><EditorialRiftVisual /></article><article><h2>CDE Rift animation</h2><p>Timed explanatory presentation of the programme’s central causal and evidentiary distinction.</p><TextLink href={RIFT_ANIMATION}>Open animation</TextLink></article></div>
        <div><p className="v2-eyebrow">Data and tools</p><article><h2>Frontier Evaluation Registry</h2><p>Part II: benchmark-native outcomes, evidence review, and testing record.</p><TextLink href={route("research/part-ii/")}>Open Registry</TextLink></article><article><h2>Election Evidence Index</h2><p>Part III: claim-level public election evidence.</p><TextLink href={ELECTION_INDEX_URL} external>Open dataset</TextLink></article><article><h2>Policy Atlas · beta.3</h2><p>Part IV: all 118 comparative assignments are in the published CSV/Parquet dataset. Existing empirical grades are unchanged; classification is not verification.</p><div className="v2-card-links"><TextLink href={POLICY_ATLAS_URL} external>Open dataset</TextLink><TextLink href={`${REPOSITORY_URL}/blob/main/policy-atlas/COMPARATIVE_EVIDENCE_GROUPS.md`} external>Read grouping</TextLink></div></article><article><h2>Agency Transfer Lab</h2><p>Evidence-harness and control-semantics prototype.</p><TextLink href={LAB_URL} external>Open Lab</TextLink></article></div>
      </section>
    </main>
  );
}

export function ExplainersPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Explainers" title="Explain the mechanism, not the spectacle" deck="These artifacts make the system legible. Synthetic scenarios are illustrations, not observations of real campaigns, authentic exposure, behaviour change, or electoral effect." />
      <AnimationFeature />
      <section className="v2-simple-section"><div className="v2-section-lead"><div><p className="v2-eyebrow">Mechanism map</p><h2>Anatomy of an AI manipulation operation</h2></div><p>A restrained editorial version of the supplied visual: capability, operator control, audience discovery, vulnerability inference, generation, delivery, feedback, adaptation, and objective.</p></div><div className="v2-wide-figure v2-wide-figure--mechanism"><MechanismStrip /><p className="v2-figure-caption">Conceptual illustration. The research did not observe this complete chain operating against real people.</p></div></section>
      <section className="v2-explainer-cards"><article><p className="v2-eyebrow">Synthetic scenario</p><h2>Manuel · Miami · US midterms</h2><p>A fictional voter is found through a political community, modelled through salient trust cues, and targeted with synthetic audio near an election. The scenario illustrates discovery, identity, delivery, repetition, and scale.</p><TextLink href={MANUEL_VIDEO_URL} external>Watch video</TextLink><small>Not evidence of a real campaign or effect.</small></article><article><p className="v2-eyebrow">Synthetic scenario</p><h2>Brazil 2026 · the final-hour voice</h2><p>A fictional cloned-audio scenario illustrates the difference between generation, deployment, individual response, and an unmeasured aggregate consequence.</p><span className="v2-status-pill">Draft master retained · public host pending</span><small>Not evidence that the depicted operation occurred or generalises to real voters.</small></article></section>
    </main>
  );
}

export function AboutPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="About" title="A maintained record of an unfinished systems problem" deck="The programme asks when frontier AI capability can become harmful influence infrastructure, who controls the joins, what evidence exists at each node, and when control becomes a transfer of agency and democratic power." />
      <section className="v2-about-grid"><article><p className="v2-eyebrow">Author</p><h2>Miguel Guerrero</h2><p>ERA:AI Research Fellow in Cambridge, senior AI adviser in government, founder of Saturdays.AI, engineer, educator, and researcher working across adoption, governance, safety, and democratic resilience.</p><p>This is independent research. It is not an official position of ERA, Cambridge, or any institution with which the author is affiliated.</p></article><article><p className="v2-eyebrow">Evidence policy</p><h2>Primary programme records are not independent replication</h2><p>Project-produced traces, recovered evaluations, coding decisions, and curated datasets document what this programme recorded. They do not constitute peer review or independent corroboration of downstream effects.</p></article><article><p className="v2-eyebrow">Responsible release</p><h2>Publish the argument, not operational tradecraft</h2><p>The public record publishes concepts, aggregates, source-linked claims, defensive methods, and synthetic explainers. It withholds campaign-ready outputs, targetable profiles, evasion methods, credentials, raw harmful traces, and private validation material.</p><TextLink href={`${REPOSITORY_URL}/blob/main/RESPONSIBLE_RELEASE.md`} external>Read policy</TextLink></article></section>
      <section className="v2-citation"><p className="v2-eyebrow">Citation</p><p>Guerrero, Miguel. 2026. <em>Harmful Manipulation and Election Security: The Capability–Deployment–Effect Gap.</em> ERA:AI Summer Research Fellowship, Cambridge. Flagship working paper, v1.2, 1 September 2026.</p></section>
    </main>
  );
}

export function UpdatesPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Draft log" title="What changed, and why" deck="This page records material revisions to the public programme. It is not a news feed." />
      <section className="v2-update-list"><article><time>1 Sep 2026</time><div><h2>Canonical synchronization · Atlas beta.3 and paper v1.2</h2><p>Published the A–F classification as data for all 118 implementations, rather than narrative only. Preserved empirical grades and the six checked effect claims. Updated the paper, source metadata and evidence boundaries: classification coverage is not verification coverage.</p></div></article><article><time>1 Sep 2026</time><div><h2>Comparative policy-evidence synthesis</h2><p>Corrected the six-policy interpretation. The six re-audited records are an audit sample, not a shortlist. Grouped all 118 implementations into six provisional recommendation postures.</p></div></article><article><time>28 Aug 2026</time><div><h2>Flagship working paper v1.0</h2><p>Reframed the programme around harmful manipulation, election security, the CDE Gap, agency transfer, and democratic self-correction.</p></div></article><article><time>28 Aug 2026</time><div><h2>Editorial redesign</h2><p>Reduced the homepage to the core claim, four research parts, the animated Rift, and key artifacts. Part II remains the complete featured public artifact.</p></div></article><article><time>Next</time><div><h2>Evidence upgrade</h2><p>Independent coding, full-text adjudication of priority sources, and intervention-specific effect studies before any stronger effectiveness claim.</p></div></article></section>
    </main>
  );
}
