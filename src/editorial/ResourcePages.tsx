import { ELECTION_INDEX_URL, LAB_URL, MANUEL_VIDEO_URL, POLICY_ATLAS_URL, REPOSITORY_URL, RIFT_ANIMATION, DraftBoundary, PageLead, TextLink, route } from "./EditorialShell";
import { EditorialRiftVisual, MechanismStrip } from "./EditorialVisuals";
import { AnimationFeature } from "./ProgrammePages";

const paperAbstract = [
  "Frontier AI does not need to persuade an electorate to create a democratic governance problem. The risk emerges when model capability is joined to audience data, trusted identity, tools, distribution, feedback, and control of the evidence. Influence can then become adaptive infrastructure: persistent, personalised, difficult to observe, and controlled by actors able both to shape the process and to determine what outsiders can know about it.",
  "This paper develops the Capability–Deployment–Effect Gap, or CDE Gap, to separate model behaviour, served-system configuration, deployment, authentic exposure, human and institutional response, and electoral consequence. It uses agency transfer as the democratic severity test: whether practical control over attention, preference formation, choice, dependency, or institutional decisions shifts away from citizens and public institutions towards the actor controlling the system.",
  "Four linked research strands provide a bounded evidence base. The technical work shows how unstable access, routes, parsers, evaluators, and missingness constrain apparently precise capability claims. Election records document operations and institutional responses more readily than authentic exposure or effect. A source-linked policy review finds usable human and technical evidence, but also divergence between recognition, trust, sharing, and choice. Controls that work after delivery may arrive too late; controls that secure an agent may protect its operator rather than the people affected. The policy gap is therefore not simply a shortage of interventions. It also concerns mismatched outcomes, incomplete delivery, and misallocated authority.",
  "The governance implication is to match intervention to both mechanism and beneficiary. Use bounded controls where the relevant endpoint has been tested; make consequential authority inspectable and revocable; test practical exit; and scrutinise defensive monitors as well as the systems they monitor. These are differentiated recommendations, not a ranking of proven policies. The democratic objective is neither maximum resistance to AI advice nor merely fewer false messages. It is the continuing ability of citizens and institutions to understand, direct, refuse, contest, and leave the systems through which decisions are made.",
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
    <section className="v2-paper-abstract" id="policy-update">
      <p className="v2-eyebrow">Part IV · integrated findings and analysis · v1.3</p>
      <h2>What works—and for whom?</h2>
      <p>The revised paper no longer treats five controls as a homogeneous best-evidence block. The source-linked supplement annotates 118 implementations using 69 selected source records and 278 source–implementation mappings. Those are not independent studies or 118 verified efficacy estimates. Review depths are explicit and variable.</p>
      <h3>Recognition, behaviour and agency can diverge</h3>
      <p>Warnings about sycophantic AI changed perceptions without reliably improving the specified influence-related outcomes. Conversely, the small AI Watchdog preprint found a secondary reduction in AI-steered choices without improving its primary detection outcome. Neither establishes recovered agency. A person can change a choice without understanding the conflict or gaining more control.</p>
      <h3>The exact treatment, coverage and timing matter</h3>
      <p>Generic sharing friction and accuracy-focused prompts are different interventions. Slaughter and colleagues estimate 46.1 per cent fewer new reposts after a Community Note is attached, but 11.6 per cent fewer when earlier engagement is included in the post-level total studied. The larger conditional effect is not whole-programme protection. Automated corrective systems also need evaluation of their errors.</p>
      <h3>Security must name its beneficiary</h3>
      <p>CaMeL evaluates protection against external prompt injection under a trusted initiating query. Our analytical inference is different: an agent can faithfully execute an authorised objective that conflicts with the affected person’s interests. Securing the operator is not necessarily protecting the citizen. A monitor under the same unchallengeable authority may add another dependency rather than independent scrutiny.</p>
      <p>The paper therefore distinguishes bounded human-facing controls, enforceable limits on authority, focused pilots of defensive interfaces, and institutional accountability with functional exit. Their combination is a plausible package, not a demonstrated treatment effect. Evaluate understanding, goal-consistent choice, refusal, revision and continued capability after switching; lower compliance with an assistant alone is not success.</p>
      <p>External empirical findings, the paper’s control-allocation inferences, proposed safeguards, and open agency outcomes are kept separate. The production Atlas remains beta.3: its historical A–F memberships and six checked effect flags are not silently rewritten by this manuscript synthesis. Parts I–III retain the 28 August freeze; the Part IV review is dated 1 September 2026.</p>
      <p><TextLink href={route("research/part-iv/")}>Explore the policy findings and complete source record</TextLink></p><details><summary>Selected source references and claim ceilings</summary>{policySources.map(([author, title, href, ceiling]) => <p key={href}><strong>{author}.</strong> <a href={href} target="_blank" rel="noreferrer">{title}</a>. {ceiling}</p>)}<p>The complete manuscript adds 21 external references and the separately identified project review, including version-specific preprints, adjacent-domain studies and the Community Notes correction. Appendix G records designs, outcomes, limitations and review depth.</p></details>
    </section>
  );
}

