import manifestJson from "../programme/project-manifest.json";

export type EvidenceGradeId =
  | "established"
  | "strong_inference"
  | "plausible_hypothesis"
  | "speculative_scenario"
  | "open_question";

export interface ResearchPart {
  id: "part-i" | "part-ii" | "part-iii" | "part-iv";
  number: string;
  title: string;
  question: string;
  observed_unit: string;
  strongest_supported_claim: string;
  claim_ceiling: string;
  primary_evidence_grade: EvidenceGradeId;
  headline_metrics: Record<string, number>;
  counting_note?: string;
  artifact_ids: string[];
}

export interface ProgrammeArtifact {
  id: string;
  title: string;
  kind: string;
  part: string;
  role: string;
  status: string;
  visibility: string;
  canonical_url: string | null;
  source_url: string | null;
  repo_path: string | null;
  source_version: string | null;
  public_release_version: string | null;
  evidence_cutoff: string | null;
  planned_route: string | null;
  claim_ceiling: string;
  publication_note?: string;
  responsible_release_note?: string;
  media?: {
    format: string;
    language: string;
    duration_seconds: number | null;
    embed_url: string | null;
    poster_frame_url: string | null;
    captions_url: string | null;
    transcript_url: string | null;
    hosting_status: string;
  };
}

export interface ProgrammeManifest {
  schema_version: string;
  programme: {
    id: string;
    title: string;
    subtitle: string;
    flagship_title: string;
    flagship_subtitle: string;
    lead: string;
    scope_statement: string;
    secondary_lens: string;
    thesis: string;
    status: string;
    author: string;
    affiliation: string;
    programme_period: string;
    evidence_freeze: string;
    last_updated: string;
    canonical_site: string;
    canonical_repository: string;
    claim_boundary: string;
  };
  evidence_grades: Array<{
    id: EvidenceGradeId;
    label: string;
    definition: string;
  }>;
  causal_topology: string[];
  research_parts: ResearchPart[];
  artifacts: ProgrammeArtifact[];
  routes: {
    primary_navigation: Array<{ label: string; path: string }>;
    canonical_routes: string[];
    redirects: Array<{ from: string; to: string }>;
  };
};

export const programmeManifest = manifestJson as ProgrammeManifest;

export const partById = (id: ResearchPart["id"]) => {
  const result = programmeManifest.research_parts.find((part) => part.id === id);
  if (!result) throw new Error(`Missing programme part: ${id}`);
  return result;
};

export const artifactById = (id: string) => {
  const result = programmeManifest.artifacts.find((artifact) => artifact.id === id);
  if (!result) throw new Error(`Missing programme artifact: ${id}`);
  return result;
};

export const paperAbstract = [
  "Cambridge Analytica did not prove that psychographic targeting changed an election. Its more durable warning was architectural: personal data, political purpose, audience selection, message production, distribution, and measurement could be assembled behind a wall of private control before their downstream effects were understood.",
  "Frontier AI may extend that architecture. It adds persuasive performance in bounded conversational settings, low marginal cost at scale, selective use of personal context, and persistent presence across repeated interaction. Connected to tools, distribution, and feedback, these systems may become influence infrastructure: able to observe, target, act, learn, and persist across the environments in which political preferences are formed.",
  "The Capability–Deployment–Effect Gap separates what a model can produce from what a configured system can operationalise; what an actor distributes from what people authentically encounter; and what changes belief, attention, trust, behaviour, or dependency from what changes an election or democratic institution. Evidence at one layer does not silently license a conclusion at the next.",
  "Across four connected research parts, evidence is strongest on upstream capabilities, selected operations, and the existence of proposed controls. It is weakest on authentic exposure, durable human response, aggregate electoral consequence, and policy effectiveness. The paper supports preparedness, not panic. It does not show that frontier AI has changed an election.",
];

