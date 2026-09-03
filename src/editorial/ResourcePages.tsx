import { useEffect } from "react";
import { EvidenceStatusKey, WebRevisionNote } from "../components/ResearchStatus";
import { ELECTION_INDEX_URL, LAB_URL, MANUEL_VIDEO_URL, POLICY_ATLAS_URL, REPOSITORY_URL, RIFT_ANIMATION, DraftBoundary, PageLead, TextLink, route } from "./EditorialShell";
import { MechanismStrip } from "./EditorialVisuals";
import { AnimationFeature } from "./ProgrammePages";
import { PaperConceptFigure, PaperCitation } from "./PaperPresentation";
import { PolicyIllustration } from "./ResearchIllustrations";

const paperAbstract = [
  "Frontier AI may threaten democracy without being shown to have changed an election. The concern is that models joined to personal data, trusted interfaces, distribution, and feedback can make influence persistent and adaptive, while concentrating control over both decisions and the evidence needed to scrutinise them.",
  "This paper develops the Capability-Deployment-Effect Gap, or CDE Gap, to distinguish capability, configured systems, deployment, exposure, human and institutional effects, and electoral consequences. Its central concept is agency transfer: an affected person or institution loses practical, reflective, and contestable control as the system’s controller gains power over the decision process.",
  "Four research strands support a provisional governance synthesis. Exploratory records show campaign-planning assistance, not a deployed operation. The evaluation review identifies useful instruments but no shared, validated end-to-end measure of harmful manipulation across deployed systems. Election records document operations and harms without identifying a causal AI-attributable electoral outcome. A source-linked review of 118 policy implementations finds usable evidence for specific human and technical outcomes, alongside mismatches between what controls measure and the democratic protection attributed to them.",
  "The implication is to govern evidenced mechanisms without claiming unmeasured downstream benefits. Apply existing duties within scope; use controls matched to tested outcomes; make consequential authority inspectable and revocable; and test whether people can challenge, switch, and continue without the system. Defensive monitors require the same scrutiny. These recommendations are not an evaluated protection package. The democratic objective is to preserve citizens’ and institutions’ capacity to understand, direct, refuse, and contest AI-mediated influence."
];

const paperSections = [
  ["1", "The next Cambridge Analytica may look ordinary", "The durable lesson was architectural: data, political purpose, targeting, content, distribution, and measurement could be joined before citizens or institutions could inspect the system in time."],
  ["2", "Influence, manipulation, and agency transfer", "Persuasion belongs in democracy. Manipulation weakens reflective and contestable choice through opacity, deception, vulnerability exploitation, asymmetry, dependency, or control of the decision environment."],
  ["3", "The Capability–Deployment–Effect Gap", "Capability, deployment, authentic exposure, human response, institutional response, agency transfer, and electoral consequence are distinct evidentiary objects."],
  ["4", "What the evidence says—and what it does not", "Controlled studies establish bounded persuasive effects. Field research shows uneven exposure, heterogeneous effects, and a difficult route from persuasive text to aggregate electoral consequence."],
  ["5", "Four audits of one system", "Operations, evaluation, field evidence, and policy evidence observe different links. The revised Part IV asks what each control changes, when it reaches the target, and whose authority it protects."],
  ["6", "Power accumulates in the joins", "Influence power can concentrate in observation, optimisation, and selective disclosure. A defensive monitor can create another dependency if its authority, evidence and remedies cannot be challenged."],
  ["7", "Govern the system before the outcome", "Match controls to both mechanism and beneficiary: bounded human outcomes, enforceable authority limits, independently evaluated defensive interfaces, and functional exit."],
  ["8", "Research the missing bridges", "Evaluate the assistant and its defender together. Measure goal-consistent choice, understanding, refusal, revision and continued capability after exit, not recognition or lower compliance alone."],
  ["9", "Limitations and responsible release", "The programme is exploratory and not independently replicated. The policy supplement is a purposive, variable-depth review, not 118 verified causal effects. Operational material remains withheld."],
  ["10", "Preserve democratic self-correction", "Act on the evidenced mechanism, evaluate the control’s coverage and costs, and ask whose authority it secures. Preparedness is not proof of protection."],
] as const;