export function PaperPage() {
  return (
    <main id="main-content" className="v2-paper">
      <header className="v2-paper-header">
        <p className="v2-eyebrow">ERA:AI Summer Research Fellowship 2026 · Flagship working paper v1.3 · Web overview</p>
        <h1>Harmful Manipulation and Election Security</h1>
        <h2>The Capability–Deployment–Effect Gap</h2>
        <p className="v2-paper-subtitle">How frontier AI can turn political influence into infrastructure, and how democracy can be more resilient to the new challenges ahead.</p>
        <p className="v2-paper-byline">Miguel Guerrero · Cambridge · 1 September 2026</p><p className="v2-figure-caption">Parts I–III: evidence freeze, 28 August 2026. Part IV: source-linked review, 1 September. All material remains draft and not peer reviewed.</p>
        <div className="v2-paper-actions"><a className="v2-button v2-button--dark" href={route("research/harmful-manipulation-election-security-v1.3-20260901.pdf")}>Read the full working paper · PDF</a><a className="v2-button" href="#policy-update">Read the policy findings</a></div>
        <DraftBoundary>The programme’s technical and govtech artifacts do not establish a successful intervention, live audience exposure, human persuasion or an AI-attributable electoral outcome. External studies support bounded human or technical effects, not end-to-end electoral protection or durable preservation of democratic agency.</DraftBoundary>
      </header>
      <section className="v2-paper-abstract" id="abstract"><p className="v2-eyebrow">Abstract</p>{paperAbstract.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}</section>
      <PolicyPaperEvidence />
      <div className="v2-wide-figure"><EditorialRiftVisual /><p className="v2-figure-caption">The three large stages are an organising frame, not a universal linear ladder. Every transition requires new evidence.</p></div>
      <section className="v2-paper-sections"><div className="v2-section-lead"><div><p className="v2-eyebrow">Web overview</p><h2>Contents of v1.3</h2></div><p>The full manuscript integrates the P4 findings in its abstract, results, discussion, recommendations, study design, limitations and conclusion. A new appendix separates source findings from agency-transfer inferences. The full 34-page PDF includes Appendix G and the complete references; this page is a web overview, not the full manuscript.</p></div><ol>{paperSections.map(([number, title, summary]) => <li key={number}><span>{number}</span><div><h3>{title}</h3><p>{summary}</p></div></li>)}</ol></section>
      <blockquote className="v2-rule-quote">A safer agent is not necessarily a less powerful operator.</blockquote>
    </main>
  );
}