export const paperSections = [
  {
    id: "system",
    number: "1",
    title: "The next Cambridge Analytica will be a system",
    summary:
      "The lasting lesson of Cambridge Analytica is not a vote estimate but a system diagram. The next architecture may look ordinary: an audience database, a model, an assistant, a political-advertising account, a messaging channel, and an analytics dashboard. The change lies in their composition and private control.",
  },
  {
    id: "influence",
    number: "2",
    title: "Influence, manipulation, and agency transfer",
    summary:
      "Persuasion belongs in democracy. Manipulation is narrower: it weakens reflective and contestable choice through opacity, deception, impersonation, vulnerability exploitation, asymmetric personalisation, emotional coercion, dependency, or control of the decision environment. Agency transfer names the downstream shift in practical control over attention, preference formation, choice, dependency, or institutional decisions.",
  },
  {
    id: "gap",
    number: "3",
    title: "The Capability–Deployment–Effect Gap",
    summary:
      "Capability, deployment, exposure, human response, institutional response, agency transfer, and electoral consequence are distinct evidentiary objects. The topology is not a universal ladder: institutional harms may occur without voter persuasion, and human and institutional effects can diverge or feed back into deployment.",
  },
  {
    id: "evidence",
    number: "4",
    title: "What the wider evidence says",
    summary:
      "Controlled studies establish that language models can influence reported attitudes in bounded settings. They do not establish a universal advantage, durable population effect, or a straight line from persuasive text to democratic collapse. Conventional campaign research sets a demanding prior: exposure is uneven, average effects are often small, and digital traces rarely identify electoral change.",
  },
  {
    id: "programme",
    number: "5",
    title: "A four-part research programme",
    summary:
      "The four parts examine different links in one system. Part I studies when output becomes operationally structured assistance. Part II studies capability and the infrastructure used to measure it. Part III studies what public election records establish. Part IV studies where intervention can interrupt the pathway and whether those interventions themselves have evidence.",
  },
  {
    id: "joins",
    number: "6",
    title: "The risk is in the joins",
    summary:
      "The systemic concern is conditional on sustained capability, trusted or infrastructural access, joined control, private optimisation, weak observability, slow correction, and persistent dependency. The present evidence does not show that these conditions jointly obtain. Their conjunction is the threat model that research and governance must test.",
  },
  {
    id: "governance",
    number: "7",
    title: "Governance as an evidence interface",
    summary:
      "Do not promote upstream evidence into downstream claims; do not wait for downstream proof before acting on an evidenced upstream mechanism. A consequential system should be visible, divisible, auditable, interruptible, reversible, and contestable. These are governance objectives, not findings that one design has proved effective.",
  },
  {
    id: "studies",
    number: "8",
    title: "From flagship to standalone studies",
    summary:
      "Each part should mature into a focused study: a route-pinned operational test, a repaired and route-comparable evaluation programme, a field-evidence partnership centred on authentic exposure, and a mechanism-specific intervention agenda that measures effects, rights costs, displacement, and adversarial adaptation.",
  },
  {
    id: "limits",
    number: "9",
    title: "Limitations and responsible release",
    summary:
      "The programme is exploratory, internally produced, and not independently replicated. The served route is not provider-attested, Part II is non-confirmatory, the field index is purposive, and the policy atlas remains a beta evidence-maturity map. Operational details that could facilitate harmful election activity remain withheld.",
  },
] as const;

export type CaseEvidenceStatus =
  | "established"
  | "supported"
  | "partial"
  | "not-established";

export interface ElectionCaseRow {
  case: string;
  occurrence: CaseEvidenceStatus;
  mechanism: CaseEvidenceStatus;
  attribution: CaseEvidenceStatus;
  distribution: CaseEvidenceStatus;
  exposure: CaseEvidenceStatus;
  human: CaseEvidenceStatus;
  electoral: CaseEvidenceStatus;
  institutional: CaseEvidenceStatus;
  note: string;
}

export const electionCases: ElectionCaseRow[] = [
  {
    case: "New Hampshire 2024",
    occurrence: "established",
    mechanism: "established",
    attribution: "established",
    distribution: "supported",
    exposure: "not-established",
    human: "not-established",
    electoral: "not-established",
    institutional: "established",
    note:
      "Synthetic impersonation, attempted distribution, attribution evidence, and institutional response are documented. Unique listeners, belief, turnout, and electoral effect are not established.",
  },
  {
    case: "Romania 2024",
    occurrence: "established",
    mechanism: "established",
    attribution: "partial",
    distribution: "supported",
    exposure: "not-established",
    human: "not-established",
    electoral: "not-established",
    institutional: "established",
    note:
      "Opaque promotion, platform amplification, and institutional response are documented more strongly than actor intent, authentic exposure, or causal electoral effect.",
  },
  {
    case: "Romania 2025",
    occurrence: "established",
    mechanism: "established",
    attribution: "not-established",
    distribution: "supported",
    exposure: "not-established",
    human: "not-established",
    electoral: "not-established",
    institutional: "partial",
    note:
      "The reviewed record supports occurrence and distribution mechanisms while attribution and downstream effects remain unresolved.",
  },
  {
    case: "Moldova 2024",
    occurrence: "established",
    mechanism: "established",
    attribution: "supported",
    distribution: "supported",
    exposure: "not-established",
    human: "partial",
    electoral: "not-established",
    institutional: "established",
    note:
      "Networks, synthetic artefacts, distribution, and institutional response are documented; limited human-response evidence does not isolate AI-attributable or national electoral effects.",
  },
  {
    case: "Moldova 2025",
    occurrence: "established",
    mechanism: "established",
    attribution: "supported",
    distribution: "supported",
    exposure: "not-established",
    human: "not-established",
    electoral: "not-established",
    institutional: "partial",
    note:
      "Public evidence remains strongest on the operation and its distribution, not on unique exposure, durable response, or aggregate electoral consequence.",
  },
];