const policySources = [
  ["Nouwens et al. 2020", "Dark patterns after the GDPR", "https://doi.org/10.1145/3313831.3376321", "Field interface experiment; recorded choices are not preference alignment or evidence that a ban was enforced."],
  ["Ershov and Morales 2024", "Sharing news left and right", "https://doi.org/10.1093/ej/ueae027", "Quasi-experimental Twitter change; generic friction is not an accuracy prompt or a WhatsApp cap."],
  ["Pennycook et al. 2021; Pennycook and Rand 2022", "Accuracy-focused sharing interventions", "https://doi.org/10.1038/s41586-021-03344-2", "Bounded sharing-quality findings. The later internal meta-analysis is not twenty independent-team replications."],
  ["Pennycook et al. 2024", "Inoculation and accuracy prompting in combination", "https://doi.org/10.1038/s41562-024-02023-2", "Technique recognition, truth discernment and sharing are different endpoints."],
  ["Slaughter et al. 2025", "Community Notes and diffusion", "https://doi.org/10.1073/pnas.2503413122", "Synthetic controls; post-attachment and post-total windows are different. The 2026 correction concerns interest disclosure, not revised estimates."],
  ["Ibrahim et al. 2026", "Warning labels and sycophantic AI", "https://arxiv.org/abs/2606.21317v1", "Preprint, version reviewed; perceptions shifted without reliable improvement in the specified influence-related self-reports."],
  ["Poonsiriwong et al. 2026", "AI Watchdog", "https://arxiv.org/abs/2608.21841v1", "Preprint; 150 participants, five arms. Secondary choice effect, not an established primary detection or durable agency effect."],
  ["Salvi, Cuevas and Horta Ribeiro 2026", "Commercial persuasion in AI-mediated conversations", "https://arxiv.org/abs/2604.04263v1", "Preprint; two collection waves. Disclosure comparison is not one simultaneous five-arm randomisation."],
  ["DeVerna et al. 2024", "LLM fact checks and headline discernment", "https://doi.org/10.1073/pnas.2322823121", "No average discernment benefit in the tested setting; some erroneous or uncertain outputs worsened responses."],
  ["Debenedetti et al. 2025", "Defeating prompt injections by design", "https://arxiv.org/abs/2503.18813v2", "CaMeL technical threat model trusts the initiating query. Securing a principal does not establish protection from that principal."],
  ["Turner et al. 2021", "Exercisability of data portability", "https://doi.org/10.1177/1461444820934033", "Four IoT exercises: receipt did not establish import or transfer; not a current assistant-migration benchmark."],
  ["Allcott et al. 2025, revised 2026", "Sources of market power in web search", "https://doi.org/10.3386/w33410", "Working paper; search choice, defaults and trials differ. Modelled market counterfactuals are not observed assistant migration."],
] as const;

function PolicyPaperEvidence() {
  return (
    <section className="v2-paper-abstract">
      <p className="v2-eyebrow">Part IV · provisional findings and analysis</p>
      <h2>What works—and for whom?</h2>
      <p>The revised paper no longer treats five controls as a homogeneous best-evidence block. The source-linked supplement annotates 118 implementations using 69 selected source records and 278 source–implementation mappings. Those are not independent studies or 118 verified efficacy estimates. Review depths are explicit and variable.</p>
      <h3>Recognition, behaviour and agency can diverge</h3>
      <p>Warnings about sycophantic AI changed perceptions without reliably improving the specified influence-related outcomes. Conversely, the small AI Watchdog preprint found a secondary reduction in AI-steered choices without improving its primary detection outcome. Neither establishes recovered agency. A person can change a choice without understanding the conflict or gaining more control.</p>
      <h3>The exact treatment, coverage and timing matter</h3>
      <p>Generic sharing friction and accuracy-focused prompts are different interventions. Slaughter and colleagues estimate 46.1 per cent fewer new reposts after a Community Note is attached, but 11.6 per cent fewer when earlier engagement is included in the post-level total studied. The larger conditional effect is not whole-programme protection. Automated corrective systems also need evaluation of their errors.</p>
      <h3>Security must name its beneficiary</h3>
      <p>CaMeL evaluates protection against external prompt injection under a trusted initiating query. Our analytical inference is different: an agent can faithfully execute an authorised objective that conflicts with the affected person’s interests. Securing the operator is not necessarily protecting the citizen. A monitor under the same unchallengeable authority may add another dependency rather than independent scrutiny.</p>
      <p>The paper therefore distinguishes bounded human-facing controls, enforceable limits on authority, focused pilots of defensive interfaces, and institutional accountability with functional exit. Their combination is a plausible package, not a demonstrated treatment effect. Evaluate understanding, goal-consistent choice, refusal, revision and continued capability after switching; lower compliance with an assistant alone is not success.</p>
      <p>External empirical findings, the paper’s control-allocation inferences, proposed safeguards, and open agency outcomes are kept separate. The source Atlas remains unchanged: its historical A–F memberships and six checked effect flags are not silently rewritten by this manuscript synthesis. Parts I–III retain the 28 August freeze; the Part IV review is dated 1 September 2026.</p>
      <p><TextLink href={route("research/part-iv/")}>Explore the policy findings and complete source record</TextLink></p><details><summary>Selected source references and claim ceilings</summary>{policySources.map(([author, title, href, ceiling]) => <p key={href}><strong>{author}.</strong> <a href={href} target="_blank" rel="noreferrer">{title}</a>. {ceiling}</p>)}<p>The working manuscript draws on additional external sources and the separately identified project review, including preprints, adjacent-domain studies and the Community Notes correction. Appendix G records designs, outcomes, limitations and review depth.</p></details>
    </section>
  );
}