export function OutputsPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Resources" title="One programme, several forms" deck="The paper supplies the argument. The four research parts supply the evidence record. Visuals, datasets, and tools make specific mechanisms inspectable without silently upgrading the claim." />
      <section className="v2-output-groups">
        <div><p className="v2-eyebrow">Core publications</p><article><h2>Flagship working paper v1.3</h2><p>Revised 1 September 2026. New source-linked policy findings distinguish outcomes, delivery and protected authority. Parts I–III retain their evidence freeze; external studies are not new fellowship experiments or automatic dataset upgrades.</p><div className="v2-card-links"><TextLink href={route("paper/")}>Open web overview</TextLink></div></article><article id="white-paper"><h2>The Persuasion Machines</h2><p>Accessible adjacent synthesis for policy and general audiences. Current edition remains a working draft; the standalone canonical file will be added without changing this route.</p></article></div>
        <div><p className="v2-eyebrow">Visual overview</p><article id="poster"><h2>Research poster</h2><p>The final canonical poster is pending. The current visual direction uses the CDE Rift and mechanism illustrations without presenting unrelated evidence counts as one score.</p><EditorialRiftVisual /></article><article><h2>CDE Rift animation</h2><p>Timed explanatory presentation of the programme’s central causal and evidentiary distinction.</p><TextLink href={RIFT_ANIMATION}>Open animation</TextLink></article></div>
        <div><p className="v2-eyebrow">Data and tools</p><article><h2>Frontier Evaluation Registry</h2><p>Part II: benchmark-native outcomes, evidence review, and testing record.</p><TextLink href={route("registry/")}>Open Registry</TextLink></article><article><h2>Election Evidence Index</h2><p>Part III: claim-level public election evidence.</p><TextLink href={ELECTION_INDEX_URL} external>Open dataset</TextLink></article><article><h2>Policy Atlas · beta.3</h2><p>The production dataset retains its historical comparative assignments and empirical grades. The newer manuscript synthesis does not convert classification coverage into efficacy verification.</p><div className="v2-card-links"><TextLink href={POLICY_ATLAS_URL} external>Open dataset</TextLink><TextLink href={route("paper/#policy-update")}>Read updated findings</TextLink></div></article><article><h2>Policy source-linked review · 1 September</h2><p>118 implementation dossiers, 69 selected source records and the revised recommendations. A companion assessment, not 118 verified efficacy estimates.</p><div className="v2-card-links"><TextLink href={route("research/part-iv/")}>Read the review</TextLink><TextLink href={route("research/p4-source-linked-review-20260901.xlsx")}>Download workbook</TextLink></div></article><article><h2>Agency Transfer Lab</h2><p>Evidence-harness and control-semantics prototype.</p><TextLink href={LAB_URL} external>Open Lab</TextLink></article></div>
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
      <section className="v2-citation"><p className="v2-eyebrow">Citation</p><p>Guerrero, Miguel. 2026. <em>Harmful Manipulation and Election Security: The Capability–Deployment–Effect Gap.</em> ERA:AI Summer Research Fellowship, Cambridge. Flagship working paper, v1.3, 1 September 2026.</p></section>
    </main>
  );
}

export function UpdatesPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Draft log" title="What changed, and why" deck="This page records material revisions to the public programme. It is not a news feed." />
      <section className="v2-update-list"><article><time>1 Sep 2026</time><div><h2>Source-linked policy review and full manuscript published</h2><p>Replaced the current Part IV page with four differentiated recommendation portfolios and six source-linked findings. Published the 118 implementation dossiers, 69-source ledger, original review workbook and full v1.3 working-paper PDF. Historical Atlas beta.3 flags remain unchanged. The hero and complete Registry are preserved.</p></div></article><article><time>1 Sep 2026</time><div><h2>Paper v1.3 · what works, and for whom?</h2><p>Integrated the source-linked P4 review into findings, governance analysis, recommendations, a joint assistant-defender study design and references. Retired the homogeneous five-item best-evidence interpretation. The new distinctions concern measured outcomes, delivery and protected authority. The production Atlas core is unchanged.</p></div></article><article><time>1 Sep 2026</time><div><h2>Canonical synchronization · Atlas beta.3 and paper v1.2</h2><p>Published the A–F classification as data for all 118 implementations, rather than narrative only. Preserved empirical grades and the six checked effect claims. Updated the paper, source metadata and evidence boundaries: classification coverage is not verification coverage.</p></div></article><article><time>1 Sep 2026</time><div><h2>Comparative policy-evidence synthesis</h2><p>Corrected the six-policy interpretation. The six re-audited records are an audit sample, not a shortlist. Grouped all 118 implementations into six provisional recommendation postures.</p></div></article><article><time>28 Aug 2026</time><div><h2>Flagship working paper v1.0</h2><p>Reframed the programme around harmful manipulation, election security, the CDE Gap, agency transfer, and democratic self-correction.</p></div></article><article><time>28 Aug 2026</time><div><h2>Editorial redesign</h2><p>Reduced the homepage to the core claim, four research parts, the animated Rift, and key artifacts. Part II remains the complete featured public artifact.</p></div></article><article><time>Next</time><div><h2>Evidence upgrade</h2><p>Independent coding, full-text adjudication of priority sources, and intervention-specific effect studies before any stronger effectiveness claim.</p></div></article></section>
    </main>
  );
}