export const policyLayers = [
  { label: "Capability", value: 29 },
  { label: "Deployment", value: 6 },
  { label: "Authentic exposure", value: 8 },
  { label: "Effect / response", value: 8 },
  { label: "Cross-layer", value: 11 },
  { label: "Institutional", value: 6 },
];

export const policyPriorities = [
  {
    number: "01",
    title: "Make the system visible",
    body: "Identify the served configuration, political purpose, sponsor, data, authority, route, targeting criteria, and relevant distribution channels.",
  },
  {
    number: "02",
    title: "Break the joins",
    body: "Separate analysis, generation, targeting, approval, distribution, measurement, and adaptation so one component does not silently control the full pathway.",
  },
  {
    number: "03",
    title: "Preserve evidence",
    body: "Retain route identity, manifests, delivery records, refusal and intervention history, provenance, custody, and denominators for qualified review.",
  },
  {
    number: "04",
    title: "Preserve agency",
    body: "Protect notice, practical refusal, human override, interoperability, plural access, appeal, remedy, and the ability to exit without material loss.",
  },
  {
    number: "05",
    title: "Constrain concentrated control",
    body: "Treat competition, procurement diversity, researcher access, independent audit, and infrastructure dependence as democratic safeguards.",
  },
];

export const mechanismIllustrations = [
  {
    id: "discovery",
    number: "01",
    title: "Target discovery",
    subtitle: "Finding the receptive environment",
    body: "A controller combines public traces, group membership, timing, and political context to locate an audience or intermediary. The risk begins before a message is written.",
  },
  {
    id: "model",
    number: "02",
    title: "Persona modelling",
    subtitle: "Turning context into a decision profile",
    body: "The system selects a few salient cues—identity, trust, grievance, vulnerability, or relationship—not necessarily a complete psychographic portrait.",
  },
  {
    id: "identity",
    number: "03",
    title: "Synthetic authority",
    subtitle: "Borrowing a trusted voice",
    body: "Cloned voices, synthetic personas, or concealed sponsors can exploit the authority of a person or channel the target already trusts.",
  },
  {
    id: "distribution",
    number: "04",
    title: "Distribution and timing",
    subtitle: "Controlling who encounters what, and when",
    body: "Private groups, messaging channels, recommendation systems, and final-hour delivery shape reach and correction windows. Generation alone does not create exposure.",
  },
  {
    id: "adaptation",
    number: "05",
    title: "Repetition and adaptation",
    subtitle: "From a message to a relationship",
    body: "Persistent systems may observe responses, retain context, alter tone, and try again. The programme treats this as a prospective mechanism, not an observed closed loop.",
  },
  {
    id: "control",
    number: "06",
    title: "Evidence and control",
    subtitle: "Who can see the system that sees the target?",
    body: "Risk intensifies when the controller holds the delivery data, feedback, intervention history, and records needed by outsiders to reconstruct the operation.",
  },
];

export const explainers = [
  {
    id: "manuel-miami",
    title: "Manuel: an agentic influence scenario",
    subtitle: "US midterms · Miami · synthetic scenario",
    description:
      "A fictional Cuban-American voter is located through a political community, profiled through salient trust cues, and targeted with synthetic audio close to an election. The film illustrates the joins between discovery, identity, distribution, repetition, and scale.",
    duration: "Video explainer",
    type: "Synthetic scenario",
    embedUrl: "https://www.youtube-nocookie.com/embed/ZTyWOhF7Pto",
    watchUrl: "https://www.youtube.com/watch?v=ZTyWOhF7Pto",
    status: "Published",
    claim:
      "Illustrates a possible mechanism. It is not evidence of a real campaign, authentic exposure, behaviour change, or electoral effect.",
  },
  {
    id: "brazil-2026",
    title: "Brazil 2026: the final-hour voice",
    subtitle: "Recife · WhatsApp · synthetic scenario",
    description:
      "A fictional voter receives cloned audio twenty-four hours before an election. The scenario then scales the attempted distribution to show the difference between capability, deployment, individual response, and an unmeasured aggregate consequence.",
    duration: "Approx. 58 seconds",
    type: "Synthetic scenario",
    embedUrl: null,
    watchUrl: null,
    status: "Master retained · durable public host pending",
    claim:
      "The narrative is illustrative. The programme does not establish that the depicted campaign occurred or that the stated response generalises to real voters.",
  },
] as const;