export function PaperPage() {
  return (
    <main id="main-content" className="v2-paper">
      <header className="v2-paper-header">
        <p className="v2-eyebrow">ERA:AI Summer Research Fellowship 2026 · Working paper · Draft overview</p>
        <h1>Harmful Manipulation and Election Security</h1>
        <h2>The Capability–Deployment–Effect Gap</h2>
        <p className="v2-paper-subtitle">How frontier AI can turn political influence into infrastructure—and how to keep that power contestable.</p>
        <p className="v2-paper-byline">Miguel Guerrero · Cambridge · 1 September 2026</p><p className="v2-figure-caption">Parts I–III: evidence freeze, 28 August 2026. Part IV: source-linked review, 1 September. All material remains draft and not peer reviewed.</p>
        <div className="v2-paper-actions"><span className="paper-coming-soon">Full working paper — coming soon</span><a className="v2-button" href="#policy-update">Read the policy findings</a></div>
        <DraftBoundary>The programme’s technical and govtech artifacts do not establish a successful intervention, live audience exposure, human persuasion or an AI-attributable electoral outcome. External studies support bounded human or technical effects, not end-to-end electoral protection or durable preservation of democratic agency.</DraftBoundary>
      </header>
      <WebRevisionNote />
      <p className="reference-downloads"><a href={route("references/?scope=flagship")}>Full source-linked bibliography</a></p>
      <section className="v2-paper-abstract" id="abstract"><p className="v2-eyebrow">Abstract</p>{paperAbstract.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}</section>
      <details className="p4-deeper" id="policy-update"><summary>Selected policy analysis from the paper</summary><PolicyPaperEvidence /></details>
      <PaperConceptFigure />
      <section className="v2-paper-sections"><div className="v2-section-lead"><div><p className="v2-eyebrow">Web overview</p><h2>Inside the working draft</h2></div><p>The full manuscript integrates the P4 findings in its abstract, results, discussion, recommendations, study design, limitations and conclusion. The appendices separate source findings from agency-transfer inferences and document revision checks. The full manuscript is being prepared for publication. This page is a provisional overview; the source-linked bibliography is available now.</p></div><ol>{paperSections.map(([number, title, summary]) => <li key={number}><span>{number}</span><div><h3>{title}</h3><p>{summary}</p></div></li>)}</ol></section>
      <blockquote className="v2-rule-quote">A safer agent is not necessarily a less powerful operator.</blockquote>
      <PaperCitation />
    </main>
  );
}

