import { ELECTION_INDEX_URL, POLICY_ATLAS_URL, DraftBoundary, PageLead, TextLink } from "./EditorialShell";
import { EditorialRiftVisual } from "./EditorialVisuals";

export function PartIIIPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Part III · Field evidence" title="Evidence thins downstream" deck="Investigations can often identify accounts, calls, posts, payments, synthetic media, removals, and institutional responses. They rarely identify authentic exposure, prior belief, durable response, or the aggregate counterfactual.">
        <DraftBoundary>No prevalence estimate, causal zero-effect claim, durable agency-transfer estimate, or AI-attributable national-election outcome.</DraftBoundary>
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
      <PageLead eyebrow="Part IV · Policy evidence" title="Adoption is not effectiveness" deck="A plausible mechanism can become a proposal, a rule, and an implementation without new evidence at each transition. The Policy Atlas maps those transitions rather than turning them into a leaderboard.">
        <DraftBoundary>No universal ranking of interventions and no inference from legal existence to democratic effectiveness.</DraftBoundary>
      </PageLead>
      <section className="v2-metrics-line" aria-label="Policy Atlas scope"><div><strong>68</strong><span>control families</span></div><div><strong>118</strong><span>implementations</span></div><div><strong>6</strong><span>bounded component-effect records currently coded as established</span></div></section>
      <section className="v2-three-column">
        <article><p className="v2-eyebrow">Locate</p><h2>Measure the nearest node</h2><p>Caller authentication should first be tested against spoofed-call delivery. Logging should first be tested against record completeness and independent reproduction.</p></article>
        <article><p className="v2-eyebrow">Preserve</p><h2>Keep the next claim testable</h2><p>Route identity, delivery denominators, interruption history, evidence custody, appeal, restoration, and missingness should survive long enough for qualified review.</p></article>
        <article><p className="v2-eyebrow">Bound</p><h2>Stop where the evidence stops</h2><p>A change in immediate belief, consent behaviour, recognition, or downloadable data does not by itself establish autonomy, turnout, resilience, or election integrity.</p></article>
      </section>
      <section className="v2-principles"><p className="v2-eyebrow">Design test</p><div>{["Identifiable", "Divided", "Auditable", "Interruptible", "Reversible", "Contestable"].map((item) => <span key={item}>{item}</span>)}</div><p>These are governance objectives, not findings that one design has proved effective.</p></section>
      <section className="v2-data-strip"><div><p>Public beta dataset</p><strong>Agency Transfer Policy Atlas</strong><span>Causal mapping, responsibility allocation, and research triage—not a policy ranking.</span></div><TextLink href={POLICY_ATLAS_URL} external>Open the Policy Atlas</TextLink></section>
    </main>
  );
}