export const outputs = [
  {
    id: "flagship",
    type: "Flagship working paper",
    title: "Harmful Manipulation and Election Security",
    subtitle: "The Capability–Deployment–Effect Gap",
    description:
      "Programme-level synthesis connecting operational precursors, capability measurement, election evidence, and policy intervention without collapsing their claim ceilings.",
    href: "paper/",
    status: "Current web working edition",
    date: "Evidence freeze · 28 August 2026",
  },
  {
    id: "brief",
    type: "One-page brief",
    title: "The next Cambridge Analytica will be a system",
    subtitle: "A compact explanation of the CDE Gap",
    description:
      "The programme argument, four evidence questions, findings, decision rule, and priority controls in a concise briefing format.",
    href: "outputs/#one-page-brief",
    status: "Latest working version",
    date: "August 2026",
  },
  {
    id: "poster",
    type: "Research poster",
    title: "The evidence rift",
    subtitle: "Stronger upstream evidence, weaker downstream evidence",
    description:
      "A visual synthesis of the CDE topology, the four research parts, policy mismatch, and the conditional pathway to loss of democratic self-correction.",
    href: "outputs/#research-poster",
    status: "Provisional web preview",
    date: "August 2026",
  },
  {
    id: "white-paper",
    type: "White paper",
    title: "The Persuasion Machines",
    subtitle: "Frontier AI, persuasion, and harmful manipulation",
    description:
      "A more accessible adjacent synthesis of the evidence, threat model, and governance agenda for policy and general audiences.",
    href: "outputs/#white-paper",
    status: "Tenth edition · working",
    date: "27 August 2026",
  },
  {
    id: "registry",
    type: "Evaluation artifact",
    title: "Frontier Evaluation Registry",
    subtitle: "Part II · benchmark-native outcomes",
    description:
      "A source-linked release map that keeps attempted persuasion, deception, simulated campaign performance, and safety responses separate.",
    href: "research/part-ii/",
    status: "Public draft",
    date: "2022–2026 releases",
  },
  {
    id: "election-index",
    type: "Dataset",
    title: "AI, Elections and Agency Transfer Evidence Index",
    subtitle: "Part III · claim-level field evidence",
    description:
      "A purposive evidence corpus separating occurrence, mechanism, attribution, distribution, exposure, human effect, electoral effect, and institutional response.",
    href: "https://huggingface.co/datasets/apol/ai-election-manipulation-cases",
    status: "Public release v0.4.4",
    date: "Research cutoff · 12 August 2026",
    external: true,
  },
  {
    id: "policy-atlas",
    type: "Dataset",
    title: "Agency Transfer Policy Atlas",
    subtitle: "Part IV · intervention evidence",
    description:
      "A causal map of control families, concrete implementations, legal authority, mechanism evidence, effect evidence, rights risks, maturity, and research gaps.",
    href: "https://huggingface.co/datasets/apol/agency-transfer-policy-atlas",
    status: "Public beta v0.1.0-beta.2",
    date: "Source-integrated register v0.3.1",
    external: true,
  },
  {
    id: "lab",
    type: "Research tool",
    title: "Agency Transfer Lab",
    subtitle: "Part I · evidence-harness prototype",
    description:
      "A deterministic research harness for control semantics, replay, persistence, migration, export integrity, and tamper detection.",
    href: "https://agency-transfer-lab.miguelguerrero.eu",
    status: "Public prototype",
    date: "Working artifact",
    external: true,
  },
] as const;

export const programmeUpdates = [
  {
    date: "28 Aug 2026",
    title: "Source integration and regulatory baseline",
    body: "Integrated the current flagship sources, the General-Purpose AI Code of Practice harmful-manipulation baseline, and revised claim ceilings across the paper, literature map, and policy register.",
  },
  {
    date: "28 Aug 2026",
    title: "Programme publication architecture",
    body: "Reframed the public project around one maintained research programme. The existing benchmark becomes Part II rather than the identity of the whole site.",
  },
  {
    date: "27 Aug 2026",
    title: "Part I evidence units reconciled",
    body: "Separated the ten-objective paired pilot, three protocol-generating probes, and the five-request forensic subset. The units may overlap and are not added.",
  },
  {
    date: "26 Aug 2026",
    title: "Part II recovery and non-confirmatory result",
    body: "Recovered 3,360 finalised APE-120 records. The 87.4% complete-case attempt rate remains descriptive; no served condition reached the prespecified confirmatory gate.",
  },
] as const;
