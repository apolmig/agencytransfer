import { POLICY_ATLAS_URL, REPOSITORY_URL, DraftBoundary, PageLead, TextLink, route } from "./EditorialShell";
import reviewJson from "../../policy-atlas/review/source-linked-20260901/review.json";
import "./policy-review.css";

const reviewBase = `${REPOSITORY_URL}/blob/main/policy-atlas/review/source-linked-20260901`;
type Review = {
  sources: { id: string; title: string; url: string; review_depth: string }[];
  coverage: { implementations: number; selected_source_records: number };
  new_substantive_checks: string[];
  evidence_modes: Record<"H" | "T" | "O" | "A" | "N", number>;
};
const review = reviewJson as Review;
const sources = new Map(review.sources.map((source) => [source.id, source]));

function Sources({ ids }: { ids: string[] }) {
  return <p className="p4-source-links">Sources recorded in the review: {ids.map((id, index) => {
    const source = sources.get(id);
    if (!source) throw new Error(`Unknown P4 source ${id}`);
    return <span key={id}>{index ? " · " : ""}<a href={source.url} target="_blank" rel="noreferrer" title={`${source.title}. Review depth: ${source.review_depth}`}>{id}</a></span>;
  })}</p>;
}

const portfolios = [
  {
    title: "Bounded human-facing controls",
    action: "Remove coercive choice architecture. Test accuracy prompts, factual corrections and technique education as separate treatments.",
    boundary: "Human-component evidence exists, but benefits differ by setting and outcome. A tested interface is not proof that a regulatory ban or nationwide programme works.",
    refs: ["R001", "R002", "R006", "R009", "R011", "R014"],
  },
  {
    title: "Enforced authority boundaries",
    action: "Limit tools, recipients and actions outside the model. Make permissions revocable and human approval meaningful.",
    boundary: "Technical protection depends on the threat model and the trusted principal. Preventing an outsider from hijacking an agent does not prevent its operator from pursuing a harmful goal.",
    refs: ["R037", "R051"],
  },
  {
    title: "Frontier-specific defensive pilots",
    action: "Independently replicate conversational monitors. Test conflicting incentives, memory, dependence and the user's own goals over time.",
    boundary: "The most directly relevant new human results are limited or preprint evidence. They justify replication, not a general mandate.",
    refs: ["R039", "R040", "R041", "R042"],
  },
  {
    title: "Accountability and structural safeguards",
    action: "Enable independent inspection, usable exit, retained public capability, plural access and practical remedies.",
    boundary: "Adjacent evidence and institutional reasoning support evaluation and proportionate action. Exporting data is not proof of successful switching or retained agency.",
    refs: ["R033", "R034", "R035", "R050", "R051"],
  },
];

const findings = [
  {
    title: "Awareness, resistance and agency are different outcomes",
    finding: "Warning labels can change perceptions of an assistant without reliably changing its influence. In AI Watchdog, a dismissible, just-in-time intervention reduced AI-steered choices on a preregistered secondary outcome; the primary detection outcome did not improve. The separate-wave sponsorship comparison is not an unqualified causal estimate of disclosure efficacy.",
    implication: "Keep disclosure for notice and accountability. Measure understanding, goal-consistent decisions, refusal and contestability separately. A defensive monitor can become a second source of steering.",
    refs: ["R039", "R040", "R041"],
  },
  {
    title: "Friction is not one treatment",
    finding: "Twitter's retweet friction reduced news sharing without selectively reducing low-factualness material. Accuracy prompts target a different mechanism and have bounded sharing-quality evidence. The selected WhatsApp simulation and label audit do not identify the exact forwarding cap's field effect.",
    implication: "Do not put all friction in a best-supported set. Test truthful information, legitimate participation, delays and displacement as well as harmful diffusion. Reanalyses of the same observations are not independent replications.",
    refs: ["R003", "R004", "R005", "R006", "R007", "R008"],
  },
  {
    title: "An effective correction must arrive in time",
    finding: "Community Notes estimates after a note appears, across a post's lifetime and across a rollout answer different questions. A strong effect on treated posts can coexist with weak coverage or late delivery. Factual correction is also a different treatment from an AI-origin label. Tested LLM fact checks did not improve average discernment, with harmful responses to some wrong or uncertain outputs; the human comparator was collected later and voluntary viewing was selected.",
    implication: "Measure reach, timeliness, correctness and subsequent response separately. Do not turn an engagement effect into an electoral claim. The source ledger records the 2026 competing-interest correction to R009.",
    refs: ["R009", "R010", "R016", "R017", "R018"],
  },
  {
    title: "Protecting the agent is not necessarily protecting the citizen",
    finding: "CaMeL supports enforced control and data-flow boundaries under a defined prompt-injection threat model. It treats the initiating query as trusted and leaves some text-only influence outside scope. A secure agent can still faithfully pursue a harmful authorised objective.",
    implication: "Ask whose authority is bounded. Test outside attacks, unauthorised actions and concealed authorised steering separately. An operator-editable guard cannot by itself protect people against that operator.",
    refs: ["R037"],
  },
  {
    title: "Exit must work after a relationship has accumulated",
    finding: "Portability research distinguishes getting an archive from actually switching services. Applying this to persistent assistants is an inference: can people or institutions continue the task with another provider, without losing essential context or control? Offline recommendation studies and voluntary-use associations do not establish that memory caps restore autonomy.",
    implication: "Test task continuity, transferred permissions, privacy costs and retained institutional expertise. Treat usable switching and public capability as structural priorities, not demonstrated effect sizes.",
    refs: ["R030", "R033", "R034", "R035", "R042"],
  },
  {
    title: "Technique education needs an accuracy and transfer test",
    finding: "Recognising a taught manipulation technique is not the same as distinguishing true from false claims. The reviewed findings vary across techniques, topics and sharing outcomes; one combination of inoculation and accuracy prompting performed differently from inoculation alone.",
    implication: "Include truthful emotional content, unfamiliar techniques, real sharing and delayed follow-up. Indiscriminate distrust is a possible cost, not recovered agency.",
    refs: ["R011", "R012", "R013", "R014"],
  },
];

