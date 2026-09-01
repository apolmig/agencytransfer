import { ELECTION_INDEX_URL, POLICY_ATLAS_URL, REPOSITORY_URL, DraftBoundary, PageLead, TextLink } from "./EditorialShell";
import { EditorialRiftVisual } from "./EditorialVisuals";
import comparativeJson from "../../policy-atlas/data/comparative-v0.4/groups.json";

type ComparativeGroup = {
  group_id: string;
  implementation_count: number;
  label: string;
  illustrative_controls: string;
  recommended_posture: string;
  claim_ceiling: string;
};
const comparative = comparativeJson as { groups: ComparativeGroup[] };

export function PartIIIPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Part III · Field evidence" title="Evidence thins downstream" deck="Investigations can often identify accounts, calls, posts, payments, synthetic media, removals, and institutional responses. They rarely identify authentic exposure, prior belief, durable response, or the aggregate counterfactual.">
        <DraftBoundary>No prevalence estimate, causal zero-effect claim, durable agency-transfer estimate, or an AI-attributable national-election outcome.</DraftBoundary>
      </PageLead>
      <div className="v2-wide-figure"><EditorialRiftVisual /><p className="v2-figure-caption">“No identified effect” is not “zero effect.” Every bridge—from delivery to authentic exposure, attention, belief, choice, and electoral consequence—requires new evidence.</p></div>
      <section className="v2-evidence-pair">
        <article><p className="v2-eyebrow">Usually documented</p><h2>Operations and institutional response</h2><ul><li>Occurrence and mechanism</li><li>Some attribution evidence</li><li>Distribution events or proxies</li><li>Removals, enforcement, or judicial response</li></ul></article>
        <article><p className="v2-eyebrow">Usually unresolved</p><h2>Authentic exposure and effect</h2><ul><li>Unique people reached</li><li>Attention and processing</li><li>Durable belief or behavioural change</li><li>Aggregate electoral consequence</li></ul></article>
      </section>
      <section className="v2-data-strip"><div><p>Current analytic layer</p><strong>10 claim-coded records · 8 eligible for incident counting</strong><span>The broader catalogue is not a count of confirmed manipulation campaigns.</span></div><TextLink href={ELECTION_INDEX_URL} external>Open the Evidence Index</TextLink></section>
    </main>
  );
}

export function PartIVPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Part IV · Policy evidence · beta.3" title="Recommend by support, not by a list of winners" deck="The Atlas groups all 118 implementations into six provisional policy postures. The original six re-audited claims were an audit sample, not six effective policies. Comparative recommendations remain useful when their evidence limits are visible.">
        <DraftBoundary>118 classified is not 118 empirically verified. This release adds no claim-source adjudications: the reproducible core retains six checked effect claims, with one established bounded component effect, three strong inferences and two open questions at implementation level.</DraftBoundary>
      </PageLead>
      <section className="v2-metrics-line" aria-label="Policy Atlas scope"><div><strong>118</strong><span>implementations classified</span></div><div><strong>{comparative.groups.length}</strong><span>provisional recommendation postures</span></div><div><strong>6</strong><span>effect claims with checked empirical sources</span></div></section>
      <section className="v2-three-column">
        {comparative.groups.map((group) => (
          <article key={group.group_id}>
            <p className="v2-eyebrow">{group.group_id} · {group.implementation_count} implementations</p>
            <h2>{group.label}</h2>
            <p>{group.illustrative_controls}</p>
            <p>{group.recommended_posture}</p>
            <small>{group.group_id === "A" ? "Provisional prioritization, not five proven policies. Support differs: the retained forwarding-limit review remains an open question. No durable agency-preservation or electoral-effect claim is established." : group.claim_ceiling}</small>
          </article>
        ))}
      </section>
      <section className="v2-simple-section"><div className="v2-section-lead"><div><p className="v2-eyebrow">How to read the comparison</p><h2>Policy posture and evidence grade are different</h2></div><p>The groups combine causal fit, maturity and evidence relevance. They are not an ordinal ranking of efficacy or democratic importance. A control in E may be more structurally important than one in A.</p></div><p>The remaining 112 effect claims lack a checked empirical relation in the released core. This is a verification gap, not a finding that no relevant literature exists or that those controls fail. Group membership never overrides the source-specific endpoint and verification status.</p></section>
      <section className="v2-principles"><p className="v2-eyebrow">Decision rule</p><div>{["Node-specific", "Layered", "Lawful", "Reversible", "Monitored", "Contestable"].map((item) => <span key={item}>{item}</span>)}</div><p>Prioritize bounded controls, build control infrastructure, enforce applicable baselines, use authenticity tools for their vectors, pilot structural safeguards and validate general triggers. Measure who gains control and whether affected people can understand, refuse, contest and exit.</p></section>
      <section className="v2-data-strip"><div><p>Comparative synthesis · 1 September 2026</p><strong>One source for the web and the dataset</strong><span>All 118 assignments are now published in CSV and Parquet. Existing empirical grades are unchanged.</span></div><TextLink href={`${REPOSITORY_URL}/blob/main/policy-atlas/COMPARATIVE_EVIDENCE_GROUPS.md`} external>Read the grouping</TextLink></section>
      <section className="v2-data-strip"><div><p>Public research preview · v0.1.0-beta.3</p><strong>Agency Transfer Policy Atlas</strong><span>Classification coverage is separate from verification coverage.</span></div><TextLink href={POLICY_ATLAS_URL} external>Open the Policy Atlas</TextLink></section>
    </main>
  );
}