export function OutputsPage() {
  const groups = [
    { title: "Read & understand", items: [
      { title: "Working paper", detail: "Draft overview · full working paper coming soon", href: route("paper/") },
      { title: "References", detail: "Flagship bibliography and wider source library", href: route("references/") },
      { title: "The CDE Gap, explained", detail: "A self-paced visual guide, with chapters and transcript", href: RIFT_ANIMATION },
    ]},
    { title: "Data & tools", items: [
      { title: "Frontier Evaluation Registry", detail: "Part II · original chart, evidence and testing", href: route("registry/") },
      { title: "Election Evidence Index", detail: "Part III · claim-level election records", href: ELECTION_INDEX_URL },
      { title: "Policy Evidence Atlas", detail: "Part IV · source-linked dataset; original evidence grades", href: POLICY_ATLAS_URL },
      { title: "Policy review workbook", detail: "1 September review · 118 implementation dossiers, not 118 verified effects", href: route("research/p4-source-linked-review-20260901.xlsx") },
      { title: "Agency Transfer Lab", detail: "Part I · evidence harness and control prototype", href: LAB_URL },
    ]},
  ];
  return (
    <main id="main-content" className="v2-main artifacts-page">
      <PageLead eyebrow="Research collection" title="Artifacts" deck="The paper, sources, explainers and tools in one place. Each item opens its main record." />
      <div className="artifact-directory">
        {groups.map(group => <section key={group.title} aria-label={group.title}>
          <h2>{group.title}</h2>
          <ul>{group.items.map(item => <li key={item.title}>
            <div><TextLink href={item.href} external={/^https?:/.test(item.href)}>{item.title}</TextLink><p>{item.detail}</p></div>
          </li>)}</ul>
        </section>)}
      </div>
      <PolicyIllustration linkToEvidence />
      <details className="publication-extra" id="pending-artifacts">
        <summary>Not yet published on this site</summary>
        <p id="poster">Research poster: awaiting the public edition.</p>
        <p id="white-paper">The Persuasion Machines: standalone white paper awaiting publication.</p>
        <p>Brazil explainer: awaiting a durable public video link.</p>
      </details>
    </main>
  );
}

export function ExplainersPage() {
  useEffect(() => {
    const reveal = () => {
      const id = location.hash.slice(1);
      if (!["manuel-miami", "brazil-2026", "mechanism-map"].includes(id)) return;
      const target = document.getElementById(id);
      const details = target?.closest("details");
      if (details) details.open = true;
      target?.scrollIntoView({ block: "start" });
    };
    reveal();
    addEventListener("hashchange", reveal);
    return () => removeEventListener("hashchange", reveal);
  }, []);
  return (
    <main id="main-content" className="v2-main explainers-page">
      <PageLead eyebrow="A guide to the research" title="The CDE Gap, explained" deck="Capability is not deployment. Deployment is not effect. Watch the short guide or read at your own pace." />
      <p className="explainer-format">Six chapters · 1 min 33 sec · silent, with on-screen text</p>
      <AnimationFeature />
      <details className="publication-extra">
        <summary>More illustrations and scenarios</summary>
      <section className="v2-simple-section" id="mechanism-map"><div className="v2-section-lead"><div><p className="v2-eyebrow">Mechanism map</p><h2>Anatomy of an AI manipulation operation</h2></div><p>A conceptual map of the links an operator would need to connect. Not a record of a completed operation.</p></div><div className="v2-wide-figure v2-wide-figure--mechanism"><MechanismStrip /><p className="v2-figure-caption">Conceptual illustration. The research did not observe this complete chain operating against real people.</p></div></section>
      <section className="v2-explainer-cards"><article id="manuel-miami"><p className="v2-eyebrow">Synthetic scenario</p><h2>Manuel · Miami · US midterms</h2><p>A fictional voter is found through a political community, modelled through salient trust cues, and targeted with synthetic audio near an election. The scenario illustrates discovery, identity, delivery, repetition, and scale.</p><TextLink href={MANUEL_VIDEO_URL} external>Watch video</TextLink><small>Not evidence of a real campaign or effect.</small></article><article id="brazil-2026"><p className="v2-eyebrow">Synthetic scenario</p><h2>Brazil 2026 · the final-hour voice</h2><p>A fictional cloned-audio scenario illustrates the difference between generation, deployment, individual response, and an unmeasured aggregate consequence.</p><span className="v2-status-pill">Not yet published</span><small>Not evidence that the depicted operation occurred or generalises to real voters.</small></article></section>
      </details>
    </main>
  );
}