export function PartIVPage() {
  const coverage = review.coverage;
  return (
    <main id="main-content" className="v2-main p4-review">
      <PageLead eyebrow="Part IV · Policy interventions · Working draft" title="What works—and for whom?" deck="Democracies do have tools. The problem is crediting them with outcomes they were not tested to deliver. Compare which control changes which decision, under whose authority, and with what benefit to the affected person.">
        <p className="p4-scope">1 September 2026 · {coverage.implementations} implementations annotated · {coverage.selected_source_records} selected source records</p>
        <DraftBoundary>Source-linked assessment, not 118 empirically verified policies. Evidence supports specific human and technical outcomes, not end-to-end electoral protection or durable preservation of agency.</DraftBoundary>
      </PageLead>

      <section className="p4-section" aria-labelledby="p4-recommendations">
        <p className="v2-eyebrow">Revised recommendations</p>
        <h2 id="p4-recommendations">Four uses, not a ranking of winners</h2>
        <div className="p4-portfolios">
          {portfolios.map((item) => <article key={item.title}>
            <h3>{item.title}</h3><p>{item.action}</p><p className="p4-boundary">{item.boundary}</p><Sources ids={item.refs} />
          </article>)}
        </div>
        <p className="p4-note">Provenance, detection and notices remain useful for their specific purposes. Applicable legal duties still apply; this research does not replace a current, jurisdiction-specific legal assessment.</p>
      </section>

      <section className="p4-section" aria-labelledby="p4-findings">
        <p className="v2-eyebrow">What the deeper review changes</p>
        <h2 id="p4-findings">Different outcomes require different evidence</h2>
        <div className="p4-findings">
          {findings.map((item) => <details key={item.title}>
            <summary>{item.title}</summary><div><p>{item.finding}</p><p><strong>Implication.</strong> {item.implication}</p><Sources ids={item.refs} /></div>
          </details>)}
        </div>
      </section>

      <section className="p4-section p4-reading" aria-labelledby="p4-agency">
        <p className="v2-eyebrow">Agency transfer</p>
        <h2 id="p4-agency">A safeguard can concentrate power too</h2>
        <p><strong>Strong inference.</strong> When one actor controls the influential assistant and the monitor or evidence used to validate it, oversight can reproduce the same dependency. Independence has to work in practice, not just appear in a policy.</p>
        <p><strong>Plausible hypothesis.</strong> User-controlled defensive interfaces, enforceable authority limits and viable exit may protect agency better than disclosure alone. Their combined effect is untested.</p>
        <p><strong>Open question.</strong> Do these controls preserve people's ability to understand, direct, refuse and contest persistent AI influence? Reduced agreement with an assistant is not enough to answer that question.</p>
      </section>

      <section className="p4-section p4-reading" aria-labelledby="p4-record">
        <p className="v2-eyebrow">Research record</p>
        <h2 id="p4-record">The assessment behind this page</h2>
        <p>The review covers all {coverage.implementations} existing records. The {coverage.selected_source_records} sources include empirical studies, technical work and institutional material—not 69 independent efficacy trials. Three candidates—accuracy prompts, timely factual corrections and independent conversational monitors—remain separate from the 118-row denominator.</p>
        <div className="p4-resource-links">
          <TextLink href={`${reviewBase}/findings.md`} external>Read the full findings</TextLink>
          <TextLink href={`${reviewBase}/implementation-dossiers.md`} external>Read the 118 dossiers and source ledger</TextLink>
          <TextLink href={route("research/p4-source-linked-review-20260901.xlsx")}>Download the review workbook</TextLink>
        </div>
        <details className="p4-methods">
          <summary>Review depth, evidence modes and version boundaries</summary>
          <p>Eight new substantive checks: {review.new_substantive_checks.join(", ")}. Other depths include primary abstracts, publication summaries and official text; six earlier adjudications are retained. This is single-pass and purposive, not independent double screening, full-text review of every source or reproduction of all data.</p>
          <p>Closest evidence modes: human component (H, {review.evidence_modes.H}); technical component (T, {review.evidence_modes.T}); implementation or quasi-experimental (O, {review.evidence_modes.O}); adjacent (A, {review.evidence_modes.A}); normative, design or measurement (N, {review.evidence_modes.N}). These are not ordered evidence grades or counts of successful policies. Source matches can be direct, partial, adjacent, normative or untested.</p>
          <p>The previous A–F groups are historical metadata. This review's recommendations supersede them for the current presentation. The published Atlas beta.3 and its empirical claim-check flags remain unchanged; this companion does not silently promote its six retained adjudications. The v1.3 manuscript integrates this review. Parts I–III retain their 28 August evidence freeze; P4 is dated 1 September. External study results are not new fellowship experiments.</p>
          <TextLink href={POLICY_ATLAS_URL} external>Open the published Atlas · beta.3</TextLink>
        </details>
      </section>
      <p className="v2-draft-line"><strong>Working draft.</strong> This page condenses the 1 September source-linked review. Examples in the supporting dossiers are hypothetical; no live voter intervention was conducted.</p>
    </main>
  );
}