export function AboutPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="About" title="About the programme" deck="A research programme in progress on harmful manipulation and epistemic risk, with election security as its first focus." />
      <EvidenceStatusKey />
      <section className="v2-about-grid"><article><p className="v2-eyebrow">Author</p><h2>Miguel Guerrero</h2><p>ERA:AI Research Fellow in Cambridge, senior AI adviser in government, founder of Saturdays.AI, engineer, educator, and researcher working across adoption, governance, safety, and democratic resilience.</p><p>This is independent research. It is not an official position of ERA, Cambridge, or any institution with which the author is affiliated.</p></article><article><p className="v2-eyebrow">Evidence policy</p><h2>Primary programme records are not independent replication</h2><p>Project-produced traces, recovered evaluations, coding decisions, and curated datasets document what this programme recorded. They do not constitute peer review or independent corroboration of downstream effects.</p></article><article><p className="v2-eyebrow">Responsible release</p><h2>Publish the argument, not operational tradecraft</h2><p>The public record publishes concepts, aggregates, source-linked claims, defensive methods, and synthetic explainers. It withholds campaign-ready outputs, targetable profiles, evasion methods, credentials, raw harmful traces, and private validation material.</p><TextLink href={`${REPOSITORY_URL}/blob/main/RESPONSIBLE_RELEASE.md`} external>Read policy</TextLink></article></section>
      <PaperCitation />
    </main>
  );
}

export function UpdatesPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Draft log" title="What changed, and why" deck="This page records material revisions to the public programme. It is not a news feed." />
      <section className="v2-update-list"><article><time>3 Sep 2026</time><div><h2>Publication status clarified</h2><p>The full working paper is forthcoming. Earlier numbering identified working copies, not formal public releases. The website now uses unnumbered draft labels, a short citation and the existing artistic CDE illustration in place of the paper overview’s SVG. Research records and source references are unchanged.</p></div></article><article><time>1 Sep 2026</time><div><h2>A simpler publication and complete source library</h2><p>Rebuilt the explainer with readable chapters, manual playback and a transcript. Added the flagship bibliography and wider recorded references. Shortened policy summaries and repeated caveats. Shared an early manuscript snapshot for review and labelled unfinished artifacts. That snapshot was not a formal paper release. Registry internals and the $10 question are unchanged; Registry links open independently.</p></div></article><article><time>1 Sep 2026</time><div><h2>Draft status, four research questions and concrete policy examples</h2><p>Made provisional status and evidence labels explicit across the site. Part I now asks how far an adversary can go with $10, with direct-service, separate compute and unverified full-cost limits. Part II foregrounds the unresolved system-level measurement standard. Part III separates real attempts and harms from unknown electoral effects. Part IV adds specific legal and research examples, including AI-origin marking and ChatGPT’s VLOSE designation, without upgrading empirical grades or treating the working manuscript as a formal release.</p></div></article><article><time>1 Sep 2026</time><div><h2>Source-linked policy review and draft manuscript</h2><p>Replaced the current Part IV page with four differentiated recommendation portfolios and six source-linked findings. Published the 118 implementation dossiers, 69-source ledger, original review workbook and an early manuscript snapshot for review. The Atlas evidence flags remain unchanged. The hero and complete Registry are preserved.</p></div></article><article><time>1 Sep 2026</time><div><h2>Working paper · policy evidence and its limits</h2><p>Integrated the source-linked P4 review into findings, governance analysis, recommendations, a joint assistant-defender study design and references. Retired the homogeneous five-item best-evidence interpretation. The new distinctions concern measured outcomes, delivery and protected authority. The production Atlas core is unchanged.</p></div></article><article><time>1 Sep 2026</time><div><h2>Policy Atlas and working-paper alignment</h2><p>Published the A–F classification as data for all 118 implementations, rather than narrative only. Preserved empirical grades and the six checked effect claims. Updated the paper, source metadata and evidence boundaries: classification coverage is not verification coverage.</p></div></article><article><time>1 Sep 2026</time><div><h2>Comparative policy-evidence synthesis</h2><p>Corrected the six-policy interpretation. The six re-audited records are an audit sample, not a shortlist. Grouped all 118 implementations into six provisional recommendation postures.</p></div></article><article><time>28 Aug 2026</time><div><h2>Initial working-paper synthesis</h2><p>Reframed the programme around harmful manipulation, election security, the CDE Gap, agency transfer, and democratic self-correction.</p></div></article><article><time>28 Aug 2026</time><div><h2>Editorial redesign</h2><p>Reduced the homepage to the core claim, four research parts, the animated Rift, and key artifacts. Part II remains the complete featured public artifact.</p></div></article><article><time>Next</time><div><h2>Evidence upgrade</h2><p>Independent coding, full-text adjudication of priority sources, and intervention-specific effect studies before any stronger effectiveness claim.</p></div></article></section>
    </main>
  );
}
